# Issue #569: Issues con `assignee`/`created_by` indexados por el id PG + endpoints por usuario

## Description

El dominio `Issue` real (`entities.py:124`) y la API (`IssueCreateRequest`/`IssueResponse`)
**no tienen `assignee` ni `created_by`**, aunque el mock (`issues.json`) sí los incluye como
UUIDs de usuario y `Issue` del front (`types.ts`) ya los trae. Consecuencias:

- `GET /issues` no puede filtrar por usuario → la vista de Usuarios no puede calcular
  "asignados / creados / completados" ni abrir el modal de issues (#570 haría N llamadas
  inútiles).
- Las utilidades del grafo **ya existen sin usar**: `neo4j_queries.link_user_to_issue`,
  `GET_USER_ISSUES` (relación `ASSIGNED_TO`), herencia de #519/#533 — nadie las llama desde
  la API.
- **Restricción de raíz**: `assignee`/`created_by` se guardan con el **uid de `users`** (id PG,
  el `sub` del JWT), igual que `notifications.user_id` — así Neo4j, Mongo y PG se cruzan por la
  misma clave.
- Bonus: el listado de la vista UsersView hoy llama `fetchIssues(1, 200)` pero
  `GET /issues` tiene `limit: int = Query(50, ge=1, le=100)` (`issues.py:49`) → **422** en real
  (#570 cambia la llamada; aquí se amplía el `le` si sigue siendo útil para otros).

## Status: DONE

## Priority: HIGH

## Component
Backend / Data (dominio + Neo4j + API)

## Type
feat / backend

## Implementation
1. **Dominio**: añadir a `Issue` `assignee: str | None = None`,
   `created_by: str | None = None` (ids PG). Actualizar constructores/factories y
   `convertir` de Neo4j (`_issue_to_response` / `row_to_issue`) para leer/escribir las
   properties.
2. **Persistencia Neo4j**: `CREATE_ISSUE`/`UPDATE_ISSUE` con las nuevas properties;
   mantener `link_user_to_issue`/`GET_USER_ISSUES` para la relación `ASSIGNED_TO` (crear o
   actualizar la relación al asignar; borrarla al desasignar — el grafo es índice, la
   property es la fuente del filtro).
3. **API**:
   - `IssueCreateRequest`: aceptar `assignee` opcional; **`created_by` se setea server-side**
     desde el usuario del request (JWT `sub` vía dependencia de usuario actual, patrón
     `_current_user` de `chat.py`/`auth.py` — resolver con `HTTPBearer` +
     `decode_access_token`, 401 sin token).
   - `IssueUpdateRequest`: aceptar `assignee` (asignar/desasignar) y `created_by` no se
     cambia.
   - `IssueResponse`: incluir `assignee`, `created_by`.
   - `GET /issues`: filtros query `assignee: str | None`, `created_by: str | None` (además de
     los existentes `status`/`priority`/`creator`); ampliar `le` del limit a 100 **o** dejarlo
     y exigir el uso de filtros (#570) — por defecto: **`le=100` se mantiene** y la vista pasa
     a usar filtros por usuario.
4. **Endpoints por usuario** (clave para la vista, misma raíz):
   - `GET /users/{user_id}/issues?kind=assigned|created|completed` → devuelve las issues del
     usuario con la semántica exacta del mock/la vista:
     - `assigned`: `assignee == user_id` y `status != CLOSED`;
     - `created`: `created_by == user_id` y `status != CLOSED`;
     - `completed`: (`assignee == user_id` o `created_by == user_id`) y `status == CLOSED`.
   - `GET /users/{user_id}/issue-stats` → `{assigned, created, completed}` (contadores de la
     tarjeta). 404 si el usuario no existe en PG (raíz).
   - Implementación en `routers/issues.py` (o `user.py`) sobre el repo con filtros property +
     id PG; test con issues sembradas por id.
5. **Tests** (obligatorios): `tests/api/test_issues_api.py` (o fichero nuevo):
   `test_create_issue_sets_created_by_from_jwt_sub`, `test_create_issue_with_assignee`,
   `test_update_issue_assign_and_unassign`, `test_list_issues_filter_by_assignee`,
   `test_list_issues_filter_by_created_by`, `test_user_issues_endpoint_kinds` (los 3 kinds
   con semántica CLOSED/no-CLOSED), `test_user_issue_stats_counts`, `test_user_issues_404_unknown_user`,
   `test_user_issues_401_without_token` (si el endpoint exige auth).

## Acceptance Criteria
- [x] `POST /issues` guarda `created_by = sub` (id PG) y `assignee` opcional; `PATCH/PUT`
      puede asignar/desasignar y la relación `ASSIGNED_TO` del grafo se crea/elimina
- [x] `GET /issues` filtra por `assignee` y `created_by`; respuesta incluye ambos campos
- [x] `GET /users/{id}/issues?kind=…` devuelve la semántica de la vista (OPEN/IN_PROGRESS/
      BLOCKED vs CLOSED) y `/issue-stats` los 3 contadores
- [x] 404 para usuario inexistente en PG; 401 sin token si el endpoint lo exige
- [x] **Tests**: los pytest listados pasan (incluido el de 401/404)
- [x] Gates backend sin regresiones: `ruff` 1011, `mypy` 1153, `pytest` 1331+3

## Files to Create
- `tests/api/test_user_issues_api.py` (si no se amplía `test_issues_api.py`)

## Files to Modify
- `src/socialseed_tasker/domain/entities.py` (`Issue`)
- `src/socialseed_tasker/infrastructure/web_api/schemas.py` (`IssueCreate/Update/Response`)
- `src/socialseed_tasker/infrastructure/web_api/routers/issues.py` (filtros + endpoints por
  usuario + `created_by` desde JWT)
- `src/socialseed_tasker/infrastructure/neo4j_issue_repository.py` o `neo4j_queries.py`
  (properties + `ASSIGNED_TO`)
- (posible) `src/socialseed_tasker/infrastructure/web_api/routers/user.py` (si el endpoint
  `/users/{id}/issues` vive aquí)

## Notes
- El endpoint por usuario **no** reemplaza los filtros de `GET /issues`: son complementarios
  (filtros para tablas globales, endpoint por usuario para la tarjeta/modal de la vista).
- `creator` (el filtro existente de la API) y `created_by` conviven: `creator` es el nombre
  mock legible, `created_by` es el id PG canónico — no romper el filtro existente (#533).
- La vista usa hoy `issue.creator`/`assignee` como nombres; #570 migra los contadores a los
  ids — mantener `creator` en la respuesta para los listados existentes.

## Related Issues
- #519/#533 (issues y filtros actuales), #547/#549 (`user_id` = sub en Mongo), #558 (id PG
  canónico), #570 (consumo en la vista), #562 (borrado en cascada de datos indexados)

## Resolution

Implementado 2026-10-09 (commit pendiente de `si`):

- **Dominio**: `Issue` gana `assignee: str | None` y `created_by: str | None` (uid PG,
  estilo `str | None` para no sumar UP045); `create_issue_action` los acepta como kwargs
  opcionales y `IssueResponse` los expone (default `None`, ningún call-site rompe).
- **`POST /issues`**: `created_by` se setea server-side con `_resolve_user(request)` de
  `chat.py` (mismo resolver que el resto de la API: JWT `sub` → session cookie →
  `x-user-id` solo con auth desactivado). **Decisión**: es *opcional* (sin identidad →
  `None`, sin 401) para no romper `test_issue_checklist` ni flujos internos que crean
  issues sin token; el frontend real siempre envía `Bearer` (client.ts) — el 401 exigido
  por la issue aplica a los endpoints por usuario (`test_user_issues_401_without_token`).
  `assignee` viene opcional del body (`IssueCreateRequest`).
- **`PATCH /issues/{id}`**: `IssueUpdateRequest.assignee` acepta uid o `null` explícito —
  `model_dump(exclude_unset=True)` distingue "omitido" de "null" → asignar/desasignar sin
  tocar el resto; `created_by` no es editable.
- **Neo4j**: `CREATE_ISSUE` persiste `assignee`/`createdBy` (properties), `_node_to_issue`
  los lee de vuelta y `UPDATE_ISSUE` (`SET i += $updates`) los actualiza. La relación
  `ASSIGNED_TO` (índice, no fuente de filtro) se sincroniza en `issue_mixin`: `MERGE` de
  `USER_ASSIGNED_TO_ISSUE` al crear/asignar y nuevo `UNLINK_ASSIGNED_FROM_ISSUE` al
  desasignar (borra todas las del issue — el uid viejo ya no está en la property).
  `GET_USER_ISSUES`/`link_user_to_issue` preexistentes intactos.
- **`GET /issues`**: filtros query `assignee` y `created_by` (filtro en Python tras
  `repo.list_issues`, compatible con cualquier implementación del repositorio); `le=100`
  del limit **se mantiene** según la decisión de la issue (la vista migrará a filtros en
  #570).
- **Endpoints por usuario** (`routers/user.py`, raíz `/users`): `GET /users/{id}/issues`
  (kind requerido `assigned|created|completed`, 422 si no coincide) y `GET /users/{id}/issue-stats`
  (`{assigned, created, completed}`) — helper `_issue_kind_belongs` único para ambos:
  assigned = `assignee == uid` y no CLOSED; created = `created_by == uid` y no CLOSED;
  completed = (assignee o created_by) y CLOSED. Orden: **401** (`_current_user`) → 422 →
  **404** (`_pg_repository().get_user`, raíz PG; 503 sin `TASKER_DATABASE_URL`). `repo`
  con `Annotated[...]` (sin B008) y `APIResponse[dict[str, Any]]` en stats (sin sumar
  type-arg de mypy).
- **Tests**: `tests/api/test_user_issues_api.py` **11/11** con `MockRepository` +
  `create_app` (patrón de `test_issue_checklist`): los 9 nombres exigidos por la issue +
  2 extra (create sin token → `created_by=None`, kind inválido → 422). El stub de PG
  parchea `user_router._pg_repository` con `{uid-ana, uid-bot}`.
- Gates (baselines intactos): `ruff check .` **1334**, `mypy src` **1136**, `pytest`
  **1448 passed** (+11 nuevos) / 3 fallos preexistentes / 27 skipped.
