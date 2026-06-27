from __future__ import annotations

import json
import os
import threading

from socialseed_tasker.application.exceptions import StorageError
from socialseed_tasker.application.ports import StoragePort


class FeatureFlagStore:
    """Persistent feature-flag storage backed by StoragePort under key 'flags:registry'."""

    def __init__(self, storage: StoragePort) -> None:
        self._storage = storage
        self._lock = threading.RLock()

    def get_flag(self, name: str) -> object | None:
        with self._lock:
            raw = self._storage.get("flags:registry")
            if raw is None:
                return None
            try:
                registry = json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                registry = {}
            return registry.get(name)

    def set_flag(self, name: str, value: object) -> None:
        with self._lock:
            raw = self._storage.get("flags:registry")
            if raw is not None:
                try:
                    registry = json.loads(raw.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    registry = {}
            else:
                registry = {}
            registry[name] = value
            try:
                self._storage.put("flags:registry", json.dumps(registry).encode("utf-8"))
            except Exception as exc:
                raise StorageError(f"failed to persist flag '{name}': {exc}") from exc

    def list_flags(self) -> dict[str, object]:
        with self._lock:
            raw = self._storage.get("flags:registry")
            if raw is None:
                return {}
            try:
                return dict(json.loads(raw.decode("utf-8")))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return {}

    def delete_flag(self, name: str) -> None:
        with self._lock:
            raw = self._storage.get("flags:registry")
            if raw is None:
                return
            try:
                registry = json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                registry = {}
            registry.pop(name, None)
            self._storage.put("flags:registry", json.dumps(registry).encode("utf-8"))


class FeatureFlagClient:
    """Client that checks env overrides (TASKER_FLAG_<NAME>) before falling back to the store."""

    def __init__(self, store: FeatureFlagStore) -> None:
        self._store = store

    @staticmethod
    def _env_name(name: str) -> str:
        return "TASKER_FLAG_" + name.upper().replace("-", "_")

    def get_flag(self, name: str, default: object = None) -> object:
        env_key = self._env_name(name)
        env_val = os.environ.get(env_key)
        if env_val is not None:
            try:
                return json.loads(env_val)
            except (json.JSONDecodeError, ValueError):
                return env_val
        stored = self._store.get_flag(name)
        if stored is not None:
            return stored
        return default
