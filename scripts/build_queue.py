#!/usr/bin/env python3
"""Offline queue builder. Reads site pages via PageAdapter, produces
content/queue.json for the runtime runners to consume.

Idempotent — deterministic SHA256 IDs mean re-running just refreshes the queue;
already-posted items (present in *_state.json) are still listed but runners skip
them via id lookup.

usage:
  python3 scripts/build_queue.py            # write content/queue.json
  python3 scripts/build_queue.py --dry-run  # print stats, write nothing
  python3 scripts/build_queue.py --stats    # summarize existing queue
"""
import argparse
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

import page_adapter


def build(cfg, voice):
    items = []
    v_ver = voice.get("version", "0.0")
    skipped_no_pm = 0
    for path in page_adapter.find_pages(cfg):
        page = page_adapter.extract(path)
        if not page:
            skipped_no_pm += 1
            continue
        for platform, i, text in page_adapter.variants_for(page, cfg, voice):
            items.append(page_adapter.make_item(page, platform, i, text, v_ver))
    return items, skipped_no_pm


def summarize(items):
    """Return {'total': N, 'per_platform': {...}, 'unique_pages': N}."""
    per = {}
    urls = set()
    for it in items:
        per[it["platform"]] = per.get(it["platform"], 0) + 1
        urls.add(it["page_url"])
    return {"total": len(items), "per_platform": per, "unique_pages": len(urls)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Print stats, don't write queue.json")
    ap.add_argument("--stats", action="store_true", help="Summarize existing queue.json")
    args = ap.parse_args()

    import yaml
    cfg = yaml.safe_load(open(os.path.join(ROOT, "config.yaml")))
    voice = yaml.safe_load(open(os.path.join(ROOT, cfg["voice_ref"])))

    queue_path = os.path.join(ROOT, cfg.get("runtime", {}).get("queue_file", "content/queue.json"))

    if args.stats:
        if not os.path.exists(queue_path):
            print(f"{queue_path}: not yet created. Run without --stats to build.")
            sys.exit(0)
        q = json.load(open(queue_path))
        s = summarize(q.get("items", []))
        print(json.dumps(s, indent=2))
        sys.exit(0)

    items, skipped = build(cfg, voice)
    s = summarize(items)
    print(f"Built {s['total']} items across {len(s['per_platform'])} platforms from {s['unique_pages']} pages.")
    for platform, n in sorted(s["per_platform"].items()):
        print(f"  {platform}: {n}")
    if skipped:
        print(f"Skipped {skipped} pages (no pm-page block).")

    if args.dry_run:
        print("--dry-run: not writing queue.json")
        sys.exit(0)

    payload = {
        "generated_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "voice_version": voice.get("version", "0.0"),
        "items": items,
    }
    os.makedirs(os.path.dirname(queue_path), exist_ok=True)
    with open(queue_path, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Wrote {queue_path}")
