# Project Roadmap

**Last updated**: 2026-05-28

## Phase 1: Foundations
- [x] Environment Setup
- [x] Core Entities Definition
- [x] Basic API/CLI implementation

## Phase 2: Knowledge & Discovery
- [x] Code Graph Integration
- [x] Semantic Search (RAG)

## Phase 3: Autonomous Testing
- [x] Agent Reasoning Implementation
- [x] Automated Test Suites

---

## Known Issues
| # | Description | Severity | Location | Status |
|---|-------------|----------|----------|--------|
| 326 | Schema init crashes with CypherSyntaxError on DEPENDS_ON index | Critical | infrastructure/neo4j_driver.py | ✅ RESOLVED |
| 327 | NameError on 'logger' in neo4j_driver.py exception handler | High | infrastructure/neo4j_driver.py | ✅ RESOLVED |
| 328 | Docker build fails with 403 Forbidden from ghcr.io | Medium | .agent/tasker/Dockerfile | ✅ RESOLVED |
| 329 | Frontend copy step not documented in scaffold README | Low | src/.../templates/README.md | ✅ RESOLVED |
| 330 | Docker build fails on fresh init due to wrong context path | Medium | .agent/tasker/docker-compose.yml | ✅ RESOLVED |
| 331 | Policy creation API returns 500 from NameError on queries | High | infrastructure/neo4j_policy_repository.py | ✅ RESOLVED |
| 332 | DB disconnect returns generic 500 instead of descriptive error | Medium | infrastructure/web_api/app.py | ✅ RESOLVED |
| 333 | UnicodeEncodeError on Windows when init prints emoji | Low | cli/init_command.py | ✅ RESOLVED |
| 342 | UnicodeEncodeError on Windows when issue CLI prints emojis | Low | cli/issue_commands.py | ✅ RESOLVED |
| 343 | API command shows verbose traceback on connection error | Medium | cli/app.py | ✅ RESOLVED |
| 344 | dependency add --depends-on flag not supported by CLI | Medium | cli/dependency_commands.py | ✅ RESOLVED |
