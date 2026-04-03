# Issue #03: Define TaskRepositoryInterface and Core Actions

## Description

Define the repository interface and core domain actions in `src/socialseed_tasker/core/task_management/actions.py`. This file establishes the contract that all storage backends (Neo4j graph database and local files) must implement, following the **Repository Pattern**.

### Required Interface: `TaskRepositoryInterface`

An abstract base class (or Protocol) defining the contract for task storage:

```python
class TaskRepositoryInterface(Protocol):
    def create_issue(self, issue: Issue) -> None: ...
    def get_issue(self, issue_id: UUID) -> Issue | None: ...
    def update_issue(self, issue_id: UUID, updates: dict) -> Issue: ...
    def close_issue(self, issue_id: UUID) -> Issue: ...
    def delete_issue(self, issue_id: UUID) -> None: ...
    def list_issues(self, component_id: UUID | None = None, status: IssueStatus | None = None) -> list[Issue]: ...
    def add_dependency(self, issue_id: UUID, depends_on_id: UUID) -> None: ...
    def remove_dependency(self, issue_id: UUID, depends_on_id: UUID) -> None: ...
    def get_dependencies(self, issue_id: UUID) -> list[Issue]: ...
    def get_dependents(self, issue_id: UUID) -> list[Issue]: ...
    def create_component(self, component: Component) -> None: ...
    def get_component(self, component_id: UUID) -> Component | None: ...
    def list_components(self, project: str | None = None) -> list[Component]: ...
```

### Required Core Actions

Implement pure domain logic functions that use the repository:

- `create_issue_action()`: Creates an issue with validation (title non-empty, component exists)
- `close_issue_action()`: Closes an issue, validates no open dependencies remain
- `move_issue_action()`: Moves an issue between components
- `add_dependency_action()`: Adds a [:DEPENDS_ON] relationship, validates no circular dependencies
- `remove_dependency_action()`: Removes a [:DEPENDS_ON] relationship
- `get_blocked_issues_action()`: Returns issues that are blocked by open dependencies
- `get_dependency_chain_action()`: Returns the full transitive dependency chain for an issue

### Requirements

- **Pure Python only** - no imports from Neo4j, FastAPI, Typer, or any external framework
- Use `Protocol` from `typing` for the interface (not ABC) for better flexibility
- All actions must accept the repository as a parameter (dependency injection)
- Each action must be documented with docstrings explaining Intent and Business Value
- Include proper error types (custom exceptions like `IssueNotFoundError`, `CircularDependencyError`, `ComponentNotFoundError`)
- Circular dependency detection must be implemented in `add_dependency_action` using graph traversal (BFS/DFS)

### Business Value

The Repository Pattern decouples business logic from storage implementation, enabling seamless switching between Neo4j and local file storage. Core actions encapsulate business rules (like "cannot close an issue with open dependencies") that must be enforced regardless of how the system is accessed (CLI, API, or direct agent communication).

## Status: COMPLETED
