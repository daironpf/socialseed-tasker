# Issue #537: Esquema del modelo y repositorio MongoDB del chat

## Description

Con el servicio Mongo disponible (#536), `tasker-api` necesita la conexión asíncrona y los esquemas de las colecciones de chat, guardando el **ID único e inalterable del usuario** del Auth Store (PostgreSQL, #526/#527) como referencia en conversaciones, mensajes, lecturas y reacciones. `notas.md` especifica el motor asíncrono `motor` y las colecciones `conversations` e `messages` con índices de alto rendimiento.

Origen: `notas.md` → Épica Chat en Tiempo Real y Persistencia MongoDB · Issue #2 (→ #537).

## Status: TODO

## Priority: HIGH

## Component
Backend / Chat / Persistence

## Type
feat / backend

## Implementation
1. **Dependencia:** `motor` en `pyproject.toml` (cliente MongoDB asíncrono oficial para asyncio).
2. **Cliente:** `infrastructure/mongo/client.py` con `get_mongo_client()`/`get_chat_database()` perezosos, cacheados y cerrados en el ciclo de vida de la app; sin `TASKER_MONGO_URL` no se crea cliente (fallback seguro de #536).
3. **Colección `conversations`:** `_id`/`id` (ObjectId/string), `title` string opcional, `type: direct | group`, `participant_ids` (array de `user_id` reales del PostgreSQL/Auth Store), `pinned_by` (array de `user_id`), `created_at`, `updated_at` timestamps.
4. **Colección `messages`:** `_id`/`id`, `conversation_id` (ObjectId/string indexado), `sender_id` (`user_id` único e inalterable del emisor), `text`, `type: text | code | system`, `read_by` (array de `user_id`), `reactions` (array de `{ user_id, emoji }`), `created_at` timestamp indexado.
5. **Repositorio:** `ChatMongoRepository` con las operaciones que consumirán REST (#539) y Socket.IO (#538): listar conversaciones por participante, crear/obtener conversación, paginar mensajes, alternar pin, insertar mensaje, marcar lectura, actualizar reacciones.
6. **Índices idempotentes:** `conversation_id` y `participant_ids` (más `created_at` en `messages`) creados en el arranque con `create_index` repetible.
7. **Degradación:** si Mongo no está configurado/caído, el repositorio falla de forma controlada (log + error tipado) sin romper el resto de la API.

## Acceptance Criteria
- [ ] Conexión a MongoDB con `motor` (motor asíncrono) en `tasker-api`
- [ ] Colección `conversations` con `_id/id`, `title`, `type`, `participant_ids`, `pinned_by`, `created_at`, `updated_at`
- [ ] Colección `messages` con `_id/id`, `conversation_id`, `sender_id`, `text`, `type`, `read_by`, `reactions`, `created_at`
- [ ] Los `user_id` persistidos son los identificadores únicos e inalterables del PostgreSQL/Auth Store
- [ ] Índices creados en `conversation_id` y `participant_ids` (+ `created_at` en mensajes) para consultas de alto rendimiento
- [ ] Fallback seguro cuando `TASKER_MONGO_URL` no está disponible (arranque sin roturas)
- [ ] Gates backend sin regresiones

## Files to Create
- `src/socialseed_tasker/infrastructure/mongo/__init__.py`
- `src/socialseed_tasker/infrastructure/mongo/client.py`
- `src/socialseed_tasker/infrastructure/mongo/chat_repository.py`
- `tests/api/test_chat_repository.py`

## Files to Modify
- `pyproject.toml` — dependencia `motor`
- `src/socialseed_tasker/config/storage.py` — URL de Mongo consumida por el cliente
- `src/socialseed_tasker/infrastructure/web_api/app.py` — ciclo de vida del cliente + índices idempotentes

## Related Issues
- #536 (servicio MongoDB), #526/#527 (user_id en PostgreSQL/Auth Store), #533 (patrón de health/fallback de dependencias)
