"""Engagement snapshotting + competitor tracking for Bluesky.

Two capture modes:

    snapshot_own_posts(client, lookback_days=30) → per-post metrics
    snapshot_competitors(client, handles, lookback_days=7) → per-account rollups

Both write compact JSONL files that stack cleanly across nightly runs.
"""
import datetime as dt
import json
import os


ANALYTICS_DIR = "content/analytics/bluesky"


def _iso(d):
    return d.isoformat(timespec="seconds") + "Z"


def _today():
    return dt.datetime.utcnow().date().isoformat()


def _write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        for r in rows:
            f.write(json.dumps(r, separators=(",", ":")) + "\n")


def _posts_metrics(post_view):
    """Extract likeCount/repostCount/replyCount/quoteCount from a PostView."""
    def _g(o, k):
        if hasattr(o, k):
            return getattr(o, k)
        if isinstance(o, dict):
            return o.get(k)
        return None
    return {
        "likes":    _g(post_view, "likeCount") or 0,
        "reposts":  _g(post_view, "repostCount") or 0,
        "replies":  _g(post_view, "replyCount") or 0,
        "quotes":   _g(post_view, "quoteCount") or 0,
    }


def snapshot_own_posts(client, lookback_days=30, dry_run=False):
    """Walk the account's author feed for the last `lookback_days` and record
    engagement metrics per post. One JSONL row per post per snapshot day."""
    from bluesky import reading
    cutoff = dt.datetime.utcnow() - dt.timedelta(days=lookback_days)
    handle = client.me.handle if hasattr(client, "me") else client.me.did

    rows = []
    cursor = None
    stop = False
    while not stop:
        page = reading.get_author_feed(client, actor=client.me.did, cursor=cursor, limit=100,
                                        filter="posts_and_author_threads")
        feed = page.feed if hasattr(page, "feed") else page.get("feed", [])
        for item in feed:
            post = getattr(item, "post", None) or item.get("post")
            if post is None:
                continue
            record = getattr(post, "record", None) or post.get("record", {})
            created = getattr(record, "createdAt", None) or record.get("createdAt")
            if created:
                try:
                    when = dt.datetime.fromisoformat(created.replace("Z", "+00:00")).replace(tzinfo=None)
                    if when < cutoff:
                        stop = True
                        break
                except Exception:
                    pass
            metrics = _posts_metrics(post)
            uri = getattr(post, "uri", None) or post.get("uri")
            rows.append({
                "snapshot_date": _today(),
                "handle": handle,
                "uri": uri,
                "created_at": created,
                **metrics,
            })
        cursor = getattr(page, "cursor", None) or page.get("cursor")
        if not cursor:
            break

    if dry_run:
        return rows

    path = os.path.join(ANALYTICS_DIR, "own_posts.jsonl")
    _write_jsonl(path, rows)
    return rows


def snapshot_competitors(client, handles, dry_run=False):
    """Nightly account-level rollup for a list of competitor handles.
    Records followers/follows/posts count per handle per day."""
    from bluesky import reading
    rows = []
    for handle in handles:
        try:
            resp = reading.get_profile(client, handle)
        except Exception as ex:
            rows.append({"snapshot_date": _today(), "handle": handle,
                         "error": str(ex)[:200]})
            continue
        def _g(k):
            return getattr(resp, k, None) if hasattr(resp, k) else (
                resp.get(k) if isinstance(resp, dict) else None)
        rows.append({
            "snapshot_date": _today(),
            "handle":     _g("handle") or handle,
            "did":        _g("did"),
            "followers":  _g("followersCount") or 0,
            "follows":    _g("followsCount") or 0,
            "posts":      _g("postsCount") or 0,
        })

    if dry_run:
        return rows

    path = os.path.join(ANALYTICS_DIR, "competitors.jsonl")
    _write_jsonl(path, rows)
    return rows


def load_own_posts(path=None):
    path = path or os.path.join(ANALYTICS_DIR, "own_posts.jsonl")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def load_competitors(path=None):
    path = path or os.path.join(ANALYTICS_DIR, "competitors.jsonl")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]
