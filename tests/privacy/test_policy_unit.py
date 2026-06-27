from __future__ import annotations
import os
import time
from socialseed_tasker.privacy.policy import evaluate_policy, get_retention_for


def test_legal_hold_always_kept():
    meta = {"kind": "issue", "created_at": 0, "tenant": None, "tags": ["legal-hold"]}
    assert evaluate_policy(meta) is True


def test_recent_record_is_kept():
    meta = {"kind": "storage", "created_at": int(time.time()), "tenant": None, "tags": []}
    assert evaluate_policy(meta) is True


def test_expired_record_is_eligible():
    meta = {"kind": "storage", "created_at": 0, "tenant": None, "tags": []}
    assert evaluate_policy(meta) is False


def test_empty_meta_is_kept():
    assert evaluate_policy({}) is True
    assert evaluate_policy(None) is True


def test_none_tags():
    meta = {"kind": "log", "created_at": 0, "tenant": None, "tags": None}
    assert evaluate_policy(meta) is False


def test_env_override_per_kind(monkeypatch):
    monkeypatch.setenv("TASKER_RETENTION_STORAGE", "9999999999")
    meta = {"kind": "storage", "created_at": 0, "tenant": None, "tags": []}
    assert evaluate_policy(meta) is True


def test_get_retention_for_default():
    assert get_retention_for("nonexistent") == 60 * 60 * 24 * 365


def test_get_retention_for_env_override(monkeypatch):
    monkeypatch.setenv("TASKER_RETENTION_ISSUE", "3600")
    assert get_retention_for("issue") == 3600


def test_get_retention_for_invalid_env(monkeypatch):
    monkeypatch.setenv("TASKER_RETENTION_ISSUE", "notanumber")
    assert get_retention_for("issue") == 60 * 60 * 24 * 365 * 3


def test_tenant_override(monkeypatch):
    monkeypatch.setenv("TASKER_RETENTION_TENANT1_STORAGE", "9999999999")
    meta = {"kind": "storage", "created_at": 0, "tenant": "tenant1", "tags": []}
    assert evaluate_policy(meta) is True


def test_retention_for_kind(monkeypatch):
    monkeypatch.setenv("TASKER_RETENTION_LOG", "1")
    meta = {"kind": "log", "created_at": int(time.time()) - 10, "tenant": None, "tags": []}
    assert evaluate_policy(meta) is False
