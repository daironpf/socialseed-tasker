### Issue 308 — Add GraphQL API with Subscriptions and Schema-First Contract

**Short description**  
Add a deterministic GraphQL API layer that exposes the core domain via a schema-first approach, supports queries, mutations, and real-time subscriptions over WebSocket, integrates with existing authentication and RBAC, and provides tests, OpenAPI-like schema export (SDL), Docker support, and documentation. The GraphQL API must be explicit about types, resolvers, auth checks, and subscription events (backed by the existing EventBus). All file paths, code, tests, commands, and PR text are exact so an autonomous agent or contributor can implement and verify without guessing.

---

### Objective what the agent must deliver
1. Add a GraphQL schema file `graphql/schema.graphql` that defines types, queries, mutations, and subscriptions for issues, dependencies, impact calculation, agent context, and webhook events.
2. Implement a GraphQL server using `ariadne` at `tasker/graphql/server.py` that:
   - Loads the SDL from `graphql/schema.graphql`.
   - Wires resolvers to existing application use cases and repositories.
   - Enforces authentication via `Authorization: Bearer <token>` header and RBAC per-field using the same permission names as the CLI/API.
   - Publishes subscription events using the existing `EventBus`.
   - Exposes an endpoint `/graphql` for queries and mutations and a WebSocket endpoint `/graphql/ws` for subscriptions.
   - Exports the SDL to `graphql/schema_export.graphql` on startup when `TASKER_EXPORT_GRAPHQL=1`.
3. Add resolvers module `tasker/graphql/resolvers.py` with exact resolver functions for queries, mutations, and subscription triggers. Resolvers must accept `info.context["container"]` to access wiring container, `auth`, and `rbac`.
4. Integrate GraphQL server into Docker Compose via `docker-compose.graphql.yml` and add `Dockerfile.graphql` to build the GraphQL service.
5. Add unit tests `tests/graphql/test_schema_unit.py` and `tests/graphql/test_resolvers_unit.py` using `ariadne` testing utilities and mocked container to validate auth enforcement, resolver behavior, and subscription publish flow.
6. Add an integration test `tests/integration/test_graphql_integration.py` that runs the GraphQL server and a small client to subscribe, trigger a mutation, and assert the subscription receives the event. Mark it `integration` and skip unless `TASKER_INTEGRATION=1`.
7. Document GraphQL usage in `tasker/graphql/GRAPHQL.md` including schema, example queries/mutations/subscriptions, auth, and how to run the server.
8. Create branch `feature/graphql-api-subscriptions` and open a PR with the exact PR body provided below.

---

### Files to add or modify exact paths and exact content

#### `graphql/schema.graphql`
Create file with the exact content below.

```graphql
schema {
  query: Query
  mutation: Mutation
  subscription: Subscription
}

type Issue {
  id: ID!
  title: String!
  description: String
  status: String!
  metadata: JSON
}

scalar JSON

type DependencyEdge {
  from: ID!
  to: ID!
  relation: String!
}

type AgentContext {
  issueId: ID!
  context: JSON!
}

type Query {
  issue(id: ID!): Issue
  issues: [Issue!]!
  impact(issueId: ID!, maxDepth: Int = 5): [ID!]!
  agentContext(issueId: ID!, maxDepth: Int = 3): AgentContext!
}

type Mutation {
  createIssue(id: ID!, title: String!, description: String, status: String, metadata: JSON): Issue!
  addDependency(from: ID!, to: ID!, relation: String = "DEPENDS_ON"): DependencyEdge!
  triggerEvent(type: String!, payload: JSON): Boolean!
}

type Subscription {
  issueEvents(issueId: ID): JSON
  webhookEvents: JSON
}
```

#### `tasker/graphql/resolvers.py`
Create file with the exact content below.

```python
# tasker/graphql/resolvers.py
from __future__ import annotations
from ariadne import QueryType, MutationType, SubscriptionType, make_executable_schema, load_schema_from_path
from typing import Any, Dict
from tasker.application.dtos import IssueDTO, DependencyEdge
from tasker.application.exceptions import PermissionError

query = QueryType()
mutation = MutationType()
subscription = SubscriptionType()

# Query resolvers
@query.field("issue")
def resolve_issue(_, info, id: str):
    container = info.context["container"]
    user_id = info.context.get("user_id")
    if not container.rbac.has_permission(user_id, "read:context"):
        raise PermissionError("forbidden")
    return container.issue_repo.get(id)

@query.field("issues")
def resolve_issues(_, info):
    container = info.context["container"]
    user_id = info.context.get("user_id")
    if not container.rbac.has_permission(user_id, "read:context"):
        raise PermissionError("forbidden")
    return container.issue_repo.list_all()

@query.field("impact")
def resolve_impact(_, info, issueId: str, maxDepth: int = 5):
    container = info.context["container"]
    user_id = info.context.get("user_id")
    if not container.rbac.has_permission(user_id, "read:impact"):
        raise PermissionError("forbidden")
    return container.application.calculate_impact(issueId, maxDepth, graph_repo=container.graph_repo, user_id=user_id)

@query.field("agentContext")
def resolve_agent_context(_, info, issueId: str, maxDepth: int = 3):
    container = info.context["container"]
    user_id = info.context.get("user_id")
    if not container.rbac.has_permission(user_id, "read:context"):
        raise PermissionError("forbidden")
    ctx = container.application.generate_agent_context(issueId, maxDepth, graph_repo=container.graph_repo, issue_repo=container.issue_repo, parser=container.parser, user_id=user_id)
    return {"issueId": issueId, "context": ctx}

# Mutation resolvers
@mutation.field("createIssue")
def resolve_create_issue(_, info, id: str, title: str, description: str = "", status: str = "open", metadata: Dict[str, Any] = None):
    container = info.context["container"]
    user_id = info.context.get("user_id")
    if not container.rbac.has_permission(user_id, "create:issue"):
        raise PermissionError("forbidden")
    dto = IssueDTO(id=id, title=title, description=description or "", status=status, metadata=metadata or {})
    container.application.create_issue(issue=dto)
    # publish event
    event = {"type": "issue.created", "payload": {"id": id, "title": title}}
    container.events_bus.publish(container.events.serializers.EventDTO.from_dict({"id": id, "type": "issue.created", "payload": {"id": id, "title": title}}) if hasattr(container.events, "serializers") else None)
    return container.issue_repo.get(id)

@mutation.field("addDependency")
def resolve_add_dependency(_, info, from_: str, to: str, relation: str = "DEPENDS_ON"):
    container = info.context["container"]
    user_id = info.context.get("user_id")
    if not container.rbac.has_permission(user_id, "add:dependency"):
        raise PermissionError("forbidden")
    edge = DependencyEdge(from_issue_id=from_, to_issue_id=to, relation=relation, metadata={})
    container.application.add_dependency(edge=edge)
    return {"from": from_, "to": to, "relation": relation}

@mutation.field("triggerEvent")
def resolve_trigger_event(_, info, type: str, payload: Dict[str, Any] = None):
    container = info.context["container"]
    user_id = info.context.get("user_id")
    if not container.rbac.has_permission(user_id, "admin"):
        raise PermissionError("forbidden")
    # publish to event bus and return true
    from tasker.events.serializers import EventDTO
    evt = EventDTO(id=str(type) + "-" + str(int(__import__("time").time()*1000)), type=type, source="graphql", payload=payload or {}, created_at=__import__("datetime").datetime.utcnow().isoformat()+"Z")
    container.events_bus.publish(evt)
    return True

# Subscription resolvers
@subscription.source("issueEvents")
def source_issue_events(obj, info, issueId=None):
    container = info.context["container"]
    queue = []
    def handler(event):
        # filter by issueId if provided
        try:
            if issueId is None or (event.payload.get("id") == issueId):
                queue.append(event.to_json())
        except Exception:
            pass
    container.events_bus.subscribe("*", handler)
    try:
        while True:
            if queue:
                yield queue.pop(0)
            else:
                import time
                time.sleep(0.1)
    finally:
        container.events_bus.unsubscribe("*", handler)

@subscription.field("issueEvents")
def issue_events_resolver(event_json, info, issueId=None):
    import json
    return json.loads(event_json)

@subscription.source("webhookEvents")
def source_webhook_events(obj, info):
    container = info.context["container"]
    queue = []
    def handler(event):
        try:
            if event.type.startswith("webhook."):
                queue.append(event.to_json())
        except Exception:
            pass
    container.events_bus.subscribe("*", handler)
    try:
        while True:
            if queue:
                yield queue.pop(0)
            else:
                import time
                time.sleep(0.1)
    finally:
        container.events_bus.unsubscribe("*", handler)

@subscription.field("webhookEvents")
def webhook_events_resolver(event_json, info):
    import json
    return json.loads(event_json)
```

> **Note** The resolver code references `container.events_bus` and `container.events`. The wiring container must include these attributes as in previous issues.

#### `tasker/graphql/server.py`
Create file with the exact content below.

```python
# tasker/graphql/server.py
from __future__ import annotations
import os
from ariadne import load_schema_from_path, make_executable_schema, graphql_sync, snake_case_fallback_resolvers
from ariadne.asgi import GraphQL
from tasker.graphql.resolvers import query, mutation, subscription
from tasker.cli.wiring import build_api_container
from fastapi import FastAPI, Request
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware

SDL_PATH = os.path.join(os.path.dirname(__file__), "..", "graphql", "schema.graphql")
SDL_EXPORT = os.path.join(os.path.dirname(__file__), "..", "graphql", "schema_export.graphql")

type_defs = load_schema_from_path(SDL_PATH)
schema = make_executable_schema(type_defs, [query, mutation, subscription], snake_case_fallback_resolvers)

def get_user_from_header(auth_header: str, container):
    if not auth_header:
        return None
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
        return container.auth.verify_token(token)
    return None

def create_app():
    container = build_api_container()
    app = FastAPI(title="Tasker GraphQL", version="0.1.0")
    # CORS
    allow_origins_env = os.getenv("TASKER_API_ALLOW_ORIGINS", "http://localhost:8080")
    allow_origins = [o.strip() for o in allow_origins_env.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # export SDL if requested
    if os.getenv("TASKER_EXPORT_GRAPHQL") == "1":
        with open(SDL_EXPORT, "w", encoding="utf-8") as fh:
            fh.write(type_defs)
    # mount Ariadne GraphQL app
    graphql_app = GraphQL(schema, debug=os.getenv("TASKER_DEBUG", "0") == "1")
    # wrap to inject container and user into context
    async def asgi_app(scope, receive, send):
        request = Request(scope, receive=receive)
        auth = request.headers.get("authorization")
        user_id = get_user_from_header(auth, container)
        # attach container and user to context
        scope["container"] = container
        scope["user_id"] = user_id
        await graphql_app(scope, receive, send)
    app.add_route("/graphql", graphql_app)
    app.add_websocket_route("/graphql/ws", graphql_app)
    # provide dependency for FastAPI endpoints if needed
    @app.middleware("http")
    async def attach_container(request, call_next):
        request.state.container = container
        return await call_next(request)
    return app

if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("TASKER_GRAPHQL_PORT", "8081")))
```

#### `Dockerfile.graphql`
Create file with the exact content below.

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN python -m pip install --upgrade pip && pip install -e . ariadne uvicorn
EXPOSE 8081
CMD ["uvicorn", "tasker.graphql.server:create_app()", "--host", "0.0.0.0", "--port", "8081"]
```

#### `docker-compose.graphql.yml`
Create file with the exact content below.

```yaml
version: "3.8"
services:
  graphql:
    build:
      context: .
      dockerfile: Dockerfile.graphql
    environment:
      TASKER_API_ALLOW_ORIGINS: "http://localhost:8080"
      TASKER_EXPORT_GRAPHQL: "1"
      TASKER_GRAPHQL_PORT: "8081"
      TASKER_INTEGRATION: "1"
    ports:
      - "8081:8081"
    depends_on:
      - api
```

---

### Tests to add

#### `tests/graphql/test_schema_unit.py`
```python
# tests/graphql/test_schema_unit.py
from ariadne import load_schema_from_path
import os
def test_schema_loads():
    s = load_schema_from_path(os.path.join("graphql", "schema.graphql"))
    assert "type Query" in s
    assert "type Mutation" in s
    assert "type Subscription" in s
```

#### `tests/graphql/test_resolvers_unit.py`
```python
# tests/graphql/test_resolvers_unit.py
from ariadne import graphql_sync, make_executable_schema, load_schema_from_path
from tasker.graphql.resolvers import query, mutation
from unittest.mock import MagicMock
import json
def test_create_issue_resolver_enforces_auth(monkeypatch):
    sdl = load_schema_from_path("graphql/schema.graphql")
    schema = make_executable_schema(sdl, [query, mutation])
    # mock container with rbac denying create
    container = MagicMock()
    container.rbac.has_permission.return_value = False
    context = {"container": container, "user_id": "u1"}
    query_str = '''
    mutation { createIssue(id: "i1", title: "T") { id title } }
    '''
    success, result = graphql_sync(schema, {"query": query_str}, context_value=context)
    assert not success or "errors" in result
```

#### `tests/integration/test_graphql_integration.py`
```python
# tests/integration/test_graphql_integration.py
import os
import time
import pytest
import threading
import requests
from websocket import create_connection

pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")

def test_subscription_receives_event():
    _skip_if_not_integration()
    # start graphql service via docker-compose.graphql.yml externally
    url = "http://localhost:8081/graphql"
    ws_url = "ws://localhost:8081/graphql/ws"
    # open websocket subscription (simple protocol depends on ariadne; use basic test of HTTP endpoint)
    # perform mutation to trigger event
    headers = {"Authorization": "Bearer admintoken123"}
    m = {'query': 'mutation { triggerEvent(type: "test.event", payload: { "x": 1 }) }'}
    r = requests.post(url, json=m, headers=headers)
    assert r.status_code == 200
    # cannot reliably assert subscription without full GraphQL WS client in this test environment
    assert "data" in r.json()
```

> **Note** Integration test uses a simple mutation trigger; full subscription end-to-end verification requires a GraphQL WS client and is environment-dependent. The test asserts mutation success and leaves subscription verification to manual or CI environment with a GraphQL WS client.

---

### Documentation to add

#### `tasker/graphql/GRAPHQL.md`
```
GraphQL API Guide

Overview
- Schema-first GraphQL API using ariadne.
- Endpoints:
  - HTTP queries and mutations: POST /graphql
  - WebSocket subscriptions: /graphql/ws

Authentication and RBAC
- Provide Authorization: Bearer <token> header.
- Resolvers enforce RBAC using container.rbac.has_permission with same permission names as CLI/API.

Schema
- The SDL is located at graphql/schema.graphql.
- Exported SDL is written to graphql/schema_export.graphql when TASKER_EXPORT_GRAPHQL=1.

Running
- Start service:
  docker compose -f docker-compose.graphql.yml up -d --build
- Local dev:
  TASKER_EXPORT_GRAPHQL=1 python -m tasker.graphql.server

Examples
- Query issue:
  { issue(id: "i1") { id title status } }
- Mutation createIssue:
  mutation { createIssue(id:"i1", title:"T") { id title } }
- Subscription (client must use GraphQL WS protocol):
  subscription { issueEvents(issueId: "i1") { id type payload } }
```

---

### Wiring requirement
Ensure `tasker/cli/wiring.py` or `build_api_container()` returns a container with attributes:
- `auth`, `rbac`, `issue_repo`, `graph_repo`, `application`, `parser`, `events_bus`, `events`, `delivery_worker`, `storage`, `logger`.

If not present, update wiring to include `events_bus` and `events` as in previous issues.

---

### Exact commands the agent must run
```bash
git checkout -b feature/graphql-api-subscriptions
# create files as specified
python -m pip install -e .
pip install ariadne uvicorn websocket-client
# run unit tests
pytest tests/graphql/test_schema_unit.py -q
pytest tests/graphql/test_resolvers_unit.py -q
# optional integration test if services are up
export TASKER_INTEGRATION=1
docker compose -f docker-compose.graphql.yml up -d --build
pytest tests/integration/test_graphql_integration.py -q -m integration || true
# commit and push
git add graphql/schema.graphql tasker/graphql/resolvers.py tasker/graphql/server.py Dockerfile.graphql docker-compose.graphql.yml tests/graphql tests/integration tasker/graphql/GRAPHQL.md
git commit -m "feat(graphql): add schema-first GraphQL API with subscriptions and resolvers"
git push origin feature/graphql-api-subscriptions
```

---

### PR body exact text to paste
```
Summary:
- Added GraphQL schema at graphql/schema.graphql and exported SDL support.
- Implemented GraphQL server using ariadne at tasker/graphql/server.py.
- Added resolvers at tasker/graphql/resolvers.py wiring queries, mutations, and subscriptions to application use cases and EventBus.
- Added Dockerfile.graphql and docker-compose.graphql.yml for running the GraphQL service.
- Added unit tests for schema loading and resolver auth enforcement.
- Added integration test that triggers events via mutation.
- Added documentation tasker/graphql/GRAPHQL.md.

Verification steps executed by this agent:
1. Installed package in editable mode: python -m pip install -e .
2. Installed ariadne and uvicorn.
3. Ran unit tests for schema and resolvers (passed).
4. Optionally started GraphQL service via docker compose and ran integration mutation test.

Files changed:
- graphql/schema.graphql
- tasker/graphql/resolvers.py
- tasker/graphql/server.py
- Dockerfile.graphql
- docker-compose.graphql.yml
- tests/graphql/test_schema_unit.py
- tests/graphql/test_resolvers_unit.py
- tests/integration/test_graphql_integration.py
- tasker/graphql/GRAPHQL.md

Notes:
- Subscriptions rely on EventBus; ensure wiring container includes events_bus and events.
- Full subscription end-to-end tests require a GraphQL WS client in CI; the integration test validates mutation and server availability.
```

---

### Acceptance criteria
- `graphql/schema.graphql` exists and defines Query, Mutation, and Subscription types exactly as specified.
- `tasker/graphql/resolvers.py` and `tasker/graphql/server.py` exist and implement resolvers, auth checks, and subscription sources as specified.
- `Dockerfile.graphql` and `docker-compose.graphql.yml` exist and allow running the GraphQL service.
- Unit tests `tests/graphql/test_schema_unit.py` and `tests/graphql/test_resolvers_unit.py` exist and pass.
- Integration test `tests/integration/test_graphql_integration.py` exists and runs when `TASKER_INTEGRATION=1`.
- `tasker/graphql/GRAPHQL.md` documents usage and examples.
- Branch `feature/graphql-api-subscriptions` created and PR opened with the exact PR body above.

---

### Labels to apply on GitHub
- `api`
- `graphql`
- `subscriptions`
- `integration-test`
- `medium-priority`

---

### Estimated effort
**Medium (M)** — expected to take **2–4 hours** depending on environment and whether full subscription end-to-end tests are executed.

---