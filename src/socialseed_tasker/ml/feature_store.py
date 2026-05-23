from __future__ import annotations
import json
import hashlib
from typing import Dict, Any, List, Optional
from socialseed_tasker.application.ports import StoragePort


class FeatureStore:
    PREFIX = "ml:features:"

    def __init__(self, storage: StoragePort):
        self.storage = storage

    def _key(self, key: str) -> str:
        return self.PREFIX + key

    def put_features(self, key: str, features: Dict[str, Any]) -> None:
        payload = json.dumps(features, sort_keys=True).encode("utf-8")
        self.storage.put(self._key(key), payload)

    def get_features(self, key: str) -> Optional[Dict[str, Any]]:
        raw = self.storage.get(self._key(key))
        if not raw:
            return None
        return json.loads(raw.decode("utf-8"))

    def list_keys(self, prefix: str = "") -> List[str]:
        if not hasattr(self.storage, "list_keys"):
            return []
        all_keys = self.storage.list_keys()
        ks = [k[len(self.PREFIX):] for k in all_keys if k.startswith(self.PREFIX)]
        if prefix:
            return [k for k in ks if k.startswith(prefix)]
        return ks

    def compute_input_hash(self, features: Dict[str, Any]) -> str:
        b = json.dumps(features, sort_keys=True).encode("utf-8")
        return hashlib.sha256(b).hexdigest()
