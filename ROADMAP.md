# Project Roadmap

**Last updated**: 2026-05-25

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
