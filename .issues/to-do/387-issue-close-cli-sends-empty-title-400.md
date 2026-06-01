# Issue #387: `tasker issue close` sends empty title causing 400 validation error

## Description
When running `tasker issue close <ID>`, the CLI makes a preliminary `GET /api/v1/issues?title=&...` with an empty title parameter, which triggers a Pydantic validation error (`String should have at least 1 character`). This prevents the close command from working via CLI. Workaround: use `POST /api/v1/issues/{id}/close` directly.

## Expected Behavior
`tasker issue close <ID>` should close the issue without a title lookup, or should omit the title parameter when resolving by ID.

## Actual Behavior
```
$ tasker issue close c558c909
Error: {"data":null,"error":{"code":"VALIDATION_ERROR","message":"1 validation error for Issue\ntitle\n  String should have at least 1 character"}}
```

## Steps to Reproduce
1. Create an issue via `tasker issue create "Test" -c <component>`
2. `tasker issue close <issue-id>`
3. Observe validation error

## Status: PENDING

## Priority: HIGH
