#!/usr/bin/env python3
"""Turn content/credibility_kit.yaml into `mode: credibility` items in queue.json.

Runs OFFLINE. Merges into the existing queue, preserving any items already
tagged mode=audience. Idempotent — SHA256 IDs mean re-runs don't dup posts.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

import yaml


CHANNELS_ALL = ["linkedin", "x", "bluesky", "mastodon", "facebook", "instagram",
                "threads", "telegraph", "blogger", "medium", "tumblr", "telegram"]


def _id(*parts):
    return hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:12]


def _now_iso():
    return dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _fmt_hashtags(kit, channel):
    tags = kit.get("platform_hashtags", {}).get(channel) or []
    return (" " + " ".join(f"#{t}" for t in tags)) if tags else ""


def _build_intro(kit, channel):
    e = kit["entity"]
    text = f"{e['tagline']} {e['elevator_pitch'].strip()} {e['home_url']}"
    return text.strip() + _fmt_hashtags(kit, channel)


def _build_service(kit, channel, svc):
    return f"{svc['one_liner']} {svc['url']}" + _fmt_hashtags(kit, channel)


def _build_faq(kit, channel, qa):
    return f"Q: {qa['q']}\n\nA: {qa['a']} {qa['url']}" + _fmt_hashtags(kit, channel)


def _build_sameas(kit, channel, sa):
    e = kit["entity"]
    # "Same shop, different room" style
    return f"Also find {e['name']} on {sa['label']}: {sa['url']}" + _fmt_hashtags(kit, channel)


def build_items(kit, channels, generated_at):
    items = []
    for ch in channels:
        # 1) intro / bio
        text = _build_intro(kit, ch)
        items.append({
            "id": _id(ch, "credibility", "intro", "v1"),
            "platform": ch,
            "mode": "credibility",
            "kind": "intro",
            "text": text,
            "link": kit["entity"]["home_url"],
            "voice_version": "credibility/1.0",
            "generated_at": generated_at,
        })
        # 2) service one-liners
        for svc in kit.get("services", []):
            items.append({
                "id": _id(ch, "credibility", "service", svc["url"]),
                "platform": ch,
                "mode": "credibility",
                "kind": "service",
                "text": _build_service(kit, ch, svc),
                "link": svc["url"],
                "voice_version": "credibility/1.0",
                "generated_at": generated_at,
            })
        # 3) FAQ Q&A
        for qa in kit.get("faq", []):
            items.append({
                "id": _id(ch, "credibility", "faq", qa["q"]),
                "platform": ch,
                "mode": "credibility",
                "kind": "faq",
                "text": _build_faq(kit, ch, qa),
                "link": qa["url"],
                "voice_version": "credibility/1.0",
                "generated_at": generated_at,
            })
        # 4) sameAs cross-refs
        for sa in kit.get("same_as", []):
            items.append({
                "id": _id(ch, "credibility", "sameas", sa["url"]),
                "platform": ch,
                "mode": "credibility",
                "kind": "sameas",
                "text": _build_sameas(kit, ch, sa),
                "link": sa["url"],
                "voice_version": "credibility/1.0",
                "generated_at": generated_at,
            })
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", default=os.path.join(ROOT, "content", "credibility_kit.yaml"))
    ap.add_argument("--queue", default=os.path.join(ROOT, "content", "queue.json"))
    ap.add_argument("--channels", help="Comma-separated. Defaults to all.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(args.kit) as f:
        kit = yaml.safe_load(f)
    channels = args.channels.split(",") if args.channels else CHANNELS_ALL

    now = _now_iso()
    new_items = build_items(kit, channels, now)

    existing = {"items": []}
    if os.path.exists(args.queue):
        with open(args.queue) as f:
            existing = json.load(f)
    # Migrate: tag any un-moded existing item as audience
    for it in existing.get("items", []):
        it.setdefault("mode", "audience")

    by_id = {it["id"]: it for it in existing.get("items", [])}
    added = updated = 0
    for it in new_items:
        if it["id"] in by_id:
            # Refresh text/link (kit edits should propagate) but preserve id
            by_id[it["id"]].update(it)
            updated += 1
        else:
            by_id[it["id"]] = it
            added += 1

    out = {"items": list(by_id.values())}
    print(f"[credibility-queue] +{added} new, {updated} refreshed, total {len(out['items'])} items")

    if args.dry_run:
        return 0
    os.makedirs(os.path.dirname(args.queue), exist_ok=True)
    with open(args.queue, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"[credibility-queue] wrote {args.queue}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
