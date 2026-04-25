# Issue #65: Add workable issues endpoint for AI agents

## Description

AI agents need to know which issues are ready to work on (not blocked by open dependencies). Currently, agents must fetch all issues, then check dependencies for each one individually - an O(N^2) operation.

## Problem Found

The README shows a Python snippet where an AI agent must:
1. Fetch all issues
2. For each issue, fetch its dependencies
3. Check if all dependencies are CLOSED

This is inefficient and error-prone. The system already has the logic to determine blocked issues via `GET /api/v1/blocked-issues`, but there is no inverse endpoint for "workable" issues.

## Impact

- AI agents waste API calls computing what the system already knows
- Agents may start working on blocked issues by mistake
- Inefficient for large projects with hundreds of issues

## Suggested Fix

- Add `GET /api/v1/issues/workable` endpoint
- Return issues where status != CLOSED AND all dependencies are CLOSED (or no dependencies exist)
- Include optional filters: `?priority=HIGH&component=xyz`
- Add `agent_working` count so agents can see which issues are already being worked on by another agent

## Priority

HIGH

## Labels

api, ai-agents, feature
