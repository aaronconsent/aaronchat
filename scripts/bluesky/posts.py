"""Post creation for Bluesky — text/reply/quote/repost/delete + threadgates/postgates.

This module intentionally builds records as plain dicts so we can control every
field on the wire (facets, langs, self-labels, gates, embeds). The atproto SDK
would do this too, but the dict-first flow makes it easier to unit-test and
mirrors what the AT Protocol schema documents.

All post-creation helpers return {'uri', 'cid'} — the two identifiers you need
to reply to, quote, delete, or gate the post afterwards.

Usage:
    from bluesky.client import get_client
    from bluesky import posts, media, facets

    client = get_client()

    text = "Free first year for East Texas service pros: https://aaron.chat"
    _, fac = facets.build(text, client=client)
    card = media.auto_link_card(client, "https://aaron.chat/plans/house-special/")
    result = posts.create(client, text, facets=fac, embed=card, langs=["en"])
    # result → {'uri': 'at://did:plc:.../app.bsky.feed.post/xxx', 'cid': 'bafy...'}
"""
import datetime as dt


DEFAULT_LANGS = ["en"]


def _now_iso():
    return dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _post_record(text, facets=None, embed=None, reply=None, langs=None, labels=None, tags=None):
    """Assemble an app.bsky.feed.post record dict from parts."""
    rec = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": _now_iso(),
        "langs": langs or DEFAULT_LANGS,
    }
    if facets:
        rec["facets"] = facets
    if embed:
        rec["embed"] = embed
    if reply:
        rec["reply"] = reply
    if labels:
        rec["labels"] = {"$type": "com.atproto.label.defs#selfLabels",
                         "values": [{"val": v} for v in labels]}
    if tags:
        rec["tags"] = tags
    return rec


def _create_record(client, collection, record, rkey=None):
    """Send createRecord to the user's PDS. Returns {'uri', 'cid'}."""
    payload = {
        "repo": client.me.did,
        "collection": collection,
        "record": record,
    }
    if rkey:
        payload["rkey"] = rkey
    resp = client.com.atproto.repo.create_record(payload)
    return {"uri": resp.uri, "cid": resp.cid}


# ---------- text post ----------

def create(client, text, facets=None, embed=None, langs=None, labels=None, tags=None,
           reply=None, threadgate=None, postgate=None):
    """Create a plain post. Returns {'uri', 'cid'}.

    threadgate/postgate: pass the dict from gates.build_threadgate/build_postgate to
    apply reply/quote controls in the same call (they're stored as SIDE records
    keyed to the same rkey).
    """
    if len(text.encode("utf-8")) > 3000:
        raise ValueError(f"post text {len(text.encode('utf-8'))} bytes; Bluesky max is 3000 graphemes ≈ 3000 bytes")
    if len(text) > 300:
        # Actual limit is 300 graphemes, but for safety
        raise ValueError(f"post text {len(text)} chars; Bluesky max is 300")
    rec = _post_record(text, facets=facets, embed=embed, reply=reply, langs=langs,
                       labels=labels, tags=tags)
    result = _create_record(client, "app.bsky.feed.post", rec)

    # Side records: threadgate/postgate share the same rkey as the post
    if threadgate is not None or postgate is not None:
        rkey = result["uri"].split("/")[-1]
        if threadgate is not None:
            gate_rec = dict(threadgate)
            gate_rec["post"] = result["uri"]
            gate_rec["createdAt"] = _now_iso()
            _create_record(client, "app.bsky.feed.threadgate", gate_rec, rkey=rkey)
        if postgate is not None:
            gate_rec = dict(postgate)
            gate_rec["post"] = result["uri"]
            gate_rec["createdAt"] = _now_iso()
            _create_record(client, "app.bsky.feed.postgate", gate_rec, rkey=rkey)

    return result


# ---------- replies ----------

def create_reply(client, root, parent, text, **kwargs):
    """Reply to a post in a thread.

    root:   {'uri': ..., 'cid': ...} — top of the thread (self-ref if you're replying
            to a top-level post).
    parent: {'uri': ..., 'cid': ...} — the immediate ancestor you're replying to.
    """
    reply_ref = {"root": root, "parent": parent}
    return create(client, text, reply=reply_ref, **kwargs)


def build_thread(client, texts, root_reply_to=None, per_post_kwargs=None):
    """Post a chain of texts as a self-reply thread. Returns a list of results.

    root_reply_to: if given ({'uri','cid'}), the chain replies to that post
                   instead of starting fresh.
    per_post_kwargs: optional list of kwarg dicts, one per text, applied per-post
                     (e.g. embed on tweet #3 only). Length must match texts.
    """
    if per_post_kwargs and len(per_post_kwargs) != len(texts):
        raise ValueError("per_post_kwargs length must equal texts length")
    per_post_kwargs = per_post_kwargs or [{}] * len(texts)

    results = []
    root = root_reply_to  # None means the first post is the root
    parent = root_reply_to
    for i, text in enumerate(texts):
        kwargs = per_post_kwargs[i]
        if root is None:
            # First post starts the thread
            first = create(client, text, **kwargs)
            root = first
            parent = first
            results.append(first)
        else:
            reply = create_reply(client, root=root, parent=parent, text=text, **kwargs)
            parent = reply
            results.append(reply)
    return results


# ---------- quote posts ----------

def create_quote(client, quoted, text, media_embed=None, **kwargs):
    """Quote-post another post with your own commentary.

    quoted:      {'uri', 'cid'} of the post being quoted
    media_embed: optional images/video/link-card to attach alongside the quote
                 (uses app.bsky.embed.recordWithMedia).
    """
    if media_embed:
        embed = {
            "$type": "app.bsky.embed.recordWithMedia",
            "record": {
                "$type": "app.bsky.embed.record",
                "record": {"uri": quoted["uri"], "cid": quoted["cid"]},
            },
            "media": media_embed,
        }
    else:
        embed = {
            "$type": "app.bsky.embed.record",
            "record": {"uri": quoted["uri"], "cid": quoted["cid"]},
        }
    return create(client, text, embed=embed, **kwargs)


# ---------- reposts ----------

def create_repost(client, target):
    """Repost (retweet-equivalent) — no commentary.

    target: {'uri', 'cid'} of the post to repost.
    """
    rec = {
        "$type": "app.bsky.feed.repost",
        "subject": {"uri": target["uri"], "cid": target["cid"]},
        "createdAt": _now_iso(),
    }
    return _create_record(client, "app.bsky.feed.repost", rec)


# ---------- delete ----------

def delete(client, uri):
    """Delete any record you own by URI. Works for posts, reposts, likes, follows..."""
    # URI shape: at://<did>/<collection>/<rkey>
    parts = uri.replace("at://", "").split("/")
    if len(parts) != 3:
        raise ValueError(f"malformed at-uri: {uri!r}")
    did, collection, rkey = parts
    client.com.atproto.repo.delete_record({
        "repo": did,
        "collection": collection,
        "rkey": rkey,
    })
    return True
