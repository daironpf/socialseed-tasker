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

## Status: OPEN

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
- [ ] Con JWT admin (login `admintoken123`), `GET/POST /admin/tenants` y
      `POST /data-quality/rules` → 2xx/4xx de negocio, ya no 403 sistemático
- [ ] Sin sesión o sin rol suficiente → 403 (la seguridad no se relaja para anónimos)
- [ ] La política de roles vive en un solo punto (sin guard duplicado rbac/data-quality)
- [ ] `docker-compose.yml` y/o el código reflejan la decisión (env documentada si se
      elige a)
- [ ] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

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
