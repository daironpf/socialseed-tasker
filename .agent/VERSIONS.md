# Project Versions

## [1.0.5] - 2026-06-07

### v1.0.5 Checklist
- [x] **#413 Duplicate dependency accepted silently:** Added `DuplicateDependencyError` exception and pre-creation check in `add_dependency_action()`. CLI now shows "Dependency already exists" warning; API returns 409 Conflict. Unit test added.

### Release History
| Version | Date | Description |
|---------|------|-------------|
| 1.0.5   | 2026-06-07 | Duplicate dependency detection |
| 1.0.4   | 2026-05-25 | Bugfixes & documentation improvements |

## [1.0.4] - 2026-05-25

### v1.0.4 Checklist
- [x] **#326 Schema init CypherSyntaxError:** Fixed invalid `DEPENDS_ON` relationship index syntax — changed `(i:Issue) ON (i.timestamp)` to `() ON (r.timestamp)`.
- [x] **#327 NameError on logger:** Added missing `logger = logging.getLogger(__name__)` in `neo4j_driver.py`.
- [x] **#328 Docker build 403 Forbidden:** Removed ghcr.io COPY from Dockerfiles to fix anonymous pull failure.
- [x] **#329 Frontend doc gap:** Added Frontend section to scaffold README template documenting build and customization.
- [x] **#362 API container ModuleNotFoundError:** Changed template Dockerfile from `pip install socialseed-tasker` (PyPI) to multi-stage local source build. Fixed `docker-compose.yml` build context. Added missing `__init__.py` to `auth/` and `infrastructure/neo4j_migrations/` packages.
- [x] **#363 Connection error exposes internal IP details:** Added `ServiceUnavailable` catch in `_verify_connection()`. Logs full details at debug level, raises clean `RuntimeError` with user-friendly message. Added `RuntimeError` handling in CLI error handler.
- [x] **#364 Code-graph scan path error lacks suggestions:** Improved `ValueError` message in `scan_repository()` to include actionable guidance on running from project root or using `--help`.
- [x] **#365 Duplicate issue detection ambiguous:** Changed CLI output from "Issue created" to "Using existing issue" when a duplicate title is detected.
- [x] **Branch lockdown policy:** Added policy #11 in `.agent/policies.md` — agents must never create/delete branches without explicit user instruction.

### Release History
| Version | Date | Description |
|---------|------|-------------|
| 1.0.4   | 2026-05-25 | Bugfixes & documentation improvements |
| 1.0.3   | 2026-05-24 | API Contract Testing & Mock Server |
| 1.0.2   | 2026-05-20 | Agent Project Assignment |
| 1.0.1   | 2026-05-05 | Quality & Testing Release |
| 1.0.0   | 2026-05-04 | Full Autonomy Release |

## [1.0.3] - 2026-05-24

### v1.0.3 Checklist
- [x] **#323 Deterministic API Contract Testing and Mock Server:** Added contract testing utilities, mock server, OpenAPI helpers, CLIs, unit/integration tests, and CI workflow.
- [x] **#324 Deterministic Secrets Management and Rotation Service:** Added SecretsStore with AES-256-GCM encryption, Rotator with configurable policies, API endpoints, CLI tool, and unit/integration tests.

### Release History
| Version | Date | Description |
|---------|------|-------------|
| 1.0.3   | 2026-05-24 | API Contract Testing & Mock Server |
| 1.0.2   | 2026-05-20 | Agent Project Assignment |
| 1.0.1   | 2026-05-05 | Quality & Testing Release |
| 1.0.0   | 2026-05-04 | Full Autonomy Release |

## [1.0.2] - 2026-05-20

### v1.0.2 Checklist
- [x] **Agent Project Assignment:** New endpoints `/projects/current`, `/projects/all`, and `/projects/{id}` to get project info.
- [x] **Agent Registration Fix:** Agents now properly linked to project via `project_id` field in registration.
- [x] **Auto-assign Project:** When no `project_id` provided, agent is automatically assigned to existing project.
- [x] **Flexible Project Lookup:** Project assignment now accepts both `id` and `slug`.
- [x] **UTF-8 Encoding Docs:** Added troubleshooting section for Windows curl with Spanish characters.
- [x] **Project-Centric Agent Workflow:** New workflow requiring agents to always consult Tasker first for project-related info.
- [x] **Single Project Architecture:** Tasker now supports only ONE project per instance. All entities belong to this single project.
- [x] **Project Data Fix:** Updated `.agent/project.json` with correct project data (was showing `dental-app`, now `socialseed-tasker`).
- [x] **Interactive Init Workflow:** New workflow for AI agents to guide users through `tasker init` with recommendations and interactive data collection.

## [1.0.1] - 2026-05-05

### v1.0.1 Checklist
- [x] **#001 Project Scaffolding:** Initial infrastructure injected by SocialSeed Tasker.
- [x] **#002 First Component:** Implementation of the first domain component.
- [x] **Dependency Enforcement Tests:** Unit tests for dependency closure validation.
- [x] **Real-Test Evaluation:** Black-box evaluation framework (prueba-el-proyecto.md).
- [x] **DX Scores:** Developer Experience metrics from real-test evaluations.

### Release History
| Version | Date | Description |
|---------|------|-------------|
| 1.0.1   | 2026-05-05 | Quality & Testing Release |
| 1.0.0   | 2026-05-04 | Full Autonomy Release |
