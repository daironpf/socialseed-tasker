# Issue #84: Graph Policy Engine

## Description

Implement "Rules of the Graph" - policy definitions that enforce architectural constraints at write time. For example, "Layer A cannot touch Layer C" or "Components in 'frontend' cannot depend on 'database'".

## Requirements

- Create policy definition format (YAML/JSON) for graph rules
- Implement rule engine that evaluates policies at write time
- Support rule types: forbidden_paths, required_dependencies, max_depth_per_component
- Add policy management API: CRUD for policy definitions
- Integrate with Dependency Guard for enforcement

## Technical Details

### Policy Definition Format
```yaml
policies:
  - name: "frontend-backend-separation"
    description: "Frontend components cannot directly access database"
    rules:
      - type: "forbidden_path"
        from: "component.type:frontend"
        to: "component.type:database"
        
  - name: "max-dependency-depth"
    description: "Components cannot have more than 3 levels of dependencies"
    rules:
      - type: "max_depth"
        value: 3
```

### API Endpoints
- `GET /policies` - List all policies
- `POST /policies` - Create policy
- `PUT /policies/{id}` - Update policy
- `DELETE /policies/{id}` - Delete policy
- `GET /policies/validate/{issue_id}` - Validate issue against policies

## Business Value

Enforces architectural boundaries defined in project governance rules. Prevents architectural drift over time.

## Status: COMPLETED