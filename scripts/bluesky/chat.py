"""Direct messages (chat.bsky.*) — send, read, react, group DMs.

Chat endpoints live on api.bsky.chat (proxy service) and REQUIRE a privileged
app password. Get one via identity.create_app_password(..., privileged=True)
and store it as BLUESKY_CHAT_APP_PASSWORD in secrets/bluesky.env.

Then get a chat-scoped client:
    from bluesky.client import get_client
    client = get_client(chat_scope=True)

Every chat call needs the special `atproto-proxy` header targeting
did:web:api.bsky.chat#bsky_chat — the atproto SDK handles this when the
session was minted with the privileged password.
"""


# ---------- convos ----------

def list_convos(client, cursor=None, limit=50):
    """List all conversations."""
    return client.chat.bsky.convo.list_convos({"cursor": cursor, "limit": limit})


def get_convo(client, convo_id):
    return client.chat.bsky.convo.get_convo({"convoId": convo_id})


def get_convo_for_members(client, members):
    """Get-or-create a convo for a set of DIDs (1 or more).
    Used to start a new 1:1 or group DM."""
    return client.chat.bsky.convo.get_convo_for_members({"members": members})


def leave_convo(client, convo_id):
    return client.chat.bsky.convo.leave_convo({"convoId": convo_id})


def mute_convo(client, convo_id):
    return client.chat.bsky.convo.mute_convo({"convoId": convo_id})


def unmute_convo(client, convo_id):
    return client.chat.bsky.convo.unmute_convo({"convoId": convo_id})


def update_read(client, convo_id, message_id=None):
    """Mark messages read up to (and including) message_id."""
    params = {"convoId": convo_id}
    if message_id:
        params["messageId"] = message_id
    return client.chat.bsky.convo.update_read(params)


# ---------- messages ----------

def send_message(client, convo_id, text, facets=None, embed=None):
    """Send a message. Optional facets (rich text) and embed (post-record ref)."""
    message = {"text": text}
    if facets:
        message["facets"] = facets
    if embed:
        message["embed"] = embed
    return client.chat.bsky.convo.send_message({
        "convoId": convo_id, "message": message,
    })


def send_message_batch(client, items):
    """Send multiple messages in one round-trip.
    items = [{'convoId': ..., 'message': {'text': ...}}, ...]
    """
    return client.chat.bsky.convo.send_message_batch({"items": items})


def delete_message_for_self(client, convo_id, message_id):
    """Delete a message from YOUR view. Others still see it."""
    return client.chat.bsky.convo.delete_message_for_self({
        "convoId": convo_id, "messageId": message_id,
    })


def get_messages(client, convo_id, cursor=None, limit=50):
    """Fetch a page of messages in a convo (newest first)."""
    return client.chat.bsky.convo.get_messages({
        "convoId": convo_id, "cursor": cursor, "limit": limit,
    })


def get_log(client, cursor=None):
    """Long-poll style event log — new messages, reactions, membership changes."""
    return client.chat.bsky.convo.get_log({"cursor": cursor})


# ---------- reactions ----------

def add_reaction(client, convo_id, message_id, value):
    """React to a message. `value` is an emoji (single grapheme)."""
    return client.chat.bsky.convo.add_reaction({
        "convoId": convo_id, "messageId": message_id, "value": value,
    })


def remove_reaction(client, convo_id, message_id, value):
    return client.chat.bsky.convo.remove_reaction({
        "convoId": convo_id, "messageId": message_id, "value": value,
    })


# ---------- accept / reject requests ----------

def accept_convo(client, convo_id):
    """Accept a chat request from a stranger."""
    return client.chat.bsky.convo.accept_convo({"convoId": convo_id})


def update_all_read(client, status=None):
    """Mark ALL conversations read (status filters which ones)."""
    params = {}
    if status:
        params["status"] = status  # request | accepted
    return client.chat.bsky.convo.update_all_read(params)
