# Architectural Policies - Tasker v1.0.0

This file contains default architectural policies that you can adopt for your project.
These policies are designed to maintain code quality and prevent architectural drift.

## How to Use

When you run `tasker init`, you'll be asked to select which policies to adopt.
You can also create custom policies later using `tasker policy create`.

## Available Policies

---

### 1. No Circular Dependencies

**Scope:** COMPONENT  
**Severity:** BLOCKER  
**Description:** Prevents circular dependencies between components.

```yaml
name: no-circular-dependencies
description: Prevent circular dependencies between components
rules:
  - rule_type: forbidden_label_dependency
    from_pattern: "component.type:*"
    to_pattern: "component.type:*"
    description: No component should depend on itself
```

---

### 2. Auth Service Isolation

**Scope:** COMPONENT  
**Severity:** BLOCKER  
**Description:** Auth service must not depend on UI components.

```yaml
name: auth-service-isolation
description: Auth service must not depend on UI components
rules:
  - rule_type: forbidden_dependency
    from_pattern: "component.type:auth"
    to_pattern: "component.type:frontend"
    description: Auth service should not import frontend code
```

---

### 3. Max Dependency Depth

**Scope:** COMPONENT  
**Severity:** WARNING  
**Description:** Limits the maximum depth of dependency chains.

```yaml
name: max-dependency-depth
description: Maximum dependency chain depth is 5
rules:
  - rule_type: max_depth
    max_depth: 5
    description: Dependency chain should not exceed 5 levels
```

---

### 4. No Database in API Layer

**Scope:** COMPONENT  
**Severity:** BLOCKER  
**Description:** API handlers should not directly access databases.

```yaml
name: no-db-in-api
description: API layer should not directly access database
rules:
  - rule_type: forbidden_path
    from_pattern: "component.type:api"
    to_pattern: "component.type:database"
    description: API handlers must use repositories, not direct DB calls
```

---

### 5. Test Coverage Required

**Scope:** COMPONENT  
**Severity:** WARNING  
**Description:** Components must have corresponding test files.

```yaml
name: test-coverage-required
description: All components must have tests
rules:
  - rule_type: required_dependency
    from_pattern: "component.type:*"
    to_pattern: "component.type:test"
    description: Every component should have tests
```

---

### 6. No External API Calls in Core

**Scope:** CODE_SYMBOL  
**Severity:** WARNING  
**Description:** Core business logic should not make external API calls.

```yaml
name: no-external-api-in-core
description: Core domain should not make external API calls
rules:
  - rule_type: forbidden_path
    from_pattern: "component.type:core"
    to_pattern: "component.type:external"
    description: Core logic must be pure and side-effect free
```

---

### 7. Semantic Commit Messages

**Scope:** COMMIT  
**Severity:** WARNING  
**Description:** Enforces conventional commit format.

```yaml
name: semantic-commits
description: Commit messages must follow conventional format
rules:
  - rule_type: required_pattern
    from_pattern: "commit:*"
    to_pattern: "format:^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?:.+$"
    description: Use conventional commits: feat, fix, docs, etc.
```

---

### 8. Security - No Hardcoded Secrets

**Scope:** CODE_SYMBOL  
**Severity:** BLOCKER  
**Description:** Prevents hardcoded passwords, API keys, or secrets.

```yaml
name: no-hardcoded-secrets
description: No hardcoded secrets in code
rules:
  - rule_type: forbidden_pattern
    from_pattern: "symbol.type:function"
    to_pattern: 'pattern:(password|api_key|secret|token)\s*='
    description: Use environment variables or secret management
```

---

### 9. Component Ownership

**Scope:** PROJECT  
**Severity:** INFO  
**Description:** Defines ownership of components for code review.

```yaml
name: component-ownership
description: Each component must have an owner
rules:
  - rule_type: required_metadata
    from_pattern: "component.type:*"
    to_pattern: "metadata:owner"
    description: Components must have an owner label
```

---

### 10. Graph Cleanliness

**Scope:** PROJECT  
**Severity:** INFO  
**description:** Prevents orphaned issues and unused components.

```yaml
name: graph-cleanliness
description: Keep the graph clean of orphaned nodes
rules:
  - rule_type: max_orphans
    max_count: 10
    description: Maximum 10 orphaned issues allowed
```

---

### 11. Branch Lockdown

**Scope:** COMMIT  
**Severity:** BLOCKER  
**Description:** Agents must NEVER create new branches or delete any existing branch unless the user explicitly and verifiably instructs it.

```yaml
name: branch-lockdown
description: Agents must not create or delete branches without explicit user instruction
rules:
  - rule_type: forbidden_action
    from_pattern: "actor.type:agent"
    to_pattern: "action:(git checkout -b|git branch|git switch -c|git push origin --delete|git branch -d|git branch -D)"
    description: Agents must not create or delete branches. Only the user may do so after explicit verified instruction.
```

---

## Creating Custom Policies

To create a custom policy, use:

```bash
tasker policy create <policy-name> --description "..." --scope <COMPONENT|CODE_SYMBOL|COMMIT|PROJECT>
```

Or edit this file and run:

```bash
tasker policy import policies.md
```

---

## Policy Severity Levels

- **INFO**: Advisory, no blocking
- **WARNING**: Non-blocking but logged
- **BLOCKER**: Prevents the action from being completed

---

## Policy Target Scopes

- **CODE_SYMBOL**: Applied to individual functions/classes
- **COMPONENT**: Applied to entire components/modules
- **COMMIT**: Applied to git commits
- **PROJECT**: Applied at project level

---

For more information, see `docs/GRAPH_MODEL.md` and the Data Model documentation.