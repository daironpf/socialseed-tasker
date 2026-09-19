# SocialSeed Tasker

A graph-based task management framework with hexagonal architecture, AI agent orchestration, code-as-graph analysis, RAG-powered reasoning, deterministic contracts, secrets management, and hardened CI/CD.

---

## Quick Start — UI Testing

### Prerequisites

- Docker Desktop running
- Node.js 18+ (for local frontend development)

### 1. Start All Services

```bash
docker compose --profile api up -d
```

This starts:
| Service | URL | Description |
|---------|-----|-------------|
| Frontend (UI) | http://127.0.0.1:8889 | Vue 3 board interface |
| Mock API | http://127.0.0.1:8001 | Persistent mock backend (read/write JSON) |
| Real API | http://127.0.0.1:8888 | FastAPI backend (optional) |
| Neo4j | http://127.0.0.1:7474 | Graph database (user: `neo4j`, pass: `neoSocial`) |

### 2. Open the UI

Navigate to **http://127.0.0.1:8889** in your browser.

The UI runs in **mock mode** (`USE_MOCK = true` in `client.ts`). All CRUD operations persist to JSON files in `frontend/dataset-de-pruebas/`.

### 3. Verify Everything Works

```bash
# Check all containers are healthy
docker compose --profile api ps

# Check mock API
curl http://127.0.0.1:8001/mock/issues

# Check frontend build
cd frontend && npm run build
```

---

## Local Frontend Development (without Docker)

You can run the full UI locally without Docker. This is faster for development since it uses Vite's hot reload.

### Prerequisites

- Python 3.10+ (for mock-api)
- Node.js 18+ (for frontend)

### 1. Start the Mock API

```bash
cd mock-api

# Set the data directory path (Windows PowerShell)
$env:DATA_DIR="..\frontend\dataset-de-pruebas"

# Or on Linux/Mac
export DATA_DIR="../frontend/dataset-de-pruebas"

# Start the server
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

The mock API will be available at `http://localhost:8001`.

### 2. Start the Frontend Dev Server

In a new terminal:

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173` with hot reload.

### How It Works

The Vite dev server proxies API requests:
- `/mock-api/*` → `http://localhost:8001/*` (mock-api server)
- `/api/*` → `http://localhost:8000` (real API, optional)

All CRUD operations persist to JSON files in `frontend/dataset-de-pruebas/`.

### Quick Commands (Windows)

```powershell
# Terminal 1: Mock API
cd mock-api
$env:DATA_DIR="..\frontend\dataset-de-pruebas"; python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Frontend
cd frontend; npm run dev
```

### Quick Commands (Linux/Mac)

```bash
# Terminal 1: Mock API
cd mock-api
DATA_DIR="../frontend/dataset-de-pruebas" python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

---

## Docker Alternative

If you prefer Docker or need the full stack (including Neo4j and real API):

### Start All Services

```bash
docker compose --profile api up -d
```

### Rebuild After Frontend Changes

```bash
# 1. Build frontend
cd frontend && npm run build

# 2. Rebuild Docker image
docker compose --profile api build --no-cache tasker-board

# 3. Restart containers
docker compose --profile api up -d
```

---

## Project Structure

```
socialseed-tasker/
├── frontend/                    # Vue 3 + TypeScript + Vite
│   ├── src/
│   │   ├── views/              # Page components (Board, List, Graph, etc.)
│   │   ├── components/         # Reusable UI components
│   │   ├── stores/             # Pinia state management
│   │   ├── composables/        # Vue composables (useToast, useExport, etc.)
│   │   ├── api/                # API client (client.ts, mockApi.ts)
│   │   ├── locales/            # i18n translations (en.json, es.json)
│   │   └── types/              # TypeScript types
│   ├── dataset-de-pruebas/     # Mock data JSON files (persisted)
│   └── Dockerfile
├── mock-api/                    # FastAPI mock backend
│   ├── server.py               # Reads/writes dataset-de-pruebas/*.json
│   └── Dockerfile
├── docker-compose.yml           # All services
└── .agent/                      # AI agent configuration
```

---

## Mock Data

Mock data lives in `frontend/dataset-de-pruebas/`:

| File | Content |
|------|---------|
| `issues.json` | All issues with status, priority, assignee |
| `components.json` | System components |
| `users.json` | Users and AI agents |
| `policies.json` | Governance policies |
| `constraints.json` | System constraints |

Data persists across container restarts. To reset, delete the JSON files and restart mock-api.

---

## i18n (Multilanguage)

The UI supports English (EN) and Spanish (ES). Switch languages via the user menu in the header.

- Translations: `frontend/src/locales/en.json`, `frontend/src/locales/es.json`
- Usage: `const { t } = useI18n()` → `t('issues.createIssue')`

---

## Key Features

- **Board View**: Kanban-style issue management with drag & drop
- **List View**: Table view with sorting, filtering, bulk actions
- **Graph View**: Interactive dependency graph with connect mode
- **Analysis**: Impact analysis, root cause analysis, blast radius simulation
- **Components**: CRUD for system components with issue tracking
- **Policies**: Governance rules (circular deps, max dependencies, etc.)
- **Constraints**: System constraint validation
- **Users & Agents**: Human/AI agent management
- **Dashboard**: System health, token usage, activity charts
- **MCP Inspector**: Real-time monitoring of Model Context Protocol connections
- **HITL Command Center**: Unified inbox for agent approval requests with diff/impact view
- **Chat**: Full messaging system between users and AI agents
- **Floating Chat**: Messenger-style widget available on all views
- **Command Palette**: `Cmd+K` / `Ctrl+K` for quick navigation
- **Dark Mode**: Toggle in user menu (persists in localStorage)
- **Toasts**: Global notification system
- **Export**: CSV, JSON, SVG, PNG, Markdown export
- **i18n**: English and Spanish support

---

## Docker Commands

```bash
# Start all services
docker compose --profile api up -d

# Stop all services
docker compose --profile api down

# Rebuild everything
docker compose --profile api build --no-cache

# View logs
docker compose logs -f tasker-board
docker compose logs -f mock-api

# Check status
docker compose --profile api ps
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Port 8889 not accessible | Ensure Docker Desktop is running |
| Mock data not persisting | Check volume mount: `./frontend/dataset-de-pruebas:/app/dataset-de-pruebas` |
| Build fails | Run `cd frontend && npm install` then `npm run build` |
| Blank page | Check browser console for errors; ensure mock-api is running |
| i18n not working | Verify `vue-i18n` is installed: `cd frontend && npm ls vue-i18n` |
| `Unexpected token '<'` error | Mock API not running. Start it: `cd mock-api && python -m uvicorn server:app --port 8001` |
| Local dev: API calls fail | Ensure mock-api is running on port 8001 before starting frontend |
| Local dev: data not saving | Check `DATA_DIR` env var points to `frontend/dataset-de-pruebas` |

---

*SocialSeed Tasker v1.0.0 — 489 issues resolved*