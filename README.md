# SocialSeed Tasker

**Where tasks become a living graph — and AI agents have to ask before they act.**

SocialSeed Tasker is a graph-native engineering management platform: issues, components and
dependencies live in a Neo4j graph instead of flat tables, so you can *see* the consequences of
every change before you make it. A FastAPI backend with a CLI exposes the graph; a Vue 3
frontend turns it into a board you actually want to work in — with AI agents wired into the
same governance rules as humans: they plan, you approve (HITL), policies veto, and an audit
log remembers everything.

**What's already built** is not a prototype sketch — it's the result of **514 resolved issues**:
~28,500 lines of typed frontend (78 components, 27 views, 24 stores, full EN/ES i18n), a real
backend with code-as-graph analysis (tree-sitter), RAG-style reasoning, secrets management and
a CLI, plus a complete mock dataset so the whole UI runs standalone in one command.

**Where it's headed** is documented in [Roadmap](#roadmap) — end-to-end wiring to the real
backend, a frontend test suite, and turning the simulated agents into real LLM-backed ones.

---

## Highlights

- **Dependency graph as the source of truth** — Board, List and Kanban are just lenses on
  the same graph; the Graph view traces impact paths and blast radius interactively.
- **AI agents with guardrails** — Agent Studio to build custom agents (prompts, tools,
  limits), a sandbox tester, HITL approval inbox with diff/impact review, and a kill switch
  that actually stops the agent on the card.
- **Governance that bites** — Policies (circular deps, max fan-out…), a constraint
  validator, a risk-governance matrix, and a hash-chained audit log you can export.
- **See the system** — Impact & root-cause analysis, code-graph overlay, GraphRAG
  explorer, auto-healing pipeline monitor, token/FinOps dashboards, executive reports with
  SLA metrics and PDF/PNG/JSON export.
- **Polish** — Dark mode, EN/ES i18n, command palette (`Cmd/Ctrl+K`), toasts with 3
  themes, sound effects, offline-first sync queue, presence & typing indicators, floating chat.

---

## Quick start

### Option A — Docker (the whole stack)

**Prerequisites:** Docker Desktop running. The frontend image serves a *pre-built* `dist/`,
so build it once first:

```bash
# 1. Build the UI (type-checks + bundles)
cd frontend
npm install
npm run build
cd ..

# 2. Start everything
docker compose up -d
```

Open **http://127.0.0.1:19001** and you're in.

| Service | URL | Notes |
|---------|-----|-------|
| **Frontend (UI)** | http://127.0.0.1:19001 | nginx, proxies `/api/` and `/mock-api/` |
| **Mock API** | http://127.0.0.1:8001 | FastAPI, persists JSON dataset |
| **Real API** | http://127.0.0.1:8888 | FastAPI + Neo4j (optional for UI) |
| **Neo4j Browser** | http://127.0.0.1:7474 | login `neo4j` / `neoSocial` |

The UI runs in **mock mode** (`USE_MOCK = true` in `frontend/src/api/client.ts`): every CRUD
operation round-trips through the mock API and persists to
`frontend/dataset-de-pruebas/*.json` — no database needed to explore.

**After changing frontend code:**

```bash
cd frontend && npm run build
docker compose build tasker-board
docker compose up -d tasker-board
```

### Option B — Local development (hot reload)

**Prerequisites:** Python 3.10+, Node.js 18+, and one-time Python deps
(`pip install -r requirements.txt`).

```powershell
# Terminal 1 — mock API (persists the JSON dataset)
cd mock-api
$env:DATA_DIR="..\frontend\dataset-de-pruebas"
python -m uvicorn server:app --port 8001 --reload

# Terminal 2 — frontend with Vite HMR
cd frontend
npm install
npm run dev
```

```bash
# Linux / macOS
# Terminal 1
cd mock-api
DATA_DIR="../frontend/dataset-de-pruebas" python -m uvicorn server:app --port 8001 --reload

# Terminal 2
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173**. Vite proxies `/mock-api/*` → `:8001` and `/api/*` → `:8000`,
so edits hot-reload instantly.

### Option C — Local development with the real backend

```bash
# 1. Neo4j only, via Docker
docker compose up -d tasker-db

# 2. Install + run the real API on port 8000 (matches the Vite proxy)
pip install -e .
TASKER_API_PORT=8000 python -m socialseed_tasker.infrastructure.web_api
# PowerShell: $env:TASKER_API_PORT="8000"; python -m socialseed_tasker.infrastructure.web_api

# 3. Point the UI at it: set USE_MOCK = false in frontend/src/api/client.ts
#    then start the frontend (Option B)
```

Bonus: `TASKER_DEMO_MODE=true` seeds the graph with demo components, issues and
dependencies on first boot.

---

## Project structure

```
socialseed-tasker/
├── frontend/                  # Vue 3 + TypeScript + Vite + Tailwind
│   ├── src/
│   │   ├── views/             # 27 pages (Board, Graph, HITL, Studio…)
│   │   ├── components/        # 78 reusable components
│   │   ├── stores/            # 24 Pinia stores
│   │   ├── composables/       # useToast, useSoundEffects, useExport…
│   │   ├── api/               # client.ts (axios) + mockApi.ts (fetch)
│   │   ├── locales/           # i18n: en.json / es.json (~1,415 keys)
│   │   └── types/             # shared TypeScript contracts
│   └── dataset-de-pruebas/    # mock dataset (live JSON persistence)
├── src/socialseed_tasker/     # Python backend (FastAPI, hexagonal-ish)
│   ├── cli/                   # `tasker` CLI (typer + rich)
│   ├── infrastructure/        # web_api (FastAPI), repos (Neo4j)
│   └── application/           # use cases, container/DI
├── tests/                     # 146 pytest files (unit, integration, e2e, contracts)
├── .github/workflows/         # CI: lint, mypy, pytest (3.10–3.12), release, security
├── mock-api/server.py         # standalone mock backend for the UI
├── docker-compose.yml         # 4 services: db, api, board, mock-api
├── features.md                # living feature inventory (57 sections)
└── .issues/                   # issue tracker: to-do/ + done/ (514 closed)
```

---

## Feature tour

| Area | What's inside |
|------|---------------|
| **Planning** | Board (drag & drop), List (filters, bulk actions), Kanban, backlog, issue detail with dependency/blocking graph, GitHub sync card |
| **Analysis** | Impact analysis, root-cause analysis, blast-radius slider, dependency chain, code-graph overlay, GraphRAG explorer |
| **Governance** | Policies & sandboxed testing, constraint validation, governance matrix (agent × risk), audit log (hash-chained), SLA metrics |
| **Human in the loop** | HITL command center, global approval banner, quick-action modal with diff & impact preview, notification click-through |
| **AI agents** | Agent Studio (builder + prompt validation + sandbox + library), agent replay, MCP inspector, kill switch & live timer, FinOps (token costs, ROI, budgets, caps) |
| **Resilience** | Auto-healing pipeline monitor, offline-first sync queue with conflict resolution, network mode simulator (online/degraded/offline) |
| **Collaboration** | Chat with agents & users, floating chat widget, presence avatars, typing indicators, mentions |
| **Reports** | Executive dashboard, analytics dashboard (MTTR, healing rate, budget), report exporter (PDF / PNG / JSON), CSV/JSON export everywhere |
| **Platform** | Dark mode, EN/ES i18n, command palette, keyboard shortcuts, toasts (3 themes), sound effects, PII detection & redaction suite, mobile responsive drawer |

---

## Architecture in one paragraph

The Vue app talks to two interchangeable backends selected by one flag in
`frontend/src/api/client.ts`: the **mock API** (a FastAPI server that reads/writes plain JSON
files — perfect for demos and UI work) and the **real API** (FastAPI → repository interface →
Neo4j, with domain use cases, tree-sitter code analysis and a Typer CLI). In Docker, nginx
inside the frontend container proxies `/api/` and `/mock-api/` to the sibling services, so the
browser only ever talks to one origin. Both backends expose the same shapes, which is why
flipping `USE_MOCK` is the only thing needed to move between them.

---

## Roadmap

Where this is going next, roughly in order:

1. **Real backend end-to-end** — finish wiring the UI against the real API as the default
   (seeded Neo4j, parity gaps closed), keeping the mock as an instant-demo switch.
2. **UI test suite** — the backend already ships 146 pytest files (unit, integration, e2e,
   contracts) behind a GitHub Actions pipeline (ruff/black/mypy/pytest across Python
   3.10–3.12); the frontend has none. Add Vitest component tests and a few Playwright smoke
   flows for the board, graph and HITL journeys.
3. **Performance pass** — split the heavy chunks (elk/cytoscape/GraphView are >500 kB each),
   virtualize long lists, lazy-load diagram libraries per view.
4. **Realtime everywhere** — promote the mocked SSE/event stream to actual WebSocket
   channels for presence, audit tail and agent logs.
5. **Real LLMs in Agent Studio** — swap the deterministic sandbox simulator for actual
   model providers behind the same prompt/tool/limit contracts.
6. **Offline v2** — upgrade the localStorage sync queue to IndexedDB with background retry
   and background sync (PWA installable shell).
7. **GitHub two-way sync** — push issues to GitHub and reconcile inbound webhooks.

---

## Tech stack

| Layer | Stack |
|-------|-------|
| Frontend | Vue 3.5 · TypeScript · Vite 6 · Tailwind 3 · Pinia · vue-i18n · vis-network |
| Backend | Python 3.10+ · FastAPI · Neo4j 5 · Typer CLI · tree-sitter · pydantic |
| Mock | FastAPI + JSON dataset (drop-in replacement, read/write) |
| Tooling | Frontend gate: `vue-tsc -b && vite build` · Backend CI: ruff, black, isort, mypy, pytest (GitHub Actions) |

```bash
cd frontend && npm run build   # type-check + production bundle (frontend's quality gate)
```

---

## Mock data

The dataset lives in `frontend/dataset-de-pruebas/` and is mounted into the mock container.
Main files:

| File | Content |
|------|---------|
| `issues.json` | Issues with status, priority, assignee, dependencies |
| `components.json` | System components |
| `users.json` | Users and AI agents |
| `policies.json` | Governance policies |
| `constraints.json` | System constraints |

…plus `dependencies.json`, `projects.json`, `organizations.json`, `agent-logs.json`,
`dashboard-stats.json`, `root-cause.json`, `index.json`.

Data persists across restarts. To factory-reset the dataset to its committed state:

```bash
git checkout -- frontend/dataset-de-pruebas
```

(Deleting a file makes the mock return empty results — there is no auto-reseed, so prefer
the `git checkout` restore above.)

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| UI shows old build | Rebuild: `cd frontend && npm run build && docker compose build tasker-board && docker compose up -d tasker-board` |
| Blank page / `Unexpected token '<'` | Mock API down — start it (Option B, terminal 1) or `docker compose up -d mock-api` |
| Port already in use | Ensure no stale containers: `docker compose ps`, `docker ps -a` |
| Data not saving locally | `DATA_DIR` must point to `frontend/dataset-de-pruebas` |
| Switching to real API | Set `USE_MOCK = false` in `frontend/src/api/client.ts` and rebuild; local dev needs the API on `:8000`, Docker routes `/api/` automatically via nginx |
| i18n missing keys | `en.json` and `es.json` must stay structurally in sync |

---

<p align="center">
  <b>SocialSeed Tasker v1.0.5</b> · 514 issues resolved · Apache-2.0<br/>
  Built by <a href="https://github.com/daironpf">Dairon Pérez Frías</a>
</p>
