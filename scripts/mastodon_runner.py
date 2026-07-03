#!/usr/bin/env python3
"""Mastodon drip runner. Called hourly by run_all.py. Runs credibility + audience modes."""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import mastodon_publish
import runner_base


if __name__ == "__main__":
    ap = runner_base.add_args(argparse.ArgumentParser())
    args = ap.parse_args()
    sys.exit(runner_base.run("mastodon", mastodon_publish, args))
