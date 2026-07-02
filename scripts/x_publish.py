#!/usr/bin/env python3
"""X (Twitter) publisher. Routes through Buffer for MVP (aggregator backend).

Future: swap to own_app backend once paid X API v2 is up.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import buffer_publish
from env_loader import MissingSecretsError, load
from linkedin_publish import PublishResult  # reuse the same simple result type


def post(item, channel_cfg):
    backend = channel_cfg.get("backend", "aggregator")
    text = item["text"]

    if backend == "aggregator" and channel_cfg.get("aggregator") == "buffer":
        try:
            e = load("buffer")
        except MissingSecretsError as ex:
            return PublishResult(False, "buffer", str(ex))
        channel_id_key = channel_cfg.get("buffer_channel_env", "BUFFER_X_CHANNEL")
        channel_id = e.get(channel_id_key)
        if not channel_id:
            return PublishResult(False, "buffer", f"missing {channel_id_key} in buffer.env")
        try:
            buffer_publish.queue_text(channel_id, text, e=e)
            return PublishResult(True, "buffer", f"queued to channel {channel_id[:8]}…")
        except Exception as ex:
            return PublishResult(False, "buffer", str(ex)[:300])

    if backend == "own_app":
        return PublishResult(False, "own_app", "X own_app publisher not yet implemented (needs paid API v2)")

    return PublishResult(False, backend, f"unknown backend {backend!r}")
