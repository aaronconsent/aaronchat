"""Starter packs — curated onboarding bundles of accounts + feeds.

Anatomy of a Bluesky starter pack:
    1) A `reference` list (app.bsky.graph.list, purpose=referencelist) that
       enumerates the accounts.
    2) One `app.bsky.graph.starterpack` record that names the pack, points at
       the reference list, and optionally lists feeds to auto-follow.

The atproto SDK exposes both, but we build the records as dicts for control.

Usage:
    from bluesky.client import get_client
    from bluesky import starterpack
    client = get_client()
    result = starterpack.create(
        client,
        name="East Texas Service Pros",
        description="Local contractors worth following",
        actor_handles=["heyaaron.bsky.social", "bookedjob.bsky.social"],
        feed_uris=["at://did:.../.../local-tx"],
    )
    # returns {'starterpack': {uri,cid}, 'list': {uri,cid}, 'share_url': 'https://...'}
"""
import datetime as dt

from bluesky import graph as graph_mod


def _now_iso():
    return dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _create(client, collection, record):
    resp = client.com.atproto.repo.create_record({
        "repo": client.me.did, "collection": collection, "record": record,
    })
    return {"uri": resp.uri, "cid": resp.cid}


def create(client, name, description="", actor_handles=None, feed_uris=None,
           list_uri=None):
    """Create a starter pack. Returns dict with 'starterpack', 'list', 'share_url'.

    actor_handles: list of handles or DIDs to include in the underlying list.
    feed_uris:     list of at-uri strings for custom feeds to auto-follow.
    list_uri:      REUSE an existing reference-list URI instead of creating one.
    """
    actor_handles = actor_handles or []
    feed_uris = feed_uris or []

    # 1) Reference list (create or reuse)
    if list_uri is None:
        lst = graph_mod.create_list(client, name=name, purpose="reference",
                                     description=description)
        list_uri = lst["uri"]
        for handle in actor_handles:
            graph_mod.add_to_list(client, list_uri, handle)
    # If reusing, caller is responsible for list membership.

    # 2) Starter pack record
    record = {
        "$type": "app.bsky.graph.starterpack",
        "name": name[:50],                        # spec max 50 chars
        "description": description[:300] if description else "",
        "list": list_uri,
        "feeds": [{"uri": u} for u in feed_uris],
        "createdAt": _now_iso(),
    }
    sp = _create(client, "app.bsky.graph.starterpack", record)

    # Derive share URL: bsky.app/starter-pack/<handle>/<rkey>
    rkey = sp["uri"].split("/")[-1]
    handle = client.me.handle if hasattr(client, "me") else ""
    share_url = f"https://bsky.app/starter-pack/{handle}/{rkey}"

    return {"starterpack": sp, "list": {"uri": list_uri}, "share_url": share_url}


def update(client, starterpack_uri, name=None, description=None,
           feed_uris=None):
    """Mutate an existing starter pack. List membership is managed via
    graph.add_to_list / graph.remove_from_list on the underlying list."""
    parts = starterpack_uri.replace("at://", "").split("/")
    did, coll, rkey = parts
    existing = client.com.atproto.repo.get_record({
        "repo": did, "collection": coll, "rkey": rkey,
    })
    rec = dict(existing.value) if hasattr(existing, "value") else dict(existing["value"])
    if name is not None:
        rec["name"] = name[:50]
    if description is not None:
        rec["description"] = description[:300]
    if feed_uris is not None:
        rec["feeds"] = [{"uri": u} for u in feed_uris]
    rec["updatedAt"] = _now_iso()
    client.com.atproto.repo.put_record({
        "repo": did, "collection": coll, "rkey": rkey, "record": rec,
    })
    return True


def delete(client, starterpack_uri):
    """Delete the starter pack record. The underlying list SURVIVES —
    delete separately via posts.delete(list_uri) if desired."""
    from bluesky import posts
    return posts.delete(client, starterpack_uri)


def get(client, starterpack_uri):
    """Fetch a starter pack (name, description, list, feeds, members via
    joinedWeekCount etc.)."""
    resp = client.app.bsky.graph.get_starter_pack({"starterPack": starterpack_uri})
    return resp


def list_own(client, actor=None, cursor=None, limit=50):
    """List starter packs created by an actor. Defaults to the logged-in user."""
    resp = client.app.bsky.graph.get_actor_starter_packs({
        "actor": actor or client.me.did,
        "cursor": cursor, "limit": limit,
    })
    return resp
