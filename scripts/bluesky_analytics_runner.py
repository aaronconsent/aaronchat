#!/usr/bin/env python3
"""Nightly Bluesky analytics — engagement snapshot + competitor rollup.

Reads competitors from content/bluesky_competitors.yaml (list of handles).
Called by GitHub Actions on the nightly cron.

Outputs (appended, one row per run):
    content/analytics/bluesky/own_posts.jsonl
    content/analytics/bluesky/competitors.jsonl
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import yaml

from bluesky.client import get_client
from bluesky import analytics


COMPETITORS_CFG = os.path.join(os.path.dirname(HERE), "content", "bluesky_competitors.yaml")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--lookback-days", type=int, default=30)
    args = ap.parse_args()

    handles = []
    if os.path.exists(COMPETITORS_CFG):
        with open(COMPETITORS_CFG) as f:
            cfg = yaml.safe_load(f) or {}
        handles = cfg.get("handles", [])

    client = get_client()

    own = analytics.snapshot_own_posts(client, lookback_days=args.lookback_days, dry_run=args.dry_run)
    print(f"[analytics] own_posts: {len(own)} rows{' (dry)' if args.dry_run else ''}")

    if handles:
        comp = analytics.snapshot_competitors(client, handles, dry_run=args.dry_run)
        print(f"[analytics] competitors: {len(comp)} rows{' (dry)' if args.dry_run else ''}")
    else:
        print(f"[analytics] no competitors configured (add handles to {COMPETITORS_CFG})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
