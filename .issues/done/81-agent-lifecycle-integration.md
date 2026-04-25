# Issue #81: Agent Lifecycle Integration

## Description

Implement full tracking of the `agent_working` state with start/finish timestamps. The field exists in the entity but needs complete lifecycle integration to track when agents start and finish working on issues.

## Requirements

- Add `agent_started_at` and `agent_finished_at` datetime fields to Issue entity
- Create API endpoints to start/finish agent work: `POST /issues/{id}/agent/start` and `POST /issues/{id}/agent/finish`
- Add validation to prevent starting on already assigned issues
- Add timeout handling for abandoned agent work (configurable duration)
- Update CLI with `tasker issue start` and `tasker issue finish` commands
- Add agent activity to the Kanban board indicator

## Technical Details

### Entity Changes
```python
class Issue(BaseModel):
    agent_working: bool = False
    agent_started_at: datetime | None = None
    agent_finished_at: datetime | None = None
    agent_id: str | None = None  # identifier for the agent
```

### API Endpoints
- `POST /issues/{id}/agent/start` - Start agent work (requires agent_working=false)
- `POST /issues/{id}/agent/finish` - Finish agent work (requires agent_working=true)
- `GET /issues/{id}/agent/status` - Get agent work status

### Neo4j Schema
- Add `agentStartedAt` and `agentFinishedAt` properties
- Update queries to include timestamp fields

### Configuration
- `TASKER_AGENT_TIMEOUT_HOURS` - Timeout for abandoned work (default: 24)

## Business Value

Enables tracking of agent productivity and identification of stuck or abandoned work. Provides audit trail of when agents work on issues.

## Status: COMPLETED