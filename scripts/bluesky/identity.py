"""Account identity admin — app passwords, recovery keys, email, session tokens.

The handle change itself was done manually in the Bluesky app. This module
covers the rest of the account-admin capability surface so the same wizard flow
can rotate an app password, mint a signing key, or export a session on demand.

Every function here needs the account app password (not a scoped chat password),
so `get_client()` is called without `chat_scope`.

Docs: https://docs.bsky.app/docs/api/com-atproto-server-*
"""


# ---------- app passwords ----------

def list_app_passwords(client):
    """List all named app passwords on the account. Returns a list of
    {name, createdAt, privileged}. Cannot show the raw password strings —
    those are only visible at creation time."""
    resp = client.com.atproto.server.list_app_passwords()
    if hasattr(resp, "passwords"):
        return [dict(p.__dict__ if hasattr(p, "__dict__") else p) for p in resp.passwords]
    return list(resp.get("passwords", []))


def create_app_password(client, name, privileged=False):
    """Mint a new app password. Returns {name, password, createdAt}.

    privileged=True is required for the DM (chat) scope. Standard posting
    passwords should stay non-privileged.
    """
    resp = client.com.atproto.server.create_app_password({
        "name": name,
        "privileged": privileged,
    })
    if hasattr(resp, "__dict__"):
        return dict(resp.__dict__)
    return dict(resp)


def revoke_app_password(client, name):
    """Delete a named app password. All sessions created with it die immediately."""
    client.com.atproto.server.revoke_app_password({"name": name})
    return True


# ---------- account recovery ----------

def request_email_confirmation(client):
    """Send a confirmation email to the account's registered address."""
    client.com.atproto.server.request_email_confirmation()
    return True


def request_email_update(client):
    """Send a token to the CURRENT email; needed before update_email()."""
    resp = client.com.atproto.server.request_email_update()
    if hasattr(resp, "tokenRequired"):
        return {"token_required": resp.tokenRequired}
    return {"token_required": bool(resp.get("tokenRequired", True))}


def update_email(client, new_email, token=None):
    """Change the account email. Token comes from request_email_update()."""
    payload = {"email": new_email}
    if token:
        payload["token"] = token
    client.com.atproto.server.update_email(payload)
    return True


def request_password_reset(client, email):
    """Trigger a password-reset email. Works pre-auth."""
    client.com.atproto.server.request_password_reset({"email": email})
    return True


def reset_password(client, token, new_password):
    """Complete the password reset with the token from the email."""
    client.com.atproto.server.reset_password({
        "token": token,
        "password": new_password,
    })
    return True


# ---------- recovery / signing keys ----------

def reserve_signing_key(client, did=None):
    """Reserve a new signing key for the DID. Used before rotating."""
    payload = {}
    if did:
        payload["did"] = did
    resp = client.com.atproto.server.reserve_signing_key(payload)
    if hasattr(resp, "signingKey"):
        return resp.signingKey
    return resp.get("signingKey")


def get_did_doc(client, handle_or_did=None):
    """Fetch the DID document for the current or specified account. Useful for
    inspecting which recovery/rotation keys are on the account."""
    target = handle_or_did or client.me.did
    if target.startswith("did:"):
        # Query the PLC directory or the DID resolver via the PDS
        resp = client.com.atproto.identity.resolve_handle({"handle": client.me.handle})
        return resp
    resp = client.com.atproto.identity.resolve_handle({"handle": target})
    return resp


# ---------- session admin ----------

def get_session(client):
    """Return current session details: did, handle, email, emailConfirmed, active."""
    resp = client.com.atproto.server.get_session()
    if hasattr(resp, "__dict__"):
        return dict(resp.__dict__)
    return dict(resp)


def refresh_session(client):
    """Rotate the access JWT using the refresh JWT. atproto SDK does this
    automatically on 401s but sometimes you want to force it (e.g. after a
    long-idle wake-up)."""
    resp = client.com.atproto.server.refresh_session()
    if hasattr(resp, "__dict__"):
        return dict(resp.__dict__)
    return dict(resp)


def delete_session(client):
    """Sign out — invalidates the refresh JWT on this device."""
    client.com.atproto.server.delete_session()
    return True
