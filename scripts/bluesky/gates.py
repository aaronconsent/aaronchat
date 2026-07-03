"""Threadgate + postgate builders — reply and quote controls.

Bluesky enforces "who can reply" and "who can quote" via SIDE records that
share the same rkey as the post they gate:

    app.bsky.feed.threadgate  — controls REPLIES to a thread
    app.bsky.feed.postgate    — controls QUOTES of a specific post

`posts.create()` accepts `threadgate=` and `postgate=` kwargs that take the
dicts these functions return.

Threadgate rules:
    followingRule   — anyone the post author follows can reply
    mentionRule     — anyone mentioned in the post can reply
    listRule        — anyone on a specific list can reply
    empty list      — NOBODY can reply
    None            — anyone (no gate record)

Postgate rules:
    disableEmbedding — quote posts are forbidden entirely
    detachedEmbeddingUris — hide specific existing quotes
"""


# ---------- threadgate builders ----------

def build_threadgate(allow_following=False, allow_mentioned=False, allow_lists=None,
                     hidden_replies=None):
    """Build a threadgate record body (minus `post` and `createdAt`, filled in
    by posts.create()).

    allow_following: bool — anyone you follow can reply
    allow_mentioned: bool — anyone you @mentioned can reply
    allow_lists: list of at-uri strings pointing to app.bsky.graph.list records
    hidden_replies: list of at-uri strings — specific replies to hide

    If ALL allow_* are False and allow_lists is empty/None, nobody can reply
    (allow: [] on the record).
    """
    rules = []
    if allow_following:
        rules.append({"$type": "app.bsky.feed.threadgate#followingRule"})
    if allow_mentioned:
        rules.append({"$type": "app.bsky.feed.threadgate#mentionRule"})
    if allow_lists:
        for uri in allow_lists:
            rules.append({"$type": "app.bsky.feed.threadgate#listRule", "list": uri})
    gate = {"allow": rules}
    if hidden_replies:
        gate["hiddenReplies"] = list(hidden_replies)
    return gate


def threadgate_nobody():
    """Convenience: nobody can reply."""
    return {"allow": []}


def threadgate_anyone():
    """Convenience: return None so posts.create() skips the gate record entirely."""
    return None


# ---------- postgate builders ----------

def build_postgate(disable_embedding=False, detached_embedding_uris=None):
    """Build a postgate record body.

    disable_embedding: True forbids anyone from quoting this post.
    detached_embedding_uris: list of at-uri strings — existing quotes to hide
        (already-published quotes get "detached" from your post's UI).
    """
    gate = {}
    if disable_embedding:
        gate["embeddingRules"] = [{"$type": "app.bsky.feed.postgate#disableRule"}]
    if detached_embedding_uris:
        gate["detachedEmbeddingUris"] = list(detached_embedding_uris)
    return gate


def postgate_no_quotes():
    """Convenience: no one can quote."""
    return {"embeddingRules": [{"$type": "app.bsky.feed.postgate#disableRule"}]}


# ---------- mutation of existing gates ----------

def _put_gate(client, collection, rkey, record):
    record["createdAt"] = record.get("createdAt")
    return client.com.atproto.repo.put_record({
        "repo": client.me.did,
        "collection": collection,
        "rkey": rkey,
        "record": record,
    })


def hide_reply(client, post_uri, reply_uri):
    """Add a reply's URI to the post's threadgate hiddenReplies list.
    Creates the threadgate if it doesn't exist yet."""
    import datetime as dt
    parts = post_uri.replace("at://", "").split("/")
    did, _, rkey = parts
    try:
        existing = client.com.atproto.repo.get_record({
            "repo": did, "collection": "app.bsky.feed.threadgate", "rkey": rkey,
        })
        rec = dict(existing.value) if hasattr(existing, "value") else dict(existing["value"])
    except Exception:
        rec = {"$type": "app.bsky.feed.threadgate", "post": post_uri, "allow": None}
    hidden = list(rec.get("hiddenReplies") or [])
    if reply_uri not in hidden:
        hidden.append(reply_uri)
    rec["hiddenReplies"] = hidden
    rec.setdefault("post", post_uri)
    rec["createdAt"] = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    return _put_gate(client, "app.bsky.feed.threadgate", rkey, rec)


def detach_quote(client, quoted_post_uri, quote_post_uri):
    """Detach an existing quote-post from your original post.
    The quoter's post remains visible on their profile, but the embed is broken."""
    import datetime as dt
    parts = quoted_post_uri.replace("at://", "").split("/")
    did, _, rkey = parts
    try:
        existing = client.com.atproto.repo.get_record({
            "repo": did, "collection": "app.bsky.feed.postgate", "rkey": rkey,
        })
        rec = dict(existing.value) if hasattr(existing, "value") else dict(existing["value"])
    except Exception:
        rec = {"$type": "app.bsky.feed.postgate", "post": quoted_post_uri}
    detached = list(rec.get("detachedEmbeddingUris") or [])
    if quote_post_uri not in detached:
        detached.append(quote_post_uri)
    rec["detachedEmbeddingUris"] = detached
    rec.setdefault("post", quoted_post_uri)
    rec["createdAt"] = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    return _put_gate(client, "app.bsky.feed.postgate", rkey, rec)
