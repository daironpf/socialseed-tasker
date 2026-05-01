# Issue #215: Agent Integration with Code-as-Graph and RAG

## Description

Integrate Code-as-Graph and RAG features with the existing agent workflow, enabling AI agents to use these features during issue resolution.

## Problem

AI agents working on issues should be able to:
- Query code structure for understanding
- Find similar past solutions
- Record reasoning for transparency

## Integration Points

### Agent Manifest Enhancement
Update the existing agent manifest to include:
- Code graph context (relevant files, dependencies)
- Similar past issues with solutions
- Reasoning log entries

### CLI Commands for Agents
```bash
# Get code context for an issue
tasker agent context --issue-id <id>

# Get similar solutions
tasker agent suggest --issue-id <id>

# Log reasoning (automated)
tasker agent reasoning --issue-id <id> --thought "..."
```

### API Integration
```bash
# Get context for issue resolution
GET /api/v1/agent/context/{issue_id}

# Search similar issues
GET /api/v1/agent/similar/{issue_id}

# Auto-log reasoning on actions
POST /api/v1/agent/reasoning/auto
```

## Context Injection

When an agent starts working on an issue:
1. Fetch relevant code files from Code-as-Graph
2. Find similar past issues via RAG
3. Include in agent manifest

```markdown
## Agent Context

### Relevant Code
- src/core/services/github_mirror.py (calls: helper.py, queries.py)
- src/storage/graph_database/repositories.py (depends_on: driver.py)

### Past Similar Issues
- #142: Fixed similar API timeout issue
- #156: Similar dependency resolution

### Reasoning So Far
- [2026-04-29 10:30] Considered using cache vs. direct query
```

## Status

**COMPLETED**

## Priority

**HIGH** - Core feature for v0.9.0

## Component

CORE, CLI, API

## Acceptance Criteria

- [x] Update agent manifest to include code context
- [x] Update agent manifest to include RAG context
- [x] Add context injection on issue start
- [x] Auto-capture reasoning during work
- [x] CLI command: `tasker agent context`
- [x] CLI command: `tasker agent suggest`
- [ ] API endpoint: GET /api/v1/agent/context/{id}
- [ ] API endpoint: GET /api/v1/agent/similar/{id}
- [x] Test integration workflow

## Related Issues

- #208 - Code-as-Graph with Tree-sitter
- #209 - RAG Native with Vector Indexes
- #210 - AI Reasoning Logs in Graph