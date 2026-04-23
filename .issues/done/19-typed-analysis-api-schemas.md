# Issue #19: Use Typed Schemas in Analysis API Endpoints

## Description

The root cause analysis (`POST /analyze/root-cause`) and impact analysis (`GET /analyze/impact/{issue_id}`) endpoints in `routes.py` accept raw `dict` bodies and return raw `dict` responses, despite having properly defined Pydantic schemas (`TestFailureRequest`, `CausalLinkResponse`) that are never used.

### Requirements

- Replace `body: dict` in `analyze_root_cause` with `body: TestFailureRequest`
- Replace the manual dict construction in the response with `CausalLinkResponse` objects
- Create a proper `ImpactAnalysisResponse` Pydantic model (currently returns `APIResponse[dict]`)
- Add input validation through Pydantic
- Write API tests for both analysis endpoints

### Technical Details

File: `src/socialseed_tasker/entrypoints/web_api/routes.py`

Current (broken pattern):
```python
def analyze_root_cause(body: dict, repo = Depends(get_repo)):
    test_failure = TestFailure(
        test_id=body.get("test_id", ""),  # No validation!
        ...
    )
    return APIResponse(data=link_data, meta=Meta())  # Raw dict
```

Should be:
```python
def analyze_root_cause(body: TestFailureRequest, repo = Depends(get_repo)):
    test_failure = TestFailure(
        test_id=body.test_id,  # Validated by Pydantic
        ...
    )
    links = [CausalLinkResponse(...) for link in causal_links]
    return APIResponse(data=links, meta=Meta())
```

Existing schemas to use:
- `TestFailureRequest` in `schemas.py:170`
- `CausalLinkResponse` in `schemas.py:223`

New schema needed:
```python
class ImpactAnalysisResponse(BaseModel):
    issue_id: str
    directly_affected: list[ImpactIssueSummary]
    transitively_affected: list[ImpactIssueSummary]
    blocked_issues: list[ImpactIssueSummary]
    affected_components: list[str]
    risk_level: str
```

Expected file paths:
- `src/socialseed_tasker/entrypoints/web_api/routes.py`
- `src/socialseed_tasker/entrypoints/web_api/schemas.py`
- `tests/unit/test_api.py`

### Business Value

This is the most exposed surface for AI agent interaction. Without input validation, malformed data causes unpredictable results. Using typed schemas provides automatic validation, OpenAPI documentation, and IDE autocomplete for consumers.

## Status: COMPLETED
