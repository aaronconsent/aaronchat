"""Minimal Mastodon HTTP client — instance URL + bearer token.

We don't need a fat SDK. Every Mastodon endpoint is HTTPS + Bearer token.
The `Client` here is a small dict-in / dict-out wrapper around urllib that:
    - Normalizes the instance URL (strips trailing slash, adds https://)
    - Sets Authorization + Accept: application/json
    - Sends form-encoded params for POST unless the caller provides `files`
      (in which case multipart is used)

Usage:
    from mastodon.client import get_client
    client = get_client()
    resp = client.get("/api/v1/accounts/verify_credentials")
    print(resp["username"])
"""
import json
import os
import sys
import urllib.parse
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
sys.path.insert(0, SCRIPTS)

from env_loader import load, MissingSecretsError


DEFAULT_UA = "aaron-chat-mastodon-publisher/1.0"


class MastodonError(Exception):
    def __init__(self, status, body, url):
        self.status, self.body, self.url = status, body, url
        super().__init__(f"HTTP {status} {url}: {body[:200]}")


class Client:
    def __init__(self, instance, access_token, user_agent=DEFAULT_UA):
        instance = instance.strip().rstrip("/")
        if not instance.startswith(("http://", "https://")):
            instance = "https://" + instance
        self.instance = instance
        self.host = urllib.parse.urlparse(instance).netloc
        self.token = access_token
        self.ua = user_agent
        self._me = None

    @property
    def me(self):
        if self._me is None:
            self._me = self.get("/api/v1/accounts/verify_credentials")
        return self._me

    def _headers(self, extra=None):
        h = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "User-Agent": self.ua,
        }
        if extra:
            h.update(extra)
        return h

    def _req(self, method, path, params=None, files=None, headers=None):
        url = self.instance + path
        data = None
        h = self._headers(headers)
        if method == "GET" and params:
            url = url + "?" + urllib.parse.urlencode(params, doseq=True)
        elif files:
            boundary = "----" + uuid.uuid4().hex
            body = _multipart(params or {}, files, boundary)
            data = body
            h["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        elif params is not None:
            data = urllib.parse.urlencode(params, doseq=True).encode()
            h["Content-Type"] = "application/x-www-form-urlencoded"
        req = urllib.request.Request(url, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read()
                text = body.decode("utf-8", errors="replace") if body else ""
                if not text:
                    return {}
                return json.loads(text)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            raise MastodonError(e.code, body, url) from None

    def get(self, path, params=None):
        return self._req("GET", path, params=params)

    def post(self, path, params=None, files=None):
        return self._req("POST", path, params=params, files=files)

    def put(self, path, params=None, files=None):
        return self._req("PUT", path, params=params, files=files)

    def patch(self, path, params=None, files=None):
        return self._req("PATCH", path, params=params, files=files)

    def delete(self, path, params=None):
        return self._req("DELETE", path, params=params)


def _multipart(fields, files, boundary):
    """Build a multipart/form-data body. Files is a dict:
        {"file": ("name.jpg", bytes, "image/jpeg")}
    Fields can also be lists (send each as a repeated key)."""
    out = []
    for k, v in fields.items():
        if isinstance(v, (list, tuple)):
            for vi in v:
                out.append(_part_field(boundary, k, vi))
        else:
            out.append(_part_field(boundary, k, v))
    for name, (filename, content, mime) in files.items():
        out.append(_part_file(boundary, name, filename, content, mime))
    out.append(f"--{boundary}--\r\n".encode())
    return b"".join(out)


def _part_field(boundary, name, value):
    return (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
        f"{value}\r\n"
    ).encode()


def _part_file(boundary, name, filename, content, mime):
    header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode()
    return header + content + b"\r\n"


def get_client():
    """Load creds from secrets/mastodon.env and return a Client."""
    try:
        e = load("mastodon")
    except MissingSecretsError:
        raise
    instance = e.get("MASTODON_INSTANCE")
    token = e.get("MASTODON_ACCESS_TOKEN")
    if not instance or not token:
        raise MissingSecretsError("MASTODON_INSTANCE + MASTODON_ACCESS_TOKEN required")
    return Client(instance, token)
