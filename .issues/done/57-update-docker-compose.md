# Issue #57: Update docker-compose.yml with all services

## Description

Configure docker-compose.yml to orchestrate all services: Neo4j, FastAPI backend, and Vue frontend.

### Requirements

- Define 3 services: neo4j, api, frontend
- Configure networking between services
- Set up environment variables for each service
- Add health checks and dependencies
- Expose ports: 8000 (API), 8080 (Frontend), 18082 (Neo4j Browser), 17689 (Neo4j Bolt)

### Technical Details

- Use docker network for inter-service communication
- Service dependencies: api depends on neo4j, frontend depends on api
- Health checks for neo4j and api
- API uses Neo4j repository by default

### Expected File Paths

- `docker-compose.yml` (updated)

## Status: COMPLETED

## Implementation Notes

- Updated docker-compose.yml with:
  - neo4j: Graph database with APOC plugin, exposed ports 18082, 17689
  - api: FastAPI backend using Neo4j repository, port 8000
  - frontend: nginx serving Vue app, port 8080
  - All services in socialseed-network bridge network
  - Health checks for neo4j and api
  - Proper dependencies (api waits for neo4j, frontend waits for api)