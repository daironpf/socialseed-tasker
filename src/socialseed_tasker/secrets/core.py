from __future__ import annotations

import base64
import hashlib
import json
import time
from typing import Any

from socialseed_tasker.application.ports import StoragePort

from .crypto import decrypt, encrypt

AUDIT_KEY = "secrets:audit"
SECRETS_PREFIX = "secrets:"


def _hash_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class SecretsStore:
    def __init__(self, storage: StoragePort) -> None:
        self.storage = storage

    def _key(self, name: str) -> str:
        return SECRETS_PREFIX + name

    def put_secret(
        self,
        name: str,
        value: bytes,
        metadata: dict[str, Any] | None = None,
        actor: str | None = None,
    ) -> None:
        enc = encrypt(value)
        meta = metadata or {}
        entry = {
            "value": base64.b64encode(enc).decode("utf-8"),
            "metadata": meta,
            "ts": int(time.time()),
        }
        self.storage.put(self._key(name), json.dumps(entry).encode("utf-8"))
        self._write_audit(
            {
                "action": "put",
                "name": name,
                "actor": actor or "cli",
                "timestamp": int(time.time()),
                "new_hash": _hash_bytes(enc),
            }
        )

    def get_secret(
        self, name: str, reveal: bool = False
    ) -> dict[str, Any]:
        raw = self.storage.get(self._key(name))
        if not raw:
            raise KeyError("secret not found")
        entry: dict = json.loads(raw.decode("utf-8"))
        if reveal:
            enc = base64.b64decode(entry["value"].encode("utf-8"))
            val = decrypt(enc)
            return {
                "value": val,
                "metadata": entry.get("metadata", {}),
                "ts": entry.get("ts"),
            }
        return {
            "metadata": entry.get("metadata", {}),
            "ts": entry.get("ts"),
        }

    def delete_secret(
        self, name: str, actor: str | None = None
    ) -> None:
        raw = self.storage.get(self._key(name))
        prev_hash = None
        if raw:
            entry: dict = json.loads(raw.decode("utf-8"))
            prev_hash = _hash_bytes(
                base64.b64decode(entry["value"].encode("utf-8"))
            )
        self.storage.delete(self._key(name))
        self._write_audit(
            {
                "action": "delete",
                "name": name,
                "actor": actor or "cli",
                "timestamp": int(time.time()),
                "prev_hash": prev_hash,
            }
        )

    def list_secrets(self, prefix: str = "") -> list[str]:
        keys = self.storage.list_keys()
        out = []
        for k in keys:
            if k.startswith(SECRETS_PREFIX):
                name = k[len(SECRETS_PREFIX) :]
                if prefix and not name.startswith(prefix):
                    continue
                out.append(name)
        return sorted(out)

    def _write_audit(self, audit: dict[str, Any]) -> None:
        raw = self.storage.get(AUDIT_KEY) or b"[]"
        try:
            arr: list = json.loads(raw.decode("utf-8")) if raw else []
        except Exception:
            arr = []
        arr.append(audit)
        self.storage.put(AUDIT_KEY, json.dumps(arr).encode("utf-8"))
