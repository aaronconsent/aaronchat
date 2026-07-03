"""Profile record management — display name, bio, avatar, banner, pinned post.

Bluesky stores your profile as a single `app.bsky.actor.profile` record at
rkey='self'. This module reads, mutates, and writes that record. Avatar/banner
uploads reuse `media.upload_image` for the blob step but bypass the aspect-ratio
enforcement (profiles use fixed shapes: square avatar, wide banner).

Usage:
    from bluesky.client import get_client
    from bluesky import profile
    client = get_client()
    profile.update(client,
        display_name="Aaron Phillips",
        description="Marketing for East Texas service pros.",
        avatar_path="content/avatar.jpg",
    )
    profile.set_pinned_post(client, uri="at://did:plc:.../app.bsky.feed.post/abc")
"""
import datetime as dt


PROFILE_COLLECTION = "app.bsky.actor.profile"


def _now_iso():
    return dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def get(client):
    """Fetch the current profile record. Returns dict or None if not set."""
    try:
        resp = client.com.atproto.repo.get_record({
            "repo": client.me.did,
            "collection": PROFILE_COLLECTION,
            "rkey": "self",
        })
        return dict(resp.value) if hasattr(resp, "value") else dict(resp["value"])
    except Exception:
        return None


def _put(client, record):
    """putRecord upserts the profile at rkey='self'."""
    return client.com.atproto.repo.put_record({
        "repo": client.me.did,
        "collection": PROFILE_COLLECTION,
        "rkey": "self",
        "record": record,
    })


def _upload_blob(client, path_or_bytes):
    if isinstance(path_or_bytes, (bytes, bytearray)):
        data = bytes(path_or_bytes)
    else:
        with open(path_or_bytes, "rb") as f:
            data = f.read()
    return client.com.atproto.repo.upload_blob(data).blob


def update(client, display_name=None, description=None, avatar_path=None,
           banner_path=None, labels=None, pinned_post=None):
    """Update whichever profile fields are provided. Untouched fields survive.

    labels: list of self-label strings (e.g. ["!no-unauthenticated"] to hide
            the profile from logged-out viewers).
    pinned_post: {"uri": ..., "cid": ...} or None. Pass 'clear' string to remove.
    """
    current = get(client) or {"$type": PROFILE_COLLECTION}
    record = dict(current)
    record["$type"] = PROFILE_COLLECTION

    if display_name is not None:
        record["displayName"] = display_name[:64]
    if description is not None:
        record["description"] = description[:2560]
    if avatar_path is not None:
        record["avatar"] = _upload_blob(client, avatar_path)
    if banner_path is not None:
        record["banner"] = _upload_blob(client, banner_path)
    if labels is not None:
        record["labels"] = {
            "$type": "com.atproto.label.defs#selfLabels",
            "values": [{"val": v} for v in labels],
        }
    if pinned_post == "clear":
        record.pop("pinnedPost", None)
    elif pinned_post is not None:
        record["pinnedPost"] = {"uri": pinned_post["uri"], "cid": pinned_post["cid"]}

    return _put(client, record)


def set_pinned_post(client, uri, cid=None):
    """Pin a specific post. If cid is None, we look it up from the URI."""
    if cid is None:
        parts = uri.replace("at://", "").split("/")
        did, coll, rkey = parts
        resp = client.com.atproto.repo.get_record({"repo": did, "collection": coll, "rkey": rkey})
        cid = resp.cid if hasattr(resp, "cid") else resp["cid"]
    return update(client, pinned_post={"uri": uri, "cid": cid})


def clear_pinned_post(client):
    return update(client, pinned_post="clear")
