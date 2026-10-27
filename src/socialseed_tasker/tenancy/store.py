# src/socialseed_tasker/tenancy/store.py
from __future__ import annotations

import json
from typing import Any

from socialseed_tasker.application.exceptions import StorageError
from socialseed_tasker.application.ports import StoragePort


class TenantStore:
    KEY = "tenants:registry"

    def __init__(self, storage: StoragePort):
        self.storage = storage
        self._cache: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        try:
            raw = self.storage.get(self.KEY)
            if raw:
                loaded: object = json.loads(raw.decode("utf-8"))
                if isinstance(loaded, dict):
                    self._cache = {
                        key: value
                        for key, value in loaded.items()
                        if isinstance(key, str) and isinstance(value, dict)
                    }
                else:
                    self._cache = {}
            else:
                self._cache = {}
        except Exception:
            self._cache = {}

    def _persist(self) -> None:
        try:
            self.storage.put(self.KEY, json.dumps(self._cache).encode("utf-8"))
        except Exception as exc:
            raise StorageError(f"Failed to persist tenants: {exc}") from exc

    def create_tenant(
        self, tenant_id: str, config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if tenant_id in self._cache:
            raise ValueError("tenant exists")
        cfg = config or {}
        self._cache[tenant_id] = {"id": tenant_id, "config": cfg}
        self._persist()
        return self._cache[tenant_id]

    def delete_tenant(self, tenant_id: str) -> None:
        if tenant_id in self._cache:
            self._cache.pop(tenant_id)
            self._persist()

    def list_tenants(self) -> list[dict[str, Any]]:
        return list(self._cache.values())

    def get_tenant(self, tenant_id: str) -> dict[str, Any] | None:
        return self._cache.get(tenant_id)
