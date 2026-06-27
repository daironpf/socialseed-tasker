from __future__ import annotations

import json
import os
from unittest.mock import MagicMock

import pytest

from socialseed_tasker.config.flags import FeatureFlagClient, FeatureFlagStore
from socialseed_tasker.application.exceptions import StorageError
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage


def _mock_storage() -> MemoryStorage:
    return MemoryStorage()


class TestFeatureFlagStore:
    def test_get_flag_returns_none_when_missing(self) -> None:
        s = _mock_storage()
        ffs = FeatureFlagStore(s)
        assert ffs.get_flag("nonexistent") is None

    def test_set_and_get_flag(self) -> None:
        s = _mock_storage()
        ffs = FeatureFlagStore(s)
        ffs.set_flag("test_flag", 42)
        assert ffs.get_flag("test_flag") == 42

    def test_list_flags(self) -> None:
        s = _mock_storage()
        ffs = FeatureFlagStore(s)
        ffs.set_flag("a", 1)
        ffs.set_flag("b", 2)
        flags = ffs.list_flags()
        assert flags == {"a": 1, "b": 2}

    def test_delete_flag(self) -> None:
        s = _mock_storage()
        ffs = FeatureFlagStore(s)
        ffs.set_flag("to_delete", "value")
        assert ffs.get_flag("to_delete") == "value"
        ffs.delete_flag("to_delete")
        assert ffs.get_flag("to_delete") is None

    def test_delete_nonexistent_does_not_raise(self) -> None:
        s = _mock_storage()
        ffs = FeatureFlagStore(s)
        ffs.delete_flag("nonexistent")

    def test_storage_error_raised_on_put_failure(self) -> None:
        s = MagicMock()
        s.get.return_value = None
        s.put.side_effect = RuntimeError("disk full")
        ffs = FeatureFlagStore(s)
        with pytest.raises(StorageError):
            ffs.set_flag("x", 1)


class TestFeatureFlagClient:
    def test_env_override_takes_precedence(self) -> None:
        s = _mock_storage()
        ffs = FeatureFlagStore(s)
        client = FeatureFlagClient(ffs)
        os.environ["TASKER_FLAG_MY_FLAG"] = '"env_value"'
        try:
            val = client.get_flag("my-flag", default="fallback")
            assert val == "env_value"
        finally:
            del os.environ["TASKER_FLAG_MY_FLAG"]

    def test_env_override_raw_string(self) -> None:
        s = _mock_storage()
        ffs = FeatureFlagStore(s)
        client = FeatureFlagClient(ffs)
        os.environ["TASKER_FLAG_RAW_STR"] = "hello"
        try:
            val = client.get_flag("raw-str")
            assert val == "hello"
        finally:
            del os.environ["TASKER_FLAG_RAW_STR"]

    def test_falls_back_to_store(self) -> None:
        s = _mock_storage()
        ffs = FeatureFlagStore(s)
        ffs.set_flag("stored_flag", "stored")
        client = FeatureFlagClient(ffs)
        val = client.get_flag("stored_flag", default="fallback")
        assert val == "stored"

    def test_falls_back_to_default(self) -> None:
        s = _mock_storage()
        ffs = FeatureFlagStore(s)
        client = FeatureFlagClient(ffs)
        val = client.get_flag("unknown", default="default_val")
        assert val == "default_val"
