"""Read-side helpers — timeline, notifications, search, threads, actor profiles.

All read endpoints paginate on `cursor`. Callers can either take a single
page or use the `iterate_*` generators.
"""


# ---------- timeline / feeds ----------

def get_timeline(client, algorithm=None, cursor=None, limit=50):
    """Get the account's home timeline."""
    params = {"cursor": cursor, "limit": limit}
    if algorithm:
        params["algorithm"] = algorithm
    return client.app.bsky.feed.get_timeline(params)


def get_author_feed(client, actor, cursor=None, limit=50, filter=None):
    """Feed of an author's posts. `filter` ∈ posts_with_replies |
    posts_no_replies | posts_with_media | posts_and_author_threads."""
    params = {"actor": actor, "cursor": cursor, "limit": limit}
    if filter:
        params["filter"] = filter
    return client.app.bsky.feed.get_author_feed(params)


def get_actor_likes(client, actor, cursor=None, limit=50):
    return client.app.bsky.feed.get_actor_likes({
        "actor": actor, "cursor": cursor, "limit": limit,
    })


def get_feed(client, feed_uri, cursor=None, limit=50):
    """Fetch a custom feed generator's content."""
    return client.app.bsky.feed.get_feed({
        "feed": feed_uri, "cursor": cursor, "limit": limit,
    })


# ---------- threads ----------

def get_post_thread(client, uri, depth=6, parent_height=80):
    """Fetch a full thread rooted at `uri`."""
    return client.app.bsky.feed.get_post_thread({
        "uri": uri, "depth": depth, "parentHeight": parent_height,
    })


def get_posts(client, uris):
    """Batch-fetch up to 25 posts by URI. Returns hydrated PostView list."""
    return client.app.bsky.feed.get_posts({"uris": uris})


# ---------- notifications ----------

def list_notifications(client, cursor=None, limit=50, seen_at=None):
    params = {"cursor": cursor, "limit": limit}
    if seen_at:
        params["seenAt"] = seen_at
    return client.app.bsky.notification.list_notifications(params)


def get_unread_count(client, seen_at=None):
    params = {}
    if seen_at:
        params["seenAt"] = seen_at
    resp = client.app.bsky.notification.get_unread_count(params)
    return resp.count if hasattr(resp, "count") else resp["count"]


def update_seen(client, seen_at):
    """Mark notifications as seen up to `seen_at` (ISO timestamp)."""
    client.app.bsky.notification.update_seen({"seenAt": seen_at})
    return True


# ---------- search ----------

def search_posts(client, q, sort="latest", author=None, mentions=None,
                 lang=None, since=None, until=None, tag=None,
                 cursor=None, limit=25):
    """Full-text post search. `sort` ∈ top | latest."""
    params = {"q": q, "sort": sort, "cursor": cursor, "limit": limit}
    for k, v in (("author", author), ("mentions", mentions), ("lang", lang),
                 ("since", since), ("until", until), ("tag", tag)):
        if v:
            params[k] = v
    return client.app.bsky.feed.search_posts(params)


def search_actors(client, q, cursor=None, limit=25):
    """Search accounts by handle/display name."""
    return client.app.bsky.actor.search_actors({
        "q": q, "cursor": cursor, "limit": limit,
    })


# ---------- actor profiles ----------

def get_profile(client, actor):
    """Return the hydrated profile view for an actor."""
    return client.app.bsky.actor.get_profile({"actor": actor})


def get_profiles(client, actors):
    """Batch-fetch up to 25 profiles."""
    return client.app.bsky.actor.get_profiles({"actors": actors})


def get_suggestions(client, cursor=None, limit=25):
    """Who-to-follow suggestions from the AppView."""
    return client.app.bsky.actor.get_suggestions({
        "cursor": cursor, "limit": limit,
    })
