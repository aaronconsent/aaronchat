"""Authenticated Bluesky client with session caching + refresh.

Wraps the official `atproto` Python SDK. Reads credentials from
secrets/bluesky.env, caches the session JWT + refresh token in
content/.bluesky_session.json so we don't `createSession` on every runner tick,
and transparently refreshes when the access JWT expires.

Env vars (from secrets/bluesky.env):
  BLUESKY_HANDLE            handle for the account (e.g. heyaaron.bsky.social)
  BLUESKY_APP_PASSWORD      standard app password
  BLUESKY_CHAT_APP_PASSWORD optional — DM-scoped app password (chat.bsky.*)
  BLUESKY_PDS_URL           optional, defaults to https://bsky.social

Usage:
    from bluesky.client import get_client
    client = get_client()
    client.send_post("hello world")
"""
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from env_loader import MissingSecretsError, load  # noqa: E402

try:
    from atproto import Client
    from atproto_client.models.common import XrpcError  # noqa: F401
except ImportError as ex:
    raise SystemExit(
        "atproto package not installed. Add `atproto` to the workflow's pip install."
    ) from ex


SESSION_FILE = os.path.join(ROOT, "content", ".bluesky_session.json")
DEFAULT_PDS = "https://bsky.social"


def _load_env(chat_scope=False):
    """Load bluesky.env, optionally overriding the app password with the chat-scoped one."""
    e = load("bluesky")
    if chat_scope:
        chat_pw = e.get("BLUESKY_CHAT_APP_PASSWORD")
        if not chat_pw:
            raise RuntimeError(
                "BLUESKY_CHAT_APP_PASSWORD missing in secrets/bluesky.env. "
                "Chat endpoints need a DM-scoped app password (create at "
                "https://bsky.app/settings/app-passwords with 'Access DMs' enabled)."
            )
        e["BLUESKY_APP_PASSWORD"] = chat_pw
    if not e.get("BLUESKY_HANDLE"):
        raise RuntimeError("BLUESKY_HANDLE missing in secrets/bluesky.env")
    if not e.get("BLUESKY_APP_PASSWORD"):
        raise RuntimeError("BLUESKY_APP_PASSWORD missing in secrets/bluesky.env")
    return e


def _load_cached_session(handle):
    """Return {handle, accessJwt, refreshJwt, did, ...} for `handle` or None if missing/stale."""
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE) as f:
            data = json.load(f)
    except Exception:
        return None
    entry = data.get(handle)
    if not entry:
        return None
    # Access JWTs expire ~2h; refresh is longer but we soft-refresh at 90 min.
    saved_at = entry.get("_saved_at")
    if saved_at:
        try:
            saved_dt = dt.datetime.fromisoformat(saved_at)
            age_min = (dt.datetime.utcnow() - saved_dt).total_seconds() / 60
            if age_min > 90:
                return None
        except Exception:
            return None
    return entry


def _save_session(handle, session_dict):
    """Persist the atproto session dict under `handle` in the session cache."""
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    data = {}
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE) as f:
                data = json.load(f)
        except Exception:
            data = {}
    session_dict = dict(session_dict)
    session_dict["_saved_at"] = dt.datetime.utcnow().isoformat(timespec="seconds")
    data[handle] = session_dict
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f, indent=2)
    # Session file may contain refresh tokens — restrict perms
    try:
        os.chmod(SESSION_FILE, 0o600)
    except Exception:
        pass


def get_client(chat_scope=False, pds_url=None):
    """Return an authenticated `atproto.Client`. Reuses cached session when fresh.

    chat_scope=True → use BLUESKY_CHAT_APP_PASSWORD instead of standard app-password.
                      Required for any chat.bsky.* endpoint.
    """
    e = _load_env(chat_scope=chat_scope)
    handle = e["BLUESKY_HANDLE"]
    pds = pds_url or e.get("BLUESKY_PDS_URL") or DEFAULT_PDS

    client = Client(base_url=pds)

    cached = _load_cached_session(handle) if not chat_scope else None
    if cached:
        try:
            # Restore the session — atproto's restore_session takes serialized string.
            # We rebuild a minimal session_string from cached fields.
            session_str = cached.get("session_string")
            if session_str:
                client.login(session_string=session_str)
                return client
        except Exception:
            # Cached session stale — fall through to fresh login
            pass

    # Fresh login
    try:
        client.login(handle, e["BLUESKY_APP_PASSWORD"])
    except Exception as ex:
        raise RuntimeError(f"Bluesky login failed for {handle}: {ex}") from ex

    # Persist session string for reuse (skip for chat-scope; different token surface)
    if not chat_scope:
        try:
            session_str = client.export_session_string()
            _save_session(handle, {"session_string": session_str, "did": client.me.did})
        except Exception:
            pass

    return client


def whoami():
    """Diagnostic: print the resolved handle + DID from the current session."""
    c = get_client()
    print(f"handle: {c.me.handle}")
    print(f"did:    {c.me.did}")
    print(f"display: {getattr(c.me, 'display_name', '') or '(none)'}")


if __name__ == "__main__":
    whoami()
