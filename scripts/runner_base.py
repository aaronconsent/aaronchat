#!/usr/bin/env python3
"""Shared drip-runner logic. Each channel's *_runner.py is a thin wrapper.

Drip loop (booked-job pattern from scripts/publisher.py):
  1. Load config + state + queue
  2. Run cadence gates (window / cap / spacing)
  3. Pick next unposted item matching this channel's platform
  4. Publish via the channel's publisher module
  5. On success: append to posted_ids, bump by_date, set last_iso, save state
  6. Always log the result
"""
import argparse
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

import cadence


def _now_iso(tz="America/Chicago"):
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo(tz)).isoformat(timespec="seconds")
    except Exception:
        return dt.datetime.now().isoformat(timespec="seconds")


def _now_date(tz="America/Chicago"):
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo(tz)).strftime("%Y-%m-%d")
    except Exception:
        return dt.datetime.now().strftime("%Y-%m-%d")


def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def log(cfg, msg):
    log_path = os.path.join(ROOT, cfg.get("runtime", {}).get("log_file", "content/run_all.log"))
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {msg}"
    print(line)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a") as f:
        f.write(line + "\n")


EMPTY_MODE_STATE = {"posted_ids": [], "by_date": {}, "last_iso": None}


def _mode_state(state, mode):
    """Return (and create) the per-mode sub-state dict."""
    modes = state.setdefault("modes", {})
    if mode not in modes:
        modes[mode] = dict(EMPTY_MODE_STATE)
    return modes[mode]


def _migrate_state_shape(state):
    """One-shot upgrade: legacy flat state → nested {modes: {audience: ...}}.
    Safe to call repeatedly."""
    if "modes" in state:
        return state
    legacy_ids = state.get("posted_ids")
    if legacy_ids is None:
        return {"modes": {}}
    return {"modes": {"audience": {
        "posted_ids": legacy_ids,
        "by_date": state.get("by_date", {}),
        "last_iso": state.get("last_iso"),
    }}}


def pick_next(queue, state, platform, mode):
    """First item whose (platform, mode) matches AND id is not in posted_ids for this mode."""
    posted = set(state.get("posted_ids", []))
    for it in queue.get("items", []):
        if it.get("platform") != platform:
            continue
        item_mode = it.get("mode") or "audience"
        if item_mode != mode:
            continue
        if it.get("id") in posted:
            continue
        return it
    return None


def mark_posted(state, item, tz):
    posted = state.setdefault("posted_ids", [])
    posted.append(item["id"])
    today = _now_date(tz)
    by_date = state.setdefault("by_date", {})
    by_date[today] = by_date.get(today, 0) + 1
    state["last_iso"] = _now_iso(tz)
    return state


def _resolve_modes(ch):
    """Return an ordered list of (mode_name, mode_cfg) from a channel config.
    Falls back to a synthesized 'audience' mode from top-level fields for any
    channel not yet migrated to the modes: block."""
    modes_cfg = ch.get("modes")
    if not modes_cfg:
        return [("audience", {
            "enabled": True,
            "daily_cap": ch.get("daily_cap", 1),
            "windows": ch.get("windows", []),
            "weekdays_only": ch.get("weekdays_only", False),
            "min_spacing_hours": ch.get("min_spacing_hours", 0),
        })]
    # Deterministic order: credibility first (slower burn, higher priority signal),
    # then audience.
    order = [m for m in ("credibility", "audience") if m in modes_cfg]
    order += [m for m in modes_cfg if m not in order]
    return [(m, modes_cfg[m]) for m in order]


def run(channel_key, publisher_module, args=None):
    """Drip loop for one channel. Iterates enabled modes independently.

    Each mode has its own cadence gates and posted-id set. One publish
    attempt per mode per tick — modes never share a slot.
    """
    args = args or argparse.Namespace(dry_run=False, force=False)

    import yaml
    cfg_path = os.path.join(ROOT, "config.yaml")
    cfg = yaml.safe_load(open(cfg_path))
    channels_cfg = cfg.get("channels", {})
    ch = channels_cfg.get(channel_key)
    if not ch:
        log(cfg, f"{channel_key}: no channel_config entry")
        return 1
    if not ch.get("enabled"):
        log(cfg, f"{channel_key}: disabled in config")
        return 0

    tz = cfg["tenant"]["timezone"]
    state_path = os.path.join(ROOT, cfg["runtime"]["state_dir"], f"{channel_key}_state.json")
    state = _migrate_state_shape(load_json(state_path, {"modes": {}}))

    queue_path = os.path.join(ROOT, cfg["runtime"]["queue_file"])
    queue = load_json(queue_path, {"items": []})

    overall_rc = 0
    any_action = False
    for mode_name, mode_cfg in _resolve_modes(ch):
        if not mode_cfg.get("enabled", True):
            continue
        mode_state = _mode_state(state, mode_name)

        # Gate check per mode
        if not args.force:
            ok, reasons = cadence.all_gates(mode_cfg, mode_state, tz=tz)
            if not ok:
                log(cfg, f"{channel_key}[{mode_name}]: gated. {' | '.join(reasons)}")
                continue

        item = pick_next(queue, mode_state, channel_key, mode_name)
        if not item:
            log(cfg, f"{channel_key}[{mode_name}]: no unposted items")
            continue

        any_action = True
        if args.dry_run:
            log(cfg, f"{channel_key}[{mode_name}]: DRY-RUN would post id={item['id']} len={len(item.get('text',''))} chars")
            continue

        result = publisher_module.post(item, ch)
        if result.ok:
            _mode_state(state, mode_name)  # ensure exists
            state["modes"][mode_name] = mark_posted(mode_state, item, tz)
            save_json(state_path, state)
            log(cfg, f"{channel_key}[{mode_name}]: POSTED id={item['id']} via {result.backend} ({result.detail})")
        else:
            log(cfg, f"{channel_key}[{mode_name}]: FAILED id={item['id']} backend={result.backend} detail={result.detail}")
            overall_rc = 2
    if not any_action:
        return 0
    return overall_rc


def add_args(ap):
    ap.add_argument("--force", action="store_true", help="Bypass window/cap/spacing gates")
    ap.add_argument("--dry-run", action="store_true", help="Show what would post; publish nothing")
    return ap
