# Project Versions

## [1.0.3] - 2026-05-24

### v1.0.3 Checklist
- [x] **#323 Deterministic API Contract Testing and Mock Server:** Added contract testing utilities, mock server, OpenAPI helpers, CLIs, unit/integration tests, and CI workflow.

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
