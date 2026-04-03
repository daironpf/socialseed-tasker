# Issue #04: Configure Neo4j Docker Compose with APOC and Memory Settings

## Description

Update and finalize the `docker-compose.yml` configuration for Neo4j Community Edition. This configuration must be production-ready and support the graph-based task management requirements of the SocialSeed ecosystem.

### Requirements

#### Neo4j Configuration
- Use Neo4j 5.x Community Edition image
- Enable **APOC plugins** (required for advanced graph operations)
- Configure proper port mappings for multi-instance scenarios (non-default ports to avoid conflicts)
- Set up persistent volumes for data, logs, import, and plugins directories

#### Memory Configuration
- Allocate **4GB heap memory** (`NEO4J_dbms_memory_heap_max__size=4G`) to ensure queries stay fast as the graph of issues grows
- Configure page cache appropriately for the expected dataset size

#### Authentication
- Set up default credentials via `NEO4J_AUTH` environment variable
- Credentials should be configurable (not hardcoded in production)

#### Health Check
- Implement a proper healthcheck using `cypher-shell` to verify Neo4j is ready to accept connections
- Configure appropriate intervals, timeouts, and retries

#### Required Environment Variables
```yaml
NEO4J_AUTH=neo4j/<password>
NEO4J_PLUGINS=["apoc"]
NEO4J_dbms_memory_heap_max__size=4G
NEO4J_server_http_listen__address=:<custom_http_port>
NEO4J_server_http_advertised__address=:<custom_http_port>
NEO4J_server_bolt_listen__address=:<custom_bolt_port>
NEO4J_server_bolt_advertised__address=:<custom_bolt_port>
```

#### Volume Mounts
- `./neo4j/data:/data` - Database files
- `./neo4j/logs:/logs` - Query and debug logs
- `./neo4j/import:/import` - CSV import directory
- `./neo4j/plugins:/plugins` - APOC and other plugins

### Business Value

A properly configured Neo4j instance is the backbone of the graph-based task management system. APOC plugins enable advanced graph algorithms for dependency analysis and causal traceability. Proper memory allocation ensures the system remains performant as projects scale to thousands of interconnected issues.

## Status: COMPLETED
