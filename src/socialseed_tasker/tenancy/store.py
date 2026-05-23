# src/socialseed_tasker/tenancy/store.py
from __future__ import annotations
from typing import Optional, Dict, List
import json
from socialseed_tasker.application.ports import StoragePort
from socialseed_tasker.application.exceptions import StorageError

class TenantStore:
    KEY = "tenants:registry"

    def __init__(self, storage: StoragePort):
        self.storage = storage
        self._cache: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        try:
            raw = self.storage.get(self.KEY)
            if raw:
                self._cache = json.loads(raw.decode("utf-8"))
            else:
                self._cache = {}
        except Exception:
            self._cache = {}

    def _persist(self):
        try:
            self.storage.put(self.KEY, json.dumps(self._cache).encode("utf-8"))
        except Exception as exc:
            raise StorageError(f"Failed to persist tenants: {exc}") from exc

    def create_tenant(self, tenant_id: str, config: Optional[Dict] = None) -> Dict:
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

    def list_tenants(self) -> List[Dict]:
        return list(self._cache.values())

    def get_tenant(self, tenant_id: str) -> Optional[Dict]:
        return self._cache.get(tenant_id)
