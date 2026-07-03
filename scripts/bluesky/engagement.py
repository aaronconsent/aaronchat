"""Engagement — like, repost, bookmark, report, viewer-state lookups.

Likes and reposts are records:  app.bsky.feed.like / app.bsky.feed.repost
Bookmarks are private and stored server-side via app.bsky.bookmark.*
Reports go through com.atproto.moderation.createReport.
Viewer state (did I like this? did I repost this?) is returned inline on
getPostThread / getPosts responses — this module surfaces a helper.
"""
import datetime as dt


def _now_iso():
    return dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _create(client, collection, record):
    resp = client.com.atproto.repo.create_record({
        "repo": client.me.did, "collection": collection, "record": record,
    })
    return {"uri": resp.uri, "cid": resp.cid}


# ---------- like ----------

def like(client, target):
    """Like a post. `target` is {'uri','cid'}."""
    return _create(client, "app.bsky.feed.like", {
        "$type": "app.bsky.feed.like",
        "subject": {"uri": target["uri"], "cid": target["cid"]},
        "createdAt": _now_iso(),
    })


def unlike(client, like_uri):
    from bluesky import posts
    return posts.delete(client, like_uri)


# ---------- repost (mirror of posts.create_repost for convenience) ----------

def repost(client, target):
    from bluesky import posts
    return posts.create_repost(client, target)


def unrepost(client, repost_uri):
    from bluesky import posts
    return posts.delete(client, repost_uri)


# ---------- bookmark (private) ----------

def bookmark(client, target):
    """Save a post to your private bookmarks."""
    try:
        client.app.bsky.bookmark.create_bookmark({
            "uri": target["uri"],
            "cid": target["cid"],
        })
    except AttributeError:
        # SDK may not expose the namespace yet; fall back to raw XRPC
        client._call_xrpc("app.bsky.bookmark.createBookmark", {
            "uri": target["uri"], "cid": target["cid"],
        })
    return True


def remove_bookmark(client, target):
    try:
        client.app.bsky.bookmark.delete_bookmark({
            "uri": target["uri"],
        })
    except AttributeError:
        client._call_xrpc("app.bsky.bookmark.deleteBookmark", {"uri": target["uri"]})
    return True


def list_bookmarks(client, cursor=None, limit=50):
    try:
        return client.app.bsky.bookmark.get_bookmarks({"cursor": cursor, "limit": limit})
    except AttributeError:
        return client._call_xrpc("app.bsky.bookmark.getBookmarks",
                                  {"cursor": cursor, "limit": limit}, method="GET")


# ---------- report (moderation) ----------

REPORT_REASONS = {
    "spam":       "com.atproto.moderation.defs#reasonSpam",
    "violation":  "com.atproto.moderation.defs#reasonViolation",
    "misleading": "com.atproto.moderation.defs#reasonMisleading",
    "sexual":     "com.atproto.moderation.defs#reasonSexual",
    "rude":       "com.atproto.moderation.defs#reasonRude",
    "other":      "com.atproto.moderation.defs#reasonOther",
}


def report_post(client, target, reason="spam", comment=""):
    """Report a post to the moderation service."""
    if reason not in REPORT_REASONS:
        raise ValueError(f"reason must be one of {list(REPORT_REASONS)}")
    client.com.atproto.moderation.create_report({
        "reasonType": REPORT_REASONS[reason],
        "reason": comment,
        "subject": {
            "$type": "com.atproto.repo.strongRef",
            "uri": target["uri"],
            "cid": target["cid"],
        },
    })
    return True


def report_account(client, did, reason="spam", comment=""):
    """Report an account/DID to the moderation service."""
    if reason not in REPORT_REASONS:
        raise ValueError(f"reason must be one of {list(REPORT_REASONS)}")
    client.com.atproto.moderation.create_report({
        "reasonType": REPORT_REASONS[reason],
        "reason": comment,
        "subject": {"$type": "com.atproto.admin.defs#repoRef", "did": did},
    })
    return True


# ---------- viewer state ----------

def get_viewer_state(client, post_uri):
    """Return {'like': like_uri or None, 'repost': repost_uri or None,
    'bookmarked': bool} for the current viewer on a given post."""
    resp = client.app.bsky.feed.get_posts({"uris": [post_uri]})
    posts = resp.posts if hasattr(resp, "posts") else resp.get("posts", [])
    if not posts:
        return {"like": None, "repost": None, "bookmarked": False}
    p = posts[0]
    viewer = getattr(p, "viewer", None) or p.get("viewer") if isinstance(p, dict) else None
    if viewer is None:
        return {"like": None, "repost": None, "bookmarked": False}
    def _g(k):
        return getattr(viewer, k, None) if hasattr(viewer, k) else viewer.get(k)
    return {
        "like":       _g("like"),
        "repost":     _g("repost"),
        "bookmarked": bool(_g("bookmarked")),
    }
