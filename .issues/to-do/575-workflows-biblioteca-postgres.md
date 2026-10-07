# Issue #575: Workflows en PostgreSQL — biblioteca de definiciones con importación de `.agent/workflows/*.md`

## Description

**No existe el concepto "workflow" en la aplicación**: grep en `frontend/src` → 0 resultados;
ni entidad, ni endpoint, ni tabla, ni vista. Lo único que hay es **documentación procedural**:

- `.agent/workflows/*.md` — 14 ficheros (`implement-issue.md`, `create-issue.md`,
  `commit-push.md`, `daily-log.md`, `test-code.md`, `project-setup.md`, `ui-review-fix.md`…)
- Plantillas empaquetadas: `src/socialseed_tasker/assets/templates/workflows/` (5 ficheros +
  README con la matriz SETUP/ISSUE/WORK/DOCS/HISTORY/TEST/COMMIT/FIND)
- `skill_manifest.json` → claves `"workflow_rules"` (reglas de texto, no ejecución)
- Scaffolding que copia `workflows/` al proyecto destino (`application/scaffolder.py`,
  `cli/init_command.py`)

Decisión del usuario: **tabla `workflows`** para que el usuario pueda consultar/crear
workflows desde la app (junto al Studio). Alcance de este issue: **biblioteca de
definiciones** (almacenar y leer) — **no** un motor de ejecución (ese sería otro ciclo: hoy
el "workflow engine" más cercano es auto-healing con runs en JSON).

## Status: TODO

## Priority: MEDIUM

## Component
Backend / Data / PostgreSQL + frontend (visor)

## Type
feat / fullstack

## Implementation
1. **DDL** (dueño de este issue, patrón idempotente de #558):

   ```sql
   CREATE TABLE IF NOT EXISTS workflows (
     id          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
     slug        TEXT NOT NULL UNIQUE,       -- 'implement-issue'
     name        TEXT NOT NULL,              -- 'Implement Issue'
     description TEXT,
     content_md  TEXT,                       -- markdown completo (fuente .md)
     steps       JSONB,                      -- futuro formato estructurado (nullable)
     source      TEXT NOT NULL DEFAULT 'custom' CHECK (source IN ('builtin','custom')),
     created_by  TEXT REFERENCES users(id) ON DELETE SET NULL,   -- uid PG si es custom
     created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
     updated_at  TIMESTAMPTZ
   );
   ```

2. **Importación seed de los `.md` existentes**: script/idempotente en el arranque (patrón
   `TASKER_AUTH_SEED` de `app.py:66-83`, activable por flag `TASKER_WORKFLOWS_SEED=1` o
   on-by-default en primera corrida): parsear front-matter/título del markdown
   (slug = nombre de fichero, name = primer `# `) e insertar `source='builtin'` con
   `ON CONFLICT (slug) DO NOTHING`. **No** sobrescribir edits del usuario (upsert solo si
   `source='builtin'` y sin cambios manuales → simplemente no actualizar).
3. **Endpoints** (router `workflows.py`):
   - `GET /workflows?source=` → lista (slug, name, description, source, created_at).
   - `GET /workflows/{slug}` → definición completa (`content_md` + `steps`).
   - `POST /workflows` → crear custom (`created_by` = uid del JWT, patrón `created_by` de
     #569) → 201; slug duplicado → 409.
   - `PUT /workflows/{slug}` → editar (los `builtin` solo si se decide permitir — por
     defecto: **editar solo custom**, builtin → 409 `detail="builtin workflow"`).
   - `DELETE /workflows/{slug}` → solo custom → 200; builtin → 409; 503 sin database.
4. **Frontend — visor**: componente `WorkflowLibrary.vue` (lista + panel de lectura del
   markdown con el renderer existente de la app) consumiendo `/workflows`; entrada en el Studio
   (botón/pestaña "Workflows" junto a Library) o en la sidebar — decisión: **dentro de
   AgentStudioView** (el usuario lo pidió junto al Studio). Crear/editar custom con textarea
   (mínimo viable: nombre + descripción + markdown).
5. **Tests** (obligatorios):
   - Backend: `test_seed_workflows_imports_builtin_markdown` (flag → filas `builtin`, 2ª
     corrida sin duplicar), `test_list_and_get_workflow_by_slug`,
     `test_create_custom_workflow_sets_created_by_uid`, `test_builtin_workflow_not_editable_409`,
     `test_delete_builtin_409`, `test_workflows_503_without_database_url`.
   - Frontend: spec de `workflowsApi` + spec del visor (lista, detalle, 409 en builtin).

## Acceptance Criteria
- [ ] Tabla `workflows` con slug único, `created_by` = uid PG y cascada
      `SET NULL` (borrar usuario no borra el workflow)
- [ ] Los 14 `.agent/workflows/*.md` (o los de `assets/templates`) importados como
      `builtin` de forma idempotente
- [ ] CRUD de workflows custom con auth (`created_by` desde JWT); builtin protegidos (409)
- [ ] Visor en el Studio: lista + lectura del markdown; crear/editar custom
- [ ] 503 sin `TASKER_DATABASE_URL`; 404 slug inexistente
- [ ] **Tests**: los pytest + specs listados pasan
- [ ] Gates: backend `ruff` 1011 / `mypy` 1153 / `pytest` 1331+3; frontend `lint` 0/2 /
      `test` 306+ (44+) / `build` OK / i18n 1693+N EN/ES

## Files to Create
- `src/socialseed_tasker/infrastructure/web_api/routers/workflows.py`
- `src/socialseed_tasker/infrastructure/web_api/workflows_seed.py` (o en `app.py`)
- `tests/api/test_workflows_api.py`
- `frontend/src/api/workflowsApi.ts` + `workflowsApi.spec.ts`
- `frontend/src/components/agents/WorkflowLibrary.vue` (+ spec)

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/app.py` (registro + seed en lifespan)
- `src/socialseed_tasker/infrastructure/web_api/schemas.py` (`WorkflowCreate/Update/Response`)
- `frontend/src/views/AgentStudioView.vue` (pestaña/entrada al visor)
- `frontend/src/locales/es.json` / `en.json`

## Notes
- `steps JSONB` queda nullable a propósito: hoy solo markdown; el día que haya motor de
  ejecución, el campo ya existe (SOLID: una columna, dos fases).
- **Fuera de alcance**: motor de ejecución de workflows, triggers, scheduling y unificación
  con auto-healing (runs en `.tasker-data/auto-healing/runs.json`).
- `workflow_rules` de `skill_manifest.json` no se migran aquí (son reglas de skills, otra
  concern).

## Related Issues
- #558 (patrón de esquema/seed), #569 (`created_by` desde JWT), #573 (Studio donde se
  integra el visor), #574 (runs, aparte), #520 (auto-healing runs en JSON, no unificar)
