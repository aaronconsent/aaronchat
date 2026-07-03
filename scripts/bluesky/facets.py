"""Rich-text facet builder for Bluesky posts.

Bluesky renders URLs, @mentions, and #hashtags as clickable ONLY when the post
record includes `facets[]` with byte-offset ranges pointing into the text.
The atproto SDK ships a TextBuilder that does most of this — this module wraps
it with aaron.chat-specific conveniences (auto-resolve handles, sensible URL
handling, unified `build()` for the publisher's simple text-in / facets-out flow).

Usage:
    text, facets = build("Check out https://aaron.chat — cc @heyaaron.bsky.social",
                         client=client)
    client.send_post(text=text, facets=facets)
"""
import re

# atproto ships an ImmutableFacet / TextBuilder that handles UTF-8 byte offsets
# correctly. Delegate to it where possible.
try:
    from atproto import client_utils
    _HAS_TB = True
except ImportError:
    _HAS_TB = False


URL_RE = re.compile(
    r"(?<![@\w])"                                # not preceded by @ or word char
    r"(https?://[^\s<>\"'\)\]]+[^\s<>\"'\)\]\.,!\?;:])"
)
MENTION_RE = re.compile(
    r"(?<![\w/])"                                # not preceded by word char or /
    r"@([a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9](?:\.[a-zA-Z0-9][a-zA-Z0-9-]*)+)"
)
HASHTAG_RE = re.compile(
    r"(?<![\w/#])"                               # not preceded by word char, /, or #
    r"#([a-zA-Z][a-zA-Z0-9_]{0,63})"             # letter first, up to 64 chars
)


def _byte_index_of(text, char_index):
    """Convert a character index into a UTF-8 byte offset (Bluesky spec)."""
    return len(text[:char_index].encode("utf-8"))


def _find_ranges(text, pattern, group=0):
    """Yield (byte_start, byte_end, matched_text) for each pattern match in `text`."""
    for m in pattern.finditer(text):
        char_start = m.start(group)
        char_end = m.end(group)
        yield (
            _byte_index_of(text, char_start),
            _byte_index_of(text, char_end),
            m.group(group),
        )


def build(text, client=None, resolve_mentions=True):
    """Given raw post text, return (text, facets[]).

    - URLs → app.bsky.richtext.facet#link
    - @handle.tld → app.bsky.richtext.facet#mention (needs handle→DID resolution)
    - #tag → app.bsky.richtext.facet#tag

    If `client` is provided and `resolve_mentions=True`, mentions are resolved
    to DIDs via com.atproto.identity.resolveHandle. Unresolvable mentions get
    silently dropped from the facet array (text remains).
    """
    facets = []

    # Links
    for byte_start, byte_end, url in _find_ranges(text, URL_RE):
        facets.append({
            "index": {"byteStart": byte_start, "byteEnd": byte_end},
            "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}],
        })

    # Mentions — need DID resolution
    if resolve_mentions and client is not None:
        for byte_start, byte_end, mention in _find_ranges(text, MENTION_RE):
            handle = mention[1:]  # strip leading @
            try:
                res = client.com.atproto.identity.resolve_handle({"handle": handle})
                did = res.did
                if did:
                    facets.append({
                        "index": {"byteStart": byte_start, "byteEnd": byte_end},
                        "features": [{"$type": "app.bsky.richtext.facet#mention", "did": did}],
                    })
            except Exception:
                # Unresolvable handle — leave the text alone, skip facet
                continue

    # Hashtags
    for byte_start, byte_end, tag in _find_ranges(text, HASHTAG_RE):
        tag_value = tag[1:]  # strip leading #
        facets.append({
            "index": {"byteStart": byte_start, "byteEnd": byte_end},
            "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": tag_value}],
        })

    # Sort by byteStart so downstream tools have a predictable order
    facets.sort(key=lambda f: f["index"]["byteStart"])
    return text, facets


def build_via_atproto(text, client):
    """Alternative path: use atproto's TextBuilder for maximum compatibility.

    Handles edge cases we might miss (Unicode normalization, complex handles).
    Returns (rendered_text, facets_list) shaped for send_post.
    """
    if not _HAS_TB:
        return build(text, client=client)

    tb = client_utils.TextBuilder()
    # We walk the text and detect URLs/mentions/tags ourselves, appending each
    # segment via the correct TextBuilder method. Simple substring approach.
    cursor = 0
    tokens = []
    for pattern, kind in [(URL_RE, "link"), (MENTION_RE, "mention"), (HASHTAG_RE, "tag")]:
        for m in pattern.finditer(text):
            tokens.append((m.start(0), m.end(0), kind, m.group(0), m.group(1) if m.groups() else m.group(0)))
    tokens.sort()

    for start, end, kind, matched, inner in tokens:
        if start < cursor:
            continue
        if start > cursor:
            tb.text(text[cursor:start])
        if kind == "link":
            tb.link(matched, matched)
        elif kind == "mention":
            try:
                did = client.com.atproto.identity.resolve_handle({"handle": inner}).did
                tb.mention(matched, did)
            except Exception:
                tb.text(matched)
        elif kind == "tag":
            tb.tag(matched, inner)
        cursor = end
    if cursor < len(text):
        tb.text(text[cursor:])
    return tb


def extract_first_link(text):
    """Return the first URL found in `text`, or None. Useful for auto-link-card."""
    m = URL_RE.search(text)
    return m.group(1) if m else None
