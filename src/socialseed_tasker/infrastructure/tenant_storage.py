# src/socialseed_tasker/infrastructure/tenant_storage.py
from __future__ import annotations
from typing import Optional, List
from socialseed_tasker.application.ports import StoragePort

class NamespacedStorage(StoragePort):
    def __init__(self, base: StoragePort, tenant_id: str):
        self._base = base
        self._prefix = f"tenant:{tenant_id}:"

    def _key(self, key: str) -> str:
        return self._prefix + key

    def put(self, key: str, value: bytes, ttl_seconds: Optional[int] = None) -> None:
        return self._base.put(self._key(key), value, ttl_seconds=ttl_seconds)

    def get(self, key: str) -> Optional[bytes]:
        return self._base.get(self._key(key))

    def delete(self, key: str) -> None:
        return self._base.delete(self._key(key))

    def list_keys(self) -> List[str]:
        if hasattr(self._base, "list_keys"):
            keys = self._base.list_keys()
            prefix = self._prefix
            return [k[len(prefix):] for k in keys if k.startswith(prefix)]
        return []
