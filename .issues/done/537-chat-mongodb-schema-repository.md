# Issue #537: Esquema del modelo y repositorio MongoDB del chat

## Description

Con el servicio Mongo disponible (#536), `tasker-api` necesita la conexión asíncrona y los esquemas de las colecciones de chat, guardando el **ID único e inalterable del usuario** del Auth Store (PostgreSQL, #526/#527) como referencia en conversaciones, mensajes, lecturas y reacciones. `notas.md` especifica el motor asíncrono `motor` y las colecciones `conversations` e `messages` con índices de alto rendimiento.

Origen: `notas.md` → Épica Chat en Tiempo Real y Persistencia MongoDB · Issue #2 (→ #537).

## Status: DONE (2026-10-02)

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
- [x] Conexión a MongoDB con `motor` (motor asíncrono) en `tasker-api`
- [x] Colección `conversations` con `_id/id`, `title`, `type`, `participant_ids`, `pinned_by`, `created_at`, `updated_at`
- [x] Colección `messages` con `_id/id`, `conversation_id`, `sender_id`, `text`, `type`, `read_by`, `reactions`, `created_at`
- [x] Los `user_id` persistidos son los identificadores únicos e inalterables del PostgreSQL/Auth Store
- [x] Índices creados en `conversation_id` y `participant_ids` (+ `created_at` en mensajes) para consultas de alto rendimiento
- [x] Fallback seguro cuando `TASKER_MONGO_URL` no está disponible (arranque sin roturas)
- [x] Gates backend sin regresiones

## Verification
- **Cliente:** `infrastructure/mongo/client.py` con `get_mongo_client()`/`get_chat_database()` perezosos y cacheados por proceso (`TASKER_MONGO_DB` > path de la URL > `tasker_chat`), `ensure_chat_indexes()` idempotente y `close_mongo()`; sin `TASKER_MONGO_URL` → `None` en todo (fallback de #536) e import de `motor` protegido.
- **Esquema:** `conversations` (`_id` ObjectId expuesto como `id` string, `title`, `type: direct|group`, `participant_ids` = `user_id` del Auth Store PostgreSQL #526/#527, `pinned_by`, `created_at`/`updated_at` UTC aware) y `messages` (`conversation_id` string indexado, `sender_id`, `text`, `type: text|code|system`, `read_by`, `reactions: [{user_id, emoji}]`, `created_at`); serialización a ISO-8601 en respuestas.
- **Repositorio:** `ChatMongoRepository` async con `list_conversations` (por participante, orden `updated_at` desc), `create_or_get_conversation` (reutiliza par directo exacto `$all`+`$size`; grupo siempre crea), `list_messages` (paginación `before` cursor ISO, asc), `toggle_pin` (`$addToSet`/`$pull`), `insert_message` (+ bump `updated_at` de la conversación sin fallar el insert), `mark_as_read` (`$addToSet` idempotente) y `set_reaction` (toggle por usuario). Errores → `ChatStoreError` (log + tipado) sin romper el resto de la API.
- **Lifespan (`web_api/app.py`):** arranque crea cliente + índices (`await ensure_chat_indexes()`) y `finally: close_mongo()` en el shutdown; sin URL es no-op.
- **Índices reales (mongosh):** `conversations`: `participant_ids_1`; `messages`: `conversation_id_1`, `conversation_id_1_created_at_-1`, `created_at_-1` (creados 2× sin error = idempotentes).
- **Gates:** `ruff check src/` = **1011** (baseline) ✓ · `mypy src/` = **1152/133** con caché fresco (220 ficheros revisados vs 217 = +3 nuevos, 0 errores nuevos) ✓ · `pytest -q` = **1225 passed / 27 skipped / 3 failed** (1209 + **16 tests nuevos**; solo los 3 fallos preexistentes) ✓.
- **Tests:** `tests/api/test_chat_repository.py` — 16 tests con fake de motor en proceso (sin MongoDB, CI-friendly): esquema, índices, reuso de par, paginación, pin, lectura, reacciones, validaciones, `ChatStoreError` sin URL/caído y `/health` 200 sin Mongo.
- **Smoke (docker):** `docker compose build tasker-api` (motor instalado desde `pyproject.toml`) + `up -d` → api `healthy`; logs `mongo chat client created` + `chat mongo indexes ensured`; roundtrip real contra `127.0.0.1:27017` (crear/reutilizar conversación, insertar/listar mensaje, pin, lectura, reacción, cleanup) ✓; **degradación**: `docker stop tasker-db-mongo` → `/health` sigue `healthy` y la API sirve; restart → índices persistidos en el volumen.
- **Nota:** `config/storage.py` ya exponía `get_mongo_url()` desde #536 (sin cambios). `requirements.txt` (ruta de instalación documentada en README/CONTRIBUTING) también recibe `motor>=3.3.0`.

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
