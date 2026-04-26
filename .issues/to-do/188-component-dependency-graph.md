# Issue #188 - Implement Component Dependency Graph

## Description

Components should be able to declare dependencies on other components, enabling system architecture visualization and impact analysis at the component level.

## Problem

Currently, only Issues can have dependencies. Components are treated as isolated units, but real systems have component-level dependencies (e.g., auth-service depends on user-database).

## Acceptance Criteria

- [ ] Add `Component`-to-`Component` relationship: `(Component)-[:DEPENDS_ON]->(Component)`
- [ ] New API endpoint: `POST /components/{id}/dependencies`
- [ ] New API endpoint: `GET /components/{id}/dependencies`
- [ ] New API endpoint: `GET /components/{id}/dependents`
- [ ] Update CLI: `tasker component add-dep <comp> --depends-on <other>`
- [ ] Update impact analysis to include component dependencies
- [ ] Add `/analysis/component-impact/{id}` endpoint

## Technical Notes

- Component dependencies are different from Issue dependencies
- Use case: "If auth-service fails, what breaks?" → traverses component dependencies
- Query example:
  ```cypher
  MATCH (c:Component)-[:DEPENDS_ON]->(dep:Component)
  WHERE c.name = 'auth-service'
  RETURN dep.name
  ```

## API Impact

| Endpoint | Method | Description |
|----------|--------|--------------|
| `/components/{id}/dependencies` | GET | List components this component depends on |
| `/components/{id}/dependents` | GET | List components that depend on this |
| `/components/{id}/dependencies` | POST | Add component dependency |
| `/analysis/component-impact/{id}` | GET | Full impact analysis |

## Business Value

- "Which components will break if auth-service goes down?"
- Architecture visualization at component level
- Better risk management for enterprise