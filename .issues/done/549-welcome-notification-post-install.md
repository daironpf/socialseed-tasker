# Issue #549: Notificación de bienvenida del sistema al instalar/iniciar

## Description

Conectar el flujo de instalación y primer arranque (*Setup Wizard* / post-install) con el motor de notificaciones en MongoDB para generar la primera notificación de bienvenida del administrador.

Contexto real del repo: `routers/setup.py` (#543) sanitiza el admin (`normalize_username`), lo crea en PostgreSQL (bcrypt) + nodo `:User`, crea el `:Project` y las políticas, y **wipea** Neo4j + tablas públicas de PostgreSQL + colecciones Mongo del chat + Redis antes de crear — hoy esa lista de colecciones Mongo **no incluye `notifications`**, por lo que hay que ampliarla para que cada instalación deje exactamente una bienvenida (AC). El destino es el propio `admin_user` creado en el initialize. El wizard (#545/#546) ya dispara `POST /api/v1/setup/initialize`; no requiere cambios de UI.

Origen: `notas.md` → Sistema de Notificaciones Real en MongoDB · Issue #3 (→ #549).

## Status: DONE (2026-10-04)

## Priority: MEDIUM

## Component
Backend / Onboarding / Setup

## Type
feat / integration

## Implementation
1. **Inserción post-alta:** al final del `setup_initialize` (#543), tras crear el admin, insertar la notificación vía el repo de #547 con los datos exactos de `notas.md`:
   * `type`: `WELCOME`, `severity`: `INFO`, `channel`: `system`, `user_id`: admin creado.
   * `title`: "¡Bienvenido a SocialSeed Tasker!"
   * `message`: "El sistema ha sido instalado correctamente. Te recomendamos crear tus primeros agentes de IA y registrar usuarios en la plataforma."
   * `requires_action`: `True`, `link_to`: `"/users"`.
2. **Wipe ampliado:** añadir la colección `notifications` al wipe de MongoDB del initialize (junto a las colecciones del chat) para que las reinstalaciones (`confirm_wipe=true`, guard de #546) también dejen exactamente una bienvenida.
3. **Degradación segura:** si `TASKER_MONGO_URL` no está configurado o Mongo falla, el initialize **no falla** (log + continuar), igual que el resto de operaciones Mongo del repo.
4. **Idempotencia:** decisión explícita — no duplicar la bienvenida si ya existe una `WELCOME` para ese usuario (guard por `(user_id, type)`), documentada en el código.
5. **Tests:** ampliar `test_setup_endpoints.py` (hoy 20 tests): bienvenida insertada con el payload exacto, colección limpia + 1 documento tras un segundo initialize con `confirm_wipe`, y degradación sin Mongo.

## Acceptance Criteria
- [x] Tras completar la instalación vía `/setup`, la colección `notifications` contiene exactamente la notificación de bienvenida (payload literal de `notas.md`)
- [x] Al iniciar sesión por primera vez con la cuenta creada, el payload de notificaciones (#548) incluye este mensaje inicial
- [x] Una reinstalación con `confirm_wipe=true` deja exactamente 1 bienvenida (wipe incluye `notifications`)
- [x] Mongo no configurado/caído no rompe `POST /setup/initialize`
- [x] Gates backend sin regresiones (`ruff check src` 1011 = baseline, `mypy src` 1153 = baseline, `pytest` 1313 passed = 1306 + 7 nuevos, 3 failed preexistentes)

## Files to Create
- (ninguno nuevo)

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/setup.py` — inserción de la bienvenida + wipe de `notifications`
- `tests/api/test_setup_endpoints.py` — nuevos tests del flujo de bienvenida

## Notes
- **El wipe ya cubría `notifications`:** `_wipe_mongo` no usa una lista fija de colecciones — recorre `db.list_collection_names()` y dropea todas las no-`system.*` (chat **y** notificaciones). No hizo falta tocar el código del wipe; el comportamiento queda fijado por `test_wipe_mongo_drops_notifications_collection` (fake `pymongo.MongoClient`) y documentado en su docstring, cumpliendo el AC de "exactamente una bienvenida" tras reinstalar.
- **Endpoint async con cuerpo síncrono protegido:** `setup_initialize` pasó a `async def` y delega el cuerpo de instalación (sesiones Neo4j síncronas, bcrypt, wipes pymongo/redis) en `_perform_initialize` mediante `run_in_threadpool` — el mismo threadpool que FastAPI ya usaba para los endpoints `def`, de modo que nada bloquea el event loop; solo la bienvenida corre en el loop con `await`.
- **Repo vía `app.state`:** la inserción usa `app.state.notification_repository` (#547/#548), por lo que comparte el motor (y el loop) con el lifespan (`ensure_notification_indexes`) — sin cliente motor nuevo ni cruce de loops, y testeable inyectando un repo fake.
- **Idempotencia:** guard por `(user_id, type)` = `list_for_user(admin, notification_type="WELCOME", limit=1)` antes de insertar (sin índice único nuevo, decidido y documentado en el código); si el wipe no borró la colección, la segunda instalación conserva la original en lugar de duplicar.
- **Degradación:** `NotificationStoreError` (repo no configurado, Mongo caído o fake degradado) → `logger.warning` + continuar; la ausencia de `app.state.notification_repository` también degrada a log.
- **Tests (7 nuevos, 27 totales):** payload literal exacto, no-duplicado con welcome preexistente, reinstalación con `confirm_wipe=true` → exactamente 1 (wipe fake limpia el repo + wipe real dropea `notifications`), store caído → 200, sin `TASKER_MONGO_URL` → 200, y primer `GET /api/v1/notifications` con JWT del admin → payload con el welcome (#548 + AC 2).

## Related Issues
- #543 (initialize que engancha), #545/#546 (wizard + guard `confirm_wipe`), #547 (modelo/repo), #548 (lectura en el primer login), #551 (visualización en el NotificationCenter)
