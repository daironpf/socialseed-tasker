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
        self.committed = False
        self.rolled_back = False

    def cursor(self) -> FakePgCursor:
        return self._cursor

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

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
        self.roles: dict[str, int] = {"ADMIN": 3, "DEVELOPER": 2, "VIEWER": 1}
        self.tools: dict[str, str] = {}
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

    def _agent_profile_row(self, uid: str) -> tuple[Any, ...]:
        """Compose the ``_AGENT_PROFILE_ROW_SQL`` tuple for one agent (#564)."""
        user = self.users[uid]
        profile = self.agents[uid]
        return (
            uid,
            user["username"],
            user.get("created_at"),
            profile.get("email"),
            profile.get("avatar"),
            profile.get("model"),
            profile.get("specialization"),
            profile.get("temperature"),
            profile.get("system_prompt"),
            profile.get("tools", "[]"),
            profile.get("write_access", "[]"),
            profile.get("limits"),
            profile.get("enabled", True),
            profile.get("last_used_at"),
        )

    # -- execute ------------------------------------------------------------
    def execute(self, sql: str, params: tuple[Any, ...] | None = None) -> None:
        norm = " ".join(sql.split())
        low = norm.lower()
        self.statements.append((norm, params))
        self._next = None
        self._rows = []
        self.rowcount = 0

        if "insert into roles" in low and params:
            self.roles[str(params[0])] = int(params[2]) if len(params) > 2 else 0
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
            if len(values) == 2:
                username, normalized = values
                # The literal lives in the SQL (#559 humans, #564 agents).
                user_type, created_at, uid = ("agent" if "'agent'" in low else "human"), None, None
            elif returning:
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
            values = tuple(params or ())
            if len(values) >= 8:
                # create_human_user with an explicit password_hash (#563)
                uid, email, password_hash, role_id, avatar, github_handle, preferences, is_active = values[:8]
            elif len(values) >= 7:
                # legacy create form: password hash was the '' literal, not a param (#559)
                uid, email, role_id, avatar, github_handle, preferences, is_active = values[:7]
                password_hash = ""
            else:
                uid, email, password_hash, role_id = values
                avatar = github_handle = preferences = None
                is_active = True
            if uid in self.human:
                self.rowcount = 0
            else:
                self.human[str(uid)] = {
                    "user_id": str(uid),
                    "email": email,
                    "password_hash": password_hash,
                    "role_id": role_id,
                    "avatar": avatar,
                    "github_handle": github_handle,
                    "preferences": preferences,
                    "is_active": is_active,
                }
                self.rowcount = 1
        elif low.startswith("insert into agents_user"):
            values = tuple(params or ())
            if len(values) >= 11:
                # Full agent profile insert (#564): 11 positional columns.
                (
                    uid, email, avatar, model, specialization, temperature,
                    system_prompt, tools, write_access, limits, enabled,
                ) = values[:11]
                if uid in self.agents:
                    self.rowcount = 0
                else:
                    self.agents[str(uid)] = {
                        "user_id": str(uid),
                        "email": email,
                        "avatar": avatar,
                        "model": model,
                        "specialization": specialization,
                        "temperature": temperature,
                        "system_prompt": system_prompt,
                        "tools": tools,
                        "write_access": write_access,
                        "limits": limits,
                        "enabled": enabled,
                        "last_used_at": None,
                    }
                    self.rowcount = 1
            else:
                uid, email = values
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
                set_clause = low.split(" set ", 1)[1].split(" where ", 1)[0]
                parts: list[str] = []
                buf, depth = "", 0
                for char in set_clause:
                    if char == "(":
                        depth += 1
                    elif char == ")":
                        depth -= 1
                    if char == "," and depth == 0:
                        parts.append(buf)
                        buf = ""
                    else:
                        buf += char
                parts.append(buf)
                columns = [part.strip().split(" =", 1)[0] for part in parts]
                for column, value in zip(columns, params[: len(params) - 1], strict=False):
                    if value is not None:
                        row[column] = value
                self.rowcount = 1
        elif low.startswith("update users set"):
            username, normalized, uid = tuple(params or ())
            row = self.users.get(str(uid))
            if row is None:
                self.rowcount = 0
            else:
                row["username"] = username
                row["username_normalized"] = normalized
                self.rowcount = 1
        elif low.startswith("update agents_user"):
            values = tuple(params or ())
            uid = str(values[-1])
            row = self.agents.get(uid)
            if row is None:
                self.rowcount = 0
            elif len(values) >= 11:
                # Full profile update (#564): 10 columns + user_id.
                (
                    email, avatar, model, specialization, temperature,
                    system_prompt, tools, write_access, limits, enabled,
                ) = values[:10]
                row.update(
                    {
                        "email": email,
                        "avatar": avatar,
                        "model": model,
                        "specialization": specialization,
                        "temperature": temperature,
                        "system_prompt": system_prompt,
                        "tools": tools,
                        "write_access": write_access,
                        "limits": limits,
                        "enabled": enabled,
                    }
                )
                self.rowcount = 1
            else:
                for key, value in zip(("avatar", "model", "specialization"), values[:3], strict=False):
                    if value is not None:
                        row[key] = value
                self.rowcount = 1
        elif low.startswith("delete from user_skills"):
            uid = str(params[0])
            existed = bool(self.user_skills.get(uid))
            self.user_skills.pop(uid, None)
            self.rowcount = 1 if existed else 0
        elif low.startswith("delete from users"):
            values = tuple(params or ())
            uid = str(values[0])
            row = self.users.get(uid)
            # #564 guards agent deletes with user_type='agent' (literal or param, never touches humans).
            wants_agent = (len(values) > 1 and str(values[1]) == "agent") or "'agent'" in low
            # #564 guards agent deletes with user_type='agent' (never touches humans).
            existed = row is not None and (not wants_agent or row.get("user_type") == "agent")
            if existed:
                self.users.pop(uid, None)
                self.human.pop(uid, None)
                self.agents.pop(uid, None)
                self.user_skills.pop(uid, None)
            self.rowcount = 1 if existed else 0
        elif low.startswith("select count(*) from users where user_type"):
            # Last-user guard counts humans in the PG root (#562).
            kind = str(params[0]) if params else "human"
            self._next = (sum(1 for row in self.users.values() if row["user_type"] == kind),)
        elif "count(*)" in low and "not exists" in low:
            kind = "identity" if "select 1 from users u" in low else "profile"
            self._next = (self._verify_count(kind),)
        elif "from users_legacy" in low:
            self._rows = list(self.legacy_rows)
        elif low.startswith("select user_type from users"):
            uid = str(params[0])
            row = self.users.get(uid)
            self._next = (row["user_type"],) if row else None
        elif low.startswith("select 1 from users where username_normalized"):
            # Update flows append `AND id <> %s` so a user keeps its own name (#560).
            if len(tuple(params or ())) > 1:
                normalized, uid = str(params[0]), str(params[1])
                self._next = (
                    (1,)
                    if any(
                        row["username_normalized"] == normalized and row["id"] != uid
                        for row in self.users.values()
                    )
                    else None
                )
            else:
                self._next = (1,) if self._normalized_username(str(params[0])) else None
        elif low.startswith("select 1 from human_user where user_id"):
            # has_password(): role-change revocation only for credentialed rows (#561).
            row = self.human.get(str(params[0]))
            self._next = (1,) if row and row.get("password_hash") else None
        elif low.startswith("select 1 from human_user where email"):
            # Update flows append `AND user_id <> %s` so a user keeps its email (#560).
            if len(tuple(params or ())) > 1:
                email, uid = str(params[0]), str(params[1])
                self._next = (
                    (1,)
                    if any(
                        row.get("email") == email and row.get("user_id") != uid
                        for row in self.human.values()
                    )
                    else None
                )
            else:
                email = str(params[0])
                self._next = (1,) if any(row.get("email") == email for row in self.human.values()) else None
        elif low.startswith("select id from roles"):
            self._rows = [(role_id,) for role_id, _ in sorted(self.roles.items(), key=lambda kv: -kv[1])]
        elif low.startswith("select username_normalized from users"):
            self._rows = [(row["username_normalized"],) for row in self.users.values()]
        elif low.startswith("select username, id from users"):
            self._rows = [
                (row["username"], row["id"]) for row in sorted(self.users.values(), key=lambda r: r["username"])
            ]
        elif low.startswith("select 1 from users where id"):
            row = self.users.get(str(params[0]))
            ok = row is not None and (len(tuple(params or ())) < 2 or row["user_type"] == str(params[1]))
            self._next = (1,) if ok else None
        elif low.startswith("select 1 from tools where id"):
            # Tool catalog validation for agent profiles (#564).
            self._next = (1,) if str(params[0]) in self.tools else None
        elif low.startswith("select email, avatar, model, specialization"):
            # update_profile keeps JSONB values it must not overwrite (#564).
            row = self.agents.get(str(params[0]))
            if row is None:
                self._next = None
            else:
                self._next = (
                    row.get("email"),
                    row.get("avatar"),
                    row.get("model"),
                    row.get("specialization"),
                    row.get("temperature"),
                    row.get("system_prompt"),
                    row.get("tools"),
                    row.get("write_access"),
                    row.get("limits"),
                    row.get("enabled", True),
                )
        elif low.startswith("select u.id, u.username, u.created_at, a."):
            # Agent profile read over users ⨝ agents_user (#564).
            if "where u.id" in low:
                uid = str(params[0])
                self._next = self._agent_profile_row(uid) if uid in self.agents else None
            else:
                ordered = sorted(
                    self.agents,
                    key=lambda key: str(self.users.get(key, {}).get("username", "")),
                )
                self._rows = [self._agent_profile_row(uid) for uid in ordered]
        elif low.startswith("select us.user_id, s.name"):
            self._rows = [
                (uid, self.skills.get(slug, slug))
                for uid, slugs in sorted(self.user_skills.items())
                for slug in sorted(slugs)
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
        if "insert into roles" in norm.lower():
            for values in params_list:
                if values:
                    self.roles[str(values[0])] = int(values[2]) if len(values) > 2 else 0
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
