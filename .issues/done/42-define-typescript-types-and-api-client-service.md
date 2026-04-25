# Issue #42: Define TypeScript types and API client service layer

## Description

Create the TypeScript type definitions that mirror the backend Pydantic schemas, and build an API client service layer to communicate with the FastAPI backend.

### Requirements

- Create TypeScript types in `frontend/src/types/` that match the backend API responses:
  - `Issue` - mirrors `IssueResponse` (id, title, description, status, priority, component_id, labels, dependencies, blocks, affects, created_at, updated_at, closed_at, architectural_constraints)
  - `Component` - mirrors `ComponentResponse` (id, name, description, project, created_at, updated_at)
  - `IssueStatus` - enum: OPEN, IN_PROGRESS, CLOSED, BLOCKED
  - `IssuePriority` - enum: LOW, MEDIUM, HIGH, CRITICAL
  - `PaginatedResponse<T>` - generic pagination wrapper
  - `APIResponse<T>` - envelope with data/error/meta
  - `DependencyRequest` - for adding dependencies
  - `IssueCreateRequest` - for creating issues
  - `IssueUpdateRequest` - for updating issues

- Create API client service in `frontend/src/api/`:
  - `issuesApi.ts` - CRUD operations for issues (create, list, get, update, delete, close)
  - `componentsApi.ts` - CRUD operations for components
  - `dependenciesApi.ts` - dependency management (add, remove, list, chain, blocked)
  - `analysisApi.ts` - root cause and impact analysis endpoints
  - `client.ts` - base Axios/fetch instance with base URL and error handling

### Technical Details

- Use fetch API (no extra dependency) or Axios
- Base URL configurable via `import.meta.env.VITE_API_URL`
- All API calls return typed promises
- Handle API error envelope consistently
- The API envelope structure: `{ data: T, error: { code, message, details }, meta: { timestamp, request_id } }`

### Expected File Paths

- `frontend/src/types/index.ts`
- `frontend/src/api/client.ts`
- `frontend/src/api/issuesApi.ts`
- `frontend/src/api/componentsApi.ts`
- `frontend/src/api/dependenciesApi.ts`
- `frontend/src/api/analysisApi.ts`

### Business Value

Provides type-safe communication between the Vue frontend and the FastAPI backend, catching errors at compile time and enabling autocomplete in the IDE.

## Status: COMPLETED
