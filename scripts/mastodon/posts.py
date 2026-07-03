"""Status creation + admin — text, CW, replies, threads, boosts, edit, delete,
quote (fallback via URL embed), scheduled statuses, language tag.

All helpers accept an optional `visibility` kwarg (public | unlisted | private
| direct) even though the feature menu didn't tick per-post visibility, because
DMs = visibility=direct. Default is 'public'.
"""


DEFAULT_LANG = "en"


def create(client, text, *, visibility="public", spoiler=None, in_reply_to_id=None,
           media_ids=None, poll=None, language=None, sensitive=False,
           scheduled_at=None, idempotency_key=None):
    """Create a status. Returns the created status dict."""
    params = {
        "status": text or "",
        "visibility": visibility,
        "language": language or DEFAULT_LANG,
        "sensitive": "true" if sensitive else "false",
    }
    if spoiler:
        params["spoiler_text"] = spoiler
    if in_reply_to_id:
        params["in_reply_to_id"] = in_reply_to_id
    if media_ids:
        params["media_ids[]"] = list(media_ids)
    if poll:
        # {options: [...], expires_in: N, multiple: bool, hide_totals: bool}
        for i, opt in enumerate(poll.get("options", [])):
            params[f"poll[options][{i}]"] = opt
        params["poll[expires_in]"] = poll.get("expires_in", 86400)
        params["poll[multiple]"] = "true" if poll.get("multiple") else "false"
        params["poll[hide_totals]"] = "true" if poll.get("hide_totals") else "false"
    if scheduled_at:
        params["scheduled_at"] = scheduled_at
    headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
    if headers:
        # form-encoded POST already sets Content-Type, so we merge via _req
        # by using client.post directly won't pass headers — do a small dance:
        return client._req("POST", "/api/v1/statuses", params=params, headers=headers)
    return client.post("/api/v1/statuses", params=params)


def reply(client, in_reply_to_id, text, **kwargs):
    """Reply to a status. Extra kwargs forwarded to create()."""
    kwargs["in_reply_to_id"] = in_reply_to_id
    return create(client, text, **kwargs)


def build_thread(client, texts, *, per_post_kwargs=None, in_reply_to_id=None, **base_kwargs):
    """Post a self-reply chain. Returns list of created statuses.

    per_post_kwargs: optional list, one dict per text (media_ids on tweet #3, etc.)
    in_reply_to_id: if given, the first post replies to that status; else new thread
    base_kwargs: applied to every post
    """
    if per_post_kwargs and len(per_post_kwargs) != len(texts):
        raise ValueError("per_post_kwargs length must equal texts length")
    per_post_kwargs = per_post_kwargs or [{}] * len(texts)
    results = []
    parent = in_reply_to_id
    for i, t in enumerate(texts):
        kw = {**base_kwargs, **per_post_kwargs[i]}
        if parent:
            kw["in_reply_to_id"] = parent
        st = create(client, t, **kw)
        results.append(st)
        parent = st["id"]
    return results


def edit(client, status_id, text, *, spoiler=None, media_ids=None,
         media_attributes=None, sensitive=None, language=None, poll=None):
    """Edit a status (Mastodon 4.0+). Returns the updated status."""
    params = {"status": text or ""}
    if spoiler is not None:
        params["spoiler_text"] = spoiler
    if language is not None:
        params["language"] = language
    if sensitive is not None:
        params["sensitive"] = "true" if sensitive else "false"
    if media_ids is not None:
        params["media_ids[]"] = list(media_ids)
    if media_attributes:
        # Update alt-text / focus without re-uploading:
        # [{"id": "...", "description": "...", "focus": "0.0,-0.5"}]
        for i, attr in enumerate(media_attributes):
            for k, v in attr.items():
                params[f"media_attributes[{i}][{k}]"] = v
    if poll:
        for i, opt in enumerate(poll.get("options", [])):
            params[f"poll[options][{i}]"] = opt
        params["poll[expires_in]"] = poll.get("expires_in", 86400)
    return client.put(f"/api/v1/statuses/{status_id}", params=params)


def delete(client, status_id):
    """Delete a status. Returns the source for redraft."""
    return client.delete(f"/api/v1/statuses/{status_id}")


def boost(client, status_id, visibility=None):
    """Reblog / boost a status. Optional visibility scope."""
    params = {}
    if visibility:
        params["visibility"] = visibility
    return client.post(f"/api/v1/statuses/{status_id}/reblog", params=params or None)


def unboost(client, status_id):
    return client.post(f"/api/v1/statuses/{status_id}/unreblog")


def pin(client, status_id):
    return client.post(f"/api/v1/statuses/{status_id}/pin")


def unpin(client, status_id):
    return client.post(f"/api/v1/statuses/{status_id}/unpin")


# ---------- quote posts ----------

def quote(client, quoted_status_url_or_id, commentary, **kwargs):
    """Quote-post another status.

    Mastodon 4.4 added native quote posts (`quote_id` param). Older instances
    have no quote primitive — the standard fallback is to include the quoted
    URL at the end of your commentary, and Mastodon renders a preview card.

    We try native first (send `quote_id`); on 400/422 fallback to URL embed.
    """
    # If it looks like a full URL, use as-is for the fallback; also try to
    # extract the numeric id for native support
    quoted_id = None
    quoted_url = None
    if str(quoted_status_url_or_id).isdigit():
        quoted_id = str(quoted_status_url_or_id)
    else:
        quoted_url = str(quoted_status_url_or_id)
        # try to parse trailing id from URL
        try:
            quoted_id = quoted_url.rstrip("/").split("/")[-1]
            if not quoted_id.isdigit():
                quoted_id = None
        except Exception:
            quoted_id = None

    # Attempt native quote first
    if quoted_id:
        try:
            params = _base_params(kwargs, commentary)
            params["quote_id"] = quoted_id
            return client.post("/api/v1/statuses", params=params)
        except Exception:
            pass

    # Fallback — URL at end of body (Mastodon fetches OG for the preview card)
    if not quoted_url:
        raise ValueError("quote fallback needs a full URL; only numeric id was given")
    text = f"{commentary}\n\n{quoted_url}".strip()
    return create(client, text, **kwargs)


def _base_params(kwargs, text):
    """Same param assembly as create() but as a plain dict — used by quote()."""
    params = {
        "status": text or "",
        "visibility": kwargs.get("visibility", "public"),
        "language": kwargs.get("language", DEFAULT_LANG),
        "sensitive": "true" if kwargs.get("sensitive") else "false",
    }
    if kwargs.get("spoiler"):
        params["spoiler_text"] = kwargs["spoiler"]
    if kwargs.get("in_reply_to_id"):
        params["in_reply_to_id"] = kwargs["in_reply_to_id"]
    if kwargs.get("media_ids"):
        params["media_ids[]"] = list(kwargs["media_ids"])
    return params


# ---------- scheduled statuses (server-side scheduling) ----------

def list_scheduled(client):
    return client.get("/api/v1/scheduled_statuses")


def get_scheduled(client, scheduled_id):
    return client.get(f"/api/v1/scheduled_statuses/{scheduled_id}")


def reschedule(client, scheduled_id, scheduled_at):
    return client.put(f"/api/v1/scheduled_statuses/{scheduled_id}",
                       params={"scheduled_at": scheduled_at})


def cancel_scheduled(client, scheduled_id):
    return client.delete(f"/api/v1/scheduled_statuses/{scheduled_id}")


# ---------- reads ----------

def get_status(client, status_id):
    return client.get(f"/api/v1/statuses/{status_id}")


def get_context(client, status_id):
    """Return the full ancestor + descendant tree for a status."""
    return client.get(f"/api/v1/statuses/{status_id}/context")


def source(client, status_id):
    """Get the plain-text source for a status (pre-render), for editing."""
    return client.get(f"/api/v1/statuses/{status_id}/source")


def get_history(client, status_id):
    """Edit history for a status."""
    return client.get(f"/api/v1/statuses/{status_id}/history")
