#!/usr/bin/env python3
"""Update the aaron.chat Bluesky profile from a YAML config.

Reads content/bluesky_profile.yaml (paths + strings), then pushes the record.
Idempotent — safe to run repeatedly.

Config shape:
    display_name: "Aaron Phillips"
    description: |
      Marketing for East Texas service pros.
      aaron.chat
    avatar: content/avatar.jpg           # optional
    banner: content/banner.jpg           # optional
    labels: ["!no-unauthenticated"]      # optional
    pinned_post_uri: at://did:.../.../   # optional
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import yaml

from bluesky.client import get_client
from bluesky import profile as profile_mod


DEFAULT_CONFIG = os.path.join(os.path.dirname(HERE), "content", "bluesky_profile.yaml")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.config):
        print(f"[fatal] no profile config at {args.config}")
        sys.exit(1)
    with open(args.config) as f:
        cfg = yaml.safe_load(f) or {}

    kw = {}
    if "display_name" in cfg:
        kw["display_name"] = cfg["display_name"]
    if "description" in cfg:
        kw["description"] = cfg["description"].strip()
    if cfg.get("avatar") and os.path.exists(cfg["avatar"]):
        kw["avatar_path"] = cfg["avatar"]
    if cfg.get("banner") and os.path.exists(cfg["banner"]):
        kw["banner_path"] = cfg["banner"]
    if "labels" in cfg:
        kw["labels"] = cfg["labels"]

    print(f"[profile] would write: { {k: (v if k not in ('description',) else v[:60]+'…') for k,v in kw.items()} }")

    if args.dry_run:
        return 0

    client = get_client()
    profile_mod.update(client, **kw)

    if cfg.get("pinned_post_uri"):
        profile_mod.set_pinned_post(client, uri=cfg["pinned_post_uri"])
        print(f"[profile] pinned {cfg['pinned_post_uri']}")

    print("[profile] updated ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
