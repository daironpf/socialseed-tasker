# Issue #147: Add mock-based unit tests for API routes

## Description

The `entrypoints/web_api/routes.py` file has only 32% code coverage (545 missing statements). API routes have complex branching that needs mock-based unit tests to increase coverage and verify error handling.

### Current State

- `routes.py`: 805 statements, 260 covered, 545 missing (32% coverage)
- Complex error handling branches not tested
- Multiple HTTP status code paths need coverage

### Requirements

1. Add mock-based unit tests for all API endpoints
2. Test all HTTP status codes (200, 201, 400, 404, 409, 422, 500)
3. Test query parameter combinations
4. Test pagination logic
5. Test filtering and sorting

### Target Endpoints to Test

- `GET/POST /api/v1/components`
- `GET/PATCH/DELETE /api/v1/issues/{id}`
- `POST /api/v1/issues/{id}/close`
- `GET/POST /api/v1/issues/{id}/dependencies`
- `GET /api/v1/workable-issues`
- `GET /api/v1/analyze/impact/{id}`
- `GET /api/v1/analyze/component-impact/{id}`
- `GET /api/v1/projects/{name}/summary`
- `GET /api/v1/graph/dependencies`

### Technical Details

Create `tests/unit/test_routes.py`:

```python
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

class TestComponentRoutes:
    @patch("routes.get_component_repository")
    def test_get_component_success(self, mock_repo, client):
        mock_repo.return_value.get_component.return_value = component
        response = client.get("/api/v1/components/test-id")
        assert response.status_code == 200
    
    @patch("routes.get_component_repository")
    def test_get_component_not_found(self, mock_repo, client):
        mock_repo.return_value.get_component.return_value = None
        response = client.get("/api/v1/components/nonexistent")
        assert response.status_code == 404
```

## Status: COMPLETED