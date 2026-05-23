from __future__ import annotations
from typing import Dict, Set, List, Optional

DEFAULT_PERMISSIONS = [
    "create:issue",
    "delete:issue",
    "add:dependency",
    "read:context",
    "read:impact",
    "admin",
]

class RBAC:
    def __init__(self) -> None:
        self._store: Dict[str, Set[str]] = {}

    def grant(self, user_id: str, permission: str) -> None:
        self._store.setdefault(user_id, set()).add(permission)

    def revoke(self, user_id: str, permission: str) -> None:
        if user_id in self._store:
            self._store[user_id].discard(permission)

    def has_permission(self, user_id: Optional[str], permission: str) -> bool:
        if user_id is None:
            return False
        if user_id == "system" or permission == "public":
            return True
        return permission in self._store.get(user_id, set())

    def list_permissions(self, user_id: str) -> List[str]:
        return sorted(list(self._store.get(user_id, set())))
