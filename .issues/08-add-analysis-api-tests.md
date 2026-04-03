# Issue #08: Add API Tests for Analysis Endpoints

## Description

The analysis endpoints (`POST /analyze/root-cause` and `GET /analyze/impact/{issue_id}`) have zero test coverage. They were implemented as placeholders and later filled in, but no tests were written.

### Requirements

- Test `POST /analyze/root-cause` with a valid test failure body
- Test `POST /analyze/root-cause` with an invalid body (missing fields) — should return 422
- Test `GET /analyze/impact/{issue_id}` with an existing issue that has dependents
- Test `GET /analyze/impact/{issue_id}` with a non-existent issue — should return 404
- Test `GET /analyze/impact/{issue_id}` with transitive dependencies
- Verify response envelope structure matches `APIResponse` pattern

### Technical Details

File: `tests/unit/test_api.py`

Add a new test class:
```python
class TestAnalysis:
    def test_root_cause_with_matching_issue(self, client, component_id):
        # Create and close an issue
        # Submit a test failure that matches the issue
        # Verify causal links are returned with confidence scores

    def test_root_cause_invalid_body_returns_422(self, client):
        resp = client.post("/api/v1/analyze/root-cause", json={})
        assert resp.status_code == 422

    def test_impact_analysis_with_dependents(self, client, component_id):
        # Create issues with dependencies
        # Request impact analysis
        # Verify directly_affected, transitively_affected, risk_level

    def test_impact_analysis_nonexistent_issue(self, client):
        resp = client.get("/api/v1/analyze/impact/nonexistent-id")
        assert resp.status_code == 404
```

Expected file paths:
- `tests/unit/test_api.py`

### Business Value

These are the endpoints most likely to be used by AI agents (per the project's positioning). Without tests, regressions in the analysis logic would go undetected.

## Status: PENDING
