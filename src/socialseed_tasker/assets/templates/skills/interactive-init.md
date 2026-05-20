# Interactive Project Initialization Guide

## Overview

When an AI agent needs to initialize Tasker in a project (`tasker init`), the agent MUST interact with the user to collect all necessary information. This ensures the project is properly configured with accurate metadata.

## Agent Behavior

The agent acts as a **project initialization assistant**. It:
1. Asks targeted questions
2. Provides recommendations based on best practices
3. Detects existing project configuration when possible
4. Helps the user make informed decisions

## Workflow

See [workflows/interactive-init.md](./workflows/interactive-init.md) for the complete step-by-step process.

## Quick Reference

| Field | Default | Recommendation |
|---|---|---|
| Architecture | hexagonal | Clean separation of concerns |
| Database | neo4j | Required by Tasker |
| Max Dependency Depth | 5 | Prevents coupling |
| Code Review Approvals | 1 | Minimum for small teams |
| Visibility | PUBLIC | Unless private repo |
| Status | DEVELOPMENT | Default for new projects |

## CLI Commands

```bash
# Full initialization
tasker init . --project-name "my-project" --architecture "hexagonal" ...

# Quick init with defaults
tasker init .

# Force overwrite
tasker init . --force
```