"""Media uploads (images / video / audio / GIFV) + polls + link cards.

Mastodon's media flow: (1) POST to /api/v2/media with the file → returns
{id, url, preview_url, ...}. (2) Reference `id` in status create's
media_ids[]. Video/audio processing may be async — /api/v1/media/:id returns
a `url` when ready.
"""
import mimetypes
import os
import time


ALLOWED_IMAGE = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO = {"video/mp4", "video/webm", "video/quicktime"}
ALLOWED_AUDIO = {"audio/mpeg", "audio/ogg", "audio/wav", "audio/flac", "audio/mp4"}


def _read(path_or_bytes):
    if isinstance(path_or_bytes, (bytes, bytearray)):
        return bytes(path_or_bytes), "blob", "application/octet-stream"
    m, _ = mimetypes.guess_type(path_or_bytes)
    with open(path_or_bytes, "rb") as f:
        data = f.read()
    return data, os.path.basename(path_or_bytes), m or "application/octet-stream"


def upload(client, path_or_bytes, *, description="", focus=None, mime=None,
           wait_for_processing=False, poll_interval=1.5, timeout=60):
    """Upload one media attachment. Returns {id, url, ...}.

    focus: tuple (x, y) or "x,y" string, floats in [-1.0, 1.0]
    wait_for_processing: for video/audio, poll /api/v1/media/:id until url set
    """
    data, filename, guessed = _read(path_or_bytes)
    mime = mime or guessed
    files = {"file": (filename, data, mime)}
    params = {}
    if description:
        params["description"] = description[:1500]
    if focus:
        params["focus"] = focus if isinstance(focus, str) else f"{focus[0]},{focus[1]}"
    resp = client.post("/api/v2/media", params=params, files=files)
    media_id = resp.get("id")
    if wait_for_processing and media_id and not resp.get("url"):
        deadline = time.time() + timeout
        while time.time() < deadline:
            got = client.get(f"/api/v1/media/{media_id}")
            if got.get("url"):
                return got
            time.sleep(poll_interval)
    return resp


def upload_image(client, path_or_bytes, description="", focus=None, mime=None):
    return upload(client, path_or_bytes, description=description, focus=focus, mime=mime)


def upload_video(client, path_or_bytes, description="", mime="video/mp4"):
    return upload(client, path_or_bytes, description=description, mime=mime,
                   wait_for_processing=True)


def upload_audio(client, path_or_bytes, description="", mime="audio/mpeg"):
    return upload(client, path_or_bytes, description=description, mime=mime,
                   wait_for_processing=True)


def upload_gifv(client, path_or_bytes, description="", mime="video/mp4"):
    """Upload an MP4 to be treated as GIFV (silent, looping). Mastodon
    auto-converts videos with no audio track."""
    return upload(client, path_or_bytes, description=description, mime=mime,
                   wait_for_processing=True)


def update_media_metadata(client, media_id, description=None, focus=None):
    """Update alt-text / focal point AFTER upload (before status is posted)."""
    params = {}
    if description is not None:
        params["description"] = description[:1500]
    if focus is not None:
        params["focus"] = focus if isinstance(focus, str) else f"{focus[0]},{focus[1]}"
    return client.put(f"/api/v1/media/{media_id}", params=params or {})


# ---------- link cards ----------

def link_card_note():
    """Mastodon auto-fetches OG tags server-side for any URL in status text.

    There is NO client-side link-card upload — you just include the URL in
    your status, and Mastodon builds the preview card asynchronously.
    This function exists so callers know why there's no build_link_card().
    """
    return (
        "Mastodon auto-generates link cards from URLs in status text. "
        "No client action required; include the URL in the post body."
    )
