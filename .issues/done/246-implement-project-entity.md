# Issue #246: Implement Project Entity and Domain Model

## Description

Define the core `Project` entity in `src/socialseed_tasker/core/task_management/entities.py`. Currently, the system handles projects as simple strings within Components, but the v1.0 specification requires a full-fledged entity to hold architectural context and governance rules.

### Required Entity: `Project`

- `id`: Unique identifier (UUID)
- `name`: Official name of the project
- `slug`: URL-friendly identifier (e.g., `socialseed-tasker`)
- `description`: Detailed description of the project
- `repositoryUrl`: Link to the remote Git repository
- `basePackage`: Root package/namespace (e.g., `socialseed_tasker`)
- `visibility`: Enum (PUBLIC, PRIVATE)
- `status`: Enum (ACTIVE, ARCHIVED, etc.)
- `techStack`: List of all integrated technologies
- `mainStack`: Core technologies (e.g., `['Spring Boot', 'Neo4j']`)
- `architectureStyle`: Architectural pattern (e.g., `Hexagonal`)
- `version`: Current semantic version
- `conventionsUrl`: Link to coding standards
- `conventionsRules`: JSON/String with specific rules for AI Agents
- `lastFullScan`: Timestamp of the last repository analysis
- `globalStatus`: Enum (DEVELOPMENT, STAGING, PRODUCTION)
- `createdAt`: Creation timestamp
- `updatedAt`: Last update timestamp

### Requirements

- Use **Pydantic v2** for schemas and validation.
- Standardize all property names to **camelCase** to match the Graph Data Model documentation.
- Update `Component` and `Issue` entities if necessary to reference `Project` by ID instead of just a string name.
- Include proper type hints and docstrings documenting Intent and Business Value.

### Business Value

The `Project` node is the root of the graph. Having a rich domain model for it allows AI agents to understand the global architectural context, follow specific project conventions, and perform cross-component analysis with high precision.

## Status: COMPLETED
