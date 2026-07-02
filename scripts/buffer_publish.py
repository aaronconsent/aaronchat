#!/usr/bin/env python3
"""Buffer GraphQL API wrapper. Adapted verbatim from
booked-job/scripts/buffer_publish.py (lines 8-56).

Buffer is aaron.chat's interim aggregator for LinkedIn + X while we defer own_app
approvals. Free plan supports addToQueue → Buffer auto-publishes on channel schedule.
"""
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from env_loader import load

ENDPOINT = "https://api.buffer.com"


def gql(query, variables=None, e=None):
    e = e or load("buffer")
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {e['BUFFER_TOKEN']}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            d = json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        raise RuntimeError(f"Buffer HTTP {ex.code}: {ex.read().decode()[:300]}")
    if d.get("errors"):
        raise RuntimeError(json.dumps(d["errors"])[:400])
    return d.get("data") or {}


def channels(e=None):
    """List all connected channels for the org (verifies auth + returns channel IDs)."""
    e = e or load("buffer")
    d = gql(
        "query($i: ChannelsInput!){ channels(input:$i){ id service displayName isDisconnected } }",
        {"i": {"organizationId": e["BUFFER_ORG"]}},
        e=e,
    )
    return d.get("channels", [])


def queue_text(channel_id, text, e=None):
    """addToQueue a text-only post. Buffer publishes on the channel's own schedule."""
    e = e or load("buffer")
    inp = {
        "channelId": channel_id,
        "text": text,
        "assets": [],
        "schedulingType": "automatic",
        "mode": "addToQueue",
    }
    d = gql(
        "mutation($input: CreatePostInput!){ createPost(input:$input){ __typename } }",
        {"input": inp},
        e=e,
    )
    tn = (d.get("createPost") or {}).get("__typename")
    if tn != "PostActionSuccess":
        raise RuntimeError(f"Buffer createPost returned {tn}: {json.dumps(d)[:300]}")
    return True


# -------- CLI probe (verifies auth + prints connected channels) --------
if __name__ == "__main__":
    try:
        e = load("buffer")
    except SystemExit as ex:
        print(ex); sys.exit(1)
    print(f"BUFFER_ORG: {e.get('BUFFER_ORG', '(missing)')}")
    try:
        chs = channels(e)
    except Exception as ex:
        print(f"probe failed: {ex}"); sys.exit(1)
    print(f"{len(chs)} channels connected:")
    for c in chs:
        print(f"  {c.get('service'):>10s}  {c.get('id')}  {c.get('displayName')}"
              + ("  [disconnected]" if c.get("isDisconnected") else ""))
