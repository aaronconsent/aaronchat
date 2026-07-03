#!/usr/bin/env python3
"""Orchestrator. Called hourly by .github/workflows/automation.yml (cron 5 * * * *).

Reads config.yaml, iterates every enabled channel, spawns the channel's runner
script as a subprocess. Each runner self-gates on windows/caps/spacing so most
hourly invocations no-op.

Modeled on booked-job/scripts/run_all.py enumerate_agents pattern.
"""
import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))

# Channel key → runner script filename. Keep aligned with config.yaml `channels:`.
RUNNERS = {
    "linkedin": "linkedin_runner.py",
    "x": "x_runner.py",
    "bluesky": "bluesky_runner.py",
    "mastodon": "mastodon_runner.py",
    # facebook / instagram deferred per config.
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="Pass --force to every runner (bypass gates)")
    ap.add_argument("--dry-run", action="store_true", help="Pass --dry-run to every runner")
    ap.add_argument("--only", help="Comma-separated channel keys to run (e.g. linkedin,x)")
    args = ap.parse_args()

    import yaml
    cfg = yaml.safe_load(open(os.path.join(ROOT, "config.yaml")))
    channels_cfg = cfg.get("channels", {})

    only = set(args.only.split(",")) if args.only else None

    print(f"run_all: start ts={time.strftime('%Y-%m-%dT%H:%M:%S%z')}")
    ok = 0; skipped = 0; failed = 0
    for key, script in RUNNERS.items():
        if only and key not in only:
            continue
        if not channels_cfg.get(key, {}).get("enabled"):
            print(f"  {key}: disabled — skip")
            skipped += 1
            continue

        cmd = [sys.executable, os.path.join(HERE, script)]
        if args.force:
            cmd.append("--force")
        if args.dry_run:
            cmd.append("--dry-run")
        print(f"  {key}: running {' '.join(cmd[1:])}")
        rc = subprocess.call(cmd, cwd=ROOT)
        if rc == 0:
            ok += 1
        else:
            failed += 1
            print(f"  {key}: nonzero exit rc={rc}")

    print(f"run_all: done ok={ok} skipped={skipped} failed={failed}")
    # Never exit nonzero from orchestrator — individual runner failures shouldn't fail the whole GHA run
    return 0


if __name__ == "__main__":
    sys.exit(main())
