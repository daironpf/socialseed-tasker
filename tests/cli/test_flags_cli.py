from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from socialseed_tasker.cli.flags_cli import cmd_flag_set, cmd_flag_get, cmd_flag_list, cmd_flag_delete


def _make_args(**kwargs):
    ns = MagicMock()
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _make_container():
    c = MagicMock()
    c.runtime_config = MagicMock()
    c.rbac = MagicMock()
    c.rbac.has_permission.return_value = True
    return c


class TestCmdFlagSet:
    def test_success(self):
        container = _make_container()
        args = _make_args(name="myflag", value="true")
        cmd_flag_set(args, container, "user1")
        container.runtime_config.set.assert_called_once_with("myflag", "true")

    def test_permission_denied(self):
        container = _make_container()
        container.rbac.has_permission.return_value = False
        args = _make_args(name="myflag", value="x")
        with pytest.raises(SystemExit) as exc:
            cmd_flag_set(args, container, "user1")
        assert exc.value.code == 2


class TestCmdFlagGet:
    def test_success(self, capsys):
        container = _make_container()
        container.runtime_config.get.return_value = "v1"
        args = _make_args(name="myflag")
        cmd_flag_get(args, container, "user1")
        out = json.loads(capsys.readouterr().out)
        assert out["status"] == "ok"
        assert out["value"] == "v1"

    def test_permission_denied(self):
        container = _make_container()
        container.rbac.has_permission.return_value = False
        args = _make_args(name="myflag")
        with pytest.raises(SystemExit) as exc:
            cmd_flag_get(args, container, "user1")
        assert exc.value.code == 2


class TestCmdFlagList:
    def test_success(self, capsys):
        container = _make_container()
        container.runtime_config.list.return_value = {"a": 1}
        args = _make_args()
        cmd_flag_list(args, container, "user1")
        out = json.loads(capsys.readouterr().out)
        assert out["status"] == "ok"
        assert out["flags"] == {"a": 1}

    def test_permission_denied(self):
        container = _make_container()
        container.rbac.has_permission.return_value = False
        args = _make_args()
        with pytest.raises(SystemExit) as exc:
            cmd_flag_list(args, container, "user1")
        assert exc.value.code == 2


class TestCmdFlagDelete:
    def test_success(self):
        container = _make_container()
        args = _make_args(name="myflag")
        cmd_flag_delete(args, container, "user1")
        container.runtime_config.delete.assert_called_once_with("myflag")

    def test_permission_denied(self):
        container = _make_container()
        container.rbac.has_permission.return_value = False
        args = _make_args(name="myflag")
        with pytest.raises(SystemExit) as exc:
            cmd_flag_delete(args, container, "user1")
        assert exc.value.code == 2
