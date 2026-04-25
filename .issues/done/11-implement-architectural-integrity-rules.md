# Issue #11: Implement Project Analysis - Architectural Integrity Rules

## Description

Build the project analysis module in `src/socialseed_tasker/core/project_analysis/`. This module implements architectural integrity checks that verify whether actions contradict established architectural rules stored in the Neo4j graph.

### Requirements

#### Module Structure

**`rules.py`** - Rule definitions
- `ArchitecturalRule` entity/model
- Rule types and validation logic
- Built-in rules and custom rule support

**`analyzer.py`** - Rule evaluation engine
- Rule checker that evaluates actions against stored rules
- Integration with repository to fetch stored rules
- Violation reporting

#### ArchitecturalRule Entity

```python
class ArchitecturalRule(BaseModel):
    id: UUID
    name: str
    description: str
    rule_type: RuleType  # FORBIDDEN_DEPENDENCY, FORBIDDEN_TECHNOLOGY, REQUIRED_PATTERN, etc.
    source_pattern: str  # Component/label pattern to match
    target_pattern: str  # Component/label pattern to check against
    severity: Severity  # ERROR, WARNING
    is_active: bool = True
    created_at: datetime
```

#### Built-in Rule Types

**`FORBIDDEN_DEPENDENCY`**
- Prevents issues in one component from depending on issues in another component
- Example: "UI components cannot depend on Database components directly"
- Cypher pattern: Check if source component -> target component relationship is forbidden

**`FORBIDDEN_TECHNOLOGY`**
- Prevents issues from using certain technologies in specific components
- Example: "Cannot use SQL in a Graph-only module"
- Validation: Check issue labels/description against forbidden technology list for the component

**`REQUIRED_PATTERN`**
- Requires issues to follow certain patterns
- Example: "All API changes must have a corresponding test issue"
- Validation: Check if related issues exist with required labels

**`MAX_DEPENDENCY_DEPTH`**
- Limits how deep dependency chains can go
- Example: "No issue can be more than 5 dependencies away from a root issue"
- Validation: Traverse dependency chain and check depth

#### Analyzer Implementation

```python
class ArchitecturalAnalyzer:
    def __init__(self, repository: TaskRepositoryInterface):
        self.repository = repository
    
    def validate_issue_creation(self, issue: Issue) -> ValidationResult:
        """Check if creating this issue violates any architectural rules."""
        violations = []
        rules = self._get_active_rules()
        
        for rule in rules:
            violation = self._evaluate_rule(rule, issue)
            if violation:
                violations.append(violation)
        
        return ValidationResult(violations=violations)
    
    def validate_dependency(self, issue_id: UUID, depends_on_id: UUID) -> ValidationResult:
        """Check if adding this dependency violates any architectural rules."""
        violations = []
        rules = self._get_active_rules()
        
        for rule in rules:
            violation = self._evaluate_dependency_rule(rule, issue_id, depends_on_id)
            if violation:
                violations.append(violation)
        
        return ValidationResult(violations=violations)
    
    def add_rule(self, rule: ArchitecturalRule) -> None:
        """Store a new architectural rule."""
        ...
    
    def list_rules(self) -> list[ArchitecturalRule]:
        """List all active architectural rules."""
        ...
    
    def remove_rule(self, rule_id: UUID) -> None:
        """Remove an architectural rule."""
        ...
```

#### ValidationResult

```python
class Violation(BaseModel):
    rule_id: UUID
    rule_name: str
    severity: Severity
    message: str
    suggestion: str  # How to fix the violation

class ValidationResult(BaseModel):
    is_valid: bool
    violations: list[Violation]
    
    @property
    def has_errors(self) -> bool:
        return any(v.severity == Severity.ERROR for v in self.violations)
    
    @property
    def has_warnings(self) -> bool:
        return any(v.severity == Severity.WARNING for v in self.violations)
```

#### Integration Points
- `create_issue_action()` must call `ArchitecturalAnalyzer.validate_issue_creation()` before creating
- `add_dependency_action()` must call `ArchitecturalAnalyzer.validate_dependency()` before adding
- CLI and API must display validation results to the user
- Warnings should be displayed but not block the action
- Errors should block the action and return a clear error message

### Requirements
- Pure Python in `core/project_analysis/` - no external dependencies
- Rules must be storable in both Neo4j and file storage
- Rule evaluation must be efficient (cache active rules)
- Clear error messages explaining which rule was violated and why
- Support for custom user-defined rules in addition to built-in rules

### Business Value

Architectural integrity checks prevent the codebase from degrading over time. By encoding architectural decisions as rules in the graph, the system actively prevents developers and AI agents from making changes that violate established patterns. This is critical for maintaining a clean architecture across multiple projects and agents.

## Status: COMPLETED
