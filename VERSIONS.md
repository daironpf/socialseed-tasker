# Project Versions

## [1.0.1] - 2026-05-25

### v1.0.1 Checklist
- [x] **#326 Schema init CypherSyntaxError:** Fixed invalid `DEPENDS_ON` relationship index syntax in `neo4j_queries.py` — changed `(i:Issue) ON (i.timestamp)` to `() ON (r.timestamp)`.
- [x] **#327 NameError on logger:** Added missing `logger = logging.getLogger(__name__)` in `neo4j_driver.py` to prevent crash in exception handlers.

## [1.0.0] - 2026-05-22

### v1.0.0 Checklist
- [x] **#001-#325 All Issues:** All 325+ issues are resolved across scaffolding, API, CLI, frontend, Neo4j, Docker, agents, code-graph, RAG, secrets, contracts, CI/CD, and release automation.

### Release History
| Version | Date | Description |
|---------|------|-------------|
| 1.0.1   | 2026-05-25 | Bugfix: Schema init CypherSyntaxError & logger NameError |
| 1.0.0   | 2026-05-24 | Full Release — All issues resolved |
