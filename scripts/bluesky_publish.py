#!/usr/bin/env python3
"""Bluesky publisher. Plugs into runner_base.run() alongside linkedin/x publishers.

Implements the standard `post(item, channel_cfg) → PublishResult` interface.
Consumes queue.json items shaped like:
  {"id": "...", "text": "...", "link": "...", "images": [...], "video": "...", ...}

Rich text facets (URL / @mention / #hashtag) are built automatically from the
text. Link cards are auto-generated when the queue item includes a `link` and
no explicit `images`. Language tag defaults to English.

Extra queue item fields we honor when present:
  images: [{"path": "...", "alt": "..."}]     up to 4
  video:  "path/to/file.mp4"                  or dict {"path", "alt"}
  reply:  {"root": {uri, cid}, "parent": {uri, cid}}
  quote:  {"uri": ..., "cid": ...}
  langs:  ["en", "es"]
  labels: ["nudity"]                           self-labels for CW
  threadgate: {"allow": ["following"]}         restrict replies
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from linkedin_publish import PublishResult  # reuse the shared result type

# atproto import errors are surfaced only when actually publishing (not on runner start)


def post(item, channel_cfg):
    """Publish `item` to Bluesky. Returns PublishResult."""
    backend = channel_cfg.get("backend", "own_app")
    if backend != "own_app":
        return PublishResult(False, backend, f"Bluesky publisher only supports own_app; got {backend!r}")

    # Late imports so a missing atproto only fails the actual runner tick, not run_all startup
    try:
        from bluesky.client import get_client
        from bluesky import posts as posts_mod
        from bluesky import media as media_mod
        from bluesky import facets as facets_mod
    except Exception as ex:
        return PublishResult(False, "own_app", f"import failed: {ex}")

    from env_loader import MissingSecretsError
    try:
        client = get_client()
    except MissingSecretsError as ex:
        return PublishResult(False, "own_app", str(ex))
    except Exception as ex:
        return PublishResult(False, "own_app", f"login failed: {ex}")

    text = item.get("text", "").strip()
    if not text and not item.get("images") and not item.get("video"):
        return PublishResult(False, "own_app", "empty item — no text/images/video")

    # Build facets from text
    _, facets = facets_mod.build(text, client=client) if text else ("", [])

    # Assemble embed: video > images > quote-with-media > link card > quote-only
    embed = None
    media_only_embed = None
    video = item.get("video")
    if video:
        vpath = video if isinstance(video, str) else video.get("path")
        valt = "" if isinstance(video, str) else video.get("alt", "")
        try:
            media_only_embed = media_mod.upload_video(client, vpath, alt=valt)
            embed = media_only_embed
        except Exception as ex:
            return PublishResult(False, "own_app", f"video upload failed: {ex}")

    images = item.get("images") or []
    if not embed and images:
        try:
            uploaded = media_mod.upload_images(client, images)
            media_only_embed = media_mod.build_image_embed(uploaded)
            embed = media_only_embed
        except Exception as ex:
            return PublishResult(False, "own_app", f"image upload failed: {ex}")

    quote_ref = item.get("quote")

    if not embed and item.get("link"):
        # Auto link-card from the URL in `link`
        try:
            embed = media_mod.auto_link_card(client, item["link"])
        except Exception:
            embed = None

    if not embed and not item.get("link"):
        # See if the text itself contains a URL and build a card
        first_link = facets_mod.extract_first_link(text)
        if first_link:
            try:
                embed = media_mod.auto_link_card(client, first_link)
            except Exception:
                embed = None

    # If quoting, combine with any media we already have
    if quote_ref:
        try:
            if media_only_embed:
                # Quote + media
                embed = None  # rebuild via create_quote path
                pass
            else:
                embed = {
                    "$type": "app.bsky.embed.record",
                    "record": {"uri": quote_ref["uri"], "cid": quote_ref["cid"]},
                }
        except Exception:
            pass

    reply = item.get("reply")
    langs = item.get("langs") or ["en"]
    labels = item.get("labels")

    # Threadgate — build the record from item.threadgate config if present
    threadgate_rec = None
    if item.get("threadgate"):
        threadgate_rec = _build_threadgate_from_config(item["threadgate"])

    try:
        if quote_ref and media_only_embed:
            # Quote + media path
            result = posts_mod.create_quote(
                client, quoted=quote_ref, text=text,
                media_embed=media_only_embed,
                facets=facets, langs=langs, labels=labels, reply=reply,
                threadgate=threadgate_rec,
            )
        elif quote_ref:
            # Quote-only
            result = posts_mod.create_quote(
                client, quoted=quote_ref, text=text,
                facets=facets, langs=langs, labels=labels, reply=reply,
                threadgate=threadgate_rec,
            )
        else:
            result = posts_mod.create(
                client, text, facets=facets, embed=embed,
                reply=reply, langs=langs, labels=labels,
                threadgate=threadgate_rec,
            )
    except Exception as ex:
        return PublishResult(False, "own_app", f"createRecord failed: {ex}")

    handle = client.me.handle if hasattr(client, "me") else "?"
    rkey = result["uri"].split("/")[-1]
    detail = f"posted {handle}/post/{rkey}"
    return PublishResult(True, "own_app", detail)


def _build_threadgate_from_config(cfg):
    """Turn a config dict like {'allow': ['following']} or {'allow': ['nobody']}
    into a threadgate record body ready for posts.create()."""
    if not cfg:
        return None
    allow_types = cfg.get("allow") or []
    if allow_types == ["nobody"] or allow_types == []:
        return {"allow": []}
    rules = []
    for r in allow_types:
        if r == "following":
            rules.append({"$type": "app.bsky.feed.threadgate#followingRule"})
        elif r == "mention":
            rules.append({"$type": "app.bsky.feed.threadgate#mentionRule"})
        elif isinstance(r, dict) and r.get("list"):
            rules.append({"$type": "app.bsky.feed.threadgate#listRule", "list": r["list"]})
    return {"allow": rules}
