# Issue #51: Fix Docker port conflicts and improve Neo4j CLI configuration

## Description

The Neo4j container failed to start due to port binding conflicts on Windows, and the CLI lacked convenient options for configuring Neo4j connection.

### Problems Identified

1. **Docker port conflicts**: Ports 8082 and 7689 were already in use or blocked on Windows
2. **CLI Neo4j options**: No convenient CLI options to set Neo4j URI and password
3. **Health check issue**: The health check command format was incorrect for the container

### Solutions Applied

1. Changed default ports in docker-compose.yml:
   - 8082 → 18082 (HTTP)
   - 7689 → 17689 (Bolt)

2. Added CLI options in `app.py`:
   - `--neo4j-uri` / `-u` - Set Neo4j connection URI
   - `--neo4j-password` / `-p` - Set Neo4j password

3. Fixed health check command format in docker-compose.yml

4. Updated template files:
   - `assets/templates/docker-compose.yml` - New ports
   - `assets/templates/configs/.env.example` - Updated default URI

### Usage

```bash
# Start Neo4j
docker compose up -d

# Use CLI with Neo4j
tasker --backend neo4j --neo4j-uri "bolt://localhost:17689" --neo4j-password "tasker_password" component list

# Or set environment variables
export TASKER_NEO4J_URI="bolt://localhost:17689"
export TASKER_NEO4J_PASSWORD="tasker_password"
tasker --backend neo4j component list
```

## Status: COMPLETED