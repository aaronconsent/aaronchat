"""Profile, custom fields, featured tags, pinned status, endorsements, preferences."""


def update(client, *, display_name=None, note=None, avatar_path=None,
           header_path=None, locked=None, bot=None, discoverable=None,
           hide_collections=None, fields=None):
    """Update profile fields. Anything left None is untouched.

    fields: list of {"name": "...", "value": "..."} up to 4 entries. Include
            rel=me URLs inside `value` (as `<a rel="me" href="...">`) or a
            bare URL — Mastodon auto-verifies with the linked-back page.
    """
    params = {}
    files = {}
    if display_name is not None:
        params["display_name"] = display_name
    if note is not None:
        params["note"] = note
    if locked is not None:
        params["locked"] = "true" if locked else "false"
    if bot is not None:
        params["bot"] = "true" if bot else "false"
    if discoverable is not None:
        params["discoverable"] = "true" if discoverable else "false"
    if hide_collections is not None:
        params["hide_collections"] = "true" if hide_collections else "false"
    if fields is not None:
        for i, f in enumerate(fields[:4]):
            params[f"fields_attributes[{i}][name]"] = f.get("name", "")
            params[f"fields_attributes[{i}][value]"] = f.get("value", "")
    if avatar_path:
        with open(avatar_path, "rb") as fh:
            files["avatar"] = (avatar_path.split("/")[-1], fh.read(), "image/png")
    if header_path:
        with open(header_path, "rb") as fh:
            files["header"] = (header_path.split("/")[-1], fh.read(), "image/png")

    return client.patch("/api/v1/accounts/update_credentials",
                         params=params or {}, files=files or None)


# ---------- featured tags ----------

def list_featured_tags(client):
    return client.get("/api/v1/featured_tags")


def feature_tag(client, name):
    """Pin a hashtag to your profile."""
    return client.post("/api/v1/featured_tags", params={"name": name})


def unfeature_tag(client, tag_id):
    return client.delete(f"/api/v1/featured_tags/{tag_id}")


def suggestions_for_featured_tags(client):
    """Server-suggested tags to feature (based on your usage)."""
    return client.get("/api/v1/featured_tags/suggestions")


# ---------- pinned statuses ----------

def list_pinned(client, actor_id=None):
    """List pinned statuses. Actor defaults to logged-in account."""
    actor = actor_id or client.me["id"]
    return client.get(f"/api/v1/accounts/{actor}/statuses",
                       params={"pinned": "true"})


def pin(client, status_id):
    return client.post(f"/api/v1/statuses/{status_id}/pin")


def unpin(client, status_id):
    return client.post(f"/api/v1/statuses/{status_id}/unpin")


# ---------- endorsed accounts ("featured people you follow") ----------

def list_endorsements(client):
    return client.get("/api/v1/endorsements")


def endorse(client, account_id):
    return client.post(f"/api/v1/accounts/{account_id}/pin")


def unendorse(client, account_id):
    return client.post(f"/api/v1/accounts/{account_id}/unpin")


# ---------- preferences ----------

def get_preferences(client):
    """Read defaults: posting:default:visibility / :sensitive / :language,
    reading:expand:media, reading:expand:spoilers."""
    return client.get("/api/v1/preferences")
