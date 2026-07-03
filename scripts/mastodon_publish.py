#!/usr/bin/env python3
"""Mastodon publisher. Consumes queue.json items with platform=mastodon and
publishes via the mastodon/ library. Same shape as bluesky_publish.

Recognized item fields:
    text        (required) — Mastodon auto-links URLs / @ / #
    link        URL to embed (Mastodon auto-generates preview from any URL in text)
    images      [{path, alt, focus}]  up to 4 (or the instance's max)
    video       "path" or {path, alt}
    audio       "path" or {path, alt}
    poll        {options: [...], expires_in: N, multiple: bool, hide_totals: bool}
    spoiler     content-warning text
    visibility  public|unlisted|private|direct  (default public)
    language    BCP47, default en
    reply_to    status id to reply to
    quote       status URL or id (Mastodon 4.4 native + URL-embed fallback)
    scheduled_at ISO timestamp (server-side scheduling)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from linkedin_publish import PublishResult
from env_loader import MissingSecretsError


def post(item, channel_cfg):
    backend = channel_cfg.get("backend", "own_app")
    if backend != "own_app":
        return PublishResult(False, backend, f"Mastodon publisher only supports own_app; got {backend!r}")

    try:
        from mastodon.client import get_client, MastodonError
        from mastodon import posts as posts_mod
        from mastodon import media as media_mod
    except Exception as ex:
        return PublishResult(False, "own_app", f"import failed: {ex}")

    try:
        client = get_client()
    except MissingSecretsError as ex:
        return PublishResult(False, "own_app", str(ex))
    except Exception as ex:
        return PublishResult(False, "own_app", f"client init failed: {ex}")

    text = (item.get("text") or "").strip()
    if not text and not item.get("images") and not item.get("video") and not item.get("audio"):
        return PublishResult(False, "own_app", "empty item — no text/media")

    # If a link is provided but not already in text, append so Mastodon builds a card
    link = item.get("link")
    if link and link not in text:
        text = (text + "\n" + link).strip() if text else link

    # Upload media (up to 4 attachments total)
    media_ids = []
    try:
        for img in (item.get("images") or [])[:4]:
            if isinstance(img, str):
                r = media_mod.upload_image(client, img)
            else:
                r = media_mod.upload_image(client, img.get("path"),
                                           description=img.get("alt", ""),
                                           focus=img.get("focus"))
            media_ids.append(r["id"])
        if item.get("video") and len(media_ids) < 4:
            v = item["video"]
            path = v if isinstance(v, str) else v.get("path")
            alt = "" if isinstance(v, str) else v.get("alt", "")
            r = media_mod.upload_video(client, path, description=alt)
            media_ids.append(r["id"])
        if item.get("audio") and len(media_ids) < 4:
            a = item["audio"]
            path = a if isinstance(a, str) else a.get("path")
            alt = "" if isinstance(a, str) else a.get("alt", "")
            r = media_mod.upload_audio(client, path, description=alt)
            media_ids.append(r["id"])
    except Exception as ex:
        return PublishResult(False, "own_app", f"media upload failed: {ex}")

    kwargs = {
        "visibility": item.get("visibility", "public"),
        "language":   item.get("language", "en"),
        "sensitive":  bool(item.get("sensitive")),
        "spoiler":    item.get("spoiler"),
        "media_ids":  media_ids or None,
        "poll":       item.get("poll"),
        "scheduled_at": item.get("scheduled_at"),
        "in_reply_to_id": item.get("reply_to"),
        "idempotency_key": item.get("id"),  # dedupe on retries
    }

    try:
        if item.get("quote"):
            resp = posts_mod.quote(client, item["quote"], text, **{
                k: v for k, v in kwargs.items() if k != "scheduled_at"
            })
        else:
            resp = posts_mod.create(client, text, **kwargs)
    except Exception as ex:
        return PublishResult(False, "own_app", f"createStatus failed: {ex}")

    url = resp.get("url") or resp.get("uri") or resp.get("id") or "?"
    handle = client.me["acct"]
    return PublishResult(True, "own_app", f"posted @{handle} → {url}")
