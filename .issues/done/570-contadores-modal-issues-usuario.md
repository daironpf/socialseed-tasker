# Issue #570: Contadores y modal de issues por usuario en la vista (consumo de los endpoints de #569)

## Description

`UsersView` calcula los contadores de la tarjeta ("Asignados/Creados/Completados") y el
contenido del modal "Issues de usuario" con `fetchIssues(1, 200)` + filtros en cliente por
`creator`/`assignee`/`status`:

- En real `GET /issues` tiene `limit le=100` → **422** y la vista no carga ningún contador.
- El filtrado por nombre (`creator: username`) es frágil (homónimos, renombres); la raíz PG
  exige filtrar por el **uid de `users`**.
- Toda la lista global se baja para contar 3 números.

Con #569 existen `GET /users/{id}/issues?kind=…` y `GET /users/{id}/issue-stats` indexados
por id PG — la vista debe consumirlos: contadores desde `issue-stats`, modal desde
`issues?kind=`, con estados de carga y error propios.

Mock de referencia: el modal lista `issue.title` + status/assignee del `issues.json` del
usuario y los contadores coinciden con `issues_assigned/created` de `users.json`.

## Status: DONE

## Priority: HIGH

## Component
Frontend (UsersView + usersApi + store)

## Type
feat / frontend

## Implementation
1. **`usersApi`** (o `issuesApi`): `fetchUserIssueStats(userId)` → `issue-stats`;
   `fetchUserIssues(userId, kind)` → `issues?kind=…`; unwrap de `APIResponse`, tipos
   `UserIssueStats {assigned, created, completed}` y de la issue (reutilizar `Issue`).
2. **Contadores de tarjeta**: sustituir `fetchIssues(1,200)` + filtros cliente por
   `issueStats` por usuario — decisión de carga: al montar la vista, en paralelo con
   `fetchUsers`, cacheando por id en el store (invalidar al refetch); en modo mock, mantener
   el cálculo actual (mock no expone `/users/{id}/issue-stats`) — **rama por `isMockMode()`**.
3. **Modal "Issues de usuario"**: al abrir → `fetchUserIssues(id, 'assigned'|'created'|
   'completed')` según la pestaña/filtro del modal; estados `loading` (spinner/skeleton
   patrón de la app), `error` (reintento + `common.error`) y vacío (`issues.emptyState` o
   clave existente); cerrar el modal aborta/cancela (patrón `AbortController` si ya existe en
   `client`).
4. **Errores de API**: 404 (usuario borrado) → refetch de usuarios; 503 → mensaje con detail.
5. **Tipos/limpieza**: el type `Issue` de front ya tiene `assignee/created_by` — verificar
   compatibilidad con la respuesta de #569; eliminar el uso de `fetchIssues(1,200)` de la
   vista (queda para donde realmente necesite la lista global).
6. **Tests** (obligatorios): `UsersView.spec.ts` (ampliar el de #560 o crear):
   - montar con usuarios + `issueStats` mockeados → contadores renderizados (3 números);
   - fallo de `issue-stats` → la tarjeta se ve igual sin contadores y sin excepción;
   - abrir modal → se llama `fetchUserIssues(id, kind)` y se pintan las issues; error → estado
     de error con reintentar;
   - modo mock → no se llama a los endpoints nuevos (cálculo mock intacto).

## Acceptance Criteria
- [x] La vista no llama `fetchIssues(1, 200)` en real (ya no hay 422 en real; el mock
      mantiene su lista global porque es su única fuente de contadores/modal)
- [x] Los contadores salen de `GET /users/{id}/issue-stats` indexado por id PG, con rama
      mock intacta
- [x] El modal lista las issues del usuario vía `GET /users/{id}/issues?kind=` con loading,
      vacío y error+retry
- [x] 404/503 de los endpoints nuevos degradan sin romper la vista
- [x] **Tests**: los specs listados pasan (6 en `UsersView.spec.ts`, los 4 obligatorios +
      404-refetch y pintado del modal)
- [x] Gates frontend: `lint` 0 errors / 2 warnings, `test` **356** (47 files), `build` OK,
      i18n **1703/1703** (+clave `common.retry` EN/ES)

## Files to Create
- (posible) `frontend/src/api/userIssuesApi.ts` (si no se añade a `usersApi.ts`)

## Files to Modify
- `frontend/src/api/usersApi.ts` (o nuevo módulo) + spec
- `frontend/src/views/UsersView.vue` (contadores + modal + carga)
- `frontend/src/stores/usersStore.ts` (estado de stats/modal)
- `frontend/src/views/UsersView.spec.ts`
- `frontend/src/locales/es.json` / `en.json` (solo si faltan claves de loading/estado vacío)

## Notes
- Depende de #569 (endpoints) — orden del lote: #569 → #570.
- Mantener semántica de estados idéntica a la del mock: `assigned` = != CLOSED,
  `completed` = CLOSED, calculada en el backend (#569) para no duplicar lógica en el front.

## Related Issues
- #569 (endpoints), #533 (fetchIssues actuales), #560 (spec de UsersView), #519 (IssuesView
  global, no tocada)

## Resolution

Implementado 2026-10-10 (commit pendiente de `si`), solo frontend (los endpoints de #569
ya están desplegados en `main`):

- **API**: módulo nuevo `frontend/src/api/userIssuesApi.ts` con
  `fetchUserIssueStats(userId)` → `GET /users/{id}/issue-stats` (unwrap `data.data`,
  tipo `UserIssueStats {assigned, created, completed}`) y
  `fetchUserIssues(userId, kind)` → `GET /users/{id}/issues?kind=…` (array de `Issue`,
  el type de front ya llevaba `assignee`/`created_by` — compatible sin cambios).
- **Store** (`usersStore.ts`): estado `issueStatsByUser: Record<id, UserIssueStats>`
  cacheado por id + `fetchAllIssueStats()`:
  - **mock → return temprano** (el mock no expone el endpoint; el cálculo de la vista
    se mantiene intacto);
  - omite las tarjetas `agent-studio-*` (viven en localStorage, nunca en la raíz PG —
    su 404 solo re-refetchearía la misma lista);
  - **404 → `void fetchUsers()`** (una sola vez; `fetchUsers` no dispara stats, sin
    bucle) y **fallo → `delete` de la entrada** → la tarjeta degrada al placeholder
    `—` sin excepción;
  - `pruneIssueStats()` tras cada `users.value = …` en `fetchUsers` (invalidación al
    refetch: ids que ya no existen pierden su caché).
- **Vista** (`UsersView.vue`):
  - contadores de tarjeta con **rama por `isMockMode()`**: mock = cálculo actual sobre
    `issuesStore.issues` (idéntico, sin regresiones); real = `issueStatsByUser[id]` o
    `—` si aún no hay stats o fallaron;
  - `onMounted`: `fetchUsers()` → `fetchAllIssueStats()` en real; `fetchIssues(1, 200)`
    **solo en mock** (paralelo con `fetchUsers`, como hasta ahora);
  - modal: real → `fetchUserIssues(user.id, kind)`; mock → filtro cliente actual;
    estados `loading` (spinner), **error** (`common.error` + detail + botón
    `common.retry` con `data-testid` propios) y vacío (`common.noData`); un token
    monotónico `modalRequest` invalida respuestas tardías al cerrar/cambiar (el
    `client` no tiene patrón `AbortController` — se comprobó antes de elegir);
    backdrop y X usan `closeIssuesModal` (antes el backdrop solo ocultaba el div);
    **404 del modal → `void fetchUsers()`**.
- **i18n**: clave nueva `common.retry` EN "Retry" / ES "Reintentar" (paridad
  1703/1703).
- **Tests** (`UsersView.spec.ts`, +6, total 16 en el archivo): contadores desde
  issue-stats sin llamar `fetchIssues` (AC), fallo de stats → tarjeta intacta con
  `—` y sin excepción, **404 → `fetchUsers` llamado 2 veces**, modal abre con
  `(id, 'assigned')` y pinta la issue, error del modal → estado con reintentar que
  repinta al recuperarse, y **mock mode → los endpoints nuevos no se llaman** y los
  contadores siguen calculándose en cliente (`1/0/1`).
- Gates: `lint` 0 errors / 2 warnings (baseline), `test` **356** (+6; baseline 350),
  `build` (vue-tsc + vite) OK, i18n **1703/1703** (baseline 1702 + `common.retry`).
- Warnings de consola preexistentes en el spec (inyección de router y
  `users.human`/`users.aiAgent` en `CreateUserModal`) — verificados con
  `vitest -t` en describes del #563/#566, no introducidos por esta issue.
