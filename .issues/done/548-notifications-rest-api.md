# Issue #548: API RESTful completa para notificaciones (`/api/v1/notifications`)

## Description

Implementar el router de FastAPI `notifications.py` que permita listar, filtrar, marcar como leídas y eliminar notificaciones del usuario autenticado vía JWT.

Contexto real del repo: no existe router ni endpoint de notificaciones (grep vacío en `src/`). Patrones ya probados a seguir: registro de routers en `routers/__init__.py` + `web_api/routes.py` (patrón de `setup.py`/`chat.py` en #543/#539); envolvente estándar `APIResponse` en camelCase con `{data, error, meta}` (contrato de #539 que ya consume el frontend); identidad del usuario derivada del JWT con el patrón de `routers/chat.py` (`_current_user(request)` → `load_auth_provider().verify_token(token)`, #527); persistencia sobre el modelo/repo de #547 con degradación tipada.

Origen: `notas.md` → Sistema de Notificaciones Real en MongoDB · Issue #2 (→ #548).

## Status: DONE (2026-10-04)

## Priority: CRITICAL

## Component
Backend / API / Notifications

## Type
feat / backend

## Implementation
1. **Router `notifications.py`** (prefix `/api/v1/notifications`, registrado en `routers/__init__.py` y `web_api/routes.py`):
   - `GET /api/v1/notifications` — query params `read` (bool), `category` (str), `limit` (int, default 50), `offset` (int); lista ordenada por `created_at` descendente.
   - `PATCH /api/v1/notifications/{id}/read` — marca `read: True`.
   - `POST /api/v1/notifications/mark-all-read` — marca todas las no leídas del usuario.
   - `DELETE /api/v1/notifications/{id}` — elimina la notificación indicada.
   - `POST /api/v1/notifications/clear-all` — elimina todas las del usuario (parámetro opcional para solo las leídas).
2. **Aislamiento estricto por usuario:** el `user_id` se deriva siempre del JWT de la petición (nunca del body); notificaciones de otro usuario → 404/403 (sin fugas de datos entre usuarios).
3. **Envolvente y wire:** respuestas bajo `APIResponse` en camelCase (`createdAt`, `requiresAction`, `hitlRequestId`, `linkTo`) — contrato que consumirá #551.
4. **Paginación:** meta con total/limit/offset coherente con los query params.
5. **Tests:** `pytest` por endpoint con repo fake en memoria (patrón `FakeRepo` de #520 y los suites de #541/#543), cubriendo contrato, aislamiento por usuario, errores 404 y validación de query params.

## Acceptance Criteria
- [x] Los 5 endpoints responden bajo la envolvente estándar `APIResponse` (camelCase)
- [x] Filtrado estricto por `user_id` derivado del JWT del cliente (una petición no puede leer/borrar notificaciones ajenas)
- [x] Pruebas de integración con `pytest` para cada endpoint (legado + aislamiento + 404)
- [x] Gates backend sin regresiones (`ruff` 1013 = baseline HEAD, `mypy` 1153, `pytest` 1306 passed = 1294 + 12 nuevos, 3 failed preexistentes)

## Files to Create
- `src/socialseed_tasker/infrastructure/web_api/routers/notifications.py`
- `tests/api/test_notifications_api.py`

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/__init__.py` — export del `notifications_router` (re-export explícito `as` para mypy strict)
- `src/socialseed_tasker/infrastructure/web_api/routes.py` — re-export con `as notifications_router`
- `src/socialseed_tasker/infrastructure/web_api/app.py` — `include_router(notifications_router, prefix="/api/v1", tags=["notifications"])` (el montaje real vive en `app.py`, no en `routes.py` como decía la issue)
- `src/socialseed_tasker/infrastructure/mongo/notification_repository.py` — ampliado con `list_for_user`/`mark_read`/`mark_all_read`/`delete`/`clear_all` (repo de #547)
- `tests/unit/test_notification_model.py` — fake Mongo extendido (cursor sort/skip/limit, count/update/delete) + 4 tests de las nuevas operaciones

## Notes
- Identidad: se reutiliza `_current_user` importándolo de `routers/chat.py` (misma cadena JWT → API key → OAuth cookie → `X-User-ID`), sin duplicar el resolver.
- `meta.pagination` usa el `PaginationMeta` estándar del repo (`page`/`limit`/`total`/`has_next`/`has_prev` en snake_case) con `page = offset // limit + 1` — coherente con los query params `limit`/`offset` sin romper el contrato de otros endpoints paginados.
- `POST /clear-all` acepta el query param opcional `onlyRead` (alias camelCase); `category` se valida contra `FRONTEND_CATEGORIES` (400 en desconocida); ids ajenos/desconocidos → 404 sin fuga de existencia; degradación Mongo → 503 tipado.

## Related Issues
- #547 (modelo/repo Mongo que persiste), #539 (contrato `APIResponse` camelCase), #527 (JWT/sesiones), #543 (patrón router + suite de endpoints), #550 (emisión en vivo tras insertar), #551 (cliente Axios que consume la API)
