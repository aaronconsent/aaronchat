"""User preferences — muted words, saved feeds, thread sort, content labels.

Bluesky preferences all live under a single `app.bsky.actor.preferences`
proc pair: getPreferences returns a heterogeneous list of preference objects,
putPreferences writes the full list back. Because it's a full-write, this
module reads → mutates → writes to avoid clobbering unrelated preferences.

Preference kinds you can set:
    adultContentPref
    contentLabelPref             per-label visibility (hide/warn/ignore)
    savedFeedsPrefV2             pinned + saved feeds
    personalDetailsPref          birthDate
    feedViewPref                 hideReplies, hideReposts, hideQuotePosts
    threadViewPref               sort, prioritizeFollowedUsers
    interestsPref                tag list for recommendations
    mutedWordsPref               list of muted terms (with scope/duration)
    hiddenPostsPref              specific post URIs to hide
    bskyAppStatePref             app-specific UI state
    labelersPref                 subscribed labelers
"""


def _get_all(client):
    """Return current preferences list (list of dicts). Empty list if none set."""
    resp = client.app.bsky.actor.get_preferences()
    prefs = resp.preferences if hasattr(resp, "preferences") else resp.get("preferences", [])
    return [dict(p.__dict__) if hasattr(p, "__dict__") else dict(p) for p in prefs]


def _put_all(client, prefs):
    return client.app.bsky.actor.put_preferences({"preferences": prefs})


def _upsert(prefs, pref_type, new_pref):
    """Replace an existing pref of pref_type, or append if absent."""
    for i, p in enumerate(prefs):
        if p.get("$type") == pref_type:
            prefs[i] = new_pref
            return prefs
    prefs.append(new_pref)
    return prefs


# ---------- muted words ----------

def add_muted_word(client, value, targets=("content",), duration=None, actor_target=None):
    """Add a muted word/phrase.

    targets: tuple of ("content", "tag") — content matches text, tag matches hashtags
    duration: ISO duration string like 'P30D' (30 days) or None for forever
    actor_target: 'all' | 'exclude-following' — restricts which authors it applies to
    """
    prefs = _get_all(client)
    muted_pref = next((p for p in prefs
                       if p.get("$type") == "app.bsky.actor.defs#mutedWordsPref"), None)
    items = list((muted_pref or {}).get("items") or [])
    new_item = {"value": value, "targets": list(targets)}
    if duration:
        new_item["expiresAt"] = duration  # ISO-8601 timestamp; SDK also accepts durations
    if actor_target:
        new_item["actorTarget"] = actor_target
    items.append(new_item)
    _upsert(prefs, "app.bsky.actor.defs#mutedWordsPref",
            {"$type": "app.bsky.actor.defs#mutedWordsPref", "items": items})
    _put_all(client, prefs)
    return True


def remove_muted_word(client, value):
    prefs = _get_all(client)
    muted_pref = next((p for p in prefs
                       if p.get("$type") == "app.bsky.actor.defs#mutedWordsPref"), None)
    if not muted_pref:
        return False
    items = [w for w in (muted_pref.get("items") or []) if w.get("value") != value]
    _upsert(prefs, "app.bsky.actor.defs#mutedWordsPref",
            {"$type": "app.bsky.actor.defs#mutedWordsPref", "items": items})
    _put_all(client, prefs)
    return True


def list_muted_words(client):
    prefs = _get_all(client)
    muted_pref = next((p for p in prefs
                       if p.get("$type") == "app.bsky.actor.defs#mutedWordsPref"), None)
    return list((muted_pref or {}).get("items") or [])


# ---------- saved / pinned feeds ----------

def set_saved_feeds(client, saved=None, pinned=None):
    """Overwrite the saved and pinned feed lists.
    Each entry is either a feed at-uri (custom feed) or a special value like
    'timeline'. Pinned feeds appear as tabs on the home screen."""
    saved = list(saved or [])
    pinned = list(pinned or [])
    items = []
    seen = set()
    for uri in pinned:
        items.append({"id": uri, "type": "feed", "value": uri, "pinned": True})
        seen.add(uri)
    for uri in saved:
        if uri in seen:
            continue
        items.append({"id": uri, "type": "feed", "value": uri, "pinned": False})
    prefs = _get_all(client)
    _upsert(prefs, "app.bsky.actor.defs#savedFeedsPrefV2",
            {"$type": "app.bsky.actor.defs#savedFeedsPrefV2", "items": items})
    _put_all(client, prefs)
    return True


def get_saved_feeds(client):
    prefs = _get_all(client)
    saved = next((p for p in prefs
                  if p.get("$type") == "app.bsky.actor.defs#savedFeedsPrefV2"), None)
    return list((saved or {}).get("items") or [])


# ---------- thread sort ----------

THREAD_SORTS = ("oldest", "newest", "most-likes", "random", "hotness")


def set_thread_sort(client, sort="hotness", prioritize_followed=True):
    """Set default thread-sort preference."""
    if sort not in THREAD_SORTS:
        raise ValueError(f"sort must be one of {THREAD_SORTS}")
    prefs = _get_all(client)
    _upsert(prefs, "app.bsky.actor.defs#threadViewPref", {
        "$type": "app.bsky.actor.defs#threadViewPref",
        "sort": sort,
        "prioritizeFollowedUsers": bool(prioritize_followed),
    })
    _put_all(client, prefs)
    return True


# ---------- content labels ----------

LABEL_VISIBILITIES = ("hide", "warn", "ignore", "show")


def set_content_label(client, label, visibility="warn", labeler_did=None):
    """Set per-label visibility (nudity/sexual/etc.)."""
    if visibility not in LABEL_VISIBILITIES:
        raise ValueError(f"visibility must be one of {LABEL_VISIBILITIES}")
    prefs = _get_all(client)
    # contentLabelPref is a LIST (one entry per label) — mutate the matching entry
    new_entries = []
    replaced = False
    for p in prefs:
        if p.get("$type") == "app.bsky.actor.defs#contentLabelPref" and p.get("label") == label:
            new_entries.append({
                "$type": "app.bsky.actor.defs#contentLabelPref",
                "label": label,
                "visibility": visibility,
                **({"labelerDid": labeler_did} if labeler_did else {}),
            })
            replaced = True
        else:
            new_entries.append(p)
    if not replaced:
        new_entries.append({
            "$type": "app.bsky.actor.defs#contentLabelPref",
            "label": label,
            "visibility": visibility,
            **({"labelerDid": labeler_did} if labeler_did else {}),
        })
    _put_all(client, new_entries)
    return True


# ---------- interests ----------

def set_interests(client, tags):
    """Set your interest tags for recommendations."""
    prefs = _get_all(client)
    _upsert(prefs, "app.bsky.actor.defs#interestsPref", {
        "$type": "app.bsky.actor.defs#interestsPref",
        "tags": list(tags),
    })
    _put_all(client, prefs)
    return True
