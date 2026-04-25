# Issue #52: Create Neo4j-backed API endpoint for the frontend

## Description

Create a dedicated API entry point that uses the Neo4j repository backend, so the Vue frontend can connect to Neo4j directly.

### Requirements

- Create `src/socialseed_tasker/entrypoints/web_api/api_neo4j.py` similar to `api.py` but wired with Neo4j repository
- The file should:
  - Create a Neo4j driver from environment config
  - Instantiate `Neo4jTaskRepository`
  - Create the FastAPI app with `create_app(repository)`
  - Export the `app` variable for uvicorn

- Update `docker-compose.yml` to ensure Neo4j is available with correct credentials
- Document the two startup modes:
  - File backend: `uvicorn socialseed_tasker.entrypoints.web_api.api:app`
  - Neo4j backend: `uvicorn socialseed_tasker.entrypoints.web_api.api_neo4j:app`

### Technical Details

- Reuse existing `create_app()` function from `app.py`
- Neo4j config from environment: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`
- Default Neo4j credentials: `neo4j` / `tasker_password` on `bolt://localhost:7689`

### Expected File Paths

- `src/socialseed_tasker/entrypoints/web_api/api_neo4j.py`
- Update `docker-compose.yml` if needed

### Business Value

The Vue frontend needs to connect to Neo4j for full graph capabilities (dependency traversal, impact analysis, root cause). This provides the Neo4j-backed API entry point.

## Status: COMPLETED
