# #331 — Completar fixes de capa de importación y runtime en black-box test

## Estado: ✅ DONE (Prioridad ALTA)

## Resolución
Se encontraron 3 causas raíz:
1. **`real-test/.agent/configs/tasker.yml`** tenía `mode: api` → forzaba `ApiTaskRepository` que se llamaba a sí mismo en loop. Fix: cambiar a `mode: direct`.
2. **`Neo4jTaskRepository.create_component/create_issue`** en `component_mixin.py` e `issue_mixin.py` retornaban `None` pero la interfaz `TaskRepositoryInterface` declara `-> Component` / `-> Issue`. Fix: cambiar `-> None` a `-> Component`/`-> Issue` y agregar `return component` / `return issue`.
3. **Black-box test** no exportaba `TASKER_NEO4J_PASSWORD` globalmente (solo para el API process). Fix: agregar `export TASKER_NEO4J_PASSWORD="neoSocial"` al inicio del script.

Resultado: **9/9 tests pasan, 0 failures.**

## Contexto
Durante la sesión del 2026-05-26 se detectó que el API crasheaba al importar por culpa de llamadas eager a `get_tracer()` a nivel de módulo. Se corrigieron 4 archivos, pero al correr el black-box test (`real-test/blackbox_test.sh`) el API arranca correctamente y el health check pasa, pero falla en runtime con `RemoteServiceError: Connection error: timed out` al crear/listar componentes.

## Lo que ya se hizo (NO REPETIR)

### Fix 1: Eager tracer → Lazy tracer (import-layer crash)
- **`infrastructure/memory_storage.py`**: `_tracer = get_tracer(...)` → `def _get_tracer(): return get_tracer(...)`
- **`infrastructure/redis_storage.py`**: Ídem (el archivo se re-escribió completo porque `replaceAll` lo dañó al matchear el substring `_tracer` dentro de `get_tracer`)
- **`events/bus.py`**: `_tracer = get_tracer(...)` → `_tracer_fn = lambda: get_tracer(...)`
- **`events/delivery.py`**: Ídem

**Root cause**: `tracing.py` ya tenía imports lazy de `opentelemetry` dentro de `get_tracer()`, pero los llamadores invocaban `get_tracer()` a nivel de módulo (no dentro de una función), lo que igual disparaba el import de opentelemetry antes de que estuviera instalado.

### Fix 2: Missing export
- **`infrastructure/web_api/routes.py`**: Faltaba re-exportar `secrets_router` (presente en `routers/__init__.py` pero no en `routes.py`), causando `ImportError` cuando `app.py` intentaba importarlo.

### Fix 3: Dependencias en venv
- Se instaló `opentelemetry-api`, `opentelemetry-sdk`, `requests` en `real-test/venv/`

## Lo que hay que hacer

### 1. Investigar runtime timeout en endpoints de componentes/issues
- El health check responde HTTP 200
- `POST /api/v1/components` y `GET /api/v1/components` lanzan `RemoteServiceError: Connection error: timed out`
- El traceback muestra `api_repository.py` (ApiTaskRepository) siendo usado, no `Neo4jTaskRepository`
- **Posibles causas**:
  - **Config file `.agent/configs/tasker.yml`** que fuerza `mode: "api"` desde el CWD del test (real-test/). Verificar si existe tal archivo.
  - **Neo4j no está corriendo** o no es accesible en `bolt://localhost:7687`. El health check del API puede pasar sin Neo4j si no lo verifica.
  - **Timeout de conexión bolt** → `Neo4jTaskRepository` tiraría timeout pero el traceback muestra `ApiTaskRepository`, lo que indica que el modo es `"api"` y no `"direct"`.

**Acciones**:
  - Verificar `real-test/.agent/configs/tasker.yml` o similar que pueda forzar `mode: api`
  - Verificar que Neo4j esté corriendo: `docker ps | grep neo4j`
  - Si el modo es `"api"`, verificar a qué URL apunta (`api_url`) y si es reachable
  - Probar con `TASKER_MODE=direct` explícito en el script de test
  - Si el modo es correcto (`direct`), verificar conectividad bolt a Neo4j

### 2. Verificar que el API use Neo4jTaskRepository en modo direct
- El container usa `Container.from_env()` → lee `DualModeConfig.load()` → default `mode: "direct"`
- Pero `_discover_config_file()` busca `.agent/configs/tasker.yml` desde el CWD
- Si existe en `real-test/`, los valores del YAML sobreescriben defaults
- Asegurarse de que el black-box test no herede un config file con `mode: api`

### 3. Ejecutar test unitario completo
- `pytest tests/unit/ -q` debe seguir dando 658 passed / 27 failures (pre-existing por deps faltantes)
- No deben haber nuevos failures introducidos por los cambios de tracer lazy

### 4. Black-box test debe pasar 9/9
- El script `real-test/blackbox_test.sh` debe terminar con 0 failures
- Esto implica:
  - Health check pasa
  - Creación de componente con ID coincidente (FIND-007)
  - Creación de issue (FIND-007)
  - Dependencias (FIND-008)
  - Unicode (FIND-009)
  - Dependency closure (FIND-010)
  - Envelope API (FIND-011)
  - Proyectos (FIND-012)

### 5. Archivos modificados (para referencia)
- `src/socialseed_tasker/infrastructure/memory_storage.py`
- `src/socialseed_tasker/infrastructure/redis_storage.py`
- `src/socialseed_tasker/infrastructure/web_api/routes.py`
- `src/socialseed_tasker/events/bus.py`
- `src/socialseed_tasker/events/delivery.py`
- `real-test/venv/` (deps instaladas)

## Criterio de aceptación
- [ ] `tasker serve` arranca sin crashes de importación desde código fuente local
- [ ] `real-test/blackbox_test.sh` pasa 9/9 tests
- [ ] `pytest tests/unit/` no introduce nuevos failures
- [ ] No hay `_tracer = get_tracer(...)` a nivel de módulo en ningún archivo fuente
