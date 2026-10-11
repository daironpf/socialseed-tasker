# Issue #574: Histórico de ejecuciones de agentes en PostgreSQL — `agent_runs` + `agent_run_logs`

## Description

Las ejecuciones/actividad de los agentes **no tienen persistencia durable** en ninguna base:

- **Logs por issue en memoria**: `RealtimeHub._logs` (`realtime.py:36,85`) es un ring buffer
  de 200 entradas por issue — **se pierde al reiniciar el proceso** (issue #517, DONE pero
  sin persistencia).
- **Replay** (`agentReplayStore.ts`): solo fixtures mock en modo real `sessions = []`.
- **Reasoning logs**: JSON embebido en la propiedad `reasoningLogs` del nodo Issue en Neo4j.
- FinOps: fixtures hardcodeadas en el store.

Con Agent Studio migrado a la API (#573) y `agents_user` en PG, el **histórico de runs** es la
pieza que le falta al usuario: ver cuándo corrió cada agente, con qué resultado, y su log
paso a paso. Es **greenfield** (tabla nueva; los tipos ya están tipados en el front:
`AgentLog {timestamp, type reasoning|progress|files|debt, content_markdown}` en
`types/index.ts:249` y `AgentSession`/`ReplayEvent` en `types/agentReplay`).

Alcance deliberado: **la tabla es para histórico**; el streaming SSE en memoria (#517/#472)
sigue como está para realtime (la tabla se alimenta al cerrar run o por flush periódico).

## Status: DONE

## Priority: MEDIUM

## Component
Backend / Data / PostgreSQL + frontend (pestaña de logs del Studio)

## Type
feat / fullstack

## Implementation
1. **DDL** (dueño de este issue, patrón idempotente de #558):

   ```sql
   CREATE TABLE IF NOT EXISTS agent_runs (
     id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
     agent_id        TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     issue_id        TEXT,                    -- id de Neo4j, sin FK (raíz de issues = grafo)
     status          TEXT NOT NULL CHECK (status IN ('running','completed','failed','cancelled')),
     model           TEXT,
     started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
     finished_at     TIMESTAMPTZ,
     total_tokens    INT,
     total_tool_calls INT,
     duration_ms     INT,
     summary         TEXT
   );
   CREATE INDEX IF NOT EXISTS ix_agent_runs_agent_started ON agent_runs (agent_id, started_at DESC);

   CREATE TABLE IF NOT EXISTS agent_run_logs (
     run_id          TEXT NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
     seq             INT NOT NULL,
     timestamp       TIMESTAMPTZ NOT NULL DEFAULT now(),
     type            TEXT NOT NULL CHECK (type IN ('reasoning','progress','files','debt','tool_call','error','violation')),
     content_markdown TEXT,
     metadata        JSONB,
     PRIMARY KEY (run_id, seq)
   );
   ```

2. **Endpoints** (router `agent_runs.py`, registro después de `agent_profiles` — sin colisión:
   `/agents/{id}/runs` sí es compatible con `{agent_id}` de `agent.py`, verificar orden):
   - `POST /agents/{agent_id}/runs` → crea run `running` (uid PG).
   - `POST /agents/{agent_id}/runs/{run_id}/logs` → append (seq incremental) — o `PATCH` de
     cierre con `status/finished_at/totals/summary`.
   - `GET /agents/{agent_id}/runs?limit=` → histórico; `GET /runs/{run_id}/logs` → entradas
     ordenadas por `seq`.
   - `DELETE /runs/{run_id}` → poda manual (admin); 404; 503 sin database.
3. **Alimentación**: integración mínima con el flujo existente de agent logs — cuando
   `POST /issues/{id}/agent-logs` (realtime.py) recibe entradas, escribir **best-effort** en
   `agent_run_logs` (abrir/continuar un run `running` para el `agent_id` de la issue si no
   existe uno abierto; no romper el SSE si PG falla). `finish`/`agent/finish` cierra el run
   (`status`, `finished_at`, totals si vienen en el payload).
4. **Frontend — pestaña de logs en Agent Studio**: en la ficha del agente (junto a la
   Library o en el panel del agente), listar `GET /agents/{id}/runs` con estado, duración y
   tokens; al expandir → `GET /runs/{id}/logs` renderizando el markdown de cada entrada
   (patrón de `AgentLogStream.vue`). Estados loading/vacío/error + retry.
5. **Tests** (obligatorios):
   - Backend: `test_create_run_and_append_logs`, `test_get_runs_list_and_logs_ordered`,
     `test_run_cascade_delete_with_agent` (borrar agente limpia runs/logs),
     `test_agent_log_stream_persists_best_effort` (fake que falla → SSE intacto),
     `test_runs_503_without_database_url`, `test_run_status_validation_422`.
   - Frontend: spec del panel de historial (lista + detalle + vacío/error) y del store/API
     (`agentRunsApi.spec.ts`).

## Acceptance Criteria
- [x] Tablas `agent_runs`/`agent_run_logs` creadas con índices y cascada desde `users`
- [x] CRUD/lectura de runs y logs vía API (503 sin database, 404/422 validados)
- [x] El stream de logs por issue sigue funcionando en realtime **y** persiste best-effort en
      la tabla (un reinicio no pierde el histórico ya cerrado)
- [x] El Studio muestra el historial de ejecuciones del agente con detalle de logs
- [x] Borrar un agente limpia sus runs (cascada)
- [x] **Tests**: los pytest + specs listados pasan
- [x] Gates: backend `ruff` delta 0 (1251 preexistentes) / `mypy` delta 0 en ficheros nuevos /
      `pytest` 1475+3 preexistentes+27 skipped; frontend `lint` 0/2 / `test` 395 / `build` OK /
      i18n 1719/1719 EN+ES

## Files to Create
- `src/socialseed_tasker/infrastructure/web_api/routers/agent_runs.py`
- `tests/api/test_agent_runs_api.py`
- `frontend/src/api/agentRunsApi.ts` + `agentRunsApi.spec.ts`
- (posible) `frontend/src/components/agents/AgentRunHistoryPanel.vue`

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/app.py` (registro)
- `src/socialseed_tasker/infrastructure/web_api/schemas.py` (`AgentRunCreate/Response`,
  `AgentRunLogResponse`)
- `src/socialseed_tasker/infrastructure/web_api/routers/realtime.py` (flush best-effort)
- `src/socialseed_tasker/infrastructure/web_api/routers/issues.py` (cierre en `agent/finish`)
- `frontend/src/views/AgentStudioView.vue` (pestaña de historial)
- `frontend/src/locales/es.json` / `en.json`

## Notes
- **No** mezclar con `session_logs` (#571, sesiones de usuario) ni con reasoning embebido en
  Neo4j (migrarlo a la tabla es un follow-up opcional).
- Los runs de auto-healing (`.tasker-data/auto-healing/runs.json`) son otra entidad — no
  unificar aquí.
- `issue_id` es texto Neo4j sin FK (los issues no viven en PG); integridad referencial en el
  grafo.

## Related Issues
- #517/#472 (SSE realtime, se conserva), #573 (Studio que consume el historial), #558 (patrón
  de esquema/repo), #564 (uid del agente), #571 (`session_logs`, aparte)

## Resolution

**DONE 2026-10-11.** Implementación greenfield completa:

- **DDL** (`auth/user_store.py`): `AGENT_RUNS_DDL` + `AGENT_RUN_LOGS_DDL` idempotentes con
  `CREATE TABLE IF NOT EXISTS` en `create_schema`, cascada `agent_runs → users(id)` y
  `agent_run_logs → agent_runs(id)`, índice `ix_agent_runs_agent_started`; `issue_id` es
  texto Neo4j sin FK (los issues no viven en PG).
- **Store** (`PostgresAgentProfileStore`, dominio agente): `create_run`, `ensure_running_run`
  (reutiliza el run abierto o lo crea), `close_open_run` (calcula `duration_ms` con
  `extract(epoch…)`), `append_run_log` (seq incremental + `metadata::jsonb`), `update_run`
  (parcial), `list_runs`, `list_run_logs`, `delete_run`. JSONB con el patrón del repo
  (texto + cast, no `psycopg.Json`).
- **Router** `routers/agent_runs.py`: `POST/GET /agents/{agent_id}/runs` (404 agente
  desconocido, `limit` 1–200), `POST/GET /runs/{run_id}/logs` (404 run), `PATCH /runs/{run_id}`
  (status validado por `Literal` → 422), `DELETE /runs/{run_id}`; 503 sin
  `TASKER_DATABASE_URL`. Sin colisión con `agent.py`: `/agents/{id}/runs` es una plantilla de
  sufijo distinto a `/agents/{id}/heartbeat` y `/agents/{id}/specialists`.
- **Alimentación best-effort**: `POST /issues/{id}/agent-logs` (realtime.py) llama
  `append_agent_log_best_effort` — usa `payload.agent_id` si viene; sin él o con cualquier
  fallo PG el SSE queda intacto (helper nunca propaga). `agent/start` abre run
  (`open_run_best_effort`), `agent/finish` cierra como `completed` y el kill switch
  `/stop-agent` como `cancelled` (issues.py); ids no-PG como `manual` son no-op.
- **Frontend**: `api/agentRunsApi.ts` (6 funciones + tipos), panel
  `components/agents/AgentRunHistoryPanel.vue` (lista con badge de estado/duración/tokens,
  expandir → logs por seq, estados loading/vacío/error+retry) montado en `AgentStudioView`
  bajo la Library con selector de agente (solo modo real; oculto en mock). i18n
  `agentStudio.runs.*` EN/ES.
- **Tests**: 17 pytest en `tests/api/test_agent_runs_api.py` (CRUD, 404/422/503, cascada al
  borrar agente, flush best-effort con y sin `agent_id`, helper inexplota-bajo-PG,
  ciclo open/close) sobre `FakePgCursor` extendido con estado `runs`/`run_logs`; 8 specs
  `agentRunsApi.spec.ts` + 6 specs `AgentRunHistoryPanel.spec.ts`.
- **Gates**: ruff delta 0 (97 preexistentes en ficheros tocados), mypy 0 en ficheros nuevos,
  pytest 1475+3 preexistentes+27 skipped; frontend lint 0/2 (warnings preexistentes),
  test 395 (52 files), build OK, i18n 1719/1719.
- Smoke en vivo pendiente de `si` (despliegue `tasker-api` + `tasker-board`).
