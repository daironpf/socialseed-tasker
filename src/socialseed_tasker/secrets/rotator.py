from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from typing import Any

from socialseed_tasker.application.ports import StoragePort

from .core import SecretsStore

ROTATIONS_KEY = "secrets:rotations"
DETERMINISTIC = os.getenv("TASKER_SECRETS_DETERMINISTIC", "0") == "1"


def _seed_master(name: str, ts: int) -> bytes:
    mk = os.getenv("TASKER_SECRETS_MASTER_KEY", "")
    data = f"{mk}:{name}:{ts}".encode("utf-8")
    return hashlib.sha256(data).digest()


class Rotator:
    def __init__(
        self, storage: StoragePort, secrets_store: SecretsStore
    ) -> None:
        self.storage = storage
        self.secrets = secrets_store

    def _load_rotations(self) -> dict[str, dict]:
        raw = self.storage.get(ROTATIONS_KEY) or b"{}"
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            return {}

    def _persist_rotations(self, data: dict[str, dict]) -> None:
        self.storage.put(ROTATIONS_KEY, json.dumps(data).encode("utf-8"))

    def schedule_rotation(
        self,
        name: str,
        interval_seconds: int,
        policy: dict[str, Any],
    ) -> str:
        rotations = self._load_rotations()
        rid = f"rot-{int(time.time() * 1000)}"
        rotations[rid] = {
            "id": rid,
            "name": name,
            "interval": interval_seconds,
            "policy": policy,
            "created_at": int(time.time()),
        }
        self._persist_rotations(rotations)
        return rid

    def list_rotations(self) -> list[dict[str, Any]]:
        return list(self._load_rotations().values())

    def run_rotation(self, rotation_id: str) -> dict[str, Any]:
        rotations = self._load_rotations()
        if rotation_id not in rotations:
            raise KeyError("rotation not found")
        r = rotations[rotation_id]
        name = r["name"]
        policy = r.get("policy", {})
        strategy = policy.get("strategy", "random")
        length = int(policy.get("length", 32))
        ts = int(time.time())
        if strategy == "random":
            if DETERMINISTIC:
                seed = _seed_master(name, ts)
                new_bytes = hmac.new(
                    seed, b"rotate", hashlib.sha256
                ).digest()[:length]
            else:
                new_bytes = os.urandom(length)
        elif strategy == "incremental":
            new_bytes = (
                str(ts).encode("utf-8")[:length].ljust(length, b"0")
            )
        elif strategy == "external":
            webhook = policy.get("webhook")
            if not webhook:
                raise ValueError("external strategy requires webhook")
            import requests

            resp = requests.post(
                webhook,
                json={"name": name, "rotation_id": rotation_id},
                timeout=10,
            )
            new_bytes = resp.content[:length]
        else:
            raise ValueError("unknown strategy")
        self.secrets.put_secret(
            name,
            new_bytes,
            metadata={"rotated_at": ts},
            actor="rotator",
        )
        return {
            "rotation_id": rotation_id,
            "name": name,
            "timestamp": ts,
            "strategy": strategy,
            "length": length,
        }
