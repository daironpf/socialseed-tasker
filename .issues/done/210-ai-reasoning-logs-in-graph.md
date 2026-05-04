# Issue #210: AI Reasoning Logs in Graph

## Description

Record agent reasoning patterns in the Neo4j graph for transparency, learning, and human review. Implement the pattern: `(Agent)-[:THOUGHT]->(ReasoningNode)-[:DECIDED]->(Task)`.

## Problem

AI agents make decisions that affect the codebase, but there's no transparency into:
- Why a particular solution was chosen
- What alternatives were considered
- Confidence level of the decision
- What can be learned from past decisions

## Expected Behavior

The system should:
- Capture reasoning at decision points
- Store in Neo4j with rich metadata
- Enable human review and feedback
- Support learning from past decisions
- Make agent thinking visible to developers

## Technical Implementation

### ReasoningNode Structure
```cypher
(:ReasoningNode {
  thought: String,           -- The agent's reasoning text
  confidence: Float,          -- Confidence score (0.0-1.0)
  alternatives_considered: List[String], -- Options evaluated
  rejected_reasons: List[String], -- Why alternatives were rejected
  timestamp: DateTime,       -- When the thought occurred
  decision_type: String,     -- e.g., "solution_selection", "architecture_choice"
  context: Map                -- Additional context data
})
```

### Relationship Pattern
```cypher
(Agent:Agent {id: "agent-123"})-[:THOUGHT {timestamp: datetime()}]->(r:ReasoningNode)-[:DECIDED]->(Task:Issue {id: "issue-456"})
```

### Automatic Capture via API Interceptors
- Add middleware to capture reasoning at key points
- Intercept before:
  - Creating an issue
  - Closing an issue (with solution summary)
  - Making architectural decisions
  - Choosing between alternatives
- Store reasoning before action execution

### Manual Logging via Agent Manifest
- Extend existing Agent Progress Manifest
- Add `## Reasoning Log` section
- Parse and store reasoning nodes
- Support structured reasoning entries

### Human Review and Feedback Loop
- UI to review reasoning traces
- Allow feedback on decisions (thumbs up/down)
- Store feedback in graph
- Use feedback for future learning
- Report on agent decision quality

### Learning from Past Decisions
- Analyze patterns in reasoning
- Identify successful strategies
- Suggest improvements
- Track decision accuracy over time

## Steps to Reproduce

```bash
# Not currently implemented - this is the feature to add

# Agent starts working on issue
curl -X POST http://localhost:8000/api/v1/issues/.../start \
  -H "Content-Type: application/json" \
  -d '{"reasoning": "I will use a buffer strategy because..."}'

# Agent logs a thought
curl -X POST http://localhost:8000/api/v1/reasoning/log \
  -H "Content-Type: application/json" \
  -d '{
    "issue_id": "...",
    "thought": "Considering two approaches: A) refactor core, B) add wrapper",
    "confidence": 0.8,
    "alternatives_considered": ["refactor core", "add wrapper", "new service"],
    "decision": "add wrapper"
  }'

# Query reasoning history
curl http://localhost:8000/api/v1/issues/.../reasoning
```

## Status

**TODO**

## Priority

**HIGH** - Core feature for v0.9.0

## Component

CORE, API, STORAGE

## Acceptance Criteria

- [ ] ReasoningNode schema in Neo4j
- [ ] [:THOUGHT] and [:DECIDED] relationship types
- [ ] API interceptor for automatic capture
- [ ] CLI command: `tasker reasoning log <issue>`
- [ ] CLI command: `tasker reasoning history <issue>`
- [ ] API endpoint: `POST /api/v1/reasoning/log`
- [ ] API endpoint: `GET /api/v1/reasoning/{issue_id}`
- [ ] UI integration in issue detail view
- [ ] Human feedback mechanism (approve/disapprove)
- [ ] Decision pattern analysis
- [ ] Unit tests for reasoning capture

## Implementation Plan

### Phase 1: Schema and Storage
1. Define ReasoningNode schema
2. Add THOUGHT and DECIDED relationship types
3. Create reasoning queries in `storage/graph_database/`
4. Add indexes for performance

### Phase 2: Capture Mechanism
1. Create reasoning interceptor middleware
2. Implement automatic capture points
3. Add manual logging endpoint
4. Support structured reasoning format

### Phase 3: API and CLI
1. Add reasoning endpoints to API
2. Add reasoning commands to CLI
3. Add pagination and filtering
4. Add reasoning to issue response

### Phase 4: UI and Feedback
1. Add reasoning section to issue detail view
2. Implement feedback buttons
3. Add reasoning timeline visualization
4. Create analytics dashboard

### Phase 5: Learning
1. Implement pattern analysis
2. Add decision success tracking
3. Create recommendation engine
4. Generate improvement suggestions

## Impact

- Provides transparency into agent decisions
- Enables learning from past decisions
- Supports human oversight
- Improves agent accuracy over time
- Documents architectural choices

## Related Issues

- #208 - Code-as-Graph with Tree-sitter
- #209 - RAG Native with Vector Indexes
- #78 - AI Reasoning Logs (existing, enhance with this)

## Technical Notes

- Store reasoning before execution (for rollback on failure)
- Consider async processing for performance
- Add reasoning to existing manifest format
- Support both structured and free-form reasoning
- Implement reasoning cleanup for old entries