#!/usr/bin/env python3
"""LinkedIn publisher. Routes through Buffer for MVP (aggregator backend).

Future: swap to own_app backend by implementing the direct LinkedIn Community
Management API path — same public function signature (`post`).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import buffer_publish
from env_loader import MissingSecretsError, load


class PublishResult:
    def __init__(self, ok, backend, detail=""):
        self.ok = ok
        self.backend = backend
        self.detail = detail

    def __repr__(self):
        return f"<PublishResult ok={self.ok} backend={self.backend} detail={self.detail[:60]!r}>"


def post(item, channel_cfg):
    """Post `item` (dict from queue.json) using `channel_cfg` from config.yaml.

    Returns PublishResult. Never raises for expected failure modes — caller decides.
    """
    backend = channel_cfg.get("backend", "aggregator")
    text = item["text"]

    if backend == "aggregator" and channel_cfg.get("aggregator") == "buffer":
        try:
            e = load("buffer")
        except MissingSecretsError as ex:
            return PublishResult(False, "buffer", str(ex))
        channel_id_key = channel_cfg.get("buffer_channel_env", "BUFFER_LINKEDIN_CHANNEL")
        channel_id = e.get(channel_id_key)
        if not channel_id:
            return PublishResult(False, "buffer", f"missing {channel_id_key} in buffer.env")
        try:
            buffer_publish.queue_text(channel_id, text, e=e)
            return PublishResult(True, "buffer", f"queued to channel {channel_id[:8]}…")
        except Exception as ex:
            return PublishResult(False, "buffer", str(ex)[:300])

    if backend == "own_app":
        return PublishResult(False, "own_app", "LinkedIn own_app publisher not yet implemented")

    return PublishResult(False, backend, f"unknown backend {backend!r}")
