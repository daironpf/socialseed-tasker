from __future__ import annotations

import base64
import json
import os
import time
import urllib.parse
from typing import Any, Dict, Optional

import requests

from socialseed_tasker.application.exceptions import StorageError
from socialseed_tasker.application.ports import StoragePort

KEYCLOAK_BASE = os.getenv("TASKER_KEYCLOAK_URL", "http://localhost:8082")
REALM = os.getenv("TASKER_KEYCLOAK_REALM", "tasker-dev")
FRONTEND_CLIENT = os.getenv("TASKER_KEYCLOAK_FRONTEND_CLIENT", "tasker-frontend")
API_CLIENT = os.getenv("TASKER_KEYCLOAK_API_CLIENT", "tasker-api")
API_CLIENT_SECRET = os.getenv("TASKER_KEYCLOAK_API_CLIENT_SECRET", "tasker-api-secret")
REDIRECT_PATH = os.getenv("TASKER_OAUTH_REDIRECT_PATH", "/auth/callback")
SESSION_COOKIE_NAME = os.getenv("TASKER_SESSION_COOKIE", "TASKER_SESSION")
SESSION_TTL = int(os.getenv("TASKER_SESSION_TTL", "3600"))


def _auth_endpoint():
    return f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/auth"


def _token_endpoint():
    return f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/token"


def _logout_endpoint():
    return f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/logout"


class SessionStore:
    PREFIX = "session:"

    def __init__(self, storage: StoragePort):
        self.storage = storage

    def create(self, data: Dict[str, Any], ttl: int = SESSION_TTL) -> str:
        sid = str(int(time.time() * 1000)) + "-" + str(hash(json.dumps(data)))
        key = self.PREFIX + sid
        try:
            self.storage.put(key, json.dumps(data).encode("utf-8"), ttl_seconds=ttl)
        except Exception as exc:
            raise StorageError(f"Failed to create session: {exc}") from exc
        return sid

    def get(self, sid: str) -> Optional[Dict[str, Any]]:
        key = self.PREFIX + sid
        raw = self.storage.get(key)
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def delete(self, sid: str) -> None:
        key = self.PREFIX + sid
        self.storage.delete(key)


def build_auth_url(state: str, redirect_uri: str, scope: str = "openid profile email") -> str:
    params = {
        "client_id": FRONTEND_CLIENT,
        "response_type": "code",
        "scope": scope,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    return _auth_endpoint() + "?" + urllib.parse.urlencode(params)


def exchange_code_for_tokens(code: str, redirect_uri: str) -> Dict[str, Any]:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": FRONTEND_CLIENT,
        "redirect_uri": redirect_uri,
    }
    r = requests.post(_token_endpoint(), data=data, timeout=5)
    r.raise_for_status()
    return r.json()


def refresh_tokens(refresh_token: str) -> Dict[str, Any]:
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": API_CLIENT,
        "client_secret": API_CLIENT_SECRET,
    }
    r = requests.post(_token_endpoint(), data=data, timeout=5)
    r.raise_for_status()
    return r.json()


def parse_id_token(id_token: str) -> Dict[str, Any]:
    try:
        parts = id_token.split(".")
        if len(parts) < 2:
            return {}
        payload = parts[1] + "=="
        decoded = base64.urlsafe_b64decode(payload.encode("utf-8"))
        return json.loads(decoded.decode("utf-8"))
    except Exception:
        return {}


def start_login_redirect(request_base_url: str, state: str) -> str:
    redirect_uri = urllib.parse.urljoin(request_base_url, REDIRECT_PATH)
    return build_auth_url(state=state, redirect_uri=redirect_uri)


def handle_oauth_callback(code: str, request_base_url: str, session_store: SessionStore) -> Dict[str, Any]:
    redirect_uri = urllib.parse.urljoin(request_base_url, REDIRECT_PATH)
    tokens = exchange_code_for_tokens(code, redirect_uri)
    id_token = tokens.get("id_token")
    refresh = tokens.get("refresh_token")
    access = tokens.get("access_token")
    claims = parse_id_token(id_token) if id_token else {}
    session = {
        "id_token": id_token,
        "access_token": access,
        "refresh_token": refresh,
        "claims": claims,
        "created_at": int(time.time()),
    }
    sid = session_store.create(session)
    return {"sid": sid, "claims": claims, "expires_in": SESSION_TTL}


def logout_session(sid: str, session_store: SessionStore) -> None:
    session_store.delete(sid)
