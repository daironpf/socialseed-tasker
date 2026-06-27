from __future__ import annotations
import os
import json
from typing import Optional, Dict, Protocol

class AuthProvider(Protocol):
    def verify_token(self, token: str) -> Optional[str]:
        ...

class InMemoryAuthProvider:
    def __init__(self, users: Optional[Dict[str, Dict]] = None) -> None:
        if users is not None:
            self._users = users
        else:
            env = os.getenv("TASKER_AUTH_USERS")
            if env:
                self._users = json.loads(env)
            else:
                path = os.path.join(os.path.dirname(__file__), "users.json")
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as fh:
                        self._users = json.load(fh)
                else:
                    self._users = {}

        self._token_map = {}
        for uid, info in self._users.items():
            token = info.get("token")
            if token:
                self._token_map[token] = uid

    def verify_token(self, token: str) -> Optional[str]:
        return self._token_map.get(token)

def load_auth_provider() -> AuthProvider:
    provider = os.getenv("TASKER_AUTH_PROVIDER", "inmemory")
    if provider == "inmemory":
        return InMemoryAuthProvider()
    return InMemoryAuthProvider()
