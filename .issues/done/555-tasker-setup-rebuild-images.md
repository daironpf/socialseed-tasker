# Issue #555: `tasker setup` reconstruye imágenes siempre (fix de despliegue obsoleto)

## Description

Causa raíz del bug de despliegue detectado al probar #552/#553: `compose_up` solo
pasaba `--build` cuando se invocaba `tasker setup --dev` (setup_command.py:146-150),
así que un `tasker setup` o `docker compose up -d` normal **reutilizaba las imágenes
viejas** — `tasker-board` hornea `frontend/dist` con `COPY dist/` y `tasker-api` hornea
el código fuente, por lo que el board servía un bundle de días atrás (las imágenes
mostraban build del 4 de octubre con el bundle local ya reconstruido). El usuario
probó contra código viejo y reportó 5 notificaciones HITL de la demo en lugar del
onboarding de #552.

## Status: DONE (2026-10-06)

## Priority: HIGH

## Component
CLI / setup + Docker

## Type
bug fix / infraestructura de despliegue

## Implementation
1. **`setup_command.py` → `compose_up(compose_file, frontend_port)`:** la firma pierde el parámetro `dev` y el comando es siempre `["docker", "compose", "up", "-d", "--build"]`; docstring explica el porqué (imágenes que hornean dist/fuente + caché de Docker por capas).
2. **`setup_command`:** el flag `--dev` se mantiene **aceptado y deprecado** (sin breaking change para docs/scripts que lo usen): help nuevo + aviso `[warning]'--dev' is deprecated: images are always rebuilt now.[/warning]` cuando se pasa.
3. **Tests (`tests/cli/test_setup_command.py`, 13 → 13):** `test_setup_happy_path` ahora exige `--build` también con `dev=False`; `test_setup_dev_rebuilds_images` renombrado a `test_setup_always_rebuilds_images` (verifica `--build` con `dev=True` + el aviso de deprecación).

## Acceptance Criteria
- [x] `tasker setup` (sin flags) ejecuta `docker compose up -d --build` → imágenes reconstruidas si el código/dist cambió
- [x] `tasker setup --dev` sigue funcionando (flag aceptado) y muestra el aviso de deprecación
- [x] Caché de Docker: rebuild sin cambios de contexto es rápido (no se fuerza `--no-cache` ni `--force-recreate`)
- [x] Gates: `ruff` 0 err nuevo (baseline 1011), `mypy` ≤1152 (baseline 1152), `pytest -q` **1329 passed + 3 preexistentes** sin regresión, `tests/cli/test_setup_command.py` 13/13
- [x] Sin cambios de frontend ni de API

## Files to Create
- `.issues/done/555-tasker-setup-rebuild-images.md` — este fichero

## Files to Modify
- `src/socialseed_tasker/cli/setup_command.py` — `compose_up` siempre `--build`, `--dev` deprecado
- `tests/cli/test_setup_command.py` — happy path con `--build`, test de deprecación
- `features.md` — §69 (fila `tasker setup CLI`)
- `.issues/to-do/INDEX-notas-v6-notifications-mongodb.md` — fila + follow-up #555

## Notes
- **Verificado en vivo:** antes del fix, `docker compose ps` mostraba imágenes con build del 2026-10-04 mientras el bundle local ya era nuevo; el rebuild manual con `--build` sirvió el bundle correcto (`index-Blyj4Sur.js` y luego `index-CNHGmwJq.js`).
- **`docker compose up` ya construía imágenes ausentes** — el fallo era solo el rebuild con código nuevo; con caché el coste de añadir `--build` siempre es ~segundos por servicio sin cambios.
- **Alcance:** solo `tasker setup`; un `docker compose up -d` manual sigue sin `--build` (documentado en el docstring/issue para no tocar otros flujos).
- **No rompe nada:** no hay scripts ni docs internos que ejecuten `tasker setup --dev` (grep `--dev` solo en `setup_command.py`); las únicas referencias documentales se actualizaron en features.md.

## Related Issues
- #542 (comando `tasker setup` original), #552/#553 (bugs enmascarados por imágenes viejas), #554 (follow-up anterior)
