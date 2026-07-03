"""Filters v2 (context-scoped keyword + status filters) + legacy v1 muted words."""


FILTER_CONTEXTS = ("home", "notifications", "public", "thread", "account")
FILTER_ACTIONS = ("warn", "hide")


# ---------- v2 filters ----------

def list_filters(client):
    return client.get("/api/v2/filters")


def get_filter(client, filter_id):
    return client.get(f"/api/v2/filters/{filter_id}")


def create_filter(client, title, *, context, action="warn", expires_in=None,
                  keywords=None, statuses=None):
    """Create a v2 filter.

    keywords: list of {"keyword": "...", "whole_word": bool}
    statuses: list of status ids to hide
    """
    if not all(c in FILTER_CONTEXTS for c in context):
        raise ValueError(f"context must be from {FILTER_CONTEXTS}")
    if action not in FILTER_ACTIONS:
        raise ValueError(f"action must be one of {FILTER_ACTIONS}")
    params = {
        "title": title,
        "context[]": list(context),
        "filter_action": action,
    }
    if expires_in:
        params["expires_in"] = expires_in
    if keywords:
        for i, k in enumerate(keywords):
            params[f"keywords_attributes[{i}][keyword]"] = k["keyword"]
            params[f"keywords_attributes[{i}][whole_word]"] = (
                "true" if k.get("whole_word") else "false"
            )
    if statuses:
        for i, sid in enumerate(statuses):
            params[f"statuses_attributes[{i}][status_id]"] = sid
    return client.post("/api/v2/filters", params=params)


def update_filter(client, filter_id, *, title=None, context=None, action=None,
                  expires_in=None):
    params = {}
    if title is not None: params["title"] = title
    if context is not None: params["context[]"] = list(context)
    if action is not None: params["filter_action"] = action
    if expires_in is not None: params["expires_in"] = expires_in
    return client.put(f"/api/v2/filters/{filter_id}", params=params)


def delete_filter(client, filter_id):
    return client.delete(f"/api/v2/filters/{filter_id}")


def add_keyword(client, filter_id, keyword, whole_word=False):
    return client.post(f"/api/v2/filters/{filter_id}/keywords", params={
        "keyword": keyword,
        "whole_word": "true" if whole_word else "false",
    })


def remove_keyword(client, keyword_id):
    return client.delete(f"/api/v2/filters/keywords/{keyword_id}")


def list_keywords(client, filter_id):
    return client.get(f"/api/v2/filters/{filter_id}/keywords")


# ---------- v1 muted words (legacy — still supported) ----------

def list_v1_filters(client):
    return client.get("/api/v1/filters")


def create_v1_filter(client, phrase, *, context, irreversible=False,
                     whole_word=True, expires_in=None):
    if not all(c in FILTER_CONTEXTS for c in context):
        raise ValueError(f"context must be from {FILTER_CONTEXTS}")
    params = {
        "phrase": phrase,
        "context[]": list(context),
        "irreversible": "true" if irreversible else "false",
        "whole_word": "true" if whole_word else "false",
    }
    if expires_in:
        params["expires_in"] = expires_in
    return client.post("/api/v1/filters", params=params)


def delete_v1_filter(client, filter_id):
    return client.delete(f"/api/v1/filters/{filter_id}")
