import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from socialseed_tasker.secrets.core import AUDIT_KEY, SecretsStore


def test_put_get_delete_list_and_audit():
    s = MemoryStorage()
    ss = SecretsStore(s)
    ss.put_secret("k1", b"v1", metadata={"env": "dev"}, actor="tester")
    meta = ss.get_secret("k1", reveal=False)
    assert meta["metadata"]["env"] == "dev"
    names = ss.list_secrets()
    assert "k1" in names
    ss.delete_secret("k1", actor="tester")
    raw = s.get(AUDIT_KEY)
    assert raw is not None
    import json

    arr = json.loads(raw.decode("utf-8"))
    assert len(arr) >= 2


def test_get_secret_not_found():
    import pytest

    s = MemoryStorage()
    ss = SecretsStore(s)
    with pytest.raises(KeyError):
        ss.get_secret("nonexistent")


def test_get_secret_reveal():
    s = MemoryStorage()
    ss = SecretsStore(s)
    ss.put_secret("reveal_test", b"hidden", actor="tester")
    res = ss.get_secret("reveal_test", reveal=True)
    assert res["value"] == b"hidden"


def test_list_secrets_with_prefix():
    s = MemoryStorage()
    ss = SecretsStore(s)
    ss.put_secret("app/db", b"pw1", actor="tester")
    ss.put_secret("app/cache", b"pw2", actor="tester")
    ss.put_secret("other/key", b"pw3", actor="tester")
    names = ss.list_secrets(prefix="app/")
    assert "app/db" in names
    assert "app/cache" in names
    assert "other/key" not in names


def test_put_overwrites_existing():
    s = MemoryStorage()
    ss = SecretsStore(s)
    ss.put_secret("overwrite", b"old", actor="tester")
    ss.put_secret("overwrite", b"new", actor="tester")
    res = ss.get_secret("overwrite", reveal=True)
    assert res["value"] == b"new"


def test_delete_nonexistent_does_not_raise():
    s = MemoryStorage()
    ss = SecretsStore(s)
    ss.delete_secret("doesnotexist", actor="tester")
