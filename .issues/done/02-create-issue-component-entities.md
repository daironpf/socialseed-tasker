# Issue #02: Create Issue and Component Entities in Core Domain

## Description

Define the core domain entities in `src/socialseed_tasker/core/task_management/entities.py`. These entities are the foundation of the graph-based task management system and must be pure Python with no external dependencies.

### Required Entities

#### `Component` Entity
Represents a logical component/module within a project that can have tasks assigned to it.

- `id`: Unique identifier (UUID)
- `name`: Component name (non-empty string)
- `description`: Optional description
- `project`: Project identifier this component belongs to
- `created_at`: Timestamp of creation
- `updated_at`: Timestamp of last update

#### `Issue` Entity
Represents a task/issue in the system. This is NOT a simple to-do item; it must support advanced graph-based features.

- `id`: Unique identifier (UUID)
- `title`: Issue title (non-empty string, max 200 chars)
- `description`: Detailed description (Markdown supported)
- `status`: Enum (OPEN, IN_PROGRESS, CLOSED, BLOCKED)
- `priority`: Enum (LOW, MEDIUM, HIGH, CRITICAL)
- `component_id`: Reference to the Component this issue belongs to
- `labels`: List of string labels/tags
- `dependencies`: List of Issue IDs this issue depends on ([:DEPENDS_ON] relationships)
- `blocks`: List of Issue IDs this issue blocks ([:BLOCKS] relationships)
- `affects`: List of Issue IDs this issue affects ([:AFFECTS] relationships)
- `created_at`: Timestamp of creation
- `updated_at`: Timestamp of last update
- `closed_at`: Timestamp when closed (nullable)
- `architectural_constraints`: List of architectural rules this issue must comply with

### Requirements

- Use **Pydantic v2** for all data schemas and validation
- All entities must be immutable (frozen=True in Pydantic) where appropriate
- Include proper type hints for all fields
- Include docstrings documenting Intent and Business Value for each entity
- Entities must be serializable to/from JSON for storage abstraction
- No imports from Neo4j, FastAPI, Typer, or any external framework in this file

### Business Value

These entities form the domain model that powers the entire task management system. They encode the graph relationships (dependencies, blocks, affects) that enable causal traceability and architectural integrity checks. Proper design here prevents cascading issues throughout the codebase.

## Status: COMPLETED
