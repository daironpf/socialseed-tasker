# Issue #78: AI Reasoning Logs

## Description

Implement in-issue Markdown summaries explaining why the AI chose a specific architectural path based on the graph. This feature provides transparency into AI decision-making by capturing reasoning traces within issue descriptions.

## Requirements

- Add `reasoning_log` field to Issue entity and API schema
- Create API endpoint to append reasoning entries to issues
- Implement template system for reasoning summaries
- Store reasoning entries with timestamp and context (component, dependencies, analysis results)
- Support rich markdown in reasoning logs (code blocks, links, tables)

## Technical Details

### Entity Changes
```python
class ReasoningLogEntry(BaseModel):
    timestamp: datetime
    context: str  # "component_selection", "dependency_analysis", "architecture_choice"
    reasoning: str
    related_nodes: list[UUID]  # related issue/component IDs
```

### API Endpoints
- `POST /issues/{id}/reasoning` - Add reasoning entry
- `GET /issues/{id}/reasoning` - Get all reasoning entries

### UI Integration
- Display reasoning logs in issue detail view
- Highlight reasoning in different color than description

## Business Value

Increases trust in AI agents by exposing their decision-making process. Human reviewers can understand and validate architectural choices made by autonomous agents.

## Status: COMPLETED