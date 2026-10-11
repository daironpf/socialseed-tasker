"""Username normalization and PostgreSQL credential store for auth seeding (issue #526).

Issue #558 replaced the single flat ``users`` table with the normalized model:
catalogs ``roles``/``skills``/``tools``, minimal identity in ``users`` (uid is the
canonical key), profiles in ``human_user``/``agents_user``, N:M ``user_skills``
and audit ``session_logs``. ``create_schema()`` migrates legacy flat tables
idempotently and keeps a ``users_legacy`` backup.
"""

from __future__ import annotations

import json
import os
import re
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, cast

import bcrypt
import psycopg

from socialseed_tasker.config.storage import get_database_url

_INVALID_USERNAME_CHARS = re.compile(r"[^a-z0-9.]")
_SKILL_SLUG_CHARS = re.compile(r"[^a-z0-9]+")

DEFAULT_SEED_PATH = "frontend/dataset-de-pruebas/users.json"

AGENT_USER_TYPE = "agent"
HUMAN_USER_TYPE = "human"
CANONICAL_ROLES = ("ADMIN", "DEVELOPER", "VIEWER")

ROLES_SEED: tuple[tuple[str, str, int], ...] = (
    ("ADMIN", "Administrator", 3),
    ("DEVELOPER", "Developer", 2),
    ("VIEWER", "Viewer", 1),
)

# Union of both divergent frontend tool lists: AGENT_TOOLS (types/agentStudio.ts) and
# EditAgentModal.availableTools, normalized to snake_case slugs (issues #558/#572).
TOOLS_SEED: tuple[tuple[str, str, str], ...] = (
    ("code_search", "Code search", "Search the codebase"),
    ("fs_read", "Filesystem read", "Read files from the workspace"),
    ("fs_write", "Filesystem write", "Write files in the workspace"),
    ("neo4j_query", "Neo4j query", "Run Cypher queries against the graph"),
    ("web_search", "Web search", "Search the web"),
    ("github_pr", "GitHub PR", "Work with GitHub pull requests"),
    ("test_runner", "Test runner", "Run the test suite"),
    ("docs_writer", "Docs writer", "Write and update documentation"),
    ("shell", "Shell", "Run shell commands"),
    ("git_tools", "Git tools", "Git stage/commit helpers"),
    ("file_manager", "File manager", "Manage project files"),
    ("api_caller", "API caller", "Call HTTP endpoints"),
    ("code_analyzer", "Code analyzer", "Analyze code structure"),
    ("doc_writer", "Document writer", "Author documents"),
)

ROLES_DDL = """
CREATE TABLE IF NOT EXISTS roles (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    rank        INT NOT NULL,
    permissions JSONB NOT NULL DEFAULT '[]'
)
"""

SKILLS_DDL = """
CREATE TABLE IF NOT EXISTS skills (
    id   TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
)
"""

TOOLS_DDL = """
CREATE TABLE IF NOT EXISTS tools (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT
)
"""

USERS_DDL = """
CREATE TABLE IF NOT EXISTS users (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    username            TEXT NOT NULL UNIQUE,
    username_normalized TEXT NOT NULL UNIQUE,
    user_type           TEXT NOT NULL CHECK (user_type IN ('human', 'agent')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""

HUMAN_USER_DDL = """
CREATE TABLE IF NOT EXISTS human_user (
    user_id       TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    email         TEXT UNIQUE,
    password_hash TEXT NOT NULL DEFAULT '',
    role_id       TEXT NOT NULL REFERENCES roles(id),
    avatar        TEXT,
    github_handle TEXT,
    preferences   TEXT,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE
)
"""

AGENTS_USER_DDL = """
CREATE TABLE IF NOT EXISTS agents_user (
    user_id        TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    email          TEXT,
    avatar         TEXT,
    model          TEXT,
    specialization TEXT,
    temperature    DOUBLE PRECISION,
    system_prompt  TEXT,
    tools          JSONB NOT NULL DEFAULT '[]',
    write_access   JSONB NOT NULL DEFAULT '[]',
    limits         JSONB,
    enabled        BOOLEAN NOT NULL DEFAULT TRUE,
    last_used_at   TIMESTAMPTZ
)
"""

USER_SKILLS_DDL = """
CREATE TABLE IF NOT EXISTS user_skills (
    user_id  TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_id TEXT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, skill_id)
)
"""

SESSION_LOGS_DDL = """
CREATE TABLE IF NOT EXISTS session_logs (
    id         TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event      TEXT NOT NULL CHECK (event IN ('login', 'logout')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ip         TEXT,
    user_agent TEXT
)
"""

AGENT_RUNS_DDL = """
CREATE TABLE IF NOT EXISTS agent_runs (
    id               TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    agent_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    issue_id         TEXT,
    status           TEXT NOT NULL CHECK (status IN ('running','completed','failed','cancelled')),
    model            TEXT,
    started_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at      TIMESTAMPTZ,
    total_tokens     INT,
    total_tool_calls INT,
    duration_ms      INT,
    summary          TEXT
)
"""

AGENT_RUN_LOGS_DDL = """
CREATE TABLE IF NOT EXISTS agent_run_logs (
    run_id           TEXT NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    seq              INT NOT NULL,
    timestamp        TIMESTAMPTZ NOT NULL DEFAULT now(),
    type             TEXT NOT NULL CHECK (type IN (
        'reasoning','progress','files','debt','tool_call','error','violation'
    )),
    content_markdown TEXT,
    metadata         JSONB,
    PRIMARY KEY (run_id, seq)
)
"""

WORKFLOWS_DDL = """
CREATE TABLE IF NOT EXISTS workflows (
    id          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    slug        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    description TEXT,
    content_md  TEXT,
    steps       JSONB,
    source      TEXT NOT NULL DEFAULT 'custom' CHECK (source IN ('builtin','custom')),
    created_by  TEXT REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ
)
"""

INDEX_DDL: tuple[str, ...] = (
    "CREATE INDEX IF NOT EXISTS ix_users_user_type ON users (user_type)",
    "CREATE INDEX IF NOT EXISTS ix_human_user_role ON human_user (role_id)",
    "CREATE INDEX IF NOT EXISTS ix_user_skills_skill ON user_skills (skill_id)",
    "CREATE INDEX IF NOT EXISTS ix_session_logs_user_created ON session_logs (user_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_agent_runs_agent_started ON agent_runs (agent_id, started_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_workflows_source ON workflows (source)",
)


def normalize_username(username: str) -> str:
    """Lowercase, trim and restrict a username to ``a-z``, ``0-9`` and ``.``."""
    return _INVALID_USERNAME_CHARS.sub("", username.strip().lower())


def normalize_user_type(user_type: str | None) -> str:
    """Map legacy ``"type"`` values (``agent``/``human``/``admin``/None) onto ``user_type``."""
    return AGENT_USER_TYPE if str(user_type or "").strip().lower() == AGENT_USER_TYPE else HUMAN_USER_TYPE


def map_role(role: str | None) -> str:
    """Canonical RBAC role (case-insensitive) with ``DEVELOPER`` fallback."""
    value = str(role or "").strip().upper()
    return value if value in CANONICAL_ROLES else "DEVELOPER"


def skill_slug(name: str) -> str:
    """Slugify a skill name for the ``skills`` catalog (``'CI/CD' -> 'ci-cd'``)."""
    slug = _SKILL_SLUG_CHARS.sub("-", str(name).strip().lower()).strip("-")
    return slug or "skill"


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the given (normalized) password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Check a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def authenticate_user(database_url: str, username: str, password: str) -> dict[str, Any] | None:
    """Return the user record when the normalized username exists and the bcrypt password matches.

    Joins ``human_user`` for the credential (issue #558): agents have no password
    row, so they can never authenticate. Returns ``None`` for unknown users or
    wrong passwords. Connection and SQL errors propagate so callers can tell an
    outage from a bad credential.
    """
    normalized = normalize_username(username)
    if not normalized or not password:
        return None
    with closing(psycopg.connect(database_url, autocommit=True)) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.id, u.username, u.user_type, h.email, h.password_hash, h.role_id
            FROM users u
            LEFT JOIN human_user h ON h.user_id = u.id
            WHERE u.username_normalized = %s
            """,
            (normalized,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    password_hash = row[4] or ""
    if not password_hash or not verify_password(password, password_hash):
        return None
    return {
        "id": row[0],
        "username": row[1],
        "email": row[3],
        "role": row[5],
        "type": row[2],
    }


def record_session_event(
    database_url: str,
    user_id: str,
    event: str,
    *,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Insert an audit row into ``session_logs`` (issue #571).

    ``event`` is ``'login'`` (credential login, issue #571) or ``'logout'``
    (session revocation, issue #561/#571). Callers treat this as best-effort:
    the credential (or an already successful role change) is the source of
    truth, so a failure here is only logged and never breaks the flow.
    """
    with closing(psycopg.connect(database_url, autocommit=True)) as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO session_logs (user_id, event, ip, user_agent) VALUES (%s, %s, %s, %s)",
            (user_id, event, ip, user_agent),
        )


class UserSeedStore(Protocol):
    """Credential store port implemented by PostgreSQL and by test fakes."""

    def existing_usernames(self) -> set[str]:
        ...

    def upsert_user(
        self,
        *,
        user_id: str | None,
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
    """Credential store backed by PostgreSQL (normalized schema, issue #558)."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def create_schema(self) -> None:
        """Create the normalized schema, seed catalogs and migrate legacy flat tables.

        Every step is idempotent: repeated runs are safe and a second run over a
        migrated database leaves the data untouched (``ON CONFLICT DO NOTHING``).
        """
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute(ROLES_DDL)
            cur.execute(SKILLS_DDL)
            cur.execute(TOOLS_DDL)
            cur.executemany(
                "INSERT INTO roles (id, name, rank) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING",
                ROLES_SEED,
            )
            cur.executemany(
                "INSERT INTO tools (id, name, description) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING",
                TOOLS_SEED,
            )
            legacy_backup = self._prepare_users_table(cur)
            for ddl in (
                HUMAN_USER_DDL,
                AGENTS_USER_DDL,
                USER_SKILLS_DDL,
                SESSION_LOGS_DDL,
                AGENT_RUNS_DDL,
                AGENT_RUN_LOGS_DDL,
                WORKFLOWS_DDL,
            ):
                cur.execute(ddl)
            for ddl in INDEX_DDL:
                cur.execute(ddl)
            if legacy_backup:
                self._migrate_legacy_users(cur, legacy_backup)

    @staticmethod
    def _table_exists(cur: Any, table: str) -> bool:
        cur.execute("SELECT to_regclass('public.' || %s)", (table,))
        row = cur.fetchone()
        return bool(row and row[0])

    @staticmethod
    def _column_exists(cur: Any, table: str, column: str) -> bool:
        cur.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = %s AND column_name = %s",
            (table, column),
        )
        return cur.fetchone() is not None

    @staticmethod
    def _fetch_count(cur: Any) -> int:
        row = cur.fetchone()
        return int(row[0]) if row else 0

    def _prepare_users_table(self, cur: Any) -> str | None:
        """Ensure the new-shape ``users`` table; return the legacy backup name when one exists."""
        legacy_backup: str | None = None
        if self._table_exists(cur, "users") and not self._column_exists(cur, "users", "user_type"):
            legacy_backup = "users_legacy"
            suffix = 1
            while self._table_exists(cur, legacy_backup):
                suffix += 1
                legacy_backup = f"users_legacy_{suffix}"
            cur.execute(f'ALTER TABLE users RENAME TO "{legacy_backup}"')
        cur.execute(USERS_DDL)
        if legacy_backup is None and self._table_exists(cur, "users_legacy"):
            legacy_backup = "users_legacy"
        return legacy_backup

    def _migrate_legacy_users(self, cur: Any, backup_table: str) -> None:
        """Copy identity and profiles from a legacy flat table; raises when rows are missing.

        Existing user ids are preserved verbatim (JWT ``sub`` and notifications
        already reference them); the legacy table is kept as ``users_legacy``.
        """
        has_last_login = self._column_exists(cur, backup_table, "last_login")
        columns = 'id, username, username_normalized, email, password_hash, role, "type", created_at'
        if has_last_login:
            columns += ", last_login"
        cur.execute(f"SELECT {columns} FROM {backup_table}")
        for row in cur.fetchall():
            values = tuple(row)
            uid, username, normalized, email, password_hash, role, legacy_type, created_at = values[:8]
            last_login = values[8] if has_last_login else None
            user_type = normalize_user_type(legacy_type)
            cur.execute(
                """
                INSERT INTO users (id, username, username_normalized, user_type, created_at)
                VALUES (%s, %s, %s, %s, COALESCE(%s, now()))
                ON CONFLICT DO NOTHING
                """,
                (uid, username, normalized, user_type, created_at),
            )
            if user_type == AGENT_USER_TYPE:
                cur.execute(
                    "INSERT INTO agents_user (user_id, email) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (uid, email),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO human_user (user_id, email, password_hash, role_id, is_active)
                    VALUES (%s, %s, %s, %s, TRUE)
                    ON CONFLICT DO NOTHING
                    """,
                    (uid, email, password_hash or "", map_role(role)),
                )
            if last_login:
                cur.execute(
                    """
                    INSERT INTO session_logs (user_id, event, created_at)
                    SELECT %s, 'login', %s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM session_logs
                        WHERE user_id = %s AND event = 'login' AND created_at = %s
                    )
                    """,
                    (uid, last_login, uid, last_login),
                )
        self._verify_migration(cur, backup_table)

    def _verify_migration(self, cur: Any, backup_table: str) -> None:
        cur.execute(
            f"SELECT count(*) FROM {backup_table} b "
            "WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = b.id)"
        )
        missing_identity = self._fetch_count(cur)
        cur.execute(
            f"""
            SELECT count(*) FROM {backup_table} b
            WHERE NOT EXISTS (
                SELECT 1 FROM human_user h WHERE h.user_id = b.id
                UNION ALL
                SELECT 1 FROM agents_user a WHERE a.user_id = b.id
            )
            """
        )
        missing_profile = self._fetch_count(cur)
        if missing_identity or missing_profile:
            raise RuntimeError(
                f"legacy users migration incomplete: {missing_identity} identity row(s), "
                f"{missing_profile} profile row(s) missing"
            )

    def existing_usernames(self) -> set[str]:
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute("SELECT username_normalized FROM users")
            rows = cur.fetchall()
        return {row[0] for row in rows}

    def list_role_ids(self) -> list[str]:
        """Seeded RBAC role ids ordered by rank (issue #559)."""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute("SELECT id FROM roles ORDER BY rank DESC")
            rows = cur.fetchall()
        return [str(row[0]) for row in rows]

    def list_skills(self) -> list[dict[str, Any]]:
        """Full skills catalog ordered by name (issue #572).

        The catalog holds the #558 seed plus every skill upserted by the
        user/agent forms (#559/#560/#566), so the frontend pickers always
        offer a single source of truth while keeping free values.
        """
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute("SELECT id, name FROM skills ORDER BY name")
            rows = cur.fetchall()
        return [{"id": str(row[0]), "name": row[1]} for row in rows]

    def list_tools(self) -> list[dict[str, Any]]:
        """Full tools catalog ordered by name (issue #572).

        Canonical snake_case slugs seeded by #558 (union of the two
        divergent frontend lists); ``/agents/profiles`` validates against
        this same catalog with 422 (#564).
        """
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute("SELECT id, name, description FROM tools ORDER BY name")
            rows = cur.fetchall()
        return [{"id": str(row[0]), "name": row[1], "description": row[2]} for row in rows]

    def has_password(self, user_id: str) -> bool:
        """True when the human row carries a bcrypt credential (issue #561).

        Users created through ``POST /users`` have an empty ``password_hash``
        until #563, so they have no password sessions to revoke on a role
        change; only credential-bearing accounts trigger session revocation.
        """
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM human_user WHERE user_id = %s AND password_hash <> ''",
                (user_id,),
            )
            return cur.fetchone() is not None

    def create_human_user(
        self,
        *,
        username: str,
        email: str | None,
        role_id: str,
        avatar: str | None = None,
        skills: list[str] | None = None,
        is_active: bool = True,
        github_handle: str | None = None,
        preferences: str | None = None,
        password_hash: str = "",
    ) -> str:
        """Insert ``users`` + ``human_user`` + ``skills``/``user_skills`` atomically.

        The uid is generated by PostgreSQL (``RETURNING id``). ``password_hash``
        is the bcrypt digest persisted in ``human_user`` (#563); the empty
        string means "no login possible". Returns the new uid. Raises
        ``ValueError("username"|"email")`` on uniqueness conflicts (mapped to
        409 by the router, issue #559).
        """
        normalized = normalize_username(username)
        with closing(psycopg.connect(self._database_url, autocommit=False)) as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM users WHERE username_normalized = %s", (normalized,))
                    if cur.fetchone():
                        raise ValueError("username")
                    if email:
                        cur.execute("SELECT 1 FROM human_user WHERE email = %s", (email,))
                        if cur.fetchone():
                            raise ValueError("email")
                    cur.execute(
                        """
                        INSERT INTO users (username, username_normalized, user_type, created_at)
                        VALUES (%s, %s, 'human', now())
                        RETURNING id
                        """,
                        (username, normalized),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise ValueError("username")
                    uid = str(row[0])
                    cur.execute(
                        """
                        INSERT INTO human_user (
                            user_id, email, password_hash, role_id,
                            avatar, github_handle, preferences, is_active
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            uid,
                            email,
                            password_hash or "",
                            role_id,
                            avatar,
                            github_handle,
                            preferences,
                            is_active,
                        ),
                    )
                    for name in skills or []:
                        slug = skill_slug(name)
                        if not slug:
                            continue
                        cur.execute(
                            "INSERT INTO skills (id, name) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (slug, name),
                        )
                        cur.execute(
                            "INSERT INTO user_skills (user_id, skill_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (uid, slug),
                        )
                conn.commit()
            except psycopg.errors.UniqueViolation as exc:
                conn.rollback()
                constraint = getattr(getattr(exc, "diag", None), "constraint_name", None) or ""
                if "email" in constraint:
                    raise ValueError("email") from exc
                raise ValueError("username") from exc
            except Exception:
                conn.rollback()
                raise
        return uid

    def update_human_user(
        self,
        *,
        user_id: str,
        username: str | None = None,
        email: str | None = None,
        role_id: str | None = None,
        avatar: str | None = None,
        skills: list[str] | None = None,
        github_handle: str | None = None,
        preferences: str | None = None,
        is_active: bool | None = None,
    ) -> bool:
        """Update ``users`` + ``human_user`` + ``user_skills`` atomically (#560).

        ``None`` keeps the stored value; ``skills`` (when not ``None``) fully
        replaces the skill links. The row is never deleted nor re-inserted, so
        ``password_hash`` survives. Returns ``False`` when the identity row does
        not exist (router maps it to 404) and raises ``ValueError("username"|
        "email")`` on uniqueness conflicts against *other* users (409).
        """
        normalized = normalize_username(username) if username else None
        with closing(psycopg.connect(self._database_url, autocommit=False)) as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT user_type FROM users WHERE id = %s", (user_id,))
                    if cur.fetchone() is None:
                        conn.rollback()
                        return False
                    if username:
                        cur.execute(
                            "SELECT 1 FROM users WHERE username_normalized = %s AND id <> %s",
                            (normalized, user_id),
                        )
                        if cur.fetchone():
                            raise ValueError("username")
                    if email:
                        cur.execute(
                            "SELECT 1 FROM human_user WHERE email = %s AND user_id <> %s",
                            (email, user_id),
                        )
                        if cur.fetchone():
                            raise ValueError("email")
                    if username:
                        cur.execute(
                            "UPDATE users SET username = %s, username_normalized = %s WHERE id = %s",
                            (username, normalized, user_id),
                        )
                    assignments = [
                        (column, value)
                        for column, value in (
                            ("email", email),
                            ("role_id", role_id),
                            ("avatar", avatar),
                            ("github_handle", github_handle),
                            ("preferences", preferences),
                            ("is_active", is_active),
                        )
                        if value is not None
                    ]
                    if assignments:
                        columns = ", ".join(f"{column} = %s" for column, _ in assignments)
                        values = tuple(value for _, value in assignments) + (user_id,)
                        cur.execute(f"UPDATE human_user SET {columns} WHERE user_id = %s", values)
                    if skills is not None:
                        cur.execute("DELETE FROM user_skills WHERE user_id = %s", (user_id,))
                        for name in skills:
                            slug = skill_slug(name)
                            if not slug:
                                continue
                            cur.execute(
                                "INSERT INTO skills (id, name) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                                (slug, name),
                            )
                            cur.execute(
                                "INSERT INTO user_skills (user_id, skill_id) VALUES (%s, %s) "
                                "ON CONFLICT DO NOTHING",
                                (user_id, slug),
                            )
                conn.commit()
            except psycopg.errors.UniqueViolation as exc:
                conn.rollback()
                constraint = getattr(getattr(exc, "diag", None), "constraint_name", None) or ""
                if "email" in constraint:
                    raise ValueError("email") from exc
                raise ValueError("username") from exc
            except Exception:
                conn.rollback()
                raise
        return True

    def upsert_user(
        self,
        *,
        user_id: str | None,
        username: str,
        username_normalized: str,
        email: str | None,
        password_hash: str,
        role: str | None,
        user_type: str | None,
        created_at: str | None,
    ) -> str:
        """Insert the identity row plus its profile row (``human_user``/``agents_user``).

        When ``user_id`` is ``None`` the uid is generated by PostgreSQL
        (``gen_random_uuid()::text ... RETURNING id``, issue #558). Returns
        ``"created"`` or ``"existing"``.
        """
        kind = normalize_user_type(user_type)
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            if user_id:
                cur.execute(
                    """
                    INSERT INTO users (id, username, username_normalized, user_type, created_at)
                    VALUES (%s, %s, %s, %s, COALESCE(%s, now()))
                    ON CONFLICT DO NOTHING
                    """,
                    (user_id, username, username_normalized, kind, created_at),
                )
                inserted = bool(cur.rowcount)
                uid: str | None = user_id
            else:
                cur.execute(
                    """
                    INSERT INTO users (username, username_normalized, user_type, created_at)
                    VALUES (%s, %s, %s, COALESCE(%s, now()))
                    ON CONFLICT DO NOTHING
                    RETURNING id
                    """,
                    (username, username_normalized, kind, created_at),
                )
                row = cur.fetchone()
                inserted = row is not None
                uid = str(row[0]) if row else None
            if uid:
                if kind == AGENT_USER_TYPE:
                    cur.execute(
                        "INSERT INTO agents_user (user_id, email) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        (uid, email),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO human_user (user_id, email, password_hash, role_id)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (uid, email, password_hash, map_role(role)),
                    )
            return "created" if inserted else "existing"

    def upsert_profile(
        self,
        *,
        user_id: str,
        avatar: str | None = None,
        skills: list[str] | None = None,
        model: str | None = None,
        specialization: str | None = None,
        github_handle: str | None = None,
        preferences: str | None = None,
        is_active: bool | None = None,
    ) -> None:
        """Merge seedable profile fields (avatar/skills/model/...) into the profile row (#558)."""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute("SELECT user_type FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            if row is None:
                return
            if row[0] == AGENT_USER_TYPE:
                cur.execute(
                    """
                    UPDATE agents_user
                    SET avatar = COALESCE(%s, avatar),
                        model = COALESCE(%s, model),
                        specialization = COALESCE(%s, specialization)
                    WHERE user_id = %s
                    """,
                    (avatar, model, specialization, user_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE human_user
                    SET avatar = COALESCE(%s, avatar),
                        github_handle = COALESCE(%s, github_handle),
                        preferences = COALESCE(%s, preferences),
                        is_active = COALESCE(%s, is_active)
                    WHERE user_id = %s
                    """,
                    (avatar, github_handle, preferences, is_active, user_id),
                )
            for name in skills or []:
                slug = skill_slug(name)
                cur.execute(
                    "INSERT INTO skills (id, name) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (slug, name),
                )
                cur.execute(
                    "INSERT INTO user_skills (user_id, skill_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (user_id, slug),
                )


_AGENT_PROFILE_ROW_SQL = """
SELECT u.id, u.username, u.created_at,
       a.email, a.avatar, a.model, a.specialization, a.temperature,
       a.system_prompt, a.tools, a.write_access, a.limits, a.enabled, a.last_used_at
FROM users u JOIN agents_user a ON a.user_id = u.id
"""


def _as_json_list(value: Any) -> list[str]:
    """Normalize a JSONB column (parsed list or text) into a list of strings."""
    if value is None:
        return []
    if isinstance(value, str):
        value = json.loads(value)
    return [str(item) for item in value or []]


def _as_json_dict(value: Any) -> dict[str, Any] | None:
    """Normalize a JSONB column (parsed dict or text) into a dict."""
    if value is None:
        return None
    if isinstance(value, str):
        return cast("dict[str, Any]", json.loads(value))
    return dict(value)


class PostgresAgentProfileStore:
    """CRUD over ``users`` + ``agents_user`` + ``user_skills`` (issue #564).

    Agent identities live in the PG root with ``user_type='agent'``, a
    PostgreSQL-generated uid and no credential or RBAC role rows. ``tools``
    are validated against the ``tools`` catalog (#558/#572) and JSONB
    columns are passed as text with an explicit ``::jsonb`` cast.
    """

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def list_profiles(self) -> list[dict[str, Any]]:
        """All agent profiles ordered by username."""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute(f"{_AGENT_PROFILE_ROW_SQL} ORDER BY u.username")
            rows = cur.fetchall()
            skills = self._load_skills(cur)
        return [self._row_to_profile(row, skills) for row in rows]

    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        """Single agent profile composed from ``users`` + ``agents_user``."""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute(f"{_AGENT_PROFILE_ROW_SQL} WHERE u.id = %s AND u.user_type = 'agent'", (user_id,))
            row = cur.fetchone()
            if row is None:
                return None
            return self._row_to_profile(row, self._load_skills(cur))

    @staticmethod
    def _load_skills(cur: Any) -> dict[str, list[str]]:
        cur.execute("SELECT us.user_id, s.name FROM user_skills us JOIN skills s ON s.id = us.skill_id")
        linked: dict[str, list[str]] = {}
        for uid, name in cur.fetchall():
            linked.setdefault(str(uid), []).append(str(name))
        return linked

    @staticmethod
    def _row_to_profile(row: Any, skills: dict[str, list[str]]) -> dict[str, Any]:
        return {
            "id": str(row[0]),
            "username": row[1],
            "created_at": row[2],
            "email": row[3],
            "avatar": row[4],
            "model": row[5],
            "specialization": row[6],
            "temperature": row[7],
            "system_prompt": row[8],
            "tools": _as_json_list(row[9]),
            "write_access": _as_json_list(row[10]),
            "limits": _as_json_dict(row[11]),
            "enabled": bool(row[12]),
            "last_used_at": row[13],
            "skills": skills.get(str(row[0]), []),
        }

    @staticmethod
    def _validate_tools(cur: Any, tools: list[str] | None) -> list[str]:
        """Raise ``ValueError('tool:<slug>')`` for slugs missing from the catalog."""
        validated: list[str] = []
        for tool in tools or []:
            cur.execute("SELECT 1 FROM tools WHERE id = %s", (tool,))
            if cur.fetchone() is None:
                raise ValueError(f"tool:{tool}")
            validated.append(tool)
        return validated

    @staticmethod
    def _write_skills(cur: Any, user_id: str, skills: list[str]) -> None:
        for name in skills:
            slug = skill_slug(name)
            if not slug:
                continue
            cur.execute(
                "INSERT INTO skills (id, name) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (slug, name),
            )
            cur.execute(
                "INSERT INTO user_skills (user_id, skill_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (user_id, slug),
            )

    def create_profile(
        self,
        *,
        username: str,
        email: str | None = None,
        avatar: str | None = None,
        model: str | None = None,
        specialization: str | None = None,
        temperature: float | None = None,
        system_prompt: str | None = None,
        tools: list[str] | None = None,
        write_access: list[str] | None = None,
        limits: dict[str, Any] | None = None,
        skills: list[str] | None = None,
        enabled: bool = True,
    ) -> str:
        """Insert ``users`` + ``agents_user`` + ``user_skills`` atomically.

        The uid is generated by PostgreSQL (``RETURNING id``); agents carry no
        credential and no role. Raises ``ValueError('tool:<slug>')`` when a
        tool is not in the catalog and ``ValueError('username')`` on
        uniqueness conflicts (mapped to 409/422 by the router, issue #564).
        """
        normalized = normalize_username(username)
        with closing(psycopg.connect(self._database_url, autocommit=False)) as conn:
            try:
                with conn.cursor() as cur:
                    validated_tools = self._validate_tools(cur, tools)
                    cur.execute("SELECT 1 FROM users WHERE username_normalized = %s", (normalized,))
                    if cur.fetchone():
                        raise ValueError("username")
                    cur.execute(
                        """
                        INSERT INTO users (username, username_normalized, user_type, created_at)
                        VALUES (%s, %s, 'agent', now())
                        RETURNING id
                        """,
                        (username, normalized),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise ValueError("username")
                    uid = str(row[0])
                    cur.execute(
                        """
                        INSERT INTO agents_user (
                            user_id, email, avatar, model, specialization, temperature,
                            system_prompt, tools, write_access, limits, enabled
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s)
                        """,
                        (
                            uid,
                            email,
                            avatar,
                            model,
                            specialization,
                            temperature,
                            system_prompt,
                            json.dumps(validated_tools or []),
                            json.dumps(write_access or []),
                            json.dumps(limits) if limits is not None else None,
                            enabled,
                        ),
                    )
                    self._write_skills(cur, uid, skills or [])
                conn.commit()
            except psycopg.errors.UniqueViolation as exc:
                conn.rollback()
                raise ValueError("username") from exc
            except Exception:
                conn.rollback()
                raise
        return uid

    def update_profile(
        self,
        user_id: str,
        *,
        username: str | None = None,
        email: str | None = None,
        avatar: str | None = None,
        model: str | None = None,
        specialization: str | None = None,
        temperature: float | None = None,
        system_prompt: str | None = None,
        tools: list[str] | None = None,
        write_access: list[str] | None = None,
        limits: dict[str, Any] | None = None,
        skills: list[str] | None = None,
        enabled: bool | None = None,
        last_used_at: datetime | None = None,
    ) -> None:
        """Partial update: ``None`` keeps the stored value, provided lists replace.

        Raises ``LookupError`` when the agent row is missing (404),
        ``ValueError('tool:<slug>')`` for unknown tools and
        ``ValueError('username')`` on uniqueness conflicts (409).
        """
        normalized = normalize_username(username) if username is not None else None
        with closing(psycopg.connect(self._database_url, autocommit=False)) as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM users WHERE id = %s AND user_type = 'agent'", (user_id,))
                    if cur.fetchone() is None:
                        raise LookupError("agent profile not found")
                    if normalized is not None:
                        cur.execute(
                            "SELECT 1 FROM users WHERE username_normalized = %s AND id <> %s",
                            (normalized, user_id),
                        )
                        if cur.fetchone():
                            raise ValueError("username")
                    validated_tools = self._validate_tools(cur, tools)
                    cur.execute(
                        """
                        SELECT email, avatar, model, specialization, temperature,
                               system_prompt, tools, write_access, limits, enabled,
                               last_used_at
                        FROM agents_user WHERE user_id = %s
                        """,
                        (user_id,),
                    )
                    current = cur.fetchone()
                    if current is None:
                        raise LookupError("agent profile not found")
                    (
                        cur_email, cur_avatar, cur_model, cur_specialization,
                        cur_temperature, cur_prompt, cur_tools, cur_write,
                        cur_limits, cur_enabled, cur_last_used,
                    ) = current
                    next_tools = validated_tools if tools is not None else _as_json_list(cur_tools)
                    next_write = write_access if write_access is not None else _as_json_list(cur_write)
                    next_limits = limits if limits is not None else _as_json_dict(cur_limits)
                    cur.execute(
                        """
                        UPDATE agents_user SET
                            email = %s, avatar = %s, model = %s, specialization = %s,
                            temperature = %s, system_prompt = %s,
                            tools = %s::jsonb, write_access = %s::jsonb,
                            limits = %s::jsonb, enabled = %s, last_used_at = %s
                        WHERE user_id = %s
                        """,
                        (
                            email if email is not None else cur_email,
                            avatar if avatar is not None else cur_avatar,
                            model if model is not None else cur_model,
                            specialization if specialization is not None else cur_specialization,
                            temperature if temperature is not None else cur_temperature,
                            system_prompt if system_prompt is not None else cur_prompt,
                            json.dumps(next_tools),
                            json.dumps(next_write),
                            json.dumps(next_limits) if next_limits is not None else None,
                            enabled if enabled is not None else cur_enabled,
                            last_used_at if last_used_at is not None else cur_last_used,
                            user_id,
                        ),
                    )
                    if normalized is not None:
                        cur.execute(
                            "UPDATE users SET username = %s, username_normalized = %s WHERE id = %s",
                            (username, normalized, user_id),
                        )
                    if skills is not None:
                        cur.execute("DELETE FROM user_skills WHERE user_id = %s", (user_id,))
                        self._write_skills(cur, user_id, skills)
                conn.commit()
            except psycopg.errors.UniqueViolation as exc:
                conn.rollback()
                raise ValueError("username") from exc
            except Exception:
                conn.rollback()
                raise

    def delete_profile(self, user_id: str) -> bool:
        """Cascade-delete the agent identity row (``agents_user``/``user_skills``).

        The ``user_type = 'agent'`` guard never touches human rows; humans are
        deleted through ``DELETE /users/{id}`` (issue #562).
        """
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s AND user_type = 'agent'", (user_id,))
            return bool(cur.rowcount)

    # ------------------------------------------------------------------
    # Agent runs (issue #574): persistent history of agent executions.
    # ------------------------------------------------------------------

    _RUN_ROW_SQL = (
        "id, agent_id, issue_id, status, model, started_at, finished_at, "
        "total_tokens, total_tool_calls, duration_ms, summary"
    )

    @staticmethod
    def _run_row(row: Any) -> dict[str, Any]:
        return {
            "id": row[0],
            "agent_id": row[1],
            "issue_id": row[2],
            "status": row[3],
            "model": row[4],
            "started_at": row[5].isoformat() if row[5] is not None else None,
            "finished_at": row[6].isoformat() if row[6] is not None else None,
            "total_tokens": row[7],
            "total_tool_calls": row[8],
            "duration_ms": row[9],
            "summary": row[10],
        }

    def _agent_exists(self, cur: Any, agent_id: str, as_agent: bool = True) -> bool:
        cur.execute("SELECT 1 FROM users WHERE id = %s", (agent_id,))
        if cur.fetchone() is None:
            return False
        if not as_agent:
            return True
        cur.execute("SELECT 1 FROM users WHERE id = %s AND user_type = 'agent'", (agent_id,))
        return cur.fetchone() is not None

    def create_run(self, agent_id: str, *, issue_id: str | None = None, model: str | None = None) -> dict[str, Any]:
        """Create a ``running`` run for an agent; raises ``LookupError`` when the agent is missing."""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            if not self._agent_exists(cur, agent_id):
                raise LookupError(f"agent not found: {agent_id}")
            cur.execute(
                "INSERT INTO agent_runs (agent_id, issue_id, status, model) "
                f"VALUES (%s, %s, 'running', %s) RETURNING {self._RUN_ROW_SQL}",
                (agent_id, issue_id, model),
            )
            return self._run_row(cur.fetchone())

    def ensure_running_run(self, agent_id: str, *, issue_id: str | None = None, model: str | None = None) -> str | None:
        """Return the id of an open ``running`` run (creating one as needed).

        Best-effort companion of :meth:`create_run` used by the realtime log
        flush (issue #574): returns ``None`` instead of raising when the agent
        does not exist so non-persisted flows degrade silently.
        """
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            if not self._agent_exists(cur, agent_id):
                return None
            cur.execute(
                "SELECT id FROM agent_runs WHERE agent_id = %s AND status = 'running' "
                "ORDER BY started_at DESC LIMIT 1",
                (agent_id,),
            )
            row = cur.fetchone()
            if row is not None:
                return str(row[0])
            cur.execute(
                "INSERT INTO agent_runs (agent_id, issue_id, status, model) "
                "VALUES (%s, %s, 'running', %s) RETURNING id",
                (agent_id, issue_id, model),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("agent_runs INSERT RETURNING id produced no row")
            return str(row[0])

    def close_open_run(
        self,
        agent_id: str,
        *,
        issue_id: str | None = None,
        status: str = "completed",
        summary: str | None = None,
    ) -> bool:
        """Close the agent's open ``running`` run (optionally scoped to an issue)."""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            if issue_id is not None:
                cur.execute(
                    "UPDATE agent_runs SET status = %s, finished_at = now(), summary = COALESCE(%s, summary), "
                    "duration_ms = CAST(extract(epoch FROM (now() - started_at)) * 1000 AS INT) "
                    "WHERE agent_id = %s AND status = 'running' AND issue_id = %s",
                    (status, summary, agent_id, issue_id),
                )
            else:
                cur.execute(
                    "UPDATE agent_runs SET status = %s, finished_at = now(), summary = COALESCE(%s, summary), "
                    "duration_ms = CAST(extract(epoch FROM (now() - started_at)) * 1000 AS INT) "
                    "WHERE agent_id = %s AND status = 'running'",
                    (status, summary, agent_id),
                )
            return bool(cur.rowcount)

    def append_run_log(
        self,
        run_id: str,
        *,
        type: str,
        content_markdown: str | None = None,
        metadata: Any = None,
    ) -> dict[str, Any]:
        """Append a log entry to a run; raises ``LookupError`` when the run is missing."""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute("SELECT 1 FROM agent_runs WHERE id = %s", (run_id,))
            if cur.fetchone() is None:
                raise LookupError(f"run not found: {run_id}")
            cur.execute("SELECT COALESCE(MAX(seq), 0) + 1 FROM agent_run_logs WHERE run_id = %s", (run_id,))
            seq_row = cur.fetchone()
            seq = int(seq_row[0]) if seq_row else 1
            metadata_text = json.dumps(metadata) if metadata is not None else None
            cur.execute(
                "INSERT INTO agent_run_logs (run_id, seq, type, content_markdown, metadata) "
                "VALUES (%s, %s, %s, %s, %s::jsonb) RETURNING timestamp",
                (run_id, seq, type, content_markdown, metadata_text),
            )
            row = cur.fetchone()
            timestamp = row[0] if row else None
            return {
                "run_id": run_id,
                "seq": seq,
                "timestamp": timestamp.isoformat() if timestamp is not None else None,
                "type": type,
                "content_markdown": content_markdown,
                "metadata": metadata,
            }

    def update_run(self, run_id: str, **fields: Any) -> dict[str, Any]:
        """Partially update a run; raises ``LookupError`` when the run is missing."""
        allowed = {"status", "finished_at", "total_tokens", "total_tool_calls", "duration_ms", "summary", "model"}
        assignments = {key: value for key, value in fields.items() if key in allowed and value is not None}
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute("SELECT 1 FROM agent_runs WHERE id = %s", (run_id,))
            if cur.fetchone() is None:
                raise LookupError(f"run not found: {run_id}")
            if assignments:
                set_clause = ", ".join(f"{key} = %s" for key in assignments)
                cur.execute(f"UPDATE agent_runs SET {set_clause} WHERE id = %s", (*assignments.values(), run_id))
            cur.execute(
                f"SELECT {self._RUN_ROW_SQL} FROM agent_runs WHERE id = %s",
                (run_id,),
            )
            return self._run_row(cur.fetchone())

    def list_runs(self, agent_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
        """List an agent's runs, newest first; raises ``LookupError`` when the agent is missing."""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            if not self._agent_exists(cur, agent_id):
                raise LookupError(f"agent not found: {agent_id}")
            cur.execute(
                f"SELECT {self._RUN_ROW_SQL} FROM agent_runs WHERE agent_id = %s ORDER BY started_at DESC LIMIT %s",
                (agent_id, limit),
            )
            return [self._run_row(row) for row in cur.fetchall()]

    def list_run_logs(self, run_id: str) -> list[dict[str, Any]]:
        """List a run's log entries ordered by ``seq``; raises ``LookupError`` when the run is missing."""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute("SELECT 1 FROM agent_runs WHERE id = %s", (run_id,))
            if cur.fetchone() is None:
                raise LookupError(f"run not found: {run_id}")
            cur.execute(
                "SELECT run_id, seq, timestamp, type, content_markdown, metadata FROM agent_run_logs "
                "WHERE run_id = %s ORDER BY seq",
                (run_id,),
            )
            return [
                {
                    "run_id": row[0],
                    "seq": row[1],
                    "timestamp": row[2].isoformat() if row[2] is not None else None,
                    "type": row[3],
                    "content_markdown": row[4],
                    "metadata": row[5],
                }
                for row in cur.fetchall()
            ]

    def delete_run(self, run_id: str) -> bool:
        """Delete a run (logs cascade); returns whether the run existed."""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM agent_runs WHERE id = %s", (run_id,))
            return bool(cur.rowcount)


class PostgresWorkflowStore:
    """CRUD over the ``workflows`` library (issue #575).

    ``builtin`` rows are imported from the packaged ``.md`` definitions and are
    read-only for the API; ``custom`` rows belong to the creating user
    (``created_by`` PG uid, ``ON DELETE SET NULL`` keeps the workflow when the
    user is removed).
    """

    _ROW_SQL = "slug, name, description, source, created_by, created_at, updated_at"
    _FULL_ROW_SQL = _ROW_SQL + ", content_md, steps"

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    @staticmethod
    def _row(row: Any, full: bool = False) -> dict[str, Any]:
        base = {
            "slug": row[0],
            "name": row[1],
            "description": row[2],
            "source": row[3],
            "created_by": row[4],
            "created_at": row[5].isoformat() if row[5] is not None else None,
            "updated_at": row[6].isoformat() if row[6] is not None else None,
        }
        if full:
            base["content_md"] = row[7]
            base["steps"] = row[8]
        return base

    def list_workflows(self, source: str | None = None) -> list[dict[str, Any]]:
        """All workflows (slug, name, description, source, created_at) ordered by slug."""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            if source:
                cur.execute(
                    f"SELECT {self._ROW_SQL} FROM workflows WHERE source = %s ORDER BY slug",
                    (source,),
                )
            else:
                cur.execute(f"SELECT {self._ROW_SQL} FROM workflows ORDER BY slug")
            return [self._row(row) for row in cur.fetchall()]

    def get_workflow(self, slug: str) -> dict[str, Any] | None:
        """Full definition (content_md + steps) of one workflow."""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute(f"SELECT {self._FULL_ROW_SQL} FROM workflows WHERE slug = %s", (slug,))
            row = cur.fetchone()
            return self._row(row, full=True) if row else None

    def create_workflow(
        self,
        *,
        slug: str,
        name: str,
        description: str | None = None,
        content_md: str | None = None,
        steps: Any = None,
        source: str = "custom",
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """Insert a workflow; raises ``ValueError("slug")`` when the slug is taken."""
        steps_text = json.dumps(steps) if steps is not None else None
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO workflows (slug, name, description, content_md, steps, source, created_by) "
                "VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s) ON CONFLICT (slug) DO NOTHING",
                (slug, name, description, content_md, steps_text, source, created_by),
            )
            if not cur.rowcount:
                raise ValueError("slug")
            cur.execute(f"SELECT {self._FULL_ROW_SQL} FROM workflows WHERE slug = %s", (slug,))
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("workflow INSERT produced no row")
            return self._row(row, full=True)

    def update_workflow(
        self,
        slug: str,
        *,
        name: str | None = None,
        description: str | None = None,
        content_md: str | None = None,
        steps: Any = None,
    ) -> dict[str, Any]:
        """Partially update a custom workflow.

        Raises ``LookupError`` when missing and ``PermissionError`` for builtin
        rows (read-only, issue #575).
        """
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute("SELECT source FROM workflows WHERE slug = %s", (slug,))
            row = cur.fetchone()
            if row is None:
                raise LookupError(f"workflow not found: {slug}")
            if str(row[0]) == "builtin":
                raise PermissionError("builtin workflow")
            assignments: dict[str, Any] = {}
            if name is not None:
                assignments["name"] = name
            if description is not None:
                assignments["description"] = description
            if content_md is not None:
                assignments["content_md"] = content_md
            if steps is not None:
                assignments["steps"] = json.dumps(steps)
            if assignments:
                set_parts = [f"{key} = %s" for key in assignments]
                if "steps" in assignments:
                    set_parts = [part + "::jsonb" if part.startswith("steps") else part for part in set_parts]
                cur.execute(
                    f"UPDATE workflows SET {', '.join(set_parts)}, updated_at = now() WHERE slug = %s",
                    (*assignments.values(), slug),
                )
            cur.execute(f"SELECT {self._FULL_ROW_SQL} FROM workflows WHERE slug = %s", (slug,))
            updated = cur.fetchone()
            if updated is None:
                raise LookupError(f"workflow not found: {slug}")
            return self._row(updated, full=True)

    def delete_workflow(self, slug: str) -> bool:
        """Delete a custom workflow; builtin rows raise ``PermissionError``."""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute("SELECT source FROM workflows WHERE slug = %s", (slug,))
            row = cur.fetchone()
            if row is None:
                return False
            if str(row[0]) == "builtin":
                raise PermissionError("builtin workflow")
            cur.execute("DELETE FROM workflows WHERE slug = %s", (slug,))
            return bool(cur.rowcount)

    def seed_builtin(self, entries: list[dict[str, Any]]) -> int:
        """Insert builtin definitions with ``ON CONFLICT (slug) DO NOTHING``.

        Never overwrites an existing row (user edits of custom rows and prior
        imports survive). Returns the number of newly inserted rows.
        """
        inserted = 0
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            for entry in entries:
                cur.execute(
                    "INSERT INTO workflows (slug, name, description, content_md, source) "
                    "VALUES (%s, %s, %s, %s, 'builtin') ON CONFLICT (slug) DO NOTHING",
                    (entry["slug"], entry["name"], entry.get("description"), entry.get("content_md")),
                )
                inserted += cur.rowcount
        return inserted


def wipe_postgres_data() -> int:
    """Delete every row from every table in the public schema (fresh-install wipe).

    Used by ``POST /setup/initialize`` so a first run starts from a pristine
    database even when development/seed data is present. Returns the number of
    truncated tables, or ``0`` when TASKER_DATABASE_URL is not configured so
    the wizard keeps working without a PostgreSQL instance.
    """
    database_url = get_database_url()
    if not database_url:
        return 0
    with closing(psycopg.connect(database_url, autocommit=True)) as conn, conn.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        tables = [str(row[0]) for row in cur.fetchall()]
        if not tables:
            return 0
        quoted = ", ".join('"' + name.replace('"', '""') + '"' for name in tables)
        cur.execute(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE")
        return len(tables)


def create_user(
    *,
    username: str,
    password: str,
    role: str | None = None,
    email: str | None = None,
    user_type: str | None = None,
) -> str:
    """Idempotently create a credential user with a bcrypt password hash (issue #543).

    The username is normalized first; an already existing username keeps its
    stored password (``ON CONFLICT DO NOTHING``). Returns ``"created"`` or
    ``"existing"``, and ``"skipped"`` when TASKER_DATABASE_URL is not
    configured so first-run flows degrade without a PostgreSQL instance.
    """
    normalized = normalize_username(username)
    if not normalized:
        raise ValueError("username must contain at least one alphanumeric character")
    database_url = get_database_url()
    if not database_url:
        return "skipped"
    store = PostgresUserStore(database_url)
    store.create_schema()
    return store.upsert_user(
        user_id=normalized,
        username=username,
        username_normalized=normalized,
        email=email,
        password_hash=hash_password(password),
        role=role,
        user_type=user_type,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def seed_users(store: UserSeedStore, json_path: str | Path) -> dict[str, int]:
    """Idempotently register dataset users with ``password_hash = bcrypt(normalize(username))``.

    Stores exposing ``upsert_profile`` also receive the dataset profile fields
    (avatar/skills/model/specialization) so ``GET /users`` can serve them (#558).
    """
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
        user_id = str(user.get("id") or normalized)
        status = store.upsert_user(
            user_id=user_id,
            username=username,
            username_normalized=normalized,
            email=user.get("email"),
            password_hash=hash_password(normalized),
            role=user.get("role"),
            user_type=user.get("type"),
            created_at=user.get("created_at"),
        )
        stats["created" if status == "created" else "existing"] += 1
        profile_writer = getattr(store, "upsert_profile", None)
        if status == "created" and callable(profile_writer):
            profile_writer(
                user_id=user_id,
                avatar=user.get("avatar"),
                skills=user.get("skills"),
                model=user.get("model"),
                specialization=user.get("specialization"),
            )
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
