# Issue #215: Agent Integration with Code-as-Graph and RAG

## Description

Integrate AI agent capabilities with the Code-as-Graph system and RAG-based semantic search. This enables agents to understand codebase structure, find relevant code, and leverage past issue resolutions when working on new issues.

## Requirements

### 1. Agent Context Endpoint
- [x] API endpoint: `GET /api/v1/agent/context/{issue_id}`
- [x] Returns relevant code files from Code-as-Graph based on issue context
- [x] CLI command: `tasker agent context --issue <id>`

### 2. Similar Issues via RAG
- [x] API endpoint: `GET /api/v1/agent/similar/{issue_id}`
- [x] Uses RAG semantic search to find similar past issues
- [x] CLI command: `tasker agent suggest --issue <id> --limit 5`

### 3. Agent Reasoning Logs
- [x] API endpoint: `POST /api/v1/reasoning/log`
- [x] CLI command: `tasker agent reasoning --issue <id> --thought <text> --decision <choice>`
- [x] Stores agent decision-making in Neo4j graph

### 4. Agent Lifecycle Management
- [x] Start agent work: Track when agent starts working on issue
- [x] Finish agent work: Track when agent completes work
- [x] Agent status: Get current agent work status for issue

### 5. Code Graph Integration in Agent Workflow
- [x] Agents can query code files via Code-as-Graph
- [x] Agents can find function callers (impact analysis)
- [x] Agents can find test files related to code

## Technical Implementation

### API Endpoints
- `/api/v1/agent/context/{issue_id}` - Get code context
- `/api/v1/agent/similar/{issue_id}` - Find similar issues
- `/api/v1/agent/lifecycle/start` - Start agent work
- `/api/v1/agent/lifecycle/finish` - Finish agent work
- `/api/v1/agent/status/{issue_id}` - Get agent status

### CLI Commands
- `tasker agent context --issue <id>`
- `tasker agent suggest --issue <id> --limit 5`
- `tasker agent reasoning --issue <id> --thought <text> --decision <choice>`

## Status: COMPLETED

All required features have been implemented in v0.9.0:
- Code-as-Graph integration with agent commands
- RAG-based similar issue suggestions  
- Agent reasoning logging
- Agent lifecycle management (start/finish work)
- CLI and API endpoints for all agent operations