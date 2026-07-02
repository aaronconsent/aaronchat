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


def pick_next(queue, state, platform):
    """First item whose platform matches AND id is not in posted_ids."""
    posted = set(state.get("posted_ids", []))
    for it in queue.get("items", []):
        if it.get("platform") == platform and it.get("id") not in posted:
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


def run(channel_key, publisher_module, args=None):
    """Drip loop for one channel. `publisher_module` must expose `post(item, channel_cfg) → PublishResult`."""
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
    state = load_json(state_path, {"posted_ids": [], "by_date": {}, "last_iso": None})

    # Gate check (skip if --force)
    if not args.force:
        ok, reasons = cadence.all_gates(ch, state, tz=tz)
        if not ok:
            log(cfg, f"{channel_key}: gated. {' | '.join(reasons)}")
            return 0

    queue_path = os.path.join(ROOT, cfg["runtime"]["queue_file"])
    queue = load_json(queue_path, {"items": []})
    item = pick_next(queue, state, channel_key)
    if not item:
        log(cfg, f"{channel_key}: no unposted items in queue")
        return 0

    if args.dry_run:
        log(cfg, f"{channel_key}: DRY-RUN would post id={item['id']} len={len(item['text'])} chars")
        return 0

    result = publisher_module.post(item, ch)
    if result.ok:
        state = mark_posted(state, item, tz)
        save_json(state_path, state)
        log(cfg, f"{channel_key}: POSTED id={item['id']} via {result.backend} ({result.detail})")
        return 0
    else:
        log(cfg, f"{channel_key}: FAILED id={item['id']} backend={result.backend} detail={result.detail}")
        return 2


def add_args(ap):
    ap.add_argument("--force", action="store_true", help="Bypass window/cap/spacing gates")
    ap.add_argument("--dry-run", action="store_true", help="Show what would post; publish nothing")
    return ap
