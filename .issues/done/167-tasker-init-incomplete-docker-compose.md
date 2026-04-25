# Issue #167: tasker init Generates Incomplete docker-compose

## Description
The `tasker init` command generates a docker-compose.yml file that only contains Neo4j database service. The REST API container (tasker-api) and Frontend (tasker-board) are NOT included in the scaffold, making it impossible to run a complete environment for testing without additional manual configuration.

## Expected Behavior
When running `tasker init`, the generated docker-compose.yml should include ALL services from the project:
- `tasker-db` (Neo4j database)
- `tasker-api` (FastAPI REST API)
- `tasker-board` (Vue.js Frontend - Kanban Board)

## Actual Behavior
1. Run `tasker init .`
2. Check generated `tasker/docker-compose.yml`
3. Only contains Neo4j service

## Full Service Definition (Reference)
The project docker-compose.yml includes:
```yaml
services:
  tasker-db:
    image: neo4j:5.26.15-community
    ports: [7474, 7687]
    environment:
      - NEO4J_AUTH=neo4j/neoSocial
    healthcheck: cypher-shell

  tasker-api:
    build: .
    ports: [8000]
    environment:
      - TASKER_NEO4J_URI=bolt://tasker-db:7687
      - TASKER_NEO4J_USERNAME=neo4j
      - TASKER_NEO4J_PASSWORD=neoSocial
    depends_on: tasker-db (healthy)

  tasker-board:
    build: ./frontend
    ports: [8080]
    depends_on: tasker-api
```

## Steps to Reproduce
1. Run `tasker init .`
2. Check generated docker-compose.yml
3. Observe only Neo4j service exists

## Status: COMPLETED

## Priority: CRITICAL

## Component
Infrastructure (tasker init, docker-compose template)

## Suggested Fix
Update the docker-compose template in `src/socialseed_tasker/assets/templates/docker-compose.yml` to include ALL services:
- `tasker-db` (Neo4j)
- `tasker-api` (FastAPI application)
- `tasker-board` (Vue.js Frontend)

Alternative: Provide flags like `tasker init --with-api` and `tasker init --with-frontend`.

## Impact
Users cannot spin up a complete test environment using only the scaffolded files. This breaks the real-test evaluation workflow (black-box testing requires API to create issues).

## Related Issues
- Issue #168: Missing Documentation in Scaffold (related)
- Issue #153: Flexible Initialization (partially related)
- Real-Test Evaluation Profile: DevOps