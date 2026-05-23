from __future__ import annotations

import os
import threading
import time
from typing import Any, Callable

from socialseed_tasker.config.flags import FeatureFlagClient, FeatureFlagStore
from socialseed_tasker.application.ports import StoragePort


Callback = Callable[[str, Any], None]


class RuntimeConfig:
    """Wraps FeatureFlagStore and FeatureFlagClient with optional polling for hot-reload."""

    def __init__(
        self,
        storage: StoragePort | None = None,
        store: FeatureFlagStore | None = None,
        client: FeatureFlagClient | None = None,
        poll_interval: int = 5,
    ) -> None:
        if store is None:
            if storage is None:
                raise ValueError("either storage or store must be provided")
            store = FeatureFlagStore(storage)
        if client is None:
            client = FeatureFlagClient(store)
        self._store = store
        self._client = client
        self._callbacks: dict[str, list[Callback]] = {}
        self._lock = threading.RLock()
        self._poll_interval = poll_interval
        self._polling = False
        self._poll_thread: threading.Thread | None = None
        self._known: dict[str, object] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, name: str, default: object = None) -> object:
        return self._client.get_flag(name, default=default)

    def set(self, name: str, value: object) -> None:
        old = self._store.get_flag(name)
        self._store.set_flag(name, value)
        if value != old:
            self._notify(name, value)

    def list(self) -> dict[str, object]:
        return self._store.list_flags()

    def delete(self, name: str) -> None:
        self._store.delete_flag(name)
        self._notify(name, None)

    def register_callback(self, name: str, fn: Callback) -> None:
        with self._lock:
            self._callbacks.setdefault(name, []).append(fn)

    # ------------------------------------------------------------------
    # Polling (hot-reload)
    # ------------------------------------------------------------------

    def start_polling(self) -> None:
        if self._polling:
            return
        self._polling = True
        self._known = dict(self._store.list_flags())
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def stop_polling(self) -> None:
        self._polling = False
        if self._poll_thread is not None:
            self._poll_thread.join(timeout=2)
            self._poll_thread = None

    def _poll_loop(self) -> None:
        while self._polling:
            time.sleep(self._poll_interval)
            try:
                current = dict(self._store.list_flags())
            except Exception:
                continue
            for name, value in current.items():
                old = self._known.get(name)
                if value != old:
                    self._known[name] = value
                    self._notify(name, value)
            for name in list(self._known):
                if name not in current:
                    self._known.pop(name, None)
                    self._notify(name, None)

    def _notify(self, name: str, value: object) -> None:
        with self._lock:
            fns = list(self._callbacks.get(name, []))
        for fn in fns:
            try:
                fn(name, value)
            except Exception:
                pass


def _env_bool(key: str, default: str = "0") -> bool:
    return os.environ.get(key, default).strip() in ("1", "true", "yes")


def build_runtime_config(
    storage: StoragePort,
    poll_interval: int | None = None,
) -> RuntimeConfig:
    if poll_interval is None:
        poll_interval = int(os.environ.get("TASKER_CONFIG_POLL_SECONDS", "5"))
    rc = RuntimeConfig(storage=storage, poll_interval=poll_interval)
    if _env_bool("TASKER_CONFIG_RELOAD"):
        rc.start_polling()
    return rc
