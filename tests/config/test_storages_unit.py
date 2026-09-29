from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from socialseed_tasker.config import storage as storage_config
from socialseed_tasker.config.storage import build_storage, get_database_url, get_redis_url
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage


def test_get_redis_url_none_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TASKER_REDIS_URL", raising=False)
    assert get_redis_url() is None


def test_get_redis_url_returns_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKER_REDIS_URL", "redis://tasker-redis:6379/0")
    assert get_redis_url() == "redis://tasker-redis:6379/0"


def test_get_redis_url_empty_string_is_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKER_REDIS_URL", "")
    assert get_redis_url() is None


def test_get_database_url_none_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TASKER_DATABASE_URL", raising=False)
    assert get_database_url() is None


def test_get_database_url_returns_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKER_DATABASE_URL", "postgresql://tasker:tasker@tasker-db-pg:5432/tasker")
    assert get_database_url() == "postgresql://tasker:tasker@tasker-db-pg:5432/tasker"


def test_build_storage_defaults_to_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TASKER_REDIS_URL", raising=False)
    backend, storage = build_storage()
    assert backend == "memory"
    assert isinstance(storage, MemoryStorage)


def test_build_storage_uses_redis_when_reachable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKER_REDIS_URL", "redis://tasker-redis:6379/0")
    fake = MagicMock()
    redis_cls = MagicMock(return_value=fake)
    monkeypatch.setattr(storage_config, "RedisStorage", redis_cls)
    backend, storage = build_storage()
    assert backend == "redis"
    assert storage is fake
    redis_cls.assert_called_once_with(url="redis://tasker-redis:6379/0")


def test_build_storage_falls_back_to_memory_when_redis_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKER_REDIS_URL", "redis://tasker-redis:6379/0")
    monkeypatch.setattr(storage_config, "RedisStorage", MagicMock(side_effect=RuntimeError("redis down")))
    backend, storage = build_storage()
    assert backend == "memory"
    assert isinstance(storage, MemoryStorage)
