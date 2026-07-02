#!/usr/bin/env python3
"""Cadence gates: is it currently OK to post on a channel?

Three gates: WINDOW (right time-of-day), CAP (under daily limit), SPACING (enough
time since last post). Each returns (ok: bool, reason: str).

Modeled on booked-job/scripts/publisher.py windows/ramp/spacing logic (lines 24-80).
Config-driven here instead of hardcoded.
"""
import datetime as dt
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _now_local(tz_name="America/Chicago"):
    """Return timezone-aware 'now' in the tenant tz. Uses zoneinfo (stdlib 3.9+)."""
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo(tz_name))
    except Exception:
        # Fallback: naive local time. In CI we set TZ env, so this is fine.
        return dt.datetime.now()


def window_ok(channel_cfg, now=None, tz="America/Chicago"):
    """OK if current local hour is inside any configured window and (if weekdays_only) it's a weekday."""
    now = now or _now_local(tz)
    if channel_cfg.get("weekdays_only") and now.weekday() >= 5:
        return (False, "weekend_skip")
    hour = now.hour
    for start, end in channel_cfg.get("windows", []):
        if start <= hour < end:
            return (True, f"window {start}-{end}")
    return (False, f"outside_windows hour={hour}")


def cap_ok(channel_cfg, state, now=None, tz="America/Chicago"):
    """OK if today's post count is under daily_cap."""
    now = now or _now_local(tz)
    today = now.strftime("%Y-%m-%d")
    n = state.get("by_date", {}).get(today, 0)
    cap = channel_cfg.get("daily_cap", 1)
    if n >= cap:
        return (False, f"cap_hit today={n} cap={cap}")
    return (True, f"cap_room today={n} cap={cap}")


def spacing_ok(channel_cfg, state, now=None, tz="America/Chicago"):
    """OK if enough hours since last post on this channel."""
    now = now or _now_local(tz)
    last_iso = state.get("last_iso")
    if not last_iso:
        return (True, "no_prior")
    try:
        # Parse; strip tz for safe comparison
        last = dt.datetime.fromisoformat(last_iso.replace("Z", "+00:00"))
        if last.tzinfo is None:
            # Assume local (America/Chicago) if naive
            try:
                from zoneinfo import ZoneInfo
                last = last.replace(tzinfo=ZoneInfo(tz))
            except Exception:
                pass
        # Normalize to same-tz for compare
        if now.tzinfo is None or last.tzinfo is None:
            delta = now.replace(tzinfo=None) - last.replace(tzinfo=None)
        else:
            delta = now - last
    except Exception:
        return (True, "unparseable_last_iso")
    hours = delta.total_seconds() / 3600
    min_spacing = channel_cfg.get("min_spacing_hours", 0)
    if hours < min_spacing:
        return (False, f"spacing_too_close {hours:.1f}h < {min_spacing}h")
    return (True, f"spacing_ok {hours:.1f}h")


def all_gates(channel_cfg, state, now=None, tz="America/Chicago"):
    """Run all three gates; return (ok: bool, reasons: [str]). ok = all-must-pass."""
    now = now or _now_local(tz)
    reasons = []
    for name, fn in [("window", window_ok), ("cap", cap_ok), ("spacing", spacing_ok)]:
        ok, why = fn(channel_cfg, state, now, tz) if name != "window" else fn(channel_cfg, now, tz)
        reasons.append(f"{name}:{'ok' if ok else 'blocked'}({why})")
        if not ok:
            return (False, reasons)
    return (True, reasons)


# -------- CLI test harness --------
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", help="Channel key (linkedin|x). Prints all gates against synthetic state.")
    args = ap.parse_args()

    if args.check:
        import yaml
        cfg_path = os.path.join(os.path.dirname(HERE), "config.yaml")
        cfg = yaml.safe_load(open(cfg_path))
        ch = cfg["channels"][args.check]
        tz = cfg["tenant"]["timezone"]
        # Synthetic empty state
        state = {"posted_ids": [], "by_date": {}, "last_iso": None}
        ok, reasons = all_gates(ch, state, tz=tz)
        print(f"channel={args.check} ok={ok}")
        for r in reasons:
            print(f"  {r}")
    else:
        ap.print_help()
