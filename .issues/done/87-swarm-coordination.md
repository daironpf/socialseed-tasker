# Issue #87: Swarm Coordination

## Description

Implement multi-agent role management (Planner, Developer, Reviewer) synchronized via Graph states. Enable coordinated work across multiple AI agents with different responsibilities.

## Requirements

- Define agent roles: Planner, Developer, Reviewer, Observer
- Implement role-based permissions (what each role can do)
- Add agent registration and heartbeat system
- Create coordination state in Neo4j for agent activities
- Implement work distribution algorithm (assign issues based on role)
- Add inter-agent communication via issue comments
- Support agent collaboration on same issue

## Technical Details

### Agent Role Definition
```python
class AgentRole(str, Enum):
    PLANNER = "planner"      # Can create issues, set priorities
    DEVELOPER = "developer"  # Can modify issues, create dependencies
    REVIEWER = "reviewer"    # Can comment, approve, close
    OBSERVER = "observer"    # Read-only access
```

### Agent Registration
- `POST /agents/register` - Register agent with role
- `POST /agents/{id}/heartbeat` - Update agent status
- `GET /agents` - List active agents
- `DELETE /agents/{id}` - Deregister agent

### Coordination State
- Track agent current assignment
- Track agent status (idle, working, blocked)
- Store work queue per role

### Work Distribution
- Planner creates issues with priority
- System assigns issues based on role availability
- Developer signals when blocked (creates dependency)
- Reviewer receives notification when work is ready

## Business Value

Enables coordinated multi-agent workflows. Different AI agents can specialize in planning, development, and review while maintaining coordination through the graph.

## Status: COMPLETED