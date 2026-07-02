#!/usr/bin/env python3
"""Load env vars from secrets/<name>.env into a plain dict.

Pattern lifted from booked-job/scripts/buffer_publish.py (lines 13-21).
Kept small and dependency-free so every runner can `from env_loader import load`.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SECRETS = os.path.join(ROOT, "secrets")


class MissingSecretsError(RuntimeError):
    """Raised when a required secrets/*.env file is missing. Publishers catch this
    and turn it into a soft PublishResult failure so run_all keeps going."""


def load(name, required=True):
    """Load secrets/<name>.env into a dict. `name` is bare (e.g. 'buffer').

    Raises MissingSecretsError when required=True and the file is absent.
    Returns {} when required=False and the file is absent.
    """
    path = os.path.join(SECRETS, f"{name}.env")
    if not os.path.exists(path):
        if required:
            raise MissingSecretsError(f"secrets/{name}.env missing. See secrets/.env.example.")
        return {}
    out = {}
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


if __name__ == "__main__":
    # Debug: print keys (not values) for a named env file
    if len(sys.argv) < 2:
        print("usage: env_loader.py <name>")
        sys.exit(2)
    e = load(sys.argv[1], required=False)
    if not e:
        print(f"secrets/{sys.argv[1]}.env not present")
    else:
        print(f"secrets/{sys.argv[1]}.env keys:")
        for k in sorted(e):
            print(f"  {k}")
