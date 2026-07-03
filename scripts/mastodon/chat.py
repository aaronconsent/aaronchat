"""Direct messages — Mastodon has no separate DM channel; DMs are just
statuses with visibility=direct. This module wraps that idiom + the
conversations feed + read markers.
"""

from mastodon import posts as posts_mod
from mastodon.graph import _resolve


def send(client, to_handles, text, *, in_reply_to_id=None, spoiler=None,
         media_ids=None, sensitive=False, language="en", idempotency_key=None):
    """Send a DM to one or more Mastodon handles.

    Mastodon DMs are statuses with visibility=direct. Recipients only see the
    status if they're mentioned by handle in the text — so we always prefix
    the mentions before your body text.

    to_handles: list of @user@instance strings (with or without leading @).
    """
    if isinstance(to_handles, str):
        to_handles = [to_handles]
    mentions = " ".join(f"@{h.lstrip('@')}" for h in to_handles)
    body = f"{mentions} {text}".strip()
    return posts_mod.create(
        client, body,
        visibility="direct",
        in_reply_to_id=in_reply_to_id,
        spoiler=spoiler,
        media_ids=media_ids,
        sensitive=sensitive,
        language=language,
        idempotency_key=idempotency_key,
    )


# ---------- conversations feed ----------

def list_conversations(client, *, max_id=None, since_id=None, min_id=None, limit=20):
    params = {"limit": limit}
    if max_id: params["max_id"] = max_id
    if since_id: params["since_id"] = since_id
    if min_id: params["min_id"] = min_id
    return client.get("/api/v1/conversations", params=params)


def mark_conversation_read(client, conv_id):
    return client.post(f"/api/v1/conversations/{conv_id}/read")


def delete_conversation(client, conv_id):
    return client.delete(f"/api/v1/conversations/{conv_id}")


# ---------- read markers ----------

def get_markers(client, timelines=("home", "notifications")):
    """Retrieve read markers for the requested timelines."""
    return client.get("/api/v1/markers",
                       params={"timeline[]": list(timelines)})


def set_markers(client, home_last=None, notifications_last=None):
    """Set the last read status/notification ids per timeline."""
    params = {}
    if home_last is not None:
        params["home[last_read_id]"] = str(home_last)
    if notifications_last is not None:
        params["notifications[last_read_id]"] = str(notifications_last)
    if not params:
        raise ValueError("nothing to update")
    return client.post("/api/v1/markers", params=params)
