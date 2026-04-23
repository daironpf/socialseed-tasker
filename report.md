# SocialSeed Tasker - Testing & Evaluation Report

## Environment Setup
- **OS**: Windows
- **Python**: 3.14 (Venv created in `temporal/.venv`)
- **Infrastructure**: Docker Compose (Neo4j, FastAPI, Vue.js)

## Initial Observations

### Positive Points
- The `pyproject.toml` is well-structured and handles dependencies correctly.
- Docker Compose setup is straightforward and includes health checks for Neo4j.
- The CLI has a clear help system and uses `rich` for beautiful output.

### Improvements & Issues Detected

#### 1. CLI Authentication UX
- **Issue**: The CLI requires the Neo4j password for every command if not set as an environment variable.
- **Impact**: It's tedious for manual use.
- **Recommendation**: Implement a way to persist session or configuration (e.g., `tasker login` or saving to a local config file after the first successful connection).

#### 2. Entry Points on Windows
- **Issue**: After `pip install -e .`, the `tasker` and `socialseed-tasker` commands were not immediately available in the `Scripts` folder of the venv (needed to run via `python -m socialseed_tasker...`).
- **Impact**: Might be a Windows-specific behavior or an issue with Python 3.14.
- **Recommendation**: Verify entry point generation in the build process for different OS/Python versions.

#### 3. Component Creation Output
- **Issue**: The output only shows the ID.
- **Impact**: Hard to track which ID belongs to which component in a batch script without extra parsing.
- **Recommendation**: Show both the Name and the ID in the success message.

#### 4. Project Initialization (tasker init)
- **Observation**: The `init` command scaffolds a useful structure for external projects.
- **Issue**: It creates a `tasker/` subdirectory inside the target. If a user is already in a `tasker/` folder or wants it in the root, it might be redundant.
- **Recommendation**: Add a flag to initialize in-place (without creating the `tasker/` subfolder).

#### 5. Issue Listing Verbosity
- **Issue**: `tasker issue list` does not show issue titles by default, only IDs, status, and priority.
- **Impact**: It's hard to identify issues without titles in a terminal view.
- **Recommendation**: Include the Title (truncated if necessary) in the default table view.

#### 6. Dependency Graph Logic
- **Observation**: The `analyze impact` command correctly identifies blocked issues and risk levels based on the graph. This is a very strong feature.

---

## Real-World Test: Ecommerce Project (50 Issues)
*Status: Resolved and Fully Operational*

- **Issues Created**: 26 connected issues across two projects (`ecommerce-store` and `demo-platform`) via `seed_issues_v2.py`.
- **Frontend Board Empty Bug**: 
    - **Diagnostics**: The board was crashing due to a TypeError (`data.data.forEach is not a function`).
    - **Root Cause**: The backend API for `/components` uses pagination (`PaginatedResponse`), but the frontend `componentsApi.ts` expected a flat array.
    - **Resolution**: Fixed the TypeScript types and response parsing in the API client to correctly extract `.items`.
- **Graph Visualization Disconnected**:
    - **Diagnostics**: The `GraphView.vue` component existed but wasn't exposed in the router, and once exposed, the nodes had no connecting edges.
    - **Root Cause**: The original seed scripts only created issue nodes without their `[:DEPENDS_ON]` relationships.
    - **Resolution**: Added the route, updated the `AppHeader` navigation, and implemented a robust `seed_issues_v2.py` that explicitly links dependencies.

## 5. Next Steps & Pending Issues to Create

1.  **Frontend Authentication Handling**: When `TASKER_AUTH_ENABLED=true` is set on the backend, the Vue dashboard breaks with `401 Unauthorized`. The frontend needs a login screen or an environment variable setup for `X-API-Key`.
2.  **API Schema Synchronization**: The discrepancy between the backend pagination and the frontend expected types indicates a lack of OpenAPI client generation. Implement `openapi-typescript` or similar to auto-generate frontend API types.
3.  **UI Store Reactivity Improvements**: While the project filter now works, managing local cache filtering vs backend fetching logic should be refactored to rely purely on the backend's paginated responses to prevent edge-case state mismatch.
4.  **Persistent Authentication**: Store credentials locally after first login to improve CLI UX.
5.  **Flexible Initialization**: Options for in-place scaffolding in `tasker init`.
