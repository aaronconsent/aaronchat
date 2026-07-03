"""Graph operations — follow, block, mute, lists.

Bluesky's social graph is a set of records under `app.bsky.graph.*`:
    follow      — you follow an account
    block       — hard block (they can't see or interact)
    listitem    — a member of one of your lists
    list        — a list container (moderation, curation, or reference)
    listblock   — subscribe to another user's list AS a block list
    starterpack — see starterpack.py

Mutes are DIFFERENT — they're private and live under
`app.bsky.graph.mute*Actor` procs, not repo records.

Every write returns {'uri', 'cid'}. Delete with `posts.delete(client, uri)`.
"""
import datetime as dt


def _now_iso():
    return dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _create(client, collection, record, rkey=None):
    payload = {"repo": client.me.did, "collection": collection, "record": record}
    if rkey:
        payload["rkey"] = rkey
    resp = client.com.atproto.repo.create_record(payload)
    return {"uri": resp.uri, "cid": resp.cid}


def _resolve_did(client, handle_or_did):
    if handle_or_did.startswith("did:"):
        return handle_or_did
    resp = client.com.atproto.identity.resolve_handle({"handle": handle_or_did})
    return resp.did if hasattr(resp, "did") else resp["did"]


# ---------- follow ----------

def follow(client, subject):
    """Follow an account. `subject` is a handle or a DID."""
    did = _resolve_did(client, subject)
    return _create(client, "app.bsky.graph.follow", {
        "$type": "app.bsky.graph.follow",
        "subject": did,
        "createdAt": _now_iso(),
    })


def unfollow(client, follow_uri):
    """Delete the follow record. Get the URI from get_follows() or from
    follow()'s return value."""
    from bluesky import posts
    return posts.delete(client, follow_uri)


# ---------- block ----------

def block(client, subject):
    """Hard-block an account. They can't see your posts or interact with you."""
    did = _resolve_did(client, subject)
    return _create(client, "app.bsky.graph.block", {
        "$type": "app.bsky.graph.block",
        "subject": did,
        "createdAt": _now_iso(),
    })


def unblock(client, block_uri):
    from bluesky import posts
    return posts.delete(client, block_uri)


# ---------- mute (private, not stored as a record) ----------

def mute_actor(client, subject):
    """Mute an account. Private — the muted user doesn't know."""
    did = _resolve_did(client, subject)
    client.app.bsky.graph.mute_actor({"actor": did})
    return True


def unmute_actor(client, subject):
    did = _resolve_did(client, subject)
    client.app.bsky.graph.unmute_actor({"actor": did})
    return True


def mute_actor_list(client, list_uri):
    """Mute everyone on a list."""
    client.app.bsky.graph.mute_actor_list({"list": list_uri})
    return True


def unmute_actor_list(client, list_uri):
    client.app.bsky.graph.unmute_actor_list({"list": list_uri})
    return True


def mute_thread(client, root_uri):
    """Mute a single thread — its notifications stop reaching you."""
    client.app.bsky.graph.mute_thread({"root": root_uri})
    return True


def unmute_thread(client, root_uri):
    client.app.bsky.graph.unmute_thread({"root": root_uri})
    return True


# ---------- lists ----------

LIST_PURPOSES = {
    "mod":       "app.bsky.graph.defs#modlist",       # block list you subscribe others to
    "curate":    "app.bsky.graph.defs#curatelist",    # curated feed source
    "reference": "app.bsky.graph.defs#referencelist", # generic reference set (used by starter packs)
}


def create_list(client, name, purpose="curate", description="", avatar_path=None):
    """Create a list container. Purpose is one of: mod, curate, reference."""
    if purpose not in LIST_PURPOSES:
        raise ValueError(f"purpose must be one of {list(LIST_PURPOSES)}")
    record = {
        "$type": "app.bsky.graph.list",
        "purpose": LIST_PURPOSES[purpose],
        "name": name[:64],
        "description": description[:300] if description else "",
        "createdAt": _now_iso(),
    }
    if avatar_path:
        with open(avatar_path, "rb") as f:
            data = f.read()
        blob = client.com.atproto.repo.upload_blob(data).blob
        record["avatar"] = blob
    return _create(client, "app.bsky.graph.list", record)


def add_to_list(client, list_uri, subject):
    """Add an account to a list. Returns the listitem {uri,cid} for removal later."""
    did = _resolve_did(client, subject)
    return _create(client, "app.bsky.graph.listitem", {
        "$type": "app.bsky.graph.listitem",
        "subject": did,
        "list": list_uri,
        "createdAt": _now_iso(),
    })


def remove_from_list(client, listitem_uri):
    from bluesky import posts
    return posts.delete(client, listitem_uri)


def subscribe_to_blocklist(client, list_uri):
    """Subscribe to someone else's modlist AS a block list — everyone on it
    is effectively blocked for you."""
    return _create(client, "app.bsky.graph.listblock", {
        "$type": "app.bsky.graph.listblock",
        "subject": list_uri,
        "createdAt": _now_iso(),
    })


def unsubscribe_from_blocklist(client, listblock_uri):
    from bluesky import posts
    return posts.delete(client, listblock_uri)


# ---------- reads ----------

def get_follows(client, actor=None, cursor=None, limit=100):
    """Who does `actor` follow? Defaults to the logged-in account."""
    resp = client.app.bsky.graph.get_follows({
        "actor": actor or client.me.did,
        "cursor": cursor, "limit": limit,
    })
    return resp


def get_followers(client, actor=None, cursor=None, limit=100):
    resp = client.app.bsky.graph.get_followers({
        "actor": actor or client.me.did,
        "cursor": cursor, "limit": limit,
    })
    return resp


def get_lists(client, actor=None, cursor=None, limit=100):
    resp = client.app.bsky.graph.get_lists({
        "actor": actor or client.me.did,
        "cursor": cursor, "limit": limit,
    })
    return resp


def get_list(client, list_uri, cursor=None, limit=100):
    """Get a list's members."""
    resp = client.app.bsky.graph.get_list({
        "list": list_uri, "cursor": cursor, "limit": limit,
    })
    return resp
