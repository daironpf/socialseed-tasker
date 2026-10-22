# Issue #593: 403 permanente en `/admin/tenants` y `POST /data-quality/rules` — RBAC condicionado a la env `TASKER_AUTH_USERS` (no definida en el stack)

## Description

Dos superficies admin quedan **inalcanzables por diseño** en el stack real, incluso
con JWT de admin válido:

```
GET  /api/v1/admin/tenants            -> 403 {"detail":"forbidden"}
POST /api/v1/admin/tenants            -> 403
GET  /api/v1/admin/tenants/{id}       -> 403
DELETE /api/v1/admin/tenants/{id}     -> 403
POST /api/v1/data-quality/rules       -> 403 {"detail":"forbidden"}
```

(Verificado en run4 con JWT de `POST /auth/login`; se reprodujo de nuevo el
2026-10-21 — `GET /admin/tenants` con Bearer admin → 403.) Nota: los **GET** de
`data-quality` (`/rules`, `/reports/{id}`, `/metrics`) sí responden 200 — solo las
operaciones de escritura/guard son 403.

**Causa raíz**: los guards exigen un mapa de usuarios/roles que solo se carga desde
variable de entorno:

- `src/socialseed_tasker/auth/rbac.py:24` — el RBAC lee `TASKER_AUTH_USERS` (lista env
  de usuarios con roles/permisos).
- `src/socialseed_tasker/data_quality/api.py:19` — el guard propio de data-quality
  hace el mismo check.

`docker-compose.yml` **no define** `TASKER_AUTH_USERS` → el mapa está vacío → toda
petición queda `forbidden` (el JWT admin de `auth/users.json` en memoria no alimenta a
estos guards). Es un agujero de configuración convertido en "la feature no existe".

## Status: DONE (commit pendiente)

## Priority: MEDIUM

## Component
Backend / Config + Auth (RBAC y data-quality)

## Type
bug fix / config

## Implementation

Decidir el contrato (recomendado: **b** + **c**):

1. **a) Compose**: definir `TASKER_AUTH_USERS` en `docker-compose.yml` con el admin
   por defecto (mismo espíritu que `TASKER_AUTH_SEED`/`auth/users.json`) — pero la env
   es frágil de mantener duplicada frente al login.
2. **b) Fallback al JWT**: cuando `TASKER_AUTH_USERS` no esté definida, resolver roles
   del **claim del propio JWT** (`auth/tokens.py::verify_access` ya devuelve
   `role`/`permissions` — el login admin emite `ADMIN` con permisos), en lugar de
   denegar en bloque. Denegar en bloque solo si ni env ni JWT aportan rol.
3. **c) Unificar guards**: `data_quality/api.py:19` y `rbac.py:24` repiten la misma
   lógica → extraer un único `require_permission(...)` (SRP) con la política elegida,
   y usarlo en `admin/tenants` + `data-quality` (+ auditar quién más llama a
   `rbac.py`).
4. **Tests**:
   - `test_admin_tenants_forbidden_without_users_env_but_admin_jwt` (según contrato
     elegido).
   - `test_data_quality_write_requires_permission`.
   - `test_denies_when_no_source_of_roles` (el 403 sigue existiendo para anónimos).

## Acceptance Criteria
- [x] Con JWT admin (login `admintoken123`), `GET/POST /admin/tenants` y
      `POST /data-quality/rules` → 2xx/4xx de negocio, ya no 403 sistemático
- [x] Sin sesión o sin rol suficiente → 403 (la seguridad no se relaja para anónimos)
- [x] La política de roles vive en un solo punto (sin guard duplicado rbac/data-quality)
- [x] `docker-compose.yml` y/o el código reflejan la decisión (env documentada si se
      elige a)
- [x] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

## Files to Modify
- `src/socialseed_tasker/auth/rbac.py` (línea 24)
- `src/socialseed_tasker/data_quality/api.py` (línea 19)
- `docker-compose.yml` (si Opción a)
- `tests/api/` — tests de permisos

## Related Issues
- #554/#552 (login/credenciales del admin), #527 (JWT con role/permissions), #592
  (503 engañoso en otro guard), #594 (observabilidad)

## Notes
- **Repro**: login → `curl .../api/v1/admin/tenants -H "Authorization: Bearer <jwt>"`
  → 403 `forbidden`.
- Antes de tocar, confirmar la intención original: puede que `TASKER_AUTH_USERS` fuera
  el diseño "multi-tenant por env" y los tenants quieran 403 sin configuración — en
  ese caso, que el 403 venga con código/detalle explícito
  (`TENANCY_NOT_CONFIGURED`) y no un `forbidden` mudo.

### Resolución (2026-10-22)

**Decisión: b) fallback al JWT + c) unificar guards** (compose intacto — AC4 se
refleja en el código). Causa real doble, más amplia que la descrita:

1. `load_auth_provider().verify_token()` solo reconoce **tokens estáticos**
   (`TASKER_AUTH_USERS`/`auth/users.json`) — un **JWT de `/auth/login` nunca
   resolvía identidad** → `has_permission(None, "admin")` → 403, con o sin env.
2. El RBAC store solo se alimenta de `TASKER_AUTH_USERS` (`cli/wiring.py:78`) —
   ni `auth/users.json` ni los claims del JWT lo alimentan.

**Fix**: nuevo `auth/permissions.py::require_permission(request, permission,
container)` — único punto de política con fuentes, en orden: (1) token estático
→ RBAC store **o** `permissions` del propio auth provider (`users.json`); (2)
JWT firmado → claims `permissions`/`role == "ADMIN"` (mismo policy que
`app.py::_require_admin` ya aplicaba a `/admin/flags`); (3) cookie de sesión
OAuth → RBAC/provider. En cualquier otro caso → 403 `forbidden`.

**Consumidores**: `routers/tenants.py` (los 4 endpoints, con helper
`_container(request)` que elimina el bloque duplicado) y
`data_quality/api.py` (`_get_user_id`/`_require_admin` eliminados —
`create_rule` llama a `require_permission`). **Auditoría de otros llamadores de
`rbac.py` (sin cambio, policy distinta/in-process)**: CLI (`cli/main.py`,
`flags_cli.py`), GraphQL (`graphql/resolvers.py`), `app.py::_require_admin`
(flags/privacy/users — ya tenía fallback JWT propio), `_require_rate_access`,
`routers/secrets.py`. Toda superficie HTTP que resuelva identidad desde
`verify_token`+RBAC sin fallback JWT tiene el mismo agujero: `secrets.py` es
candidato para un follow-up con `require_permission`.

**Tests** `tests/api/test_admin_permissions.py` (10): JWT admin sin
`TASKER_AUTH_USERS` → 200 en GET/DELETE `/admin/tenants` y `POST
/data-quality/rules` (con aserción de efecto: registry.add / delete
registrado); JWT developer → 403; sin identidad → 403; token estático
`admintoken123` (users.json) → 200 y `readertoken123` → 403 (fuente
provider); GET `/data-quality/rules` sigue 200 sin auth. `test_flags_api_unit`
(8) intacto.

**Verificación en vivo** (tasker-api reconstruido, 2026-10-22): 11/11 —
`GET/POST/DELETE /admin/tenants` con JWT admin → **200** (antes 403;
create+read+delete de tenant `t-593` con limpieza), `POST /data-quality/rules`
con JWT admin → **200** (antes 403), `GET /data-quality/rules` → 200, JWT
reader → **403** en ambas superficies, anónimo → 401 del middleware global
(nunca 200), nodos Neo4j 5 → 5, `docker logs` sin ERROR/Traceback. Nota: tokens
estáticos en Bearer viven rechazados por el middleware con 401 (política
pre-existente de `api_key_auth_middleware`, fuera de alcance); la fuente
estática del guard queda cubierta por tests unit.

**Gates**: ruff (`tenants.py`+`api.py`) 1 error HEAD → 0 (delta −1),
`mypy src/` 1110 (HEAD 1117, −7), `pytest -q` **1622 passed / 62 skipped /
0 failed**.
