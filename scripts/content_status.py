#!/usr/bin/env python3
"""Scan the repo for per-channel content sources and emit setup/content-status.json.

The wizard fetches this once per session and, for every channel a provider
unlocks, renders a Content Readiness grid with red/green dots.

Design: one manifest, keyed by channel id. Each channel has a list of
content types — {key, label, ok, detail}. Types with `ok: true` are ready
to publish; `ok: false` means source content missing.
"""
import datetime as dt
import glob
import json
import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)


# ------------------------------------------------------------------
# Small helpers
# ------------------------------------------------------------------

def _yaml(path):
    import yaml
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _queue():
    p = os.path.join(SITE, "content", "queue.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


def _queue_items(platform, mode=None):
    q = _queue()
    if not q:
        return None  # sentinel: no queue at all
    items = [i for i in q.get("items", []) if i.get("platform") == platform]
    if mode is not None:
        items = [i for i in items if (i.get("mode") or "audience") == mode]
    return items


# ------------------------------------------------------------------
# Generic queue-based checks (platform-parameterized)
# ------------------------------------------------------------------

def _make_queue_check(field, singular, plural=None):
    def check(platform, mode=None):
        items = _queue_items(platform, mode=mode)
        if items is None:
            return False, "content/queue.json missing"
        matches = [i for i in items if i.get(field)]
        n = len(matches)
        noun = plural or f"{singular}s"
        return (n > 0, f"{n} {noun if n != 1 else singular} queued")
    return check


def check_text_posts(platform, mode=None):
    items = _queue_items(platform, mode=mode)
    if items is None:
        return False, "content/queue.json missing"
    with_text = [i for i in items if (i.get("text") or "").strip()]
    n = len(with_text)
    return (n > 0, f"{n} text post{'s' if n != 1 else ''} queued")


check_images     = _make_queue_check("images", "item with images", "items with images")
check_video      = _make_queue_check("video",  "item with video",  "items with video")
check_link_cards = _make_queue_check("link",   "item with link card", "items with link cards")
check_threads    = _make_queue_check("thread", "thread")
check_quotes     = _make_queue_check("quote",  "quote post")


# ------------------------------------------------------------------
# Bluesky-specific file checks
# ------------------------------------------------------------------

def check_bluesky_profile(_platform):
    p = os.path.join(SITE, "content", "bluesky_profile.yaml")
    if not os.path.exists(p):
        return False, "content/bluesky_profile.yaml missing"
    cfg = _yaml(p)
    fields = [k for k in ("display_name", "description") if cfg.get(k)]
    return (bool(fields), ", ".join(fields) or "no fields set")


def check_bluesky_avatar(_platform):
    p = os.path.join(SITE, "content", "bluesky_profile.yaml")
    if not os.path.exists(p):
        return False, "profile config missing"
    av = _yaml(p).get("avatar")
    if not av:
        return False, "avatar not configured"
    exists = os.path.exists(os.path.join(SITE, av))
    return (exists, av if exists else f"{av} (file missing)")


def check_bluesky_banner(_platform):
    p = os.path.join(SITE, "content", "bluesky_profile.yaml")
    if not os.path.exists(p):
        return False, "profile config missing"
    bn = _yaml(p).get("banner")
    if not bn:
        return False, "banner not configured"
    exists = os.path.exists(os.path.join(SITE, bn))
    return (exists, bn if exists else f"{bn} (file missing)")


def check_bluesky_pinned(_platform):
    p = os.path.join(SITE, "content", "bluesky_profile.yaml")
    if not os.path.exists(p):
        return False, "profile config missing"
    uri = _yaml(p).get("pinned_post_uri")
    return (bool(uri), uri or "no pinned post set")


def check_bluesky_starter_packs(_platform):
    files = [f for f in glob.glob(os.path.join(SITE, "content", "starter_packs", "*.yaml"))
             if not f.endswith(".state.json")]
    with_handles = 0
    for f in files:
        if _yaml(f).get("handles"):
            with_handles += 1
    return (with_handles > 0, f"{with_handles}/{len(files)} pack(s) have handles")


def check_bluesky_competitors(_platform):
    p = os.path.join(SITE, "content", "bluesky_competitors.yaml")
    if not os.path.exists(p):
        return False, "content/bluesky_competitors.yaml missing"
    handles = _yaml(p).get("handles") or []
    return (len(handles) > 0, f"{len(handles)} handle(s) tracked")


# ------------------------------------------------------------------
# Long-form / one-off checks
# ------------------------------------------------------------------

def check_articles(_platform):
    """Anything in content/articles/*.md or similar."""
    for root in ("content/articles", "content/blog"):
        found = glob.glob(os.path.join(SITE, root, "*.md"))
        if found:
            return True, f"{len(found)} article(s) in {root}/"
    return False, "no markdown articles in content/articles/ or content/blog/"


def check_gbp_photos(_platform):
    found = glob.glob(os.path.join(SITE, "content", "gbp", "photos", "*"))
    return (len(found) > 0, f"{len(found)} photo(s) staged")


def check_gbp_offers(_platform):
    p = os.path.join(SITE, "content", "gbp", "offers.yaml")
    if not os.path.exists(p):
        return False, "content/gbp/offers.yaml missing"
    offers = _yaml(p).get("offers") or []
    return (len(offers) > 0, f"{len(offers)} offer(s) configured")


# ------------------------------------------------------------------
# Per-channel content type registry
# ------------------------------------------------------------------

# (type_key, label, checker_fn)
CHANNEL_TYPES = {
    "bluesky": [
        ("text_posts",    "Text posts",              check_text_posts),
        ("images",        "Images (1–4 per post)",   check_images),
        ("video",         "Video",                   check_video),
        ("link_cards",    "Link cards (auto OG)",    check_link_cards),
        ("threads",       "Threads (self-reply)",    check_threads),
        ("quote_posts",   "Quote posts",             check_quotes),
        ("profile",       "Profile (name + bio)",    check_bluesky_profile),
        ("avatar",        "Avatar image",            check_bluesky_avatar),
        ("banner",        "Banner image",            check_bluesky_banner),
        ("pinned_post",   "Pinned post",             check_bluesky_pinned),
        ("starter_packs", "Starter packs",           check_bluesky_starter_packs),
        ("competitors",   "Competitor tracking",     check_bluesky_competitors),
    ],
    "linkedin": [
        ("text_posts", "Text posts",           check_text_posts),
        ("images",     "Images (1–9 per post)", check_images),
        ("link_cards", "Link previews",        check_link_cards),
    ],
    "x": [
        ("text_posts", "Text posts",           check_text_posts),
        ("images",     "Images (1–4)",         check_images),
        ("video",      "Video",                check_video),
        ("threads",    "Threads",              check_threads),
        ("link_cards", "Link cards",           check_link_cards),
    ],
    "facebook": [
        ("text_posts", "Text posts",           check_text_posts),
        ("images",     "Images",               check_images),
        ("video",      "Video",                check_video),
        ("link_cards", "Link cards",           check_link_cards),
    ],
    "instagram": [
        ("images",     "Feed images (1–10 carousel)", check_images),
        ("video",      "Reels / video",       check_video),
    ],
    "threads": [
        ("text_posts", "Text posts",           check_text_posts),
        ("images",     "Images",               check_images),
    ],
    "telegraph": [
        ("articles",   "Long-form articles",   check_articles),
    ],
    "mastodon": [
        ("text_posts", "Text toots (auto-linked)", check_text_posts),
        ("images",     "Images (1–4, w/ alt-text)", check_images),
        ("video",      "Video",                check_video),
        ("audio",      "Audio",                _make_queue_check("audio", "item with audio", "items with audio")),
        ("link_cards", "Link cards (auto OG)", check_link_cards),
        ("polls",      "Polls",                _make_queue_check("poll", "poll")),
        ("threads",    "Threads (self-reply)", check_threads),
        ("cw",         "Content warnings",     _make_queue_check("spoiler", "item with CW", "items with CW")),
    ],
    "telegram": [
        ("text_posts", "Broadcast text",       check_text_posts),
        ("images",     "Images",               check_images),
        ("video",      "Video",                check_video),
    ],
    "tumblr": [
        ("text_posts", "Text posts",           check_text_posts),
        ("images",     "Photo posts",          check_images),
        ("video",      "Video posts",          check_video),
        ("link_cards", "Link posts",           check_link_cards),
    ],
    "pinterest": [
        ("images",     "Pin images",           check_images),
        ("link_cards", "Rich pins (URL)",      check_link_cards),
    ],
    "tiktok": [
        ("video",      "Vertical video",       check_video),
    ],
    "blogger": [
        ("articles",   "Blog posts (markdown)", check_articles),
    ],
    "youtube": [
        ("video",      "Videos to upload",     check_video),
    ],
    "gbp": [
        ("text_posts", "GBP posts (text)",     check_text_posts),
        ("images",     "GBP photos",           check_gbp_photos),
        ("link_cards", "GBP posts (CTA link)", check_link_cards),
        ("offers",     "Offers / promotions",  check_gbp_offers),
    ],
    "medium": [
        ("articles",   "Long-form articles",   check_articles),
    ],
}


MODES = ("credibility", "audience")


def _run_checks(channel, mode):
    """Run all content-type checks for a channel filtered by mode. Non-queue
    checks (profile files, etc.) run identically in both modes — they're
    prerequisites regardless of mode."""
    rows = []
    for key, label, fn in CHANNEL_TYPES.get(channel, []):
        try:
            # Only queue-based checks accept the mode kwarg; others ignore it
            try:
                ok, detail = fn(channel, mode=mode)
            except TypeError:
                ok, detail = fn(channel)
        except Exception as ex:
            ok, detail = False, f"check errored: {ex}"[:200]
        rows.append({"key": key, "label": label, "ok": bool(ok), "detail": detail})
    return rows


def main():
    channels = {}
    for chan in CHANNEL_TYPES:
        channels[chan] = {m: _run_checks(chan, m) for m in MODES}

    out = {
        "generated_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "modes": list(MODES),
        "channels": channels,
    }
    dest = os.path.join(SITE, "setup", "content-status.json")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w") as f:
        json.dump(out, f, indent=2)

    total_types = sum(len(v) for cvals in channels.values() for v in cvals.values())
    ready = sum(1 for cvals in channels.values() for v in cvals.values() for r in v if r["ok"])
    print(f"[content-status] {ready}/{total_types} type-checks ready across {len(channels)} channels × {len(MODES)} modes → {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
