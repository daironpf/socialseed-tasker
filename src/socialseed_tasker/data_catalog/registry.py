from __future__ import annotations
import json
import re
import time
from typing import Dict, List, Optional
from socialseed_tasker.application.ports import StoragePort
from socialseed_tasker.application.exceptions import StorageError

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


class SchemaCompatibilityError(Exception):
    pass


class SchemaRegistry:
    def __init__(self, storage: StoragePort):
        self.storage = storage

    def _schema_key(self, name: str, version: str) -> str:
        return f"schema:{name}:{version}"

    def _versions_key(self, name: str) -> str:
        return f"schema:versions:{name}"

    def _dataset_key(self, dataset_id: str) -> str:
        return f"dataset:{dataset_id}"

    def register_schema(self, name: str, version: str, schema: Dict, compatibility: str = "BACKWARD") -> None:
        if not SEMVER_RE.match(version):
            raise ValueError("version must be semantic MAJOR.MINOR.PATCH")
        versions = self.get_versions(name)
        if versions:
            latest = versions[-1]
            latest_schema = self.get_schema(name, latest)
            if not self._check_compatibility(latest_schema, schema, mode=compatibility):
                raise SchemaCompatibilityError("schema incompatible with latest version under mode " + compatibility)
        try:
            self.storage.put(self._schema_key(name, version), json.dumps(schema).encode("utf-8"))
            versions = versions + [version]
            self.storage.put(self._versions_key(name), json.dumps(versions).encode("utf-8"))
        except Exception as exc:
            raise StorageError(f"failed to persist schema: {exc}") from exc

    def get_schema(self, name: str, version: str) -> Dict:
        raw = self.storage.get(self._schema_key(name, version))
        if not raw:
            raise KeyError("schema not found")
        return json.loads(raw.decode("utf-8"))

    def get_versions(self, name: str) -> List[str]:
        raw = self.storage.get(self._versions_key(name))
        if not raw:
            return []
        return json.loads(raw.decode("utf-8"))

    def list_schemas(self) -> List[Dict]:
        if not hasattr(self.storage, "list_keys"):
            return []
        keys = self.storage.list_keys()
        names = set()
        for k in keys:
            if k.startswith("schema:versions:"):
                names.add(k.split("schema:versions:")[1])
        out = []
        for n in sorted(names):
            out.append({"name": n, "versions": self.get_versions(n)})
        return out

    def register_dataset(self, dataset_id: str, title: str, description: str, schema_name: str, default_schema_version: str, owner: str, tags: Optional[List[str]] = None) -> None:
        meta = {
            "dataset_id": dataset_id,
            "title": title,
            "description": description,
            "schema_name": schema_name,
            "default_schema_version": default_schema_version,
            "owner": owner,
            "tags": tags or [],
            "created_at": int(time.time()),
        }
        try:
            self.storage.put(self._dataset_key(dataset_id), json.dumps(meta).encode("utf-8"))
            raw = self.storage.get("dataset:list") or b"[]"
            arr = json.loads(raw.decode("utf-8")) if raw else []
            if dataset_id not in arr:
                arr.append(dataset_id)
                self.storage.put("dataset:list", json.dumps(arr).encode("utf-8"))
        except Exception as exc:
            raise StorageError(f"failed to persist dataset: {exc}") from exc

    def get_dataset(self, dataset_id: str) -> Dict:
        raw = self.storage.get(self._dataset_key(dataset_id))
        if not raw:
            raise KeyError("dataset not found")
        return json.loads(raw.decode("utf-8"))

    def list_datasets(self) -> List[Dict]:
        raw = self.storage.get("dataset:list") or b"[]"
        arr = json.loads(raw.decode("utf-8")) if raw else []
        out = []
        for did in arr:
            try:
                out.append(self.get_dataset(did))
            except Exception:
                pass
        return out

    def _check_compatibility(self, old_schema: Dict, new_schema: Dict, mode: str = "BACKWARD") -> bool:
        if mode == "NONE":
            return True

        def extract_required(sch: Dict) -> Dict[str, str]:
            props = sch.get("properties", {})
            req = {}
            for k, v in props.items():
                t = v.get("type")
                if t:
                    req[k] = t
            return req

        old_req = extract_required(old_schema)
        new_req = extract_required(new_schema)
        if mode in ("BACKWARD", "FULL"):
            for k, t in old_req.items():
                if k not in new_req:
                    return False
                if new_req[k] != t:
                    return False
        if mode in ("FORWARD", "FULL"):
            for k, t in new_req.items():
                if k not in old_req:
                    return False
                if old_req[k] != t:
                    return False
        return True
