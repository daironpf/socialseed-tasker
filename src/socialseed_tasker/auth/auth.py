from __future__ import annotations

import json
import os
from typing import Any, Protocol


class AuthProvider(Protocol):
    def verify_token(self, token: str) -> str | None:
        ...

    def get_user_info(self, user_id: str) -> dict[str, Any] | None:
        ...

class InMemoryAuthProvider:
    def __init__(self, users: dict[str, dict[str, Any]] | None = None) -> None:
        if users is not None:
            self._users = users
        else:
            env = os.getenv("TASKER_AUTH_USERS")
            if env:
                self._users = json.loads(env)
            else:
                path = os.path.join(os.path.dirname(__file__), "users.json")
                if os.path.exists(path):
                    with open(path, encoding="utf-8") as fh:
                        self._users = json.load(fh)
                else:
                    self._users = {}

        self._token_map = {}
        for uid, info in self._users.items():
            token = info.get("token")
            if token:
                self._token_map[token] = uid

    def verify_token(self, token: str) -> str | None:
        return self._token_map.get(token)

    def get_user_info(self, user_id: str) -> dict[str, Any] | None:
        return self._users.get(user_id)

def load_auth_provider() -> AuthProvider:
    provider = os.getenv("TASKER_AUTH_PROVIDER", "inmemory")
    if provider == "inmemory":
        return InMemoryAuthProvider()
    return InMemoryAuthProvider()
