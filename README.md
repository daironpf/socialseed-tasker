# SocialSeed Tasker

A graph-based task management framework with hexagonal architecture, AI agent orchestration, code-as-graph analysis, RAG-powered reasoning, deterministic contracts, secrets management, and hardened CI/CD.

---

## Quick Start

### 1. Start the Database

```bash
cd .agent && docker compose up -d
```

### 2. Configure Environment

```bash
cp .agent/configs/.env.example .agent/configs/.env
# Edit .agent/configs/.env with your settings
```

### 3. Verify Setup

```bash
# Check database health
curl http://localhost:8000/health

# List components
curl http://localhost:8000/api/v1/components
```

---

## Operation Modes: Direct vs API

Tasker supports two operation modes to suit different workflows:

- **Direct Mode** (default): Direct connection to Neo4j via Bolt protocol → Ideal for local development
- **API Mode**: HTTP calls to FastAPI backend → Ideal for production and integrated testing

Both modes support all CLI commands with identical syntax. Switch modes by setting the `TASKER_MODE` environment variable:

```bash
# Direct mode (default)
tasker component list

# API mode
TASKER_MODE=api tasker component list
TASKER_MODE=api TASKER_API_URL=http://localhost:8888 tasker component list
```

**Documentation:**
- [docs/cli_modes.md](./docs/cli_modes.md) — Complete dual-mode guide with examples
- [docs/dual_mode_setup.md](./docs/dual_mode_setup.md) — Setup troubleshooting for both modes
- [docs/api_contract.md](./docs/api_contract.md) — REST API endpoint reference

---

## Available CLI Commands

```bash
# Components
tasker component create <name> -p <project>
tasker component list
tasker component show <id>
tasker component update <id>
tasker component delete <id>

# Issues
tasker issue create <title> -c <component> -p <priority>
tasker issue list
tasker issue show <id>
tasker issue close <id>

# Dependencies
tasker dependency add <issue> --depends-on <dep>
tasker dependency chain <issue>
tasker dependency blocked

# Analysis
tasker analyze root-cause <issue>
tasker analyze impact <issue>

# Code-as-Graph
tasker code-graph scan <path>
tasker code-graph find <symbol>
tasker code-graph prune
tasker code-graph gc

# RAG & Reasoning
tasker rag search "<query>"
tasker rag status
tasker reasoning log --issue <id> --thought <thought>
tasker reasoning list --issue <id>

# Tenants
tasker tenant-create --id <name> --config '<json>'
tasker tenant-list
tasker tenant-delete --id <name>

# Feature Flags
tasker flag-set --name <name> --value '<json>'
tasker flag-get --name <name>
tasker flag-list
tasker flag-delete --name <name>

# Secrets
tasker secret set --name <key> --value <value>
tasker secret get --name <key>
tasker secret delete --name <key>
tasker secret rotate --name <key> --policy <policy>

# Backup
tasker backup create
tasker backup list
tasker backup restore <timestamp>

# Server Management
tasker serve
tasker serve --port 9000
tasker restart
tasker restart --force
```

---

## Standard Tooling (CLI Utilities)

```bash
# Changelog generation
python tools/release/changelogctl.py generate --from <ref> --to <ref> --out CHANGELOG.md

# Contract validation
python tools/contracts/contractctl.py run --provider http://localhost:8000 --spec openapi.json --out report.json

# Mock server
python tools/contracts/mockctl.py run --spec openapi.json --port 9000

# Secrets management
python tools/secrets/secretctl.py put --name <key> --file <path>
python tools/secrets/secretctl.py get --name <key>
python tools/secrets/secretctl.py delete --name <key>
python tools/secrets/secretctl.py rotate --name <key> --interval 30 --policy monthly

# Chaos scenarios
python tools/chaos/chaosctl.py run redis-flap
python tools/chaos/chaosctl.py list
python tools/chaos/chaosctl.py report
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/graphql` | POST | GraphQL API with subscriptions |
| `/api/v1/components` | GET/POST | CRUD for components |
| `/api/v1/issues` | GET/POST | CRUD for issues |
| `/api/v1/workable-issues` | GET | Issues ready to work on |
| `/api/v1/analyze/impact/{id}` | GET | Impact analysis |
| `/api/v1/analyze/architect` | POST | Architecture constraint validation |
| `/api/v1/graph/dependencies` | GET | Full dependency graph |
| `/api/v1/graph/impact/{id}` | GET | Impact propagation path |
| `/api/v1/code-graph/scan` | POST | Parse repository with Tree-sitter |
| `/api/v1/code-graph/find` | GET | Find symbol in code graph |
| `/api/v1/rag/search` | POST | Semantic similarity search |
| `/api/v1/rag/index` | POST | Rebuild vector index |
| `/api/v1/reasoning/log` | POST | Log agent reasoning |
| `/api/v1/reasoning/{id}` | GET | Get reasoning trace |
| `/api/v1/admin/flags` | GET/POST | Feature flags CRUD |
| `/api/v1/admin/metrics` | GET | Prometheus metrics |
| `/api/v1/tenants` | GET/POST | Multi-tenant management |
| `/api/v1/tenants/{id}` | DELETE | Remove tenant |
| `/api/v1/secrets` | GET/POST | Secrets CRUD |
| `/api/v1/secrets/rotate` | POST | Rotate secret |
| `/api/v1/privacy/export` | POST | GDPR data export |
| `/api/v1/privacy/delete` | POST | GDPR data deletion |
| `/api/v1/webhooks` | GET/POST | Webhook registration |
| `/api/v1/backup` | GET/POST | Backup and restore |
| `/api/v1/auth/login` | POST | OAuth2 / SSO login |
| `/api/v1/auth/session` | GET | Session validation |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TASKER_NEO4J_URI` | `bolt://localhost:7687` | Neo4j URI |
| `TASKER_NEO4J_USER` | `neo4j` | Neo4j user |
| `TASKER_NEO4J_PASSWORD` | (required) | Neo4j password |
| `TASKER_API_KEY` | (optional) | API authentication key |
| `TASKER_API_KEY_HEADER` | `X-API-Key` | Custom API key header name |
| `TASKER_RATE_LIMIT` | `100/minute` | Rate limiting policy |
| `TASKER_ENCRYPTION_KEY` | (optional) | AES-256-GCM key for secrets |
| `TASKER_FEATURE_FLAGS` | `{}` | Runtime feature flags |
| `TASKER_LOG_LEVEL` | `INFO` | Logging level |
| `TASKER_METRICS_ENABLED` | `true` | Prometheus metrics |
| `TASKER_OTEL_ENABLED` | `false` | OpenTelemetry tracing |
| `TASKER_REDIS_URI` | `redis://localhost:6379` | Redis / Celery broker |
| `API_PORT` | `8000` | API port |
| `OAUTH2_ISSUER` | (optional) | OAuth2 / Keycloak issuer URL |

---

## Docker Commands

```bash
# Start all services
docker compose up -d

# Start full stack with monitoring
docker compose -f docker-compose.api.yml up -d
docker compose -f docker-compose.chaos.yml up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f tasker-api

# Stop (data persists)
docker compose down

# Stop and remove data
docker compose down -v
```

---

## CI/CD

| Workflow | Trigger | Description |
|----------|---------|-------------|
| `pipeline.yml` | Push/PR to main | Lint, unit tests, security scan, build, docker, sign, publish |
| `release.yml` | Tag `v*` | Changelog generation, GPG signing, GitHub Release |
| `canary-deploy.yml` | Manual | Docker build, smoke tests, rollback on failure |
| `security-scan.yml` | Weekly / manual | Safety and Bandit vulnerability scanning |

```bash
# Run CI locally
./scripts/ci/run_local_pipeline.sh

# Sign artifacts
export RELEASE_GPG_PRIVATE_KEY="<base64-key>"
./scripts/ci/sign_artifact.sh dist/tasker-*.whl
```

---

## Local Development

```bash
# Start dev services (Neo4j + CLI)
make dev-up

# Run unit tests
make test

# Run integration tests (requires services)
make integration

# Run the reproducible example
make example-run
# output written to examples/output.json

# Start API, Neo4j and Board
docker compose -f docker-compose.api.yml up -d

# Open the board
http://localhost:8080

# Open API docs
http://localhost:8000/docs
```

---

## Testing

```bash
# Unit + domain + application tests
pytest tests/unit/ tests/domain/ tests/application/ -v

# With coverage
pytest tests/unit/ tests/domain/ tests/application/ --cov=socialseed_tasker --cov-report=term-missing

# Integration tests (requires Neo4j running)
pytest tests/integration/ -v -m integration

# CI pipeline smoke tests
pytest tests/ci/ -q

# Security scan
bandit -r src -lll
safety check --full-report
```

---

## For AI Agents

This project is optimized for AI agent collaboration. All operational knowledge is stored in the **`.agent/`** directory.

- **Skills**: Specialized capabilities in `.agent/skills/`.
- **Workflows**: Step-by-step guides in `.agent/workflows/`.
- **Protocol**: Rules of engagement in **`.agent/AGENT_GUIDE.md`**.

### Quick Start for Agents:
1. Read `.agent/project.md` for context.
2. Read `.agent/AGENT_GUIDE.md` for protocol.
3. Follow `.agent/workflows/implement-issue.md` for tasks.

---

*Generated by SocialSeed Tasker v1.0.0 — 325+ issues resolved*