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

## Status: TODO

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

## Acceptance Criteria
- [ ] `POST /users` (humano) devuelve `temporary_password` y con ella el login inmediato
      funciona (bcrypt verificado contra PG)
- [ ] `GET /users*` **nunca** devuelve `temporary_password`; no queda en claro en PG
- [ ] Crear con `password` explícito usa ese y no devuelve temporal; agentes → sin credencial
- [ ] El modal muestra la contraseña una sola vez con copiar y aviso, y la limpia al confirmar
- [ ] **Tests**: los backend + frontend listados pasan
- [ ] Gates: backend `ruff` 1011 / `mypy` 1153 / `pytest` 1331+3; frontend `lint` 0/2 /
      `test` 306+ / `build` OK / i18n 1693+N (`users.passwordOnce` + aviso) EN/ES

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
