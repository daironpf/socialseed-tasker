# Skill: API Client

## Description
Provides HTTP client capabilities for interacting with Tasker REST API. Used for black-box testing to create issues without CLI contamination.

---

## Capabilities

### 1. Base Configuration
```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}
```

### 2. Issue Operations

```python
# Create issue
POST /api/v1/issues
{
  "title": "string",
  "description": "string",
  "priority": "LOW|MEDIUM|HIGH|CRITICAL",
  "component_id": "uuid"
}

# List issues (paginated)
GET /api/v1/issues?page=1&page_size=50

# Get single issue
GET /api/v1/issues/{id}

# Update issue
PATCH /api/v1/issues/{id}
{
  "title": "string",
  "status": "OPEN|IN_PROGRESS|CLOSED|BLOCKED"
}

# Delete issue
DELETE /api/v1/issues/{id}

# Close issue
POST /api/v1/issues/{id}/close
```

### 3. Component Operations

```python
# Create component
POST /api/v1/components
{
  "name": "string",
  "description": "string",
  "project": "string"
}

# List components
GET /api/v1/components

# Get component
GET /api/v1/components/{id}
```

### 4. Dependency Operations

```python
# Add dependency
POST /api/v1/issues/{id}/dependencies
{
  "depends_on_id": "uuid"
}

# Get dependencies
GET /api/v1/issues/{id}/dependencies
```

### 5. Analysis

```python
# Root cause analysis
GET /api/v1/analyze/root-cause/{id}

# Impact analysis
GET /api/v1/analyze/impact/{id}
```

### 6. Health Check

```python
GET /health
```

---

## Usage Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

def create_issue(title, description, priority, component_id):
    response = requests.post(
        f"{BASE_URL}/issues",
        json={
            "title": title,
            "description": description,
            "priority": priority,
            "component_id": component_id
        },
        headers={"Content-Type": "application/json"}
    )
    return response

def list_issues():
    response = requests.get(f"{BASE_URL}/issues")
    return response.json()

def verify_issue_count(expected_count):
    issues = list_issues()
    actual = len(issues.get("items", []))
    return actual == expected_count
```

---

## Error Handling

| Status Code | Meaning | Action |
|------------|--------|--------|
| 200 | Success | Parse response |
| 201 | Created | Parse new entity |
| 400 | Bad Request | Fix payload |
| 401 | Unauthorized | Add API key |
| 404 | Not Found | Check endpoint |
| 500 | Server Error | **MARK AS FINDING** |

---

## Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/v1/issues` | GET/POST | Issue CRUD |
| `/api/v1/issues/{id}` | GET/PATCH/DELETE | Single issue |
| `/api/v1/issues/{id}/close` | POST | Close issue |
| `/api/v1/components` | GET/POST | Component CRUD |
| `/api/v1/workable-issues` | GET | Ready issues |