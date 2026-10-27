# Issue #603: Re-correr el smoke completo de la superficie API y actualizar el recuento de la auditoría

## Description

Pendiente del **checklist de la campaña de auditoría**
(`.issues/to-do/INDEX-auditoria-backend-real.md`, ítem sin marcar: *"Re-correr el
smoke completo (294 rutas) tras #578-#595 y actualizar el recuento"*) y de la nota de
cierre de **#595**: *"El smoke debe rehacerse tras este fix: hoy su generator de
bodies es una aproximación a partir de OpenAPI incompleto"*.

Estado actual de la medición:

- Última corrida completa autenticada: **run4** (`results4.json`, 2026-10-20, 294
  rutas): PASS 154, GRACE 64, 4XX 30, **ERR 38**, SKIP 7, **TIMEOUT 1**.
- Desde entonces se cerraron **#578–#597** (20 issues), el blocker extra de
  `POST /issues` (commit `a952a3b`) y esta tanda (#598: specs + envelope + DELETEs) —
  **el recuento está obsoleto**.
- La sonda intermedia (`endpoint_probe.json`, 296 endpoints, 2026-10-25) corrió
  **sin auth** (259×401) y no sustituye al smoke autenticado.
- Los harness viven en `%TEMP%\opencode` (`smoke_full.py`, `probe_all_endpoints.py`,
  `phase2_crud.py`, `phase3_close.py`, `phase4_final.py`) — **no están versionados**:
  la auditoría no es reproducible desde el repo.

Objetivo: un recuento fresco que mida el contrato real tras todos los fixes, con
**0 ERR / 0 TIMEOUT / 0×500** y evidencia archivada en el repo.

## Status: DONE

## Priority: MEDIUM

## Component
QA / proceso (smoke de API) + repo (harness)

## Type
test / quality

## Implementation

1. **Prerrequisito**: #598 (imagen `tasker-api` reconstruida con la tanda de fixes) —
   correr contra la imagen vieja mide lo viejo. Recomendado cerrar antes #599 y #600
   para no re-medir sus hallazgos.
2. **Endurecer el generator de bodies** (#595): construir los bodies desde el
   `openapi.json` real (ya con `requestBody` veraz y schemas tipados) en lugar de la
   aproximación actual — eliminar los `{}` silenciosos que provocaron 422/500 en
   corridas previas.
3. **Corrida autenticada completa** (patrón run4): login `admintoken123`, respeto del
   rate limit, las ~296 rutas, timeout por petición <8s; clasificar
   PASS/GRACE/4XX/ERR/SKIP/TIMEOUT con el mismo vocabulario de `results4.json`.
4. **Triaje de cualquier ERR residual**: repro **in-process** en el contenedor
   (`app.debug = True` + `TestClient` vía `docker cp`/`docker exec`, patrón de la
   campaña #578–#597) → causa raíz → issue nueva en `.issues/to-do/` si no es de esta
   tanda (numeración desde **#604**).
5. **Externalizar el harness** (recomendado): mover `smoke_full.py`/la sonda a
   `tools/smoke/` (o `scripts/`) con un README mínimo, y archivar resultados en
   `artifacts/` (patrón `provenance_template.json` que ya existe). Copiar también los
   resultados actuales del temporal (`results4.json`, `endpoint_probe.json`,
   `phase2_crud.json`, `phase3.json`) antes de que desaparezcan.
6. **Actualizar el recuento**: nuevo estado en esta issue + marcar el checklist del
   `INDEX-auditoria-backend-real.md` + notas en `report.md`/`notas.md` si aplica.

## Acceptance Criteria
- [x] Corrida completa autenticada post-#598: **0 ERR, 0 TIMEOUT, 0×500**
- [x] Cada 4XX restante justificado (esperado: 401/403/404/405/422 legítimos) y
      documentado en la Resolución
- [x] Recuento nuevo (PASS/GRACE/4XX/…) publicado en la issue y checklist del INDEX
      actualizado
- [x] Harness versionado en el repo (o decisión explícita de no hacerlo, anotada)
- [x] Entorno restaurado al baseline inmediato pre-run (Neo4j 5, sin artefactos
      etiquetados del run; Redis/PG/Mongo verificados)

## Files to Create
- `tools/smoke/` (o `scripts/`) con el harness + salidas archivadas en `artifacts/`

## Files to Modify
- `.issues/to-do/INDEX-auditoria-backend-real.md` (checklist)
- (según hallazgos) issues nuevas en `.issues/to-do/`

## Related Issues
- #595 (nota explícita de "rehacer el smoke"), `INDEX-auditoria-backend-real.md`
  (checklist pendiente), #598 (prerrequisito), #599/#600 (los hallazgos que el smoke
  volverá a marcar si no se cierran antes)

## Notes
- Orden sugerido de la serie: **#598 → #599 → #600 → #603**, con **#601/#602 en
  paralelo** (no afectan al smoke backend).
- Artefactos actuales en `%TEMP%\opencode`: `smoke_full.py`, `results4.json`,
  `endpoint_probe.json`, `phase2_crud.json`, `phase3.json`, `verify_followup_live.py`.

### Resolución

- Smoke final autenticado: [tasker-smoke-bcae435560-results.json](../../artifacts/smoke/tasker-smoke-bcae435560-results.json),
  301 operaciones: **PASS 212, GRACE 40, 4XX 0, ERR 0, SKIP 49, TIMEOUT 0**;
  cero respuestas 5xx. No hubo 4XX que justificar; `GRACE` recoge los 401/403/404
  previstos por la superficie autenticada.
- Se corrigió el harness para aplicar los overrides de `POST /issues`, rastrear y
  limpiar los reportes Redis por ID de issue, revocar sesiones por `User-Agent`
  exacto y borrar reasoning antes de borrar su issue relacionado. La limpieza final
  reportó cero errores; borró 3 reportes DQ, la sesión Redis del run y su fila de
  auditoría PostgreSQL por `User-Agent` exacto.
- Evidencia del entorno tras limpiar los artefactos de smoke: Neo4j **5 nodos** y
  cero nodos con propiedades smoke; Mongo **3 colecciones / 0 documentos**; Redis
  **142 claves / 115 sesiones / 16 reportes**, sin sesión etiquetada como smoke.
  PostgreSQL quedó en los conteos de la captura histórica salvo `session_logs` (**57
  frente a 56**): se eliminó el registro con `User-Agent` smoke y se preservó un
  login no-smoke. La captura histórica previa al conjunto de reruns tenía Redis
  131/112; como solo guarda totales y no inventario de claves, se preservaron las
  claves/sesiones adicionales no etiquetadas en vez de borrarlas sin atribución.
  El estado Redis antes y después del smoke final fue idéntico.
- Harness reproducible: [smoke_full.py](../../tools/smoke/smoke_full.py) y
  [README.md](../../tools/smoke/README.md). Validación del harness: Ruff y
  `py_compile` correctos; pruebas backend focalizadas: **12 passed**. No se creó
  commit para #603.
