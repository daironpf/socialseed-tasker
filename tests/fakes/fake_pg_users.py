"""Stateful psycopg fakes for the normalized PostgreSQL user model (issue #558).

``FakePgCursor`` simulates just enough of PostgreSQL for ``PostgresUserStore``:
schema DDL bookkeeping (``to_regclass``/``information_schema``), the legacy
table rename, ``ON CONFLICT DO NOTHING`` upserts with state, the migration
count verification and the authenticated JOIN query. ``ScriptedCursor`` is a
minimal fetch-all fake for the read repository.
"""

from __future__ import annotations

import re
from typing import Any

import psycopg
import pytest

_CREATE_TABLE = re.compile(r"CREATE TABLE IF NOT EXISTS (\w+)\s*\(", re.IGNORECASE)
_COLUMN_LINE = re.compile(r"^\s+(\w+)\s+(?:TEXT|INT|BOOLEAN|TIMESTAMPTZ|JSONB|DOUBLE|SERIAL)\b", re.MULTILINE)
_RENAME = re.compile(r'ALTER TABLE (\w+) RENAME TO "([^"]+)"', re.IGNORECASE)


def _create_table_parts(sql: str) -> tuple[str, set[str]] | None:
    match = _CREATE_TABLE.search(sql)
    if not match:
        return None
    name = match.group(1)
    body = sql[match.end() :]
    if "\n)" in body:
        body = body.split("\n)", 1)[0]
    columns = {m.group(1) for m in _COLUMN_LINE.finditer(body)}
    return name, columns


class FakePgConnection:
    """Connection fake returning the shared cursor on every ``cursor()`` call."""

    def __init__(self, cursor: FakePgCursor) -> None:
        self._cursor = cursor
        self.closed = False

    def cursor(self) -> FakePgCursor:
        return self._cursor

    def close(self) -> None:
        self.closed = True


class FakePgCursor:
    """Cursor fake tracking schema state, upserts and migration verification."""

    def __init__(self) -> None:
        self.statements: list[tuple[str, tuple[Any, ...] | None]] = []
        self.executemany_statements: list[tuple[str, list[tuple[Any, ...]]]] = []
        self.tables: set[str] = set()
        self.columns: dict[str, set[str]] = {}
        self.users: dict[str, dict[str, Any]] = {}
        self.human: dict[str, dict[str, Any]] = {}
        self.agents: dict[str, dict[str, Any]] = {}
        self.skills: dict[str, str] = {}
        self.user_skills: dict[str, set[str]] = {}
        self.session_logs: list[tuple[str, str, Any]] = []
        self.legacy_rows: list[tuple[Any, ...]] = []
        self.rowcount = 0
        self._next: Any = None
        self._rows: list[tuple[Any, ...]] = []
        self._generated = 0

    # -- context manager ----------------------------------------------------
    def __enter__(self) -> FakePgCursor:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    # -- helpers ------------------------------------------------------------
    @property
    def sql_log(self) -> list[str]:
        return [sql for sql, _ in self.statements]

    def _normalized_username(self, value: str) -> str | None:
        for row in self.users.values():
            if row["username_normalized"] == value:
                return row["username_normalized"]
        return None

    def _verify_count(self, kind: str) -> int:
        if kind == "identity":
            return sum(1 for row in self.legacy_rows if row[0] not in self.users)
        return sum(
            1
            for row in self.legacy_rows
            if row[0] not in self.human and row[0] not in self.agents
        )

    # -- execute ------------------------------------------------------------
    def execute(self, sql: str, params: tuple[Any, ...] | None = None) -> None:
        norm = " ".join(sql.split())
        low = norm.lower()
        self.statements.append((norm, params))
        self._next = None
        self._rows = []
        self.rowcount = 0

        if low.startswith("select to_regclass"):
            table = str(params[0])
            self._next = (table,) if table in self.tables else None
        elif "information_schema.columns" in low:
            table, column = str(params[0]), str(params[1])
            self._next = (1,) if column in self.columns.get(table, set()) else None
        elif low.startswith("alter table"):
            match = _RENAME.search(norm)
            if match:
                old, new = match.group(1), match.group(2)
                self.tables.discard(old)
                self.tables.add(new)
                self.columns[new] = self.columns.pop(old, set())
        elif low.startswith("create table"):
            parts = _create_table_parts(sql)
            if parts:
                name, cols = parts
                self.tables.add(name)
                self.columns.setdefault(name, set()).update(cols)
        elif low.startswith("create index"):
            pass
        elif low.startswith("insert into users"):
            values = tuple(params or ())
            returning = "returning id" in low
            if returning:
                username, normalized, user_type, created_at = values
                uid = None
            else:
                uid, username, normalized, user_type, created_at = values
            conflict = bool(uid and uid in self.users) or self._normalized_username(str(normalized)) is not None
            if conflict:
                self.rowcount = 0
                self._next = None
            else:
                if uid is None:
                    self._generated += 1
                    uid = f"pg-gen-{self._generated}"
                self.users[str(uid)] = {
                    "id": str(uid),
                    "username": username,
                    "username_normalized": normalized,
                    "user_type": user_type,
                    "created_at": created_at,
                }
                self.rowcount = 1
                self._next = (str(uid),) if returning else None
        elif low.startswith("insert into human_user"):
            uid, email, password_hash, role_id = tuple(params or ())
            if uid in self.human:
                self.rowcount = 0
            else:
                self.human[str(uid)] = {
                    "user_id": str(uid),
                    "email": email,
                    "password_hash": password_hash,
                    "role_id": role_id,
                    "avatar": None,
                    "github_handle": None,
                    "preferences": None,
                    "is_active": True,
                }
                self.rowcount = 1
        elif low.startswith("insert into agents_user"):
            uid, email = tuple(params or ())
            if uid in self.agents:
                self.rowcount = 0
            else:
                self.agents[str(uid)] = {
                    "user_id": str(uid),
                    "email": email,
                    "avatar": None,
                    "model": None,
                    "specialization": None,
                    "enabled": True,
                }
                self.rowcount = 1
        elif low.startswith("insert into skills"):
            slug, name = tuple(params or ())
            if slug in self.skills or name in self.skills.values():
                self.rowcount = 0
            else:
                self.skills[str(slug)] = str(name)
                self.rowcount = 1
        elif low.startswith("insert into user_skills"):
            uid, slug = tuple(params or ())
            linked = self.user_skills.setdefault(str(uid), set())
            if str(slug) in linked:
                self.rowcount = 0
            else:
                linked.add(str(slug))
                self.rowcount = 1
        elif low.startswith("insert into session_logs"):
            uid, created_at = str(params[0]), params[1]
            if any(log[0] == uid and log[1] == "login" and log[2] == created_at for log in self.session_logs):
                self.rowcount = 0
            else:
                self.session_logs.append((uid, "login", created_at))
                self.rowcount = 1
        elif low.startswith("update human_user"):
            uid = str(params[-1])
            row = self.human.get(uid)
            if row is None:
                self.rowcount = 0
            else:
                profile_keys = ("avatar", "github_handle", "preferences", "is_active")
                for key, value in zip(profile_keys, params[:4], strict=False):
                    if value is not None:
                        row[key] = value
                self.rowcount = 1
        elif low.startswith("update agents_user"):
            uid = str(params[-1])
            row = self.agents.get(uid)
            if row is None:
                self.rowcount = 0
            else:
                for key, value in zip(("avatar", "model", "specialization"), params[:3], strict=False):
                    if value is not None:
                        row[key] = value
                self.rowcount = 1
        elif low.startswith("delete from users"):
            uid = str(params[0])
            existed = uid in self.users
            self.users.pop(uid, None)
            self.human.pop(uid, None)
            self.agents.pop(uid, None)
            self.user_skills.pop(uid, None)
            self.rowcount = 1 if existed else 0
        elif "count(*)" in low and "not exists" in low:
            kind = "identity" if "select 1 from users u" in low else "profile"
            self._next = (self._verify_count(kind),)
        elif "from users_legacy" in low:
            self._rows = list(self.legacy_rows)
        elif low.startswith("select user_type from users"):
            uid = str(params[0])
            row = self.users.get(uid)
            self._next = (row["user_type"],) if row else None
        elif low.startswith("select username_normalized from users"):
            self._rows = [(row["username_normalized"],) for row in self.users.values()]
        elif low.startswith("select username, id from users"):
            self._rows = [
                (row["username"], row["id"]) for row in sorted(self.users.values(), key=lambda r: r["username"])
            ]
        elif "from users u" in low:
            normalized = str(params[0])
            for row in self.users.values():
                if row["username_normalized"] == normalized:
                    profile = self.human.get(row["id"], {})
                    self._next = (
                        row["id"],
                        row["username"],
                        row["user_type"],
                        profile.get("email"),
                        profile.get("password_hash"),
                        profile.get("role_id"),
                    )
                    break

    def executemany(self, sql: str, params_list: list[tuple[Any, ...]]) -> None:
        norm = " ".join(sql.split())
        self.statements.append((norm, None))
        self.executemany_statements.append((norm, list(params_list)))
        self.rowcount = len(params_list)
        self._next = None
        self._rows = []

    def fetchone(self) -> Any:
        row, self._next = self._next, None
        return row

    def fetchall(self) -> list[tuple[Any, ...]]:
        rows, self._rows = self._rows, []
        return rows


class ScriptedCursor:
    """Minimal cursor returning pre-canned rows (read repository tests)."""

    def __init__(
        self,
        fetchall_rows: list[tuple[Any, ...]] | None = None,
        fetchone_row: tuple[Any, ...] | None = None,
        rowcount: int = 1,
    ) -> None:
        self.statements: list[tuple[str, tuple[Any, ...] | None]] = []
        self.fetchall_rows = fetchall_rows if fetchall_rows is not None else []
        self.fetchone_row = fetchone_row
        self.rowcount = rowcount
        self.last_params: tuple[Any, ...] | None = None

    def __enter__(self) -> ScriptedCursor:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def execute(self, sql: str, params: tuple[Any, ...] | None = None) -> None:
        self.statements.append((" ".join(sql.split()), params))
        self.last_params = params

    def fetchone(self) -> tuple[Any, ...] | None:
        return self.fetchone_row

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self.fetchall_rows


class ScriptedConnection:
    """Connection returning a pre-built cursor."""

    def __init__(self, cursor: Any) -> None:
        self._cursor = cursor
        self.closed = False

    def cursor(self) -> Any:
        return self._cursor

    def close(self) -> None:
        self.closed = True


def install_fake_pg(monkeypatch: pytest.MonkeyPatch, cursor: Any) -> Any:
    """Route every ``psycopg.connect`` call to a fake connection wrapping ``cursor``."""
    connection = ScriptedConnection(cursor) if not isinstance(cursor, FakePgCursor) else FakePgConnection(cursor)
    monkeypatch.setattr(psycopg, "connect", lambda *args, **kwargs: connection)
    return connection
