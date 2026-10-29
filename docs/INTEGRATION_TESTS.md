# Integration tests

The integration suite (`tests/integration/`) is **opt-in**. Every test carries an
`integration` marker plus one or more prerequisite markers, so a group can be
selected and provisioned independently. This avoids depending on implicit local
services and keeps the destructive tests (Neo4j wipe, chaos runs) out of the
default pipeline.

## Prerequisite markers

| Marker | What it needs | Default location |
|--------|---------------|------------------|
| `self_contained` | Nothing external: in-memory stores, mocks, a thread/HTTP server started by the test | — |
| `requires_neo4j` | Disposable Neo4j | `TASKER_NEO4J_URI` (`bolt://localhost:7687`), user/password `neo4j`/`neoSocial` |
| `requires_redis` | Disposable Redis | `TASKER_REDIS_URL` (`redis://localhost:6379/0`) |
| `requires_api` | FastAPI service | `TASKER_API_URL` (`http://localhost:8000`) |
| `requires_board` | tasker-board UI | `TASKER_BOARD_URL` (`http://localhost:8080`) |
| `requires_graphql` | GraphQL service | `TASKER_GRAPHQL_URL` (`http://localhost:8081/graphql`) |
| `requires_graphviz` | Graphviz service | `TASKER_GRAPHVIZ_URL` (`http://localhost:8082`; CI uses `8083` to avoid Keycloak) |
| `requires_jaeger` | Jaeger (API exports UDP 6831) | `TASKER_JAEGER_URL` (`http://localhost:16686`) |
| `requires_grafana` | Prometheus + Grafana | `TASKER_PROM_URL` (`:9090`), `TASKER_GRAFANA_URL` (`:3000`) |
| `requires_sso` | Keycloak realm `tasker-dev` | `TASKER_KEYCLOAK_URL` (`http://localhost:8082`) |
| `requires_celery` | Celery worker + Redis broker + Neo4j | `TASKER_CELERY_BROKER_URL` (`redis://localhost:6379/0`) |
| `requires_chaos` | `tools/chaos/chaosctl.py` against a live API/Redis; **destructive** | `TASKER_CHAOS=1` |
| `requires_treesitter` | Compiled tree-sitter grammar | `TASKER_TREESITTER_PYTHON_SO` |

Additional variables used by the tests: `TASKER_TEST_TOKEN` (`admintoken123`),
`TASKER_METRICS_PORT` (auto-selects a free port unless set),
`TASKER_CONTRACT_MOCK_PORT` (`9100`),
`TASKER_WEBHOOK_ECHO_PORT` (`9010`).

## Inventory

| File | Markers | Notes |
|------|---------|-------|
| `test_api_integration.py` | `requires_api` (+ `requires_board` on the board test) | Health, CORS preflight and board root |
| `test_auth_integration.py` | `requires_neo4j` | Thin CLI with `TASKER_AUTH_USERS`; writes to Neo4j |
| `test_backup_restore_integration.py` | `self_contained` | Memory storage + mocked repositories |
| `test_celery_integration.py` | `requires_celery`, `requires_redis`, `requires_neo4j` | Enqueues `tasker.parse_and_index_files` and waits for the result |
| `test_chaos_api_latency.py` | `requires_chaos`, `requires_api` | `chaosctl.py run api-latency` |
| `test_chaos_redis_flap.py` | `requires_chaos`, `requires_redis` | `chaosctl.py run redis-flap` |
| `test_cli_integration.py` | `requires_neo4j` | Creates/deletes issues through the CLI |
| `test_contracts_integration.py` | `self_contained` | Starts `tools/contracts/mockctl.py` on `TASKER_CONTRACT_MOCK_PORT` |
| `test_data_quality_integration.py` | `self_contained` | Pipeline + event bus |
| `test_flags_integration.py` | `self_contained` | CLI/API roundtrip with mocks |
| `test_grafana_provisioning.py` | `requires_grafana` | Dashboard `Tasker Overview` and Prometheus targets |
| `test_graphql_integration.py` | `requires_graphql` | Mutation `triggerEvent` |
| `test_graphviz_integration.py` | `requires_api`, `requires_graphviz` | Reads the graph and posts a dependency |
| `test_metrics_endpoint.py` | `self_contained` | Starts the exporter on `TASKER_METRICS_PORT` |
| `test_ml_inference_integration.py` | `self_contained` | Feature store roundtrip |
| `test_neo4j_adapter_integration.py` | `requires_neo4j` | Adapter CRUD + Cypher |
| `test_neo4j_repository.py` | `requires_neo4j` | **Destructive**: `MATCH (n) DETACH DELETE n` on teardown |
| `test_parser_adapter_treesitter_integration.py` | `requires_treesitter` | Skips if the grammar `.so` is missing |
| `test_rate_limit_integration.py` | `requires_api`, `requires_redis` | Token bucket via Redis |
| `test_redis_storage_integration.py` | `requires_redis` | Put/get/TTL/delete |
| `test_repositories_integration.py` | `requires_neo4j` | Issue + graph repositories |
| `test_retention_integration.py` | `self_contained` | Retention worker with memory storage |
| `test_schema_registry_integration.py` | `self_contained` | Schema/dataset registry |
| `test_secrets_api_integration.py` | `requires_api` | Create/rotate/audit secrets |
| `test_sso_flow.py` | `requires_api`, `requires_sso` | Keycloak password grant + session cookie + `whoami` |
| `test_tenant_isolation.py` | `self_contained` | Namespaced memory storage |
| `test_tracing_integration.py` | `requires_api`, `requires_jaeger` | Trace visible in Jaeger |
| `test_use_cases_integration.py` | `requires_neo4j` | Agent context / impact with a real graph |
| `test_webhooks.py` | `self_contained` | Webhook handlers with mocks |
| `test_webhooks_integration.py` | `self_contained` | Local echo server on `TASKER_WEBHOOK_ECHO_PORT` |

## Running locally

Use a disposable stack, never a development database:

```bash
export TASKER_INTEGRATION=1

pytest -m self_contained                      # no services
pytest -m requires_neo4j                      # Neo4j only
pytest -m requires_redis                      # Redis only
pytest -m "requires_api and not requires_graphviz and not requires_jaeger and not requires_sso and not requires_chaos"
pytest -m requires_graphql
pytest -m requires_graphviz
pytest -m "requires_jaeger or requires_grafana"
pytest -m requires_sso
pytest -m requires_celery
```

Without `TASKER_INTEGRATION=1` every test in the suite is skipped, including
`self_contained`, so the default `pytest` run never touches local services.

Chaos scenarios are destructive and stay disabled even with
`TASKER_INTEGRATION=1`; they require `TASKER_CHAOS=1` and a disposable API/Redis.

## CI

The `integration` job in `.github/workflows/ci.yml` is opt-in:

```text
Actions -> CI -> Run workflow -> integration = true
```

It provisions a disposable environment with fixed ports (Neo4j `7687`, Redis
`6379`, API `8000`, board `8080`, GraphQL `8081`, Keycloak `8082`, Graphviz
`8083`, Jaeger `16686`, Prometheus `9090`, Grafana `3000`), waits for every
endpoint, runs the suite except `requires_chaos`/`requires_treesitter`, and dumps
the container logs on failure.

Locally the same stack can be reproduced with:

```bash
API_PORT=8000 FRONTEND_PORT=8080 \
  docker compose -f docker-compose.yml -f compose/ci/integration.yml up -d --build \
  tasker-db-neo4j tasker-db-pg tasker-db-redis tasker-db-mongo tasker-api tasker-board
```

The GraphQL and Graphviz services, Celery worker, Keycloak, Jaeger and
Prometheus/Grafana are started by the CI job; see the workflow for the exact
commands and environment variables.
