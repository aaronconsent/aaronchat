#!/usr/bin/env python3
"""X (Twitter) drip runner. Called hourly by run_all.py. Self-gates on window / cap / spacing."""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import runner_base
import x_publish


if __name__ == "__main__":
    ap = runner_base.add_args(argparse.ArgumentParser())
    args = ap.parse_args()
    rc = runner_base.run("x", x_publish, args)
    sys.exit(rc)
