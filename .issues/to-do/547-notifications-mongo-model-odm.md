# Issue #547: Modelo de datos MongoDB e infraestructura ODM para notificaciones

## Description

Crear la colección de MongoDB `notifications` con un modelo tipado (Motor/Pydantic) en el backend de FastAPI (`tasker-api`), conectando a través de la variable de entorno `TASKER_MONGO_URL`, con los índices de lectura y ordenación que exige el NotificationCenter.

Contexto real del repo: no existe el paquete `src/socialseed_tasker/models/` ni ningún rastro de `/api/v1/notifications` (todo verde). El patrón de persistencia MongoDB ya está probado por el chat (#537): `config/storage.py:get_mongo_url()` lee `TASKER_MONGO_URL`, `infrastructure/mongo/client.py:get_chat_database()` devuelve la base `tasker` (contenedor `tasker-db-mongo`, #536) y `infrastructure/mongo/chat_repository.py` muestra el estilo asíncrono con degradación tipada (`ChatStoreError`: log + raise, nunca rompe el resto de la API). `notas.md` pide expresamente `src/socialseed_tasker/models/notification.py`; se crea el paquete siguiendo el plan (alternativa válida siguiendo la convención de #537: schema dentro de `infrastructure/mongo/`).

Origen: `notas.md` → Sistema de Notificaciones Real en MongoDB · Issue #1 (→ #547).

## Status: TODO

## Priority: HIGH

## Component
Backend / Data / MongoDB

## Type
feat / backend

## Implementation
1. **Modelo `Notification`:** `src/socialseed_tasker/models/notification.py` con campos `id` (PyObjectId mapeado a `id` en JSON), `user_id` (`str`, usuario destino o `"global"` / `"system"`), `type` (enum `MENTION`, `HITL`, `CONSTRAINT_VIOLATION`, `AGENT_FAILURE`, `SLA`, `WELCOME`), `severity` (enum `EMERGENCY`, `WARNING`, `INFO`), `title`, `message`, `read: bool = False`, `requires_action: bool = False`, `link_to: Optional[str]`, `hitl_request_id: Optional[str]`, `channel: str`, `created_at: datetime` (UTC ISO 8601).
2. **Colección y acceso:** reutilizar `get_chat_database()` de `infrastructure/mongo/client.py` (misma DB `tasker`, no hará falta nueva env) exponiendo la colección `notifications` con una abstracción de repo y error tipado propio (`NotificationStoreError`, análoga a `ChatStoreError`): log + degradación segura cuando Mongo no está configurado o es inaccesible.
3. **Índices idempotentes:** `{ user_id: 1, read: 1 }` y `{ created_at: -1 }`, creados de forma idempotente (ensure en el primer acceso o hook de arranque), tal como pide `notas.md`.
4. **Mapeo de tipos a la UI:** correspondencia estable entre los enums del modelo y las 5 categorías actuales del frontend (`mention`, `hitl`, `constraint_violation`, `agent_failure`, `sla`) más la nueva `welcome`/`system` que introduce #549/#551, sin romper `frontend/src/types/notifications.ts`.
5. **Tests:** unitario que crea y lee un documento de notificación directamente en Mongo (o con repo fake en memoria cuando no hay `TASKER_MONGO_URL` en el entorno, patrón de #541); tipos limpios en `ruff`/`mypy` sobre los ficheros nuevos.

## Acceptance Criteria
- [ ] La aplicación FastAPI accede a la colección `notifications` de `TASKER_MONGO_URL` al iniciar
- [ ] Definición de tipos válida con `pydantic` sin errores de `mypy`/`ruff` en los ficheros nuevos
- [ ] Los índices `{user_id, read}` y `{created_at}` existen y su creación es idempotente
- [ ] Test unitario creando y leyendo un documento de notificación (Mongo real o fake equivalente sin servicios externos)
- [ ] Gates backend sin regresiones (`ruff` 1011 / `mypy` 1153 / `pytest` 1282 + 3 preexistentes)

## Files to Create
- `src/socialseed_tasker/models/__init__.py`
- `src/socialseed_tasker/models/notification.py`
- `tests/unit/test_notification_model.py`

## Files to Modify
- `src/socialseed_tasker/infrastructure/mongo/client.py` — alias/ensure de la colección `notifications` si procede

## Related Issues
- #536 (contenedor MongoDB + `TASKER_MONGO_URL`), #537 (patrón repo/errores Mongo), #525 (config storage), #548 (API REST que consume el modelo), #549 (inserción de la bienvenida), #551 (mapeo a las categorías del store)
