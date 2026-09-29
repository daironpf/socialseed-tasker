# Issue #526: Username Normalization & PostgreSQL User Seeding (bcrypt)

## Description

Las credenciales de prueba viven en ficheros (`auth/users.json` / `TASKER_AUTH_USERS`) con `InMemoryAuthProvider`, y no existe ninguna normalización de usernames ni hashing moderno en el backend (`normalize_username`/`bcrypt` no aparecen en el código). La ÉPICA 1 de `notas.md` pide sanitizar nombres de usuario y poblar PostgreSQL con los usuarios del dataset del frontend, usando contraseña bcrypt = username normalizado.

Origen: `notas.md` → ÉPICA 1 · Issue #2 (→ #526).

## Status: TODO

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
- [ ] `normalize_username` convierte a minúsculas, limpia espacios y restringe el valor a `a-z`, `0-9` y `.`
- [ ] Script/endpoint de seeding que registra los usuarios de `users.json` (frontend) en PostgreSQL
- [ ] Contraseña encriptada (bcrypt) = username normalizado (`admin`/`admin`, `juan.perez`/`juan.perez`)
- [ ] Seeding idempotente, ejecutable desde CLI o arranque gated por env
- [ ] Tests unitarios de normalización y seeding; gates backend sin regresiones

## Files to Create
- `src/socialseed_tasker/auth/user_store.py` — `normalize_username` + repository PostgreSQL
- `tests/unit/test_username_and_seeding.py`

## Files to Modify
- `pyproject.toml` — `bcrypt`, `psycopg[binary]`
- `src/socialseed_tasker/auth/auth.py` — convivencia/fallback con `InMemoryAuthProvider`
- `docker-compose.yml` — env de seeding de `tasker-api`
- `features.md` — §2 cuando esté done

## Related Issues
- #260 (Implement user repository), #69/#107 (API key auth), #155/#162 (frontend auth), #519 (login JWT que validará contra este store), #525 (servicio PostgreSQL), #527 (consumidor del hash)
