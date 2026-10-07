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
from typing import Any, Protocol

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

INDEX_DDL: tuple[str, ...] = (
    "CREATE INDEX IF NOT EXISTS ix_users_user_type ON users (user_type)",
    "CREATE INDEX IF NOT EXISTS ix_human_user_role ON human_user (role_id)",
    "CREATE INDEX IF NOT EXISTS ix_user_skills_skill ON user_skills (skill_id)",
    "CREATE INDEX IF NOT EXISTS ix_session_logs_user_created ON session_logs (user_id, created_at DESC)",
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
            for ddl in (HUMAN_USER_DDL, AGENTS_USER_DDL, USER_SKILLS_DDL, SESSION_LOGS_DDL):
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
