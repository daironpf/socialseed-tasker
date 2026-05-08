# Issue #262: Complete Policy Repository with Graph Relationships

## Description

According to the Graph Data Model (GraphDataModelDetails.md), the **Policy** node represents a set of architectural rules, coding standards, or security constraints that the system must enforce. It serves as the "Law" of the repository, which Agents must consult during their reasoning phase.

### Current State

The Policy entity exists in `core/project_analysis/policy.py` with:
- `id` (UUID)
- `name` (String)
- `description` (String)
- `severity` (Enum: INFO, WARNING, BLOCKER)
- `targetScope` (Enum: CODE_SYMBOL, COMPONENT, COMMIT, PROJECT)
- `logicDefinition` (JSON/String)
- `remediationStrategy` (String)
- `autofixTemplate` (String)
- `isActive` (Boolean)
- `createdAt` (DateTime)

There are also some API endpoints in `routes.py` (create_policy, get_policy, delete_policy, validate_policy).

However, there is **no dedicated PolicyRepository** in `storage/graph_database/` to persist policies and their relationships to Neo4j.

### Requirements

#### Create `storage/graph_database/policy_repository.py`

Implement a `PolicyRepository` class with the following methods:

```python
class PolicyRepository:
    def create_policy(self, policy: Policy) -> None:
        """Create a new Policy node in Neo4j."""
    
    def get_policy(self, policy_id: str) -> Policy | None:
        """Get a policy by ID."""
    
    def get_policy_by_name(self, name: str) -> Policy | None:
        """Get a policy by name."""
    
    def update_policy(self, policy_id: str, updates: dict) -> Policy:
        """Update policy properties."""
    
    def delete_policy(self, policy_id: str) -> None:
        """Delete a policy from Neo4j."""
    
    def list_policies(
        self,
        severity: str | None = None,
        target_scope: str | None = None,
        is_active: bool | None = None,
    ) -> list[Policy]:
        """List policies with optional filters."""
    
    # Relationships
    def link_policy_to_project(self, policy_id: str, project_id: str) -> None:
        """Create (Project)-[:ENFORCES]->(Policy) relationship."""
    
    def link_policy_to_agent(self, policy_id: str, agent_id: str) -> None:
        """Create (Agent)-[:MUST_COMPLY_WITH]->(Policy) relationship."""
    
    def link_policy_to_component(self, policy_id: str, component_id: str) -> None:
        """Create (Policy)-[:APPLIES_TO]->(Component) relationship."""
    
    def get_policies_for_project(self, project_id: str) -> list[Policy]:
        """Get all policies enforced by a project."""
    
    def get_policies_for_agent(self, agent_id: str) -> list[Policy]:
        """Get all policies an agent must comply with."""
    
    def get_policies_for_component(self, component_id: str) -> list[Policy]:
        """Get all policies that apply to a component."""
    
    def validate_against_policies(
        self,
        entity_type: str,  # "issue", "commit", "component"
        entity_id: str,
    ) -> list[PolicyViolation]:
        """Validate an entity against all applicable policies."""
```

#### Add Policy Queries in `queries.py`

```cypher
CREATE_POLICY = """..."""
GET_POLICY = """..."""
GET_POLICY_BY_NAME = """..."""
UPDATE_POLICY = """..."""
DELETE_POLICY = """..."""
LIST_POLICIES = """..."""
LINK_POLICY_TO_PROJECT = """..."""
LINK_POLICY_TO_AGENT = """..."""
LINK_POLICY_TO_COMPONENT = """..."""
GET_POLICIES_FOR_PROJECT = """..."""
GET_POLICIES_FOR_AGENT = """..."""
GET_POLICIES_FOR_COMPONENT = """..."""
```

#### Update API Endpoints

Existing endpoints should be updated to use the new repository:
- `POST /api/v1/policies` - Create policy (use repository)
- `GET /api/v1/policies/{policy_id}` - Get policy (use repository)
- `PUT /api/v1/policies/{policy_id}` - Update policy (use repository)
- `DELETE /api/v1/policies/{policy_id}` - Delete policy (use repository)
- `GET /api/v1/policies` - List policies (use repository)

Add new relationship endpoints:
- `POST /api/v1/policies/{policy_id}/link/project/{project_id}` - Link policy to project
- `POST /api/v1/policies/{policy_id}/link/agent/{agent_id}` - Link policy to agent
- `POST /api/v1/policies/{policy_id}/link/component/{component_id}` - Link policy to component
- `GET /api/v1/policies/project/{project_id}` - Get policies for project
- `GET /api/v1/policies/agent/{agent_id}` - Get policies for agent

#### Relationships to Implement (from model)

The Policy node has these key relationships:
- **(Project)-[:ENFORCES]->(Policy):** Global or project-specific rules
- **(Agent)-[:MUST_COMPLY_WITH]->(Policy):** Governance link agents must check
- **(ReasoningNode)-[:VALIDATED_AGAINST]->(Policy):** Records agent checked this rule
- **(Commit)-[:VIOLATES]->(Policy):** Audit for changes that break policies
- **(Policy)-[:APPLIES_TO]->(Component):** Granular rules for specific modules

### Implementation Note (from model)

The Policy node enables "Autonomous Quality Assurance":
1. Agent generates a ReasoningNode
2. Agent queries graph for all Policy nodes linked to the Project
3. Agent evaluates thought and proposed code against these policies
4. If BLOCKER found, Agent uses remediationStrategy to self-correct
5. If autofixTemplate exists, Agent can apply it before presenting to Human

This ensures the Human-in-the-Loop only spends time on architectural decisions, not linting errors.

### Business Value

The Policy repository enables:
1. **Governance automation** - Agents automatically check policies before acting
2. **Audit trails** - Track which policies were validated against each decision
3. **Component-specific rules** - Stricter policies for auth-service, etc.
4. **Auto-fix capabilities** - Agents can self-correct using autofixTemplate

## Status: COMPLETED

## Priority: MEDIUM