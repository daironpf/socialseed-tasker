# Issue #31: Add API Endpoint for Issue Move

## Description

The CLI has `issue move` command but there's no corresponding API endpoint (`PATCH /issues/{id}/move` or `PUT /issues/{id}/component`). Users of the REST API cannot move issues between components.

### Requirements

- Add `PATCH /api/v1/issues/{issue_id}` endpoint that accepts `component_id` in body
- Or add `PUT /api/v1/issues/{issue_id}/move` with `component_id`
- Keep consistency with existing patterns
- Add tests

### Technical Details

File: `src/socialseed_tasker/entrypoints/web_api/routes.py`

Add to issues_router:
```python
@issues_router.patch(
    "/issues/{issue_id}",
    response_model=APIResponse[IssueResponse],
    ...
)
def update_issue(
    issue_id: str,
    body: IssueUpdateRequest,
    ...
): ...
```

### Business Value

API parity with CLI functionality.

## STATUS: COMPLETED