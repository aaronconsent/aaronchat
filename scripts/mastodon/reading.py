"""Reads — timelines, search, notifications, trends, suggestions, instance info,
announcements."""


# ---------- timelines ----------

def home_timeline(client, *, max_id=None, since_id=None, min_id=None, limit=40):
    params = _cursor(max_id, since_id, min_id, limit)
    return client.get("/api/v1/timelines/home", params=params)


def public_timeline(client, *, local=False, remote=False, only_media=False,
                    max_id=None, since_id=None, min_id=None, limit=40):
    params = _cursor(max_id, since_id, min_id, limit)
    if local:
        params["local"] = "true"
    if remote:
        params["remote"] = "true"
    if only_media:
        params["only_media"] = "true"
    return client.get("/api/v1/timelines/public", params=params)


def hashtag_timeline(client, name, *, any_tags=None, all_tags=None, none_tags=None,
                    local=False, only_media=False,
                    max_id=None, since_id=None, min_id=None, limit=40):
    params = _cursor(max_id, since_id, min_id, limit)
    if local:
        params["local"] = "true"
    if only_media:
        params["only_media"] = "true"
    if any_tags:
        params["any[]"] = list(any_tags)
    if all_tags:
        params["all[]"] = list(all_tags)
    if none_tags:
        params["none[]"] = list(none_tags)
    return client.get(f"/api/v1/timelines/tag/{name}", params=params)


def list_timeline(client, list_id, *, max_id=None, since_id=None, min_id=None, limit=40):
    params = _cursor(max_id, since_id, min_id, limit)
    return client.get(f"/api/v1/timelines/list/{list_id}", params=params)


def account_statuses(client, account_id, *, pinned=False, exclude_replies=False,
                     exclude_reblogs=False, only_media=False, tagged=None,
                     max_id=None, since_id=None, min_id=None, limit=40):
    params = _cursor(max_id, since_id, min_id, limit)
    if pinned: params["pinned"] = "true"
    if exclude_replies: params["exclude_replies"] = "true"
    if exclude_reblogs: params["exclude_reblogs"] = "true"
    if only_media: params["only_media"] = "true"
    if tagged: params["tagged"] = tagged
    return client.get(f"/api/v1/accounts/{account_id}/statuses", params=params)


def _cursor(max_id, since_id, min_id, limit):
    p = {"limit": limit}
    if max_id: p["max_id"] = max_id
    if since_id: p["since_id"] = since_id
    if min_id: p["min_id"] = min_id
    return p


# ---------- search ----------

def search(client, q, *, type=None, resolve=False, following=False,
           account_id=None, exclude_unreviewed=False, limit=20, offset=0):
    """type: accounts | hashtags | statuses (None = all three).

    Full-text status search only returns YOUR statuses unless the instance
    runs full-text via ElasticSearch — expect empty status results on
    most instances.
    """
    params = {"q": q, "limit": limit, "offset": offset,
              "resolve": "true" if resolve else "false"}
    if type:
        params["type"] = type
    if following:
        params["following"] = "true"
    if account_id:
        params["account_id"] = account_id
    if exclude_unreviewed:
        params["exclude_unreviewed"] = "true"
    return client.get("/api/v2/search", params=params)


# ---------- notifications ----------

NOTIF_TYPES = ("mention", "status", "reblog", "follow", "follow_request",
               "favourite", "poll", "update", "admin.sign_up", "admin.report")


def list_notifications(client, *, types=None, exclude_types=None,
                       account_id=None,
                       max_id=None, since_id=None, min_id=None, limit=40):
    params = _cursor(max_id, since_id, min_id, limit)
    if types: params["types[]"] = list(types)
    if exclude_types: params["exclude_types[]"] = list(exclude_types)
    if account_id: params["account_id"] = account_id
    return client.get("/api/v1/notifications", params=params)


def get_notification(client, notif_id):
    return client.get(f"/api/v1/notifications/{notif_id}")


def clear_notifications(client):
    return client.post("/api/v1/notifications/clear")


def dismiss_notification(client, notif_id):
    return client.post(f"/api/v1/notifications/{notif_id}/dismiss")


def unread_count(client, types=None):
    params = {}
    if types:
        params["types[]"] = list(types)
    return client.get("/api/v1/notifications/unread_count", params=params or None)


# ---------- trends ----------

def trending_statuses(client, limit=20, offset=0):
    return client.get("/api/v1/trends/statuses",
                       params={"limit": limit, "offset": offset})


def trending_tags(client, limit=20, offset=0):
    return client.get("/api/v1/trends/tags",
                       params={"limit": limit, "offset": offset})


def trending_links(client, limit=20, offset=0):
    return client.get("/api/v1/trends/links",
                       params={"limit": limit, "offset": offset})


# ---------- follow suggestions ----------

def suggestions(client, limit=40):
    return client.get("/api/v2/suggestions", params={"limit": limit})


def dismiss_suggestion(client, account_id):
    return client.delete(f"/api/v1/suggestions/{account_id}")


# ---------- instance info ----------

def instance_info(client):
    return client.get("/api/v2/instance")


def instance_info_v1(client):
    """Older /api/v1/instance — some fields differ."""
    return client.get("/api/v1/instance")


def get_instance_limits(client):
    """Extract max_toot_chars, poll option count/length, media size limits."""
    inst = instance_info(client)
    cfg = inst.get("configuration") or {}
    statuses = cfg.get("statuses") or {}
    media = cfg.get("media_attachments") or {}
    polls = cfg.get("polls") or {}
    return {
        "max_toot_chars": statuses.get("max_characters", 500),
        "max_media_attachments": statuses.get("max_media_attachments", 4),
        "characters_reserved_per_url": statuses.get("characters_reserved_per_url", 23),
        "image_size_limit": media.get("image_size_limit"),
        "video_size_limit": media.get("video_size_limit"),
        "video_frame_rate_limit": media.get("video_frame_rate_limit"),
        "max_poll_options": polls.get("max_options", 4),
        "max_poll_char_per_option": polls.get("max_characters_per_option", 50),
        "min_expiration": polls.get("min_expiration"),
        "max_expiration": polls.get("max_expiration"),
        "languages": inst.get("languages") or [],
    }


# ---------- announcements ----------

def list_announcements(client, with_dismissed=False):
    params = {"with_dismissed": "true"} if with_dismissed else None
    return client.get("/api/v1/announcements", params=params)


def dismiss_announcement(client, ann_id):
    return client.post(f"/api/v1/announcements/{ann_id}/dismiss")


def add_announcement_reaction(client, ann_id, name):
    return client.put(f"/api/v1/announcements/{ann_id}/reactions/{name}")


def remove_announcement_reaction(client, ann_id, name):
    return client.delete(f"/api/v1/announcements/{ann_id}/reactions/{name}")
