# Issue #526: Username Normalization & PostgreSQL User Seeding (bcrypt)

## Description

Las credenciales de prueba viven en ficheros (`auth/users.json` / `TASKER_AUTH_USERS`) con `InMemoryAuthProvider`, y no existe ninguna normalización de usernames ni hashing moderno en el backend (`normalize_username`/`bcrypt` no aparecen en el código). La ÉPICA 1 de `notas.md` pide sanitizar nombres de usuario y poblar PostgreSQL con los usuarios del dataset del frontend, usando contraseña bcrypt = username normalizado.

Origen: `notas.md` → ÉPICA 1 · Issue #2 (→ #526).

## Status: DONE (2026-09-29)

## Priority: HIGH

## Component
Backend / Auth / Database

## Type
feat / security

## Implementation
1. **`normalize_username(username: str) -> str`:** minúsculas, recorte de espacios, restricción a `a-z`, `0-9` y `.` (normaliza/elimina el resto); función pura con tests exhaustivos.
2. **Store de usuarios en PostgreSQL:** tabla `users` (`id`, `username` UNIQUE, `username_normalized` UNIQUE, `email`, `password_hash` bcrypt, `role`, `type`, `created_at`) siguiendo el patrón hexagonal de puertos/adaptadores del repo.
3. **Seeding idempotente:** lee `frontend/dataset-de-pruebas/users.json` (shape `{users: [...]}`) y registra cada usuario con `password_hash = bcrypt(normalize_username(username))` (p.ej. `admin` → `admin`, `juan.perez` → `juan.perez`); re-ejecuciones no duplican filas.
4. **Punto de ejecución:** comando CLI o hook de arranque de la API gated por env (`TASKER_AUTH_SEED=true`), ejecutable también en compose como paso de init.
5. **Dependencias:** añadir `bcrypt` y `psycopg[binary]` a `pyproject.toml`.

## Acceptance Criteria
- [x] `normalize_username` convierte a minúsculas, limpia espacios y restringe el valor a `a-z`, `0-9` y `.`
- [x] Script/endpoint de seeding que registra los usuarios de `users.json` (frontend) en PostgreSQL
- [x] Contraseña encriptada (bcrypt) = username normalizado (`admin`/`admin`, `juan.perez`/`juan.perez`)
- [x] Seeding idempotente, ejecutable desde CLI o arranque gated por env
- [x] Tests unitarios de normalización y seeding; gates backend sin regresiones

## Verification (2026-09-29)
- **Normalización:** `normalize_username` = `strip().lower()` + eliminación de todo lo que no sea `a-z`/`0-9`/`.` (p.ej. `agent-architect` → `agentarchitect`, `lucas-agent-XXzz` → `lucasagentxxzz`); 9 tests de casos límite.
- **Store PostgreSQL:** `PostgresUserStore` en `auth/user_store.py` con tabla `users` (`id` PK, `username` UNIQUE, `username_normalized` UNIQUE, `email`, `password_hash`, `role`, `"type"`, `created_at TIMESTAMPTZ`), `CREATE TABLE IF NOT EXISTS` + `INSERT ... ON CONFLICT DO NOTHING`; puerto `UserSeedStore` (Protocol) con fake en memoria para tests.
- **Seeding:** `seed_users()` lee `{users: [...]}` de `frontend/dataset-de-pruebas/users.json`, `password_hash = bcrypt(normalize_username(username))`, fast-path con `existing_usernames()` (no hashea existentes); `seed_auth_users()` gated por `TASKER_DATABASE_URL` (+ `TASKER_AUTH_SEED_PATH`).
- **Puntos de ejecución:** hook de arranque de la API en `lifespan` gated por `TASKER_AUTH_SEED=true` (fallo = warning, la API sigue); CLI `python -m socialseed_tasker.auth.user_store`. Compose monta el dataset en `/app/dataset:ro` con `TASKER_AUTH_SEED=true`.
- **Smoke:** arranque → log `auth users seeded: {'total': 8, 'created': 8, 'existing': 0}`; 8 filas en PG con hashes `$2b$12$`; verificado in-container que `bcrypt.checkpw(normalize(username), hash)` es True para los 8; restart → `{'created': 0, 'existing': 8}` (idempotente, sigue 8 filas); CLI con y sin `TASKER_DATABASE_URL` OK; `/health` 200.
- **`auth.py` sin cambios:** el seeding es aditivo y convive con `InMemoryAuthProvider` (verificación de credenciales contra PG llega en #527).
- **Gates:** `ruff` = 1011 (baseline), `mypy` = 1155/133 (≤ 1158), `pytest` = 1118 passed (+17 tests) / 27 skipped / 3 failed preexistentes.

## Files to Create
- `src/socialseed_tasker/auth/user_store.py` — `normalize_username` + repository PostgreSQL
- `tests/unit/test_username_and_seeding.py`

## Files to Modify
- `pyproject.toml` — `bcrypt`, `psycopg[binary]`
- `src/socialseed_tasker/auth/auth.py` — sin cambios necesarios (convivencia aditiva con `InMemoryAuthProvider`; ver Verification)
- `src/socialseed_tasker/infrastructure/web_api/app.py` — hook `TASKER_AUTH_SEED` en `lifespan`
- `docker-compose.yml` — env de seeding + volumen `dataset:ro` de `tasker-api`
- `features.md` — §2 cuando esté done

## Related Issues
- #260 (Implement user repository), #69/#107 (API key auth), #155/#162 (frontend auth), #519 (login JWT que validará contra este store), #525 (servicio PostgreSQL), #527 (consumidor del hash)
