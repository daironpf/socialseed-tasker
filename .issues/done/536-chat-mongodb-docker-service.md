# Issue #536: Servicio Docker MongoDB para chat

## Description

La UI de chat (`ChatView`, `FloatingChat`, `chatStore`) funciona solo con fixtures en memoria y respuestas simuladas: no hay persistencia real de conversaciones ni mensajes. La ÉPICA "Chat en Tiempo Real y Persistencia MongoDB" de `notas.md` pide añadir un contenedor de MongoDB al `docker-compose.yml` exclusivo para la persistencia del chat del proyecto Tasker, siguiendo el patrón de servicios híbridos ya introducido en #525 (PostgreSQL/Redis con `TASKER_*` y fallback seguro).

Origen: `notas.md` → Épica Chat en Tiempo Real y Persistencia MongoDB · Issue #1 (→ #536).

## Status: DONE (2026-10-01)

## Priority: HIGH

## Component
Backend / Infrastructure / Chat

## Type
infra / devops

## Implementation
1. **Servicio `tasker-db-mongo`:** nuevo bloque en `docker-compose.yml` con la imagen `mongo:7.0-alpine`, dentro de la red del proyecto y con healthcheck (`mongosh --quiet --eval "db.adminCommand('ping')"`).
2. **Puerto host:** mapeado opcionalmente a `127.0.0.1:27017` (rango no reservado por Hyper-V en Windows); también alcanzable internamente como `tasker-db-mongo` desde `tasker-api`.
3. **Volumen persistente:** volumen nombrado `tasker-mongo-data` montado en `/data/db` para evitar pérdida de datos entre reinicios.
4. **Variable de entorno:** `TASKER_MONGO_URL=mongodb://tasker-db-mongo:27017/tasker_chat` inyectada a `tasker-api` (convención `TASKER_*` de #525).
5. **Lectura con fallback:** `config/storage.py` expone la URL de Mongo con el mismo patrón que Redis/Postgres: si la env no está definida o el servicio no responde, la app continúa degradada con log y sin romper el arranque (los endpoints de chat devolverán el estado controlado correspondiente).
6. **Documentación:** README/compose anotado con el nuevo servicio y la env.

## Acceptance Criteria
- [x] Servicio `tasker-db-mongo` configurado en `docker-compose.yml` con la imagen `mongo:7.0` (el tag `mongo:7.0-alpine` no existe en Docker Hub: la imagen oficial no publica variantes alpine para 7.0 — ver Verification) en la red del proyecto
- [x] Expuesto opcionalmente al host en `127.0.0.1:27017` o comunicado internamente con `tasker-api`
- [x] Volumen persistente `tasker-mongo-data` configurado para evitar pérdida de datos
- [x] Variable `TASKER_MONGO_URL=mongodb://tasker-db-mongo:27017/tasker_chat` leída mediante `config/storage.py` con fallback seguro si no está disponible
- [x] `docker compose up` levanta el stack completo sin regresiones y gates backend en baseline

## Verification
- **Compose:** nuevo servicio `tasker-db-mongo` (`mongo:7.0`, healthcheck `mongosh db.adminCommand('ping')`, límite de memoria 512M) en la red `tasker-net`, volumen nombrado `mongo-data`, puerto `127.0.0.1:27017:27017`; `tasker-api` gana env `TASKER_MONGO_URL=mongodb://tasker-db-mongo:27017/tasker_chat` y `depends_on: tasker-db-mongo (service_healthy)`; `docker compose config --quiet` OK.
- **Desviación justificada:** la ÉPICA pedía `mongo:7.0-alpine`, pero la imagen oficial `library/mongo` **no tiene tags alpine para 7.0** (0 tags `*alpine*` en Docker Hub; solo jammy/nanoserver/windowsservercore). Se usa `mongo:7.0` manteniendo la versión 7.0 requerida.
- **`config/storage.py`:** `get_mongo_url()` → `None` sin la env (fallback seguro, la app no depende de Mongo) y la URL completa con `TASKER_MONGO_URL` ✓.
- **Smoke (stack compose):** `tasker-db-mongo` → `healthy`, `mongosh` ping → `{ ok: 1 }`, volumen `socialseed-tasker_mongo-data` creado, `tasker-api` recreado → `healthy` con `printenv TASKER_MONGO_URL` = `mongodb://tasker-db-mongo:27017/tasker_chat`, `GET /health` → `status: healthy` ✓.
- **Gates:** `ruff check src/` = **1011** (baseline) ✓ · `mypy src/` = **1152/133** (caché fresco, idéntico a baseline; el conteo 1153/134 fue caché incremental obsoleto) ✓ · `pytest -q` = **1209 passed / 27 skipped / 3 failed** (solo los 3 preexistentes: `test_delivery_retries`, 2× `test_tasks_unit`; los 3 de `test_mock_server_unit` pasaron en esta corrida) ✓.
- **Docs:** `README.md` no tiene tabla de topología (no aplica); fila `tasker-db-mongo` añadida en `features.md` §1 *Container topology*.

## Files to Modify
- `docker-compose.yml` — servicio `tasker-db-mongo`, volumen `tasker-mongo-data`, healthcheck y env `TASKER_MONGO_URL` en `tasker-api`
- `src/socialseed_tasker/config/storage.py` — lectura de `TASKER_MONGO_URL` con fallback seguro
- `README.md` — topología de contenedores (nuevo servicio)

## Related Issues
- #525 (Docker Compose híbrido PostgreSQL + Redis, patrón `TASKER_*`), #533 (health multi-dependencia, candidato a sumar Mongo después), #527 (Auth Store en PostgreSQL)
