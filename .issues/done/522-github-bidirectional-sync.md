# Issue #522: Bidirectional Real Sync with GitHub

## Description

El widget de sincronización con GitHub (`GitHubSyncCard`) simula los estados (SYNCED / PENDING_PUSH / ERROR). Se debe integrar la sincronización bidireccional real vía Webhooks de GitHub para actualizar el estado de issues, pull requests y comentarios, y manejar la resolución de conflictos cuando una issue se actualiza simultáneamente en GitHub y en Tasker.

Origen: `notas.md` → [ISSUE-06] Sincronización Bidireccional Real con GitHub (→ #522).

## Status: DONE (2026-09-28)

## Priority: MEDIUM

## Component
Frontend / Integration / GitHub / Sync

## Type
feat / integration

## Implementation
1. **Servicio de merge 3-way:** nuevo `application/github_sync.py` con snapshot `github_base` (último estado conocido de GitHub) para detectar conflictos por campo sin confiar en timestamps: conflicto solo cuando local≠base, remote≠base y local≠remote; estados `SYNCED` / `CONFLICT` / `ERROR` con `github_conflict{fields, local, remote, detected_at}` y `github_error`.
2. **Webhooks bidireccionales:** `POST /api/v1/webhooks/github` valida `X-Hub-Signature-256` (HMAC-SHA256 con `GITHUB_WEBHOOK_SECRET`, 401 sin firma) y procesa `issues`, `issue_comment` y `pull_request` (aplicar edición remota, añadir comentarios con autor de GitHub — el eco de Tasker se omite con el marcador `<!-- socialseed-tasker -->` —, PR `pr_url`/`pr_number` y cierre automático al hacer merge); la ruta queda exenta del middleware de API key (GitHub no puede adjuntarla, la autenticación es la firma); logs de entrega con campo `detail`.
3. **Push local → GitHub:** `PATCH /issues/{id}` y `POST /issues/{id}/close` persisten y luego empujan los campos espejo (title, description, status, labels); sin `GITHUB_TOKEN`/`GITHUB_REPO` degrada a estado `ERROR` visible sin fallar la petición.
4. **Resolución + resync:** `POST /issues/{id}/github-sync/resolve` (`local` empuja local, `remote` aplica remoto, `merge` aplica los valores enviados; 400 sin conflicto) y `POST /issues/{id}/github-sync` fuerza re-sync (pull + merge); `link-github` guarda metadata + snapshot base y `unlink-github` limpia los nueve campos.
5. **UI real:** `GitHubSyncCard` reescrito contra la API (sin `setTimeout`): badge CONFLICT, panel de error real, enlace a PR, último sync null-safe y panel de conflicto con valores Tasker vs GitHub por campo y acciones Keep local / Keep remote / Merge (textareas editables) vía `githubSyncApi.ts`; `IssueDetailView` refresca en `sync:updated` y por SSE (`GET /issues/{id}/github-sync/stream`, eventos `sync`) en modo real; `GitHubSyncHealth` con bucket CONFLICT.
6. **Offline queue (#515):** el push ocurre en el servidor sobre los mismos endpoints PATCH/close que la cola reintenta, así que las mutaciones offline fluyen a GitHub al reconectar sin cola separada.
7. i18n + build + smoke con backend.

## Acceptance Criteria
- [x] `GitHubSyncCard` shows the real sync state (no simulated SYNCED/PENDING_PUSH/ERROR)
- [x] Webhook-driven, bidirectional updates for issues, pull requests and comments
- [x] Conflict resolution UI when an issue changes in GitHub and Tasker simultaneously
- [x] Actions made offline integrate with the #515 queue
- [x] i18n support (EN + ES)
- [x] `npm run build` passes

## Verification (2026-09-28)

- Backend: `ruff check src/` 1011 errores (baseline 1012), `mypy src/` 1158 errores / 133 ficheros (baseline 1159/133), `pytest -k "not integration"` 1040 passed / 3 fallos preexistentes; nuevo `tests/unit/test_github_sync.py` 24/24.
- Frontend: `npm run lint` 0 errores (2 warnings preexistentes), `npm test` 119/119 (nuevo `GitHubSyncCard.spec.ts` 6 tests), `npm run build` green (vue-tsc + vite).
- Docker (:19001): `GITHUB_WEBHOOK_SECRET` añadido a `docker-compose.yml`, `tasker-api` + `tasker-board` reconstruidos, 4 contenedores healthy; smoke 28/28 → bundle sirve la nueva i18n de conflicto, webhook secret configurado, webhook sin firma 401, `link-github` → SYNCED, edición remota aplicada sin conflicto, edición local → ERROR elegante sin token, segunda edición remota → CONFLICT con valores local/remote, resolve `remote` → SYNCED, resolve `local` conserva el título local y muestra el error de push, force re-sync degrada a ERROR, `issue_comment` añade el comentario, logs de entrega con `detail`, stream SSE emite `event: connected`.

## Files to Create
- `src/socialseed_tasker/application/github_sync.py`
- `frontend/src/api/githubSyncApi.ts`
- `frontend/src/components/issue/GitHubSyncCard.spec.ts`
- `tests/unit/test_github_sync.py`

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/{webhook,issues,realtime,helpers}.py` — receiver firmado, push/pull/resolve, stream SSE, representación
- `src/socialseed_tasker/infrastructure/web_api/{schemas.py,app.py}` — modelos GitHubSync/GitHubConflict/GitHubResolve + exención de auth para el webhook
- `src/socialseed_tasker/{domain/entities.py,infrastructure/neo4j_impl/{shared,issue_mixin}.py,infrastructure/github_adapter.py}` — campos github en entidad/Nodo + `is_configured`
- `frontend/src/components/issue/GitHubSyncCard.vue` — estado real + conflicto
- `frontend/src/views/IssueDetailView.vue` — SSE + refetch
- `frontend/src/components/dashboard/GitHubSyncHealth.vue` — bucket CONFLICT
- `frontend/src/{types/index.ts,api/client.ts,api/mockApi.ts,locales/en.json,locales/es.json}`, `frontend/src/views/GraphView.vue`, `mock-api/server.py`, `docker-compose.yml`
- `features.md` — §67

## Related Issues
- #88 (GitHub API Adapter), #89 (Bidirectional Webhook Listener), #93 (GitHub Issue Mapper), #95 (Webhook Signature Validator), #307 (Webhook Receiver & Event Bus), #500 (GitHub Sync Widget on Issue Detail), #515 (Offline Queue)
