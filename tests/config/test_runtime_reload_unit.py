from __future__ import annotations

import os
import threading
import time
from unittest.mock import MagicMock

import pytest

from socialseed_tasker.config.runtime import RuntimeConfig
from socialseed_tasker.config.flags import FeatureFlagStore
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage


def test_runtime_get_set_delete() -> None:
    rc = RuntimeConfig(storage=MemoryStorage(), poll_interval=1)
    rc.set("key1", "val1")
    assert rc.get("key1") == "val1"
    rc.delete("key1")
    assert rc.get("key1") is None


def test_runtime_list() -> None:
    rc = RuntimeConfig(storage=MemoryStorage())
    rc.set("a", 1)
    rc.set("b", 2)
    assert rc.list() == {"a": 1, "b": 2}


def test_register_callback_fires_on_set() -> None:
    rc = RuntimeConfig(storage=MemoryStorage())
    events = []

    def cb(name: str, value: object) -> None:
        events.append((name, value))

    rc.register_callback("cb_key", cb)
    rc.set("cb_key", "hello")
    assert ("cb_key", "hello") in events


def test_register_callback_fires_on_delete() -> None:
    rc = RuntimeConfig(storage=MemoryStorage())
    rc.set("del_key", "x")
    events = []

    def cb(name: str, value: object) -> None:
        events.append((name, value))

    rc.register_callback("del_key", cb)
    rc.delete("del_key")
    assert ("del_key", None) in events


def test_runtime_reload_triggers_callback() -> None:
    storage = MemoryStorage()
    store = FeatureFlagStore(storage)
    store.set_flag("poll_flag", "old")
    rc = RuntimeConfig(store=store, poll_interval=0.05)
    events = []

    def cb(name: str, value: object) -> None:
        events.append((name, value))

    rc.register_callback("poll_flag", cb)
    rc.start_polling()
    try:
        store.set_flag("poll_flag", "new")
        time.sleep(0.2)
        assert ("poll_flag", "new") in events
    finally:
        rc.stop_polling()


def test_start_stop_polling() -> None:
    s = MagicMock()
    s.get.return_value = None
    s.put.return_value = None
    s.delete.return_value = None
    s.list_keys.return_value = []
    rc = RuntimeConfig(storage=s, poll_interval=0.05)
    rc.start_polling()
    assert rc._polling is True
    assert rc._poll_thread is not None
    rc.stop_polling()
    assert rc._polling is False
