"""Social graph — follow/unfollow accounts + hashtags, requests, mute, block, lists."""


def _resolve(client, handle_or_id):
    """Turn a handle (@user@instance or user@instance) or DID-style local id
    into a numeric account id. Numeric ids pass through."""
    s = str(handle_or_id).lstrip("@")
    if s.isdigit():
        return s
    resp = client.get("/api/v1/accounts/lookup", params={"acct": s})
    if not resp or "id" not in resp:
        # Fall back to search
        r = client.get("/api/v2/search",
                        params={"q": s, "type": "accounts", "resolve": "true", "limit": 1})
        accounts = r.get("accounts", [])
        if not accounts:
            raise ValueError(f"could not resolve account: {handle_or_id}")
        return accounts[0]["id"]
    return resp["id"]


# ---------- follow / unfollow accounts ----------

def follow(client, handle_or_id, *, notify=False, reblogs=True, languages=None):
    aid = _resolve(client, handle_or_id)
    params = {
        "reblogs": "true" if reblogs else "false",
        "notify": "true" if notify else "false",
    }
    if languages:
        params["languages[]"] = list(languages)
    return client.post(f"/api/v1/accounts/{aid}/follow", params=params)


def unfollow(client, handle_or_id):
    aid = _resolve(client, handle_or_id)
    return client.post(f"/api/v1/accounts/{aid}/unfollow")


# ---------- follow requests (locked accounts) ----------

def list_follow_requests(client, limit=40):
    return client.get("/api/v1/follow_requests", params={"limit": limit})


def accept_follow_request(client, account_id):
    return client.post(f"/api/v1/follow_requests/{account_id}/authorize")


def reject_follow_request(client, account_id):
    return client.post(f"/api/v1/follow_requests/{account_id}/reject")


# ---------- follow / unfollow hashtags ----------

def follow_hashtag(client, name):
    return client.post(f"/api/v1/tags/{name}/follow")


def unfollow_hashtag(client, name):
    return client.post(f"/api/v1/tags/{name}/unfollow")


def list_followed_hashtags(client, limit=100):
    return client.get("/api/v1/followed_tags", params={"limit": limit})


def get_hashtag(client, name):
    return client.get(f"/api/v1/tags/{name}")


# ---------- mute / block ----------

def mute(client, handle_or_id, *, notifications=True, duration=0):
    """duration in seconds (0 = indefinite). notifications=False = mute posts
    but still receive notifications."""
    aid = _resolve(client, handle_or_id)
    params = {
        "notifications": "true" if notifications else "false",
        "duration": duration,
    }
    return client.post(f"/api/v1/accounts/{aid}/mute", params=params)


def unmute(client, handle_or_id):
    aid = _resolve(client, handle_or_id)
    return client.post(f"/api/v1/accounts/{aid}/unmute")


def list_mutes(client, limit=100):
    return client.get("/api/v1/mutes", params={"limit": limit})


def block(client, handle_or_id):
    aid = _resolve(client, handle_or_id)
    return client.post(f"/api/v1/accounts/{aid}/block")


def unblock(client, handle_or_id):
    aid = _resolve(client, handle_or_id)
    return client.post(f"/api/v1/accounts/{aid}/unblock")


def list_blocks(client, limit=100):
    return client.get("/api/v1/blocks", params={"limit": limit})


# ---------- relationships (batch lookup) ----------

def relationships(client, account_ids):
    """Fetch relationships to N accounts in one call: following, followed_by,
    muting, blocking, requested, etc."""
    return client.get("/api/v1/accounts/relationships",
                       params={"id[]": list(account_ids)})


def familiar_followers(client, account_ids):
    """'You know X, Y who follow this person.' Great for social proof CTAs."""
    return client.get("/api/v1/accounts/familiar_followers",
                       params={"id[]": list(account_ids)})


# ---------- lists ----------

def create_list(client, title, *, replies_policy="list", exclusive=False):
    """replies_policy: followed | list | none"""
    return client.post("/api/v1/lists", params={
        "title": title,
        "replies_policy": replies_policy,
        "exclusive": "true" if exclusive else "false",
    })


def get_lists(client):
    return client.get("/api/v1/lists")


def get_list(client, list_id):
    return client.get(f"/api/v1/lists/{list_id}")


def update_list(client, list_id, *, title=None, replies_policy=None, exclusive=None):
    params = {}
    if title is not None:
        params["title"] = title
    if replies_policy is not None:
        params["replies_policy"] = replies_policy
    if exclusive is not None:
        params["exclusive"] = "true" if exclusive else "false"
    return client.put(f"/api/v1/lists/{list_id}", params=params)


def delete_list(client, list_id):
    return client.delete(f"/api/v1/lists/{list_id}")


def add_to_list(client, list_id, account_ids):
    return client.post(f"/api/v1/lists/{list_id}/accounts",
                        params={"account_ids[]": list(account_ids)})


def remove_from_list(client, list_id, account_ids):
    return client.delete(f"/api/v1/lists/{list_id}/accounts",
                          params={"account_ids[]": list(account_ids)})


def list_members(client, list_id, limit=100):
    return client.get(f"/api/v1/lists/{list_id}/accounts", params={"limit": limit})
