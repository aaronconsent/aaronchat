"""Favourite (like), bookmark, poll voting."""


def favourite(client, status_id):
    return client.post(f"/api/v1/statuses/{status_id}/favourite")


def unfavourite(client, status_id):
    return client.post(f"/api/v1/statuses/{status_id}/unfavourite")


def list_favourites(client, limit=40):
    """Your favourited statuses (paginated by Link header)."""
    return client.get("/api/v1/favourites", params={"limit": limit})


def bookmark(client, status_id):
    return client.post(f"/api/v1/statuses/{status_id}/bookmark")


def unbookmark(client, status_id):
    return client.post(f"/api/v1/statuses/{status_id}/unbookmark")


def list_bookmarks(client, limit=40):
    return client.get("/api/v1/bookmarks", params={"limit": limit})


# ---------- poll voting ----------

def vote_in_poll(client, poll_id, choices):
    """`choices` is a list of integer option indexes (0-based)."""
    return client.post(f"/api/v1/polls/{poll_id}/votes",
                        params={"choices[]": [str(c) for c in choices]})


def get_poll(client, poll_id):
    return client.get(f"/api/v1/polls/{poll_id}")


# ---------- reach-quality signal — who boosted / favourited ----------

def reblogged_by(client, status_id, limit=80):
    return client.get(f"/api/v1/statuses/{status_id}/reblogged_by",
                       params={"limit": limit})


def favourited_by(client, status_id, limit=80):
    return client.get(f"/api/v1/statuses/{status_id}/favourited_by",
                       params={"limit": limit})
