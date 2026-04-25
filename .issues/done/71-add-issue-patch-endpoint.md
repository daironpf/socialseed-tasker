# Issue #71: Add issue update (PATCH) endpoint for status and priority

## Description

The API supports creating and closing issues, but there is no general PATCH endpoint to update issue fields like status (OPEN, IN_PROGRESS, BLOCKED), priority, labels, description, or agent_working flag.

## Problem Found

The README shows examples like `curl -X PATCH /api/v1/issues/{id} -d '{"status": "IN_PROGRESS"}'` but this endpoint may not fully support all the documented fields. During the ecommerce test, there was no way to move an issue to IN_PROGRESS via the API other than closing it.

## Impact

- AI agents cannot update progress on issues
- Kanban board cannot move cards between columns
- Cannot set agent_working flag via documented API
- Issue lifecycle is incomplete (only create and close)

## Suggested Fix

- Implement full PATCH `/api/v1/issues/{id}` supporting: status, priority, labels, description, agent_working
- Validate status transitions (e.g., CLOSED cannot go back to OPEN without explicit reopen)
- Return updated issue in response
- Add validation that agent_working can only be set on OPEN/IN_PROGRESS issues

## Priority

HIGH

## Labels

api, bug, ai-agents
