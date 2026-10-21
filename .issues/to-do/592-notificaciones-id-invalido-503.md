# Issue #592: Notificaciones con id no-ObjectId → 503 "store unavailable" en vez de 404

## Description

`PATCH /notifications/{id}/read` y `DELETE /notifications/{id}` devuelven **503
"notifications store unavailable"** cuando el id no es un ObjectId de Mongo válido —
mintiendo sobre el estado de la tienda (que funciona perfectamente).

Verificado en vivo contra el servidor real (uvicorn, `127.0.0.1:8888`, 2026-10-21,
con JWT admin):

```
PATCH /api/v1/notifications/aaaaaaaaaaaaaaaaaaaaaaaa/read  -> 404 {"detail":"notification not found"}   (ObjectId de 24 hex: OK)
DELETE /api/v1/notifications/aaaaaaaaaaaaaaaaaaaaaaaa      -> 404 {"detail":"notification not found"}   (OK)
PATCH /api/v1/notifications/not-a-real-id/read             -> 503 {"detail":"notifications store unavailable"}   (BUG)
DELETE /api/v1/notifications/not-a-real-id                 -> 503 {"detail":"notifications store unavailable"}   (BUG)
POST /api/v1/notifications/mark-all-read                  -> 200   (OK)
POST /api/v1/notifications/clear-all                      -> 200   (OK)
GET  /api/v1/notifications                                -> 200   (OK)
```

**Causa raíz**: el repositorio Mongo convierte el id con `ObjectId(notification_id)`
sin validar el formato; para basura (`not-a-real-id`) PyMongo lanza `InvalidId:
invalid document id: ...`, que el repo envuelve en `NotificationStoreError`
(`infrastructure/mongo/notification_repository.py:47`), y el router lo traduce con
`_store_error(...)` a **503** (`routers/notifications.py:68-70`). El logger del router
sí deja la causa real:

```
notifications mark read degraded: invalid document id: nonexistent-id
notifications delete degraded: invalid document id: nonexistent-id
```

O sea: un **dato de entrada malo** se clasifica como **indisponibilidad del
servicio**. Los clientes (y el smoke de auditoría, que reportó `PATCH/DELETE
notifications` como ERR en run4) lo interpretan como caída de Mongo.

Nota: `POST /notifications/clear-all` en el mismo run4 también salió 503 con
`clear notifications failed: Event loop is closed` — verificado ahora que es
**artefacto del TestClient** (en uvicorn real → 200), no un bug de producción; queda
documentado para no "arreglarlo".

## Status: OPEN

## Priority: MEDIUM

## Component
Backend / Notificaciones (repo Mongo + router)

## Type
bug fix / backend

## Implementation

1. **Validar el id antes de tocar Mongo** (`infrastructure/mongo/notification_repository.py`
   y/o `routers/notifications.py`):
   - Si `notification_id` no matchea `^[0-9a-fA-F]{24}$` → tratarlo como **no
     encontrado**: devolver `None`/`False` del repo para que el router responda
     `404 notification not found` (el router ya tiene ese camino en
     `notifications.py:255-256` y `279-280`).
   - `NotificationStoreError` debe reservarse para fallos reales de Mongo
     (conexión/timeout/permisos) — el `InvalidId` de un input no lo es.
2. **Alternativa equivalente**: envolver solo `InvalidId` en el repo y devolver
   "not found" sin subir `NotificationStoreError` (try/except específico en vez del
   catch-all actual).
3. **Tests** (`tests/api/`, patrón de #548 con repo fake):
   - `test_mark_read_invalid_id_returns_404` (id no-ObjectId → 404, nunca 503).
   - `test_delete_invalid_id_returns_404`.
   - `test_mark_read_store_failure_returns_503` (fake que lanza error real de Mongo →
     503 — el 503 sigue existiendo para lo que sí es).
   - Id ObjectId válido inexistente → 404 (regresión del caso ya correcto).

## Acceptance Criteria
- [ ] `PATCH /notifications/{id}/read` y `DELETE /notifications/{id}` con id no-ObjectId
      → **404** (ya no 503)
- [ ] 503 sigue reservado para fallos reales del store (test con error simulado de
      Mongo)
- [ ] Id ObjectId válido inexistente → 404 (sin cambios)
- [ ] `GET`, `mark-all-read`, `clear-all` siguen en 200 (verificado hoy sobre
      uvicorn real)
- [ ] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

## Files to Modify
- `src/socialseed_tasker/infrastructure/mongo/notification_repository.py` (línea 47 /
  validación de ObjectId)
- `src/socialseed_tasker/infrastructure/web_api/routers/notifications.py` (68-70, 255,
  279)
- `tests/api/` — tests de ids inválidos

## Related Issues
- #548 (router REST original de notificaciones), #547 (repo Mongo), #593/#594 (otros
  códigos de estado engañosos), #590 (500 engañoso de AI)

## Notes
- **Repro**: login → `curl -X PATCH .../api/v1/notifications/not-a-real-id/read -H
  "Authorization: Bearer <jwt>"` → 503; con 24 hex → 404.
- El smoke de auditoría clasifica 401/403/404 como GRACE — por eso este bug solo
  salió a la luz con la repro dirigida: el 503 esconde un 404 esperable.
