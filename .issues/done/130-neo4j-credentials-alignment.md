# Issue #130: Neo4j Credentials Inconsistency

## Description

Neo4j credentials are not aligned across different components:
- Docker Compose: configured as `neo4j/neoSocial`
- CLI: requires `TASKER_NEO4J_PASSWORD` env var (default empty)
- .env.example: has different hardcoded password

This causes confusion and makes testing harder.

### Current Files and Their Values

| File | User | Password |
|------|------|---------|
| docker-compose.yml | neo4j | neoSocial |
| assets/templates/.env.example | neo4j | (varies) |
| CLI default | neo4j | "" (empty) |

### Requirements

1. Standardize on `neo4j/neoSocial` everywhere
2. Update `.env.example` to have correct default password
3. Add password to scaffolded `.env` in `tasker init`
4. Document in README.md which password to use

### Files to Update

- `src/socialseed_tasker/assets/templates/configs/.env.example`
- `src/socialseed_tasker/assets/templates/docker-compose.yml`
- `README.md`
- `docker-compose.yml` (source project)

### Priority: MEDIUM

### Status: COMPLETED (2026-04-11) - Already aligned

### Verification

All credentials are now aligned to `neo4j/neoSocial`:

```bash
# docker-compose.yml
NEO4J_AUTH=${NEO4J_USERNAME:-neo4j}/${NEO4J_PASSWORD:-neoSocial}
TASKER_NEO4J_PASSWORD=neoSocial

# templates/docker-compose.yml  
NEO4J_AUTH=neo4j/neoSocial

# templates/.env.example
TASKER_NEO4J_USER=neo4j
TASKER_NEO4J_PASSWORD=neoSocial

# documentation
# Neo4j Browser: neo4j/neoSocial
```