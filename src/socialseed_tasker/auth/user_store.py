"""Username normalization and PostgreSQL credential store for auth seeding (issue #526)."""

from __future__ import annotations

import json
import os
import re
from contextlib import closing
from pathlib import Path
from typing import Any, Protocol

import bcrypt
import psycopg

from socialseed_tasker.config.storage import get_database_url

_INVALID_USERNAME_CHARS = re.compile(r"[^a-z0-9.]")

DEFAULT_SEED_PATH = "frontend/dataset-de-pruebas/users.json"


def normalize_username(username: str) -> str:
    """Lowercase, trim and restrict a username to ``a-z``, ``0-9`` and ``.``."""
    return _INVALID_USERNAME_CHARS.sub("", username.strip().lower())


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the given (normalized) password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Check a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def authenticate_user(database_url: str, username: str, password: str) -> dict[str, Any] | None:
    """Return the user record when the normalized username exists and the bcrypt password matches.

    Returns ``None`` for unknown users or wrong passwords. Connection and SQL
    errors propagate so callers can tell an outage from a bad credential.
    """
    normalized = normalize_username(username)
    if not normalized or not password:
        return None
    with closing(psycopg.connect(database_url, autocommit=True)) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, username, email, password_hash, role, "type"
            FROM users
            WHERE username_normalized = %s
            """,
            (normalized,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    password_hash = row[3] or ""
    if not password_hash or not verify_password(password, password_hash):
        return None
    return {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "role": row[4],
        "type": row[5],
    }


class UserSeedStore(Protocol):
    """Credential store port implemented by PostgreSQL and by test fakes."""

    def existing_usernames(self) -> set[str]:
        ...

    def upsert_user(
        self,
        *,
        user_id: str,
        username: str,
        username_normalized: str,
        email: str | None,
        password_hash: str,
        role: str | None,
        user_type: str | None,
        created_at: str | None,
    ) -> str:
        ...


class PostgresUserStore:
    """Credential store backed by PostgreSQL (``users`` table, bcrypt hashes)."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def create_schema(self) -> None:
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    username_normalized TEXT NOT NULL UNIQUE,
                    email TEXT,
                    password_hash TEXT NOT NULL,
                    role TEXT,
                    "type" TEXT,
                    created_at TIMESTAMPTZ
                )
                """
            )

    def existing_usernames(self) -> set[str]:
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute("SELECT username_normalized FROM users")
            rows = cur.fetchall()
        return {row[0] for row in rows}

    def upsert_user(
        self,
        *,
        user_id: str,
        username: str,
        username_normalized: str,
        email: str | None,
        password_hash: str,
        role: str | None,
        user_type: str | None,
        created_at: str | None,
    ) -> str:
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, username, username_normalized, email,
                                   password_hash, role, "type", created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (
                    user_id,
                    username,
                    username_normalized,
                    email,
                    password_hash,
                    role,
                    user_type,
                    created_at,
                ),
            )
            return "created" if cur.rowcount else "existing"


def seed_users(store: UserSeedStore, json_path: str | Path) -> dict[str, int]:
    """Idempotently register dataset users with ``password_hash = bcrypt(normalize(username))``."""
    with Path(json_path).open(encoding="utf-8") as fh:
        payload: dict[str, Any] = json.load(fh)
    users: list[dict[str, Any]] = payload.get("users") or []
    existing = store.existing_usernames()
    stats = {"total": len(users), "created": 0, "existing": 0}
    for user in users:
        username = str(user.get("username") or "")
        normalized = normalize_username(username)
        if normalized in existing:
            stats["existing"] += 1
            continue
        status = store.upsert_user(
            user_id=str(user.get("id") or normalized),
            username=username,
            username_normalized=normalized,
            email=user.get("email"),
            password_hash=hash_password(normalized),
            role=user.get("role"),
            user_type=user.get("type"),
            created_at=user.get("created_at"),
        )
        stats["created" if status == "created" else "existing"] += 1
    return stats


def seed_auth_users() -> dict[str, int] | None:
    """Env-driven seeding entry point; None when TASKER_DATABASE_URL is not configured."""
    database_url = get_database_url()
    if not database_url:
        return None
    json_path = os.getenv("TASKER_AUTH_SEED_PATH") or DEFAULT_SEED_PATH
    store = PostgresUserStore(database_url)
    store.create_schema()
    return seed_users(store, json_path)


if __name__ == "__main__":
    result = seed_auth_users()
    print(json.dumps(result, indent=2) if result is not None else "TASKER_DATABASE_URL not configured")
