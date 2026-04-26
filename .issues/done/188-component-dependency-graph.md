# Issue #188 - Implement Component Dependency Graph

## Description

Components should be able to declare dependencies on other components, enabling system architecture visualization and impact analysis at the component level.

## Problem

Currently, only Issues can have dependencies. Components are treated as isolated units, but real systems have component-level dependencies (e.g., auth-service depends on user-database).

## Acceptance Criteria

- [x] Add `Component`-to-`Component` relationship: `(Component)-[:DEPENDS_ON]->(Component)` → **Query added**
- [x] New API endpoint: `POST /components/{id}/dependencies` → **Implemented**
- [x] New API endpoint: `GET /components/{id}/dependencies` → **Implemented**
- [x] New API endpoint: `GET /components/{id}/dependents` → **Implemented**
- [ ] Update CLI: `tasker component add-dep <comp> --depends-on <other>` → **Not implemented**
- [ ] Update impact analysis to include component dependencies → **Not implemented**
- [ ] Add `/analysis/component-impact/{id}` endpoint → **Not implemented**

## Implementation

Added queries:
- `ADD_COMPONENT_DEPENDENCY` - Creates `(Component)-[:DEPENDS_ON]->(Component)`
- `REMOVE_COMPONENT_DEPENDENCY` - Removes relationship
- `GET_COMPONENT_DEPENDENCIES` - Gets components this component depends on
- `GET_COMPONENT_DEPENDENTS` - Gets components that depend on this

Added repository methods:
- `add_component_dependency(component_id, depends_on_id)`
- `remove_component_dependency(component_id, depends_on_id)`
- `get_component_dependencies(component_id)` → list[Component]
- `get_component_dependents(component_id)` → list[Component]

Added API endpoints:
- `POST /api/v1/components/{id}/dependencies` with body `{"depends_on_id": "..."}`
- `GET /api/v1/components/{id}/dependencies`
- `GET /api/v1/components/{id}/dependents`

## API Impact

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/components/{id}/dependencies` | GET | List components this component depends on |
| `/components/{id}/dependents` | GET | List components that depend on this |
| `/components/{id}/dependencies` | POST | Add component dependency |

## Business Value

- "Which components will break if auth-service goes down?"
- Architecture visualization at component level
- Better risk management for enterprise