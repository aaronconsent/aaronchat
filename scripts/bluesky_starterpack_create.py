#!/usr/bin/env python3
"""Create or update a Bluesky starter pack from a YAML config.

Reads content/starter_packs/<slug>.yaml, then either creates the pack fresh
or updates it in place if state file remembers a prior URI.

Config shape:
    slug: east-texas-service-pros
    name: East Texas Service Pros
    description: |
      Contractors and local marketers worth following in East Texas.
    handles:
      - heyaaron.bsky.social
      - bookedjob.bsky.social
    feeds: []                    # optional at-uri list

State file: content/starter_packs/<slug>.state.json (auto-managed)
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import yaml

from bluesky.client import get_client
from bluesky import starterpack, graph as graph_mod


def _state_path(slug):
    return os.path.join(os.path.dirname(HERE), "content", "starter_packs", f"{slug}.state.json")


def _load_state(slug):
    p = _state_path(slug)
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return {}


def _save_state(slug, state):
    p = _state_path(slug)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        json.dump(state, f, indent=2)


def _sync_list_membership(client, list_uri, desired_handles, current_members):
    """Ensure list membership matches desired_handles. Adds missing, removes stale."""
    current_dids = set()
    listitem_by_did = {}
    for item in current_members:
        did = item.get("subject", {}).get("did") if isinstance(item, dict) else getattr(item.subject, "did", None)
        uri = item.get("uri") if isinstance(item, dict) else getattr(item, "uri", None)
        if did:
            current_dids.add(did)
            listitem_by_did[did] = uri

    desired_dids = set()
    for handle in desired_handles:
        did = handle if handle.startswith("did:") else client.com.atproto.identity.resolve_handle({"handle": handle}).did
        desired_dids.add(did)

    to_add = desired_dids - current_dids
    to_remove = current_dids - desired_dids

    for did in to_add:
        graph_mod.add_to_list(client, list_uri, did)
    for did in to_remove:
        uri = listitem_by_did.get(did)
        if uri:
            graph_mod.remove_from_list(client, uri)

    return {"added": len(to_add), "removed": len(to_remove)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config", help="Path to starter-pack YAML config")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    slug = cfg["slug"]
    name = cfg["name"]
    desc = cfg.get("description", "").strip()
    handles = cfg.get("handles", [])
    feeds = cfg.get("feeds", [])

    print(f"[starterpack {slug}] name={name!r} handles={len(handles)} feeds={len(feeds)}")
    if args.dry_run:
        return 0

    client = get_client()
    state = _load_state(slug)

    if state.get("starterpack_uri"):
        # Update in place
        starterpack.update(client, state["starterpack_uri"],
                            name=name, description=desc, feed_uris=feeds)
        list_uri = state["list_uri"]
        current = graph_mod.get_list(client, list_uri)
        members = current.items if hasattr(current, "items") else current.get("items", [])
        stats = _sync_list_membership(client, list_uri, handles, members)
        print(f"[starterpack {slug}] updated — members +{stats['added']}/-{stats['removed']}")
        print(f"[starterpack {slug}] share: {state.get('share_url')}")
    else:
        result = starterpack.create(client, name=name, description=desc,
                                     actor_handles=handles, feed_uris=feeds)
        state = {
            "starterpack_uri": result["starterpack"]["uri"],
            "list_uri": result["list"]["uri"],
            "share_url": result["share_url"],
        }
        _save_state(slug, state)
        print(f"[starterpack {slug}] created ok")
        print(f"[starterpack {slug}] share: {result['share_url']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
