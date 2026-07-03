"""Analytics — nightly snapshots of own-post engagement, competitor rollups,
hashtag momentum. Same JSONL shape as bluesky/analytics.py so downstream
charts can read either.

Outputs:
    content/analytics/mastodon/own_posts.jsonl
    content/analytics/mastodon/competitors.jsonl
    content/analytics/mastodon/hashtag_momentum.jsonl
"""
import datetime as dt
import json
import os


ANALYTICS_DIR = "content/analytics/mastodon"


def _today():
    return dt.datetime.utcnow().date().isoformat()


def _append(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        for r in rows:
            f.write(json.dumps(r, separators=(",", ":")) + "\n")


def snapshot_own_posts(client, lookback_days=30, dry_run=False):
    """Walk your account statuses for the last N days; write per-post metrics."""
    from mastodon import reading
    cutoff = dt.datetime.utcnow() - dt.timedelta(days=lookback_days)
    handle = client.me["username"]
    account_id = client.me["id"]

    rows = []
    max_id = None
    stop = False
    while not stop:
        page = reading.account_statuses(client, account_id, max_id=max_id,
                                         limit=40, exclude_reblogs=True)
        if not page:
            break
        for st in page:
            created = st.get("created_at")
            try:
                when = dt.datetime.fromisoformat(created.replace("Z", "+00:00")).replace(tzinfo=None)
                if when < cutoff:
                    stop = True
                    break
            except Exception:
                pass
            rows.append({
                "snapshot_date": _today(),
                "handle": handle,
                "id": st.get("id"),
                "url": st.get("url"),
                "created_at": created,
                "language": st.get("language"),
                "visibility": st.get("visibility"),
                "favourites": st.get("favourites_count") or 0,
                "reblogs":    st.get("reblogs_count") or 0,
                "replies":    st.get("replies_count") or 0,
            })
        max_id = page[-1].get("id")
        if not max_id:
            break

    if dry_run:
        return rows
    _append(os.path.join(ANALYTICS_DIR, "own_posts.jsonl"), rows)
    return rows


def snapshot_competitors(client, handles, dry_run=False):
    """Followers / following / statuses count per handle per day."""
    from mastodon.graph import _resolve
    rows = []
    for handle in handles:
        try:
            aid = _resolve(client, handle)
            acct = client.get(f"/api/v1/accounts/{aid}")
        except Exception as ex:
            rows.append({"snapshot_date": _today(), "handle": handle,
                          "error": str(ex)[:200]})
            continue
        rows.append({
            "snapshot_date": _today(),
            "handle": acct.get("acct") or handle,
            "id":       acct.get("id"),
            "followers": acct.get("followers_count") or 0,
            "following": acct.get("following_count") or 0,
            "statuses":  acct.get("statuses_count") or 0,
            "note":      (acct.get("note") or "")[:200],
        })

    if dry_run:
        return rows
    _append(os.path.join(ANALYTICS_DIR, "competitors.jsonl"), rows)
    return rows


def snapshot_hashtag_momentum(client, tags, dry_run=False):
    """Nightly snapshot of tag momentum — Mastodon's tag object includes a
    7-day history: [{day, uses, accounts}]."""
    from mastodon import reading  # noqa
    rows = []
    for tag in tags:
        try:
            t = client.get(f"/api/v1/tags/{tag}")
        except Exception as ex:
            rows.append({"snapshot_date": _today(), "tag": tag, "error": str(ex)[:200]})
            continue
        history = t.get("history") or []
        # Sum last 7 days' uses + accounts
        uses_7d = sum(int(h.get("uses", 0)) for h in history)
        accts_7d = sum(int(h.get("accounts", 0)) for h in history)
        rows.append({
            "snapshot_date": _today(),
            "tag": t.get("name") or tag,
            "url": t.get("url"),
            "following": bool(t.get("following")),
            "uses_7d": uses_7d,
            "accounts_7d": accts_7d,
            "history": history,
        })

    if dry_run:
        return rows
    _append(os.path.join(ANALYTICS_DIR, "hashtag_momentum.jsonl"), rows)
    return rows


def snapshot_reach_signals(client, status_ids, dry_run=False):
    """For each status id, pull reblogged_by + favourited_by and record the
    total unique-account reach. Useful audience-quality signal beyond raw
    counts."""
    from mastodon import engagement
    rows = []
    for sid in status_ids:
        try:
            rb = engagement.reblogged_by(client, sid, limit=80) or []
            fv = engagement.favourited_by(client, sid, limit=80) or []
        except Exception as ex:
            rows.append({"snapshot_date": _today(), "status_id": sid,
                          "error": str(ex)[:200]})
            continue
        rb_ids = {a.get("id") for a in rb if isinstance(a, dict)}
        fv_ids = {a.get("id") for a in fv if isinstance(a, dict)}
        rows.append({
            "snapshot_date": _today(),
            "status_id": sid,
            "reblogged_by_count": len(rb_ids),
            "favourited_by_count": len(fv_ids),
            "unique_reach": len(rb_ids | fv_ids),
        })
    if dry_run:
        return rows
    _append(os.path.join(ANALYTICS_DIR, "reach_signals.jsonl"), rows)
    return rows
