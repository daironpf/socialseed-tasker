# Issue #264: Create Developer Onboarding Guide

## Description

Create a comprehensive onboarding guide that allows new developers (human or AI) to understand Tasker, set up their environment, and start contributing to the project within minutes.

### Current State

The project has:
- README.md with basic info
- .agent/README.md with agent instructions
- Various docs in docs/
- .agent/skills/ for agent workflows

However, there's **no single onboarding document** that guides a new developer from "I just cloned this repo" to "I'm implementing my first feature."

### Requirements

#### Create `docs/ONBOARDING.md`

This document should serve as the definitive guide for onboarding and must include:

```markdown
# Developer Onboarding Guide - Tasker v1.0.0

## Quick Start (5 minutes)

1. Clone the repo
2. Run `pip install -e .`
3. Start Neo4j via Docker
4. Run `tasker init .`
5. Start API: `tasker api`

## Prerequisites

- Python 3.11+
- Neo4j 5.x (via Docker)
- Docker & Docker Compose
- Git

## Architecture Overview

Explain the three pillars:
1. Organizational: Project -> Component -> Issue
2. Code-as-Graph: File -> Symbol -> Import
3. Intelligence: Agent -> ReasoningNode -> Commit

Include diagrams.

## Directory Walkthrough

For each directory in src/socialseed_tasker/:
- What it contains
- What belongs here
- What DOESN'T belong here
- Example file to examine

## Your First Feature

Step-by-step guide to implement a small feature:
1. Create an issue file
2. Implement in core/
3. Add to repository in storage/
4. Add CLI command in entrypoints/
5. Add API endpoint in web_api/
6. Write tests
7. Run tests
8. Update documentation

## Common Patterns

- Repository Pattern implementation
- Entity definition in core/
- API endpoint creation
- CLI command creation

## Testing

- How to run tests
- Test structure
- Writing new tests

## Troubleshooting

- Common issues and solutions
- Debug tips

## Next Steps

- List of good first issues
- Architecture deep dive references
```

### Integration Points

The onboarding guide should reference existing documentation:
- `docs/GRAPH_MODEL.md` for data model details
- `.agent/skills/hexagonal-architecture.md` for architecture rules
- `docs/CLI_COMMANDS.md` for CLI reference
- `docs/API_REFERENCE.md` for API reference

### Business Value

1. **Faster onboarding** - New developers can start contributing in minutes
2. **Consistent implementations** - Everyone follows the same patterns
3. **Reduced support load** - Less "how do I..." questions
4. **Agent autonomy** - AI agents can understand how to work on the project

## Status: PENDING

## Priority: HIGH