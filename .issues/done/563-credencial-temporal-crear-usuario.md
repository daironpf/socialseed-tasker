# Issue #563: Credencial temporal al crear usuario humano (login inmediato con password visible una vez)

## Description

Decisión del usuario: al crear un usuario desde la vista se **genera una credencial PG con
password temporal visible una sola vez** — el administrador puede dársela al usuario (o usarla
él mismo) y el login funciona de inmediato sin flujo extra de "asignar contraseña".

Hoy (#559) el usuario nace con `password_hash=''` = **sin login posible** (`authenticate_user`
trata `''` como no login, `user_store.py:59`). Las piezas ya están en el repo de #526: bcrypt
via `hashlib`/bcrypt (`user_store.py` valida con `checkpw`) y `TASKER_AUTH_SEED` ya convierte
plaintext del dataset en hash en el seeding (`app.py:66-83`) — el mismo patrón aplica aquí.

Mock de referencia: `mockApi.createUser` no maneja contraseñas (login mock es por perfil), por
lo que el contrato "password visible una vez" es **nuevo en el contrato real** y debe fijarse
con tests.

## Status: DONE

## Priority: MEDIUM

## Component
Fullstack (Backend /users + modal + UsersView)

## Type
feat / fullstack

## Implementation
1. **Backend — generar password en `POST /users`** (solo `type='human'` y solo si el request
   no trae credencial explícita):
   - Generar con `secrets.token_urlsafe(12)` (o prefijo fijo tipo `tasker-` + random —
     decidir en la issue, por defecto `secrets.token_urlsafe(12)`), `hash` con bcrypt (mismo
     parámetro de coste que `user_store.py`).
   - Se persiste en **`human_user.password_hash`** (esquema normalizado #558 — los agentes no
     tienen esa fila/credencial).
   - `UserCreateRequest` opcionalmente acepta `password: str | None` (si el front lo manda, se
     usa ese en claro y **no** se devuelve `temporary_password`).
   - Respuesta 201 ampliada: campo **`temporary_password: str | None`** en `UserResponse`
     (populado **solo** en este POST, `None` en cualquier otra lectura — nunca se persiste en
     claro y `GET` jamás lo devuelve).
2. **Backend — agentes no llevan credencial** (#564 crea con `password_hash=''`) — condición
   explícita en el código y en el test.
3. **Frontend — mostrarla una vez**: en `usersStore.createUser`, si la respuesta trae
   `temporary_password`, abrir un pequeño diálogo/toast persistente en `CreateUserModal`
   (o panel de resultado) con: la contraseña en monoespaciada + botón copiar (Clipboard API,
   ya usada en la app) + aviso `users.passwordOnce` (EN/ES: "Se muestra solo una vez") y botón
   "Entendido" que cierra y limpia el estado (no se guarda en el store).
4. **Frontend — normalizar** la respuesta (`normalizeBackendUser` ignora
   `temporary_password` para la tarjeta — verificar que no contamina).
5. **Tests** (obligatorios):
   - Backend: `test_create_user_returns_temporary_password_and_login_works` — crear → usar
     `temporary_password` en `POST /auth/login` con ese username → **200 con tokens**;
     `test_create_user_password_field_overrides_temporary` (si trae `password`, login con ese
     y `temporary_password is None`); `test_get_users_never_returns_temporary_password`;
     `test_create_agent_has_no_credential` (login con cualquier password → 401).
   - Frontend: spec de `usersApi`/store — la respuesta con `temporary_password` no contamina la
     tarjeta normalizada; spec del modal/panel que muestra la password y la limpia al cerrar.

## Resolution

**Resuelto 2026-10-08.**

- **Backend**: `POST /users` (humanos) genera `secrets.token_urlsafe(12)` salvo que el body
  traiga `password` explícito; se hashea con `hash_password` (bcrypt, coste por defecto del
  repo) y se persiste vía el nuevo parámetro `password_hash` de `create_human_user` (el SQL
  dejó de usar el literal `''`). `UserResponse.temporary_password` se rellena **solo** en el
  201 (`_profile_to_response` → default `None`; el handler lo pisa únicamente cuando la
  password es temporal); con `password` explícito se devuelve `None` y nada se refleja.
- **Nunca en claro**: PG solo guarda el hash (`$2b$…`); `GET /users` y `GET /users/{id}`
  devuelven `temporary_password: null` (el schema lo fija a `None` en toda lectura). Agentes:
  fuera de este endpoint (422 ya existente, sin fila `human_user` → sin login, #564).
- **Frontend**: `usersApi.createUser` devuelve `{ user, temporaryPassword }`
  (`normalizeBackendUser` ignora el campo → la tarjeta no se contamina), el store reenvía el
  resultado sin persistir el plaintext, `UsersView` abre el nuevo `TemporaryPasswordDialog`
  (monoespaciada + copiar con Clipboard API + aviso `users.passwordOnce` + botón "Entendido"
  que limpia el estado — no vive en el store); i18n EN/ES con 5 claves nuevas
  (`tempPasswordTitle`, `passwordOnce`, `copy`, `copied`, `understood`).
- **Tests** (+4 backend, +3 frontend): los 4 obligatorios —
  `test_create_user_returns_temporary_password_and_login_works` (201 con `temporary_password`,
  hash bcrypt ≠ claro, login real con ella → 200 y `user.id` coincide),
  `test_create_user_password_field_overrides_temporary` (`None` + `verify_password`),
  `test_get_users_never_returns_temporary_password` (GET by id + lista → null) y
  `test_create_agent_has_no_credential` (agente → `authenticate_user` None con cualquier
  password); `test_create_user_201_returns_uid_and_profile` pasó a exigir hash bcrypt y
  `test_update_user_full_profile_persisted` compara el hash pre/post (el seed ya no es `''`).
  Frontend: specs de `usersApi` (normalización sin contaminación + `null`) y 2 de
  `UsersView.spec.ts` (diálogo con `data-testid`, ack lo limpia; sin temporal no se abre).
  Helper `_install_login_env`: app completa con el `authenticate_user` real sobre el fake PG.
- **Gates** (2026-10-08): `ruff` **1334** / `mypy` **1136** / `pytest` **1426 passed** + 3
  preexistentes + 27 skipped; frontend `lint` 0/2 / `test` **320 (45)** / `build` OK /
  i18n **1701/1701**.

## Acceptance Criteria
- [x] `POST /users` (humano) devuelve `temporary_password` y con ella el login inmediato
      funciona (bcrypt verificado contra PG)
- [x] `GET /users*` **nunca** devuelve `temporary_password`; no queda en claro en PG
- [x] Crear con `password` explícito usa ese y no devuelve temporal; agentes → sin credencial
- [x] El modal muestra la contraseña una sola vez con copiar y aviso, y la limpia al confirmar
- [x] **Tests**: los backend + frontend listados pasan
- [x] Gates: backend `ruff` 1334 / `mypy` 1136 / `pytest` 1426+3 preexistentes; frontend
      `lint` 0/2 / `test` 320 / `build` OK / i18n 1701/1701 (`users.passwordOnce` + aviso) EN/ES

## Files to Create
- (posible) `frontend/src/components/users/TemporaryPasswordDialog.vue`

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/schemas.py` (`UserCreateRequest.password`,
  `UserResponse.temporary_password`)
- `src/socialseed_tasker/infrastructure/web_api/routers/user.py` (generación bcrypt)
- `frontend/src/components/users/CreateUserModal.vue` (panel de password)
- `frontend/src/stores/usersStore.ts` (mostrar/limpiar)
- `frontend/src/locales/es.json` / `en.json`
- `tests/api/test_users_api.py` + specs frontend

## Notes
- bcrypt ya es dependencia del backend (lo usa `user_store.py`) — no añadir librerías.
- `temporary_password` vive solo en el response del POST: se calcula en el handler y se asigna
  a la respuesta; el resto de endpoints la fijan a `None` por defecto del schema.
- Alternativa descartada: endpoint `POST /users/{id}/password` — se eligió el flujo de la
  issue para que el alta y la credencial sean un solo paso (decisión explícita del usuario).

## Related Issues
- #559 (crear usuario), #558 (raíz PG), #561 (rol efectivo tras login), #564 (agentes sin
  credencial), #526/#543 (bcrypt y seeding)
