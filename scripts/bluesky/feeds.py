"""Custom feed generator publishing — expose an algorithmic feed on your DID.

A "custom feed" on Bluesky is:
    1) A public HTTP service (feed generator) that returns a list of post URIs
       when polled at getFeedSkeleton — you host this elsewhere (Cloudflare
       Worker, Deno Deploy, etc.).
    2) An `app.bsky.feed.generator` record on YOUR repo advertising the feed
       (name, description, avatar, its service DID).

This module handles the RECORD side only. The actual feed algorithm lives in
your feed-generator service.

Usage:
    from bluesky.client import get_client
    from bluesky import feeds
    result = feeds.publish(
        client,
        rkey="east-texas-service",
        did="did:web:feeds.aaron.chat",   # your feed-generator's DID
        display_name="East Texas Service",
        description="Posts from Texas contractors",
        avatar_path="content/feed-avatar.jpg",
    )
"""
import datetime as dt


def _now_iso():
    return dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def publish(client, rkey, did, display_name, description="", avatar_path=None,
            accepts_interactions=False, content_mode=None):
    """Create or update a feed generator record.

    rkey: unique key for the feed on your repo (e.g. 'east-texas-service')
    did:  DID of the feed-generator service (usually did:web:<host>)
    accepts_interactions: True if the service handles interaction telemetry
    content_mode: 'app.bsky.feed.defs#contentModeVideo' etc, or None
    """
    record = {
        "$type": "app.bsky.feed.generator",
        "did": did,
        "displayName": display_name[:24],
        "description": description[:300],
        "acceptsInteractions": bool(accepts_interactions),
        "createdAt": _now_iso(),
    }
    if content_mode:
        record["contentMode"] = content_mode
    if avatar_path:
        with open(avatar_path, "rb") as f:
            data = f.read()
        record["avatar"] = client.com.atproto.repo.upload_blob(data).blob

    client.com.atproto.repo.put_record({
        "repo": client.me.did,
        "collection": "app.bsky.feed.generator",
        "rkey": rkey,
        "record": record,
    })
    uri = f"at://{client.me.did}/app.bsky.feed.generator/{rkey}"
    return {"uri": uri, "share_url": f"https://bsky.app/profile/{client.me.handle}/feed/{rkey}"}


def unpublish(client, rkey):
    """Remove a feed generator record. The underlying service keeps running
    but won't appear in feed pickers anymore."""
    client.com.atproto.repo.delete_record({
        "repo": client.me.did,
        "collection": "app.bsky.feed.generator",
        "rkey": rkey,
    })
    return True


def describe(client, feed_uri):
    """Describe a feed generator — its policies, accepted params, etc."""
    return client.app.bsky.feed.describe_feed_generator({})


def get_actor_feeds(client, actor=None, cursor=None, limit=50):
    """List all feeds published by an actor."""
    return client.app.bsky.feed.get_actor_feeds({
        "actor": actor or client.me.did, "cursor": cursor, "limit": limit,
    })


def get_popular_feeds(client, query=None, cursor=None, limit=50):
    """Discover popular feeds (unspecced but widely available)."""
    params = {"cursor": cursor, "limit": limit}
    if query:
        params["query"] = query
    try:
        return client.app.bsky.unspecced.get_popular_feed_generators(params)
    except AttributeError:
        # Some SDK versions namespace this differently
        return client._call_xrpc("app.bsky.unspecced.getPopularFeedGenerators",
                                  params, method="GET")
