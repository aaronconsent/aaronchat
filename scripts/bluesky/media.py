"""Blob upload + link-card OG fetching for Bluesky posts.

Bluesky media flow: (1) upload each asset via com.atproto.repo.uploadBlob,
(2) reference the returned BlobRef in the post record's embed field.

Public helpers:
  upload_image(client, path_or_bytes, alt='', aspect_ratio=None) → dict
  upload_video(client, path_or_bytes, mime='video/mp4') → BlobRef
  build_link_card(client, url, title=None, description=None, thumb_url=None) → dict
  auto_link_card(client, url) → dict     (fetches OG tags, uploads thumb)
"""
import io
import json
import mimetypes
import os
import re
import urllib.request

from PIL import Image  # only used for aspect-ratio detection; already in requirements


MAX_IMAGE_BYTES = 976_562           # Bluesky hard limit
IMAGE_MIME_ALLOWED = {"image/jpeg", "image/png", "image/webp", "image/gif"}
VIDEO_MIME_ALLOWED = {"video/mp4", "video/quicktime"}
UA = "aaron-chat-bluesky-publisher/1.0"


# ---------- image upload ----------

def _read_bytes(path_or_bytes):
    if isinstance(path_or_bytes, (bytes, bytearray)):
        return bytes(path_or_bytes)
    with open(path_or_bytes, "rb") as f:
        return f.read()


def _guess_mime(path):
    m, _ = mimetypes.guess_type(path)
    return m or "application/octet-stream"


def _aspect_ratio(data):
    """Return {'width': w, 'height': h} for image bytes, or None on failure."""
    try:
        img = Image.open(io.BytesIO(data))
        w, h = img.size
        return {"width": int(w), "height": int(h)}
    except Exception:
        return None


def upload_image(client, path_or_bytes, alt="", aspect_ratio=None, mime=None):
    """Upload one image and return the image embed entry:
        {"alt": "...", "image": <blob ref>, "aspectRatio": {"width": w, "height": h}}
    """
    data = _read_bytes(path_or_bytes)
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError(
            f"Image is {len(data):,} bytes — Bluesky max is {MAX_IMAGE_BYTES:,}. "
            f"Re-encode smaller before upload."
        )
    if mime is None and isinstance(path_or_bytes, str):
        mime = _guess_mime(path_or_bytes)
    if mime and mime not in IMAGE_MIME_ALLOWED:
        raise ValueError(f"Image mime {mime!r} not accepted; use jpeg/png/webp/gif")
    blob_resp = client.com.atproto.repo.upload_blob(data)
    ar = aspect_ratio or _aspect_ratio(data)
    entry = {"alt": (alt or "")[:2000], "image": blob_resp.blob}
    if ar:
        entry["aspectRatio"] = ar
    return entry


def upload_images(client, images):
    """Upload up to 4 images. Each entry is either a path/bytes OR a dict:
        {"path": "...", "alt": "..."}   or
        {"bytes": b"...", "alt": "...", "aspect_ratio": {"width":..,"height":..}}
    Returns [dict, ...] shaped for embed.images.
    """
    if len(images) > 4:
        raise ValueError(f"Bluesky max 4 images per post; got {len(images)}")
    out = []
    for entry in images:
        if isinstance(entry, dict):
            src = entry.get("path") or entry.get("bytes")
            alt = entry.get("alt", "")
            ar = entry.get("aspect_ratio")
            mime = entry.get("mime")
        else:
            src = entry
            alt = ""
            ar = None
            mime = None
        out.append(upload_image(client, src, alt=alt, aspect_ratio=ar, mime=mime))
    return out


def build_image_embed(image_entries):
    """Turn a list of upload_image results into the post's embed field."""
    return {"$type": "app.bsky.embed.images", "images": image_entries}


# ---------- video upload ----------

def upload_video(client, path_or_bytes, alt="", mime="video/mp4"):
    """Upload a video and return the video embed dict.

    Bluesky processes videos server-side to HLS; the returned embed just points
    at the raw blob and Bluesky does the rest.
    """
    if mime not in VIDEO_MIME_ALLOWED:
        raise ValueError(f"Video mime {mime!r} not accepted; use mp4/quicktime")
    data = _read_bytes(path_or_bytes)
    blob = client.com.atproto.repo.upload_blob(data).blob
    embed = {"$type": "app.bsky.embed.video", "video": blob, "alt": (alt or "")[:2000]}
    return embed


# ---------- link cards ----------

def fetch_og_tags(url, timeout=8):
    """Fetch a URL and return {'title', 'description', 'image'} from Open Graph.

    Falls back to <title> and <meta name="description"> when og:* aren't present.
    Returns empty dict on failure.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read(200_000).decode("utf-8", errors="replace")
    except Exception:
        return {}

    def meta(pattern):
        m = re.search(pattern, html, re.I | re.S)
        return m.group(1).strip() if m else None

    og_title = meta(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']')
    og_desc = meta(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']')
    og_image = meta(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']')

    # Fallbacks
    if not og_title:
        og_title = meta(r'<title[^>]*>([^<]+)</title>')
    if not og_desc:
        og_desc = meta(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']')

    out = {}
    if og_title:
        out["title"] = og_title[:300]
    if og_desc:
        out["description"] = og_desc[:1000]
    if og_image:
        # Handle protocol-relative and root-relative URLs
        if og_image.startswith("//"):
            og_image = "https:" + og_image
        elif og_image.startswith("/"):
            from urllib.parse import urlparse
            parsed = urlparse(url)
            og_image = f"{parsed.scheme}://{parsed.netloc}{og_image}"
        out["image"] = og_image
    return out


def _download_image(url, timeout=10, max_bytes=MAX_IMAGE_BYTES * 2):
    """Fetch an image, return (bytes, mime). Truncates at max_bytes."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        mime = resp.headers.get_content_type() or "image/jpeg"
        data = resp.read(max_bytes)
    return data, mime


def _shrink_to_limit(data, mime, max_bytes=MAX_IMAGE_BYTES):
    """If image exceeds Bluesky's 976 KB blob limit, re-encode as JPEG at falling quality."""
    if len(data) <= max_bytes:
        return data, mime
    try:
        img = Image.open(io.BytesIO(data))
        img = img.convert("RGB") if img.mode != "RGB" else img
        for quality in (85, 75, 65, 55, 45):
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True)
            if buf.tell() <= max_bytes:
                return buf.getvalue(), "image/jpeg"
        # Last resort: downscale
        img.thumbnail((1200, 1200))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70, optimize=True)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        # Give up — return truncated original
        return data[:max_bytes], mime


def auto_link_card(client, url, title=None, description=None, thumb_url=None):
    """Build an embed.external dict for `url` by fetching its OG tags.

    Manually pass `title`/`description`/`thumb_url` to override any OG value.
    Returns a dict shaped for the post's embed field.
    """
    og = fetch_og_tags(url) if (not title or not description or not thumb_url) else {}
    external = {
        "uri": url,
        "title": (title or og.get("title") or url)[:300],
        "description": (description or og.get("description") or "")[:1000],
    }
    thumb_source = thumb_url or og.get("image")
    if thumb_source:
        try:
            data, mime = _download_image(thumb_source)
            if mime not in IMAGE_MIME_ALLOWED:
                mime = "image/jpeg"
            data, mime = _shrink_to_limit(data, mime)
            blob_resp = client.com.atproto.repo.upload_blob(data)
            external["thumb"] = blob_resp.blob
        except Exception:
            pass  # link card still works without thumb
    return {"$type": "app.bsky.embed.external", "external": external}
