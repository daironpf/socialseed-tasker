# INDEX — Follow-ups de la auditoría de 296 endpoints: specs, envelope, DELETEs y errores

**Fuente:** informe de la prueba completa del backend desplegado (`tasker-api` en
`127.0.0.1:8888`, 296 endpoints, fases A/B, 2026-10-25/26) + revisión de cierre de
#595/#596/#597 y del blocker extra de `POST /issues`.
**Created:** 2026-10-26
**Status:** TODO (1/6) — #598 DONE 2026-10-26
**Numeración:** **#598–#603** (continúa tras **#597**, máximo en `.issues/done/`)

> **Nota de numeración:** los commits recientes citan `#610` (campaña de agent skills
> del 2026-10-24, sin fichero `.issues`) — si esa serie es externa (GitHub), vigilar
> la colisión cuando esta serie avance.

---

## Contexto y metodología

- **Stack probado:** `tasker-api` (8888), `tasker-board` (19001), `tasker-db-neo4j`,
  `tasker-db-pg`, `tasker-db-mongo`, `tasker-db-redis`; auth real
  (`TASKER_AUTH_ENABLED=true`, JWT vía `POST /api/v1/auth/login`).
- **Hallazgos del informe (nomenclatura del informe, NO números de `.issues`):**

  | # | Hallazgo | Estado |
  |---|---|---|
  | 1 | Blocker: `POST /issues` → 500 (pipeline de data-quality con kind sin soporte) | **CERRADO** — commit `a952a3b`, verify 10/10 |
  | 2 | Specs de petición incompletos (secret/deployment/registry/chat) | Código listo → cierre en **#598** |
  | 3 | Envelope inconsistente (6 superficies en plano) | Código listo → cierre en **#598** |
  | 4 | Semántica engañosa de los 400 | → **#599** |
  | 5 | DELETEs faltantes (dq rules, registry, deployments) | Código listo → cierre en **#598** |
  | 6 | `GET /secrets` colección → 405 | → **#600** |

- **Tanda 2 (esta serie):** hallazgos #2/#3/#5 tienen el código completo y **gates en
  verde** (2026-10-26: pytest **1690/62/0**, mypy **1053** ≤1100, ruff **1239** =
  baseline, vitest **467/467**, eslint 0, build ✓) pero **sin rebuild ni commit** →
  issue **#598**.
- **Diferidos explícitos** (registrados como fuera de alcance en el informe):
  envelope de `/auth/me` por su consumidor frontend → **#601**; cableado UI de los
  DELETE de #596 → **#602**; re-corrida del smoke (checklist de la campaña anterior +
  nota de #595) → **#603**.
- **Limite de alcance:** `POST /webhooks/receive` conserva su cuerpo de ingress
  externo con HMAC (sin envelope) — **por diseño, no deuda**.

## Issue Index

| # | Issue | Priority | Type | Status |
|---|---|---|---|---|
| #598 | Cierre de follow-ups: rebuild, verificación en vivo y commit (specs, envelope, DELETEs) | HIGH | infra / quality | DONE |
| #599 | Semántica engañosa de los 400 (not-found→400, ids→VALIDATION_ERROR, HTTPException sin envelope) | MEDIUM | bug fix / backend | TODO |
| #600 | `GET /secrets` (colección) → 405: existe alta pero no listado | MEDIUM | feat / backend | TODO |
| #601 | Envelope de `GET /auth/me` + consumidor frontend `authApi.ts` | MEDIUM | bug fix / backend + frontend | TODO |
| #602 | Cablear borrado real (skills, mcp/servers, chat) en la UI + i18n EN/ES | MEDIUM | feat / frontend | TODO |
| #603 | Re-correr el smoke completo y actualizar el recuento de la auditoría | MEDIUM | test / quality | TODO |

## Orden sugerido (dependencias)

1. **#598** primero — todo lo demás se mide contra la imagen nueva (rebuild +
   verify 25/25 + commit de la tanda ya codeada).
2. **#599 → #600** — cierran los hallazgos #4 y #6 antes de la medición grande.
3. **#603** con la superficie cerrada (objetivo medible: 0 ERR / 0 TIMEOUT).
4. **#601 y #602** en paralelo — no bloquean el smoke backend.

## Descartados (por diseño, NO deuda)

- `POST /webhooks/receive`: ingress externo con HMAC — cuerpo propio, fuera del
  envelope de éxito.
- `{"detail"}` de los 401/403 del middleware: política preexistente (#593 dejó
  constancia de los tokens estáticos) — solo entra en #599 si se decide migrar el
  handler global de `HTTPException` (opción 2 de esa issue).
- Gaps de config de compose (`OPENAI_API_KEY`, `GITHUB_TOKEN`): decisión de
  despliegue, comportamiento ya cubierto por #589/#590.

## Related Done Issues

| Done | Relevante para |
|---|---|
| #595 (OpenAPI requestBody + affects) | #598 (mismo enfoque de contrato), #603 (smoke con bodies fiables) |
| #596 (DELETEs backend: skills/mcp/chat) | #602 (cableado UI), #598 (patrón de verify en vivo) |
| #597 (trío SSO → 410 Gone) | superficie del smoke (ya sin TIMEOUT) |
| #593 (guard `require_permission` + RBAC) | #600 (guard de secrets), #599 (política de errores) |
| #594 (tracebacks con `request_id` en logs) | #599 (no perder `request_id` al migrar handlers) |
| #592 (id inválido → 404, no 503) | #599 (patrón a seguir en analyze/chat) |
| #581 (orden de rutas en secrets) | #600 (orden del GET colección vs `/{name}`) |
| #578–#590 (campaña de los 500) | contexto de causas raíz ya cerradas |

## Release Checklist (backlog de esta serie)

- [x] **#598**: imagen reconstruida, `verify_followup_live.py` 25/25, commit en
      `main` (español sin tildes, ref `#598`), sección Resolución, mover a `done/`
- [ ] **#599/#600**: fixes backend con tests de contrato + verify en vivo
- [ ] **#601**: backend + `authApi.ts` + specs, gates backend y frontend
- [ ] **#602**: stores/vistas/i18n EN+ES, vitest/eslint/build
- [ ] **#603**: recuento fresco 0 ERR/0 TIMEOUT; harness versionado; artefactos en
      `artifacts/`
- [ ] Cada issue cerrada → sección `Resolución` con recuentos (patrón #595–#597) y
      fichero a `.issues/done/`
- [ ] Commit solo tras `si` explícito; mensaje en español sin tildes referenciando
      `#NNN`
