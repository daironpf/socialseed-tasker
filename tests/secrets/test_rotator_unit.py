import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from socialseed_tasker.secrets.core import SecretsStore
from socialseed_tasker.secrets.rotator import Rotator


def test_schedule_and_run_rotation(monkeypatch):
    monkeypatch.setenv("TASKER_SECRETS_DETERMINISTIC", "1")
    s = MemoryStorage()
    ss = SecretsStore(s)
    ss.put_secret("krot", b"old", actor="tester")
    rot = Rotator(storage=s, secrets_store=ss)
    rid = rot.schedule_rotation(
        "krot", 10, {"strategy": "random", "length": 16}
    )
    res = rot.run_rotation(rid)
    assert res["rotation_id"] == rid
    val = ss.get_secret("krot", reveal=True)
    assert val["value"] != b"old"


def test_rotation_not_found():
    import pytest

    s = MemoryStorage()
    ss = SecretsStore(s)
    rot = Rotator(storage=s, secrets_store=ss)
    with pytest.raises(KeyError):
        rot.run_rotation("nonexistent")


def test_list_rotations():
    s = MemoryStorage()
    ss = SecretsStore(s)
    rot = Rotator(storage=s, secrets_store=ss)
    rid = rot.schedule_rotation(
        "test", 60, {"strategy": "incremental", "length": 8}
    )
    rotations = rot.list_rotations()
    ids = [r["id"] for r in rotations]
    assert rid in ids


def test_incremental_rotation(monkeypatch):
    monkeypatch.setenv("TASKER_SECRETS_DETERMINISTIC", "1")
    s = MemoryStorage()
    ss = SecretsStore(s)
    ss.put_secret("inc_test", b"original", actor="tester")
    rot = Rotator(storage=s, secrets_store=ss)
    rid = rot.schedule_rotation(
        "inc_test", 10, {"strategy": "incremental", "length": 8}
    )
    res = rot.run_rotation(rid)
    assert res["strategy"] == "incremental"
    val = ss.get_secret("inc_test", reveal=True)
    assert val["value"] != b"original"
