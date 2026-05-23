### Issue 310 — Add Single Sign‑On (OAuth2) with Keycloak and Session Management

**Short description**  
Add deterministic Single Sign‑On (SSO) support using OAuth2 / OpenID Connect with Keycloak for local development and CI. Provide backend endpoints to handle the OAuth2 authorization code flow, session cookie management, logout, and token refresh. Integrate the frontend board to use SSO (redirects and token storage), add a Keycloak service to Docker Compose, provide deterministic realm/client configuration files, unit and integration tests, and documentation. All file paths, exact configuration, code, commands, and PR text are explicit so an autonomous agent or engineer can implement and verify without guessing.

---

## Objective (what the agent must deliver)
1. **Keycloak dev service**: Add `keycloak` service to `docker-compose.auth.yml` (or extend existing compose files) with deterministic admin credentials and a realm import file.
2. **Realm and client config**: Add `auth/keycloak-realm.json` that defines a realm `tasker-dev`, a client `tasker-frontend` (public) and `tasker-api` (confidential), and two test users `admin` and `reader` with passwords and roles that map to RBAC permissions.
3. **Backend OAuth handlers**: Add `tasker/auth/oauth.py` implementing:
   - `start_login_redirect(request)` — builds authorization URL and redirects.
   - `oauth_callback(request)` — exchanges code for tokens, validates ID token, creates a server-side session, sets a secure HTTP-only cookie `TASKER_SESSION`.
   - `refresh_token(session)` — refreshes access token using refresh token.
   - `logout(request)` — clears session and redirects to Keycloak logout endpoint.
   - A small `SessionStore` backed by `StoragePort` to persist session data.
4. **Frontend integration**: Update `frontend` to support SSO:
   - Add `frontend/src/auth.js` with deterministic login/logout helpers that redirect to backend login endpoints and read session state.
   - Update `examples/board/index.html` (or frontend entry) to show login/logout buttons and to include `TASKER_API_URL` for API calls.
5. **CLI and API wiring**: Update `tasker/cli/wiring.py` and `tasker/api/app.py` to:
   - Accept bearer tokens from Authorization header as before, **and** accept server session cookie `TASKER_SESSION` for authenticated requests (session lookup via `SessionStore`).
   - Provide a `session_store` in the container wiring.
6. **Tests**:
   - Unit tests for `tasker/auth/oauth.py` using mocked Keycloak endpoints (`tests/auth/test_oauth_unit.py`).
   - Integration test `tests/integration/test_sso_flow.py` that starts Keycloak, API, and frontend via Docker Compose, performs the authorization code flow (using deterministic test user credentials), and verifies that:
     - The frontend receives a session cookie.
     - The API accepts requests authenticated via the session cookie.
     - Logout clears the session.
   - Mark integration test with `@pytest.mark.integration` and skip unless `TASKER_INTEGRATION=1`.
7. **Documentation**: Add `tasker/auth/SSO.md` describing how to run Keycloak locally, how the flow works, environment variables, and security notes.
8. **Branch and PR**: Create branch `feature/sso-keycloak` and open a PR with the exact PR body provided below.

---

## Why this must be done exactly this way
- SSO with OAuth2/OpenID Connect is standard and interoperable; Keycloak provides a reproducible local dev environment.
- Server-side sessions avoid exposing long-lived tokens to the browser and allow consistent RBAC enforcement across CLI, API, and frontend.
- Deterministic realm and client configuration ensures tests and agents can run the flow without manual Keycloak setup.

---

## Files to add or modify (exact paths)

- `docker-compose.auth.yml` **(new)** — Keycloak service and optional helper
- `auth/keycloak-realm.json` **(new)** — realm import for Keycloak
- `tasker/auth/oauth.py` **(new)** — OAuth2 handlers and `SessionStore`
- `tasker/auth/SSO.md` **(new)** — documentation
- `frontend/src/auth.js` **(new)** — frontend SSO helpers
- `frontend/Dockerfile.frontend` **(modify)** — ensure `TASKER_API_URL` and SSO endpoints are available
- `tasker/cli/wiring.py` **(modify)** — add `session_store` wiring
- `tasker/api/app.py` **(modify)** — add session cookie handling and login/logout endpoints
- `tests/auth/test_oauth_unit.py` **(new)** — unit tests for OAuth handlers
- `tests/integration/test_sso_flow.py` **(new, integration)** — end-to-end SSO flow test
- `README.md` **(modify)** — add SSO local dev instructions

---

## Exact Keycloak realm file

Create `auth/keycloak-realm.json` with the exact content below. This file imports a realm `tasker-dev` with two users and two clients. **Do not change credentials** — they are for local dev only.

```json
{
  "realm": "tasker-dev",
  "enabled": true,
  "users": [
    {
      "username": "admin",
      "enabled": true,
      "credentials": [{"type":"password","value":"admintoken123","temporary":false}],
      "realmRoles": ["admin"]
    },
    {
      "username": "reader",
      "enabled": true,
      "credentials": [{"type":"password","value":"readertoken123","temporary":false}],
      "realmRoles": ["reader"]
    }
  ],
  "clients": [
    {
      "clientId": "tasker-frontend",
      "publicClient": true,
      "redirectUris": ["http://localhost:8080/*", "http://localhost:8080"],
      "protocol": "openid-connect",
      "directAccessGrantsEnabled": true,
      "standardFlowEnabled": true
    },
    {
      "clientId": "tasker-api",
      "publicClient": false,
      "secret": "tasker-api-secret",
      "redirectUris": ["http://localhost:8000/*"],
      "protocol": "openid-connect",
      "serviceAccountsEnabled": true,
      "standardFlowEnabled": true
    }
  ],
  "roles": {
    "realm": [
      {"name": "admin"},
      {"name": "reader"}
    ]
  }
}
```

---

## Exact Docker Compose for Keycloak

Create `docker-compose.auth.yml` with the exact content below.

```yaml
version: "3.8"
services:
  keycloak:
    image: quay.io/keycloak/keycloak:21.1.1
    command: start-dev --http-enabled=true
    environment:
      KEYCLOAK_ADMIN: "kcadmin"
      KEYCLOAK_ADMIN_PASSWORD: "kcadminpass"
    ports:
      - "8082:8080"
    volumes:
      - ./auth/keycloak-realm.json:/opt/keycloak/data/import/tasker-realm.json:ro
    entrypoint:
      - "/opt/keycloak/bin/kc.sh"
      - "start-dev"
      - "--import-realm"
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8080/realms/tasker-dev || exit 1"]
      interval: 5s
      timeout: 5s
      retries: 12
```

**Notes**
- Keycloak admin UI will be available at `http://localhost:8082` (mapped from container port 8080).
- The realm import will create `tasker-dev` with the clients and users defined above.

---

## Exact backend OAuth handlers

Create `tasker/auth/oauth.py` with the exact content below.

```python
# tasker/auth/oauth.py
from __future__ import annotations
import os
import json
import time
import urllib.parse
import requests
from typing import Optional, Dict, Any
from tasker.application.ports import StoragePort
from tasker.application.exceptions import StorageError

# Configurable via env
KEYCLOAK_BASE = os.getenv("TASKER_KEYCLOAK_URL", "http://localhost:8082")
REALM = os.getenv("TASKER_KEYCLOAK_REALM", "tasker-dev")
FRONTEND_CLIENT = os.getenv("TASKER_KEYCLOAK_FRONTEND_CLIENT", "tasker-frontend")
API_CLIENT = os.getenv("TASKER_KEYCLOAK_API_CLIENT", "tasker-api")
API_CLIENT_SECRET = os.getenv("TASKER_KEYCLOAK_API_CLIENT_SECRET", "tasker-api-secret")
REDIRECT_PATH = os.getenv("TASKER_OAUTH_REDIRECT_PATH", "/auth/callback")
SESSION_COOKIE_NAME = os.getenv("TASKER_SESSION_COOKIE", "TASKER_SESSION")
SESSION_TTL = int(os.getenv("TASKER_SESSION_TTL", "3600"))

def _auth_endpoint():
    return f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/auth"

def _token_endpoint():
    return f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/token"

def _logout_endpoint():
    return f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/logout"

class SessionStore:
    """
    Simple session store backed by StoragePort. Stores session data under key "session:<sid>".
    """

    PREFIX = "session:"

    def __init__(self, storage: StoragePort):
        self.storage = storage

    def create(self, data: Dict[str, Any], ttl: int = SESSION_TTL) -> str:
        sid = str(int(time.time() * 1000)) + "-" + str(hash(json.dumps(data)))
        key = self.PREFIX + sid
        try:
            self.storage.put(key, json.dumps(data).encode("utf-8"), ttl_seconds=ttl)
        except Exception as exc:
            raise StorageError(f"Failed to create session: {exc}") from exc
        return sid

    def get(self, sid: str) -> Optional[Dict[str, Any]]:
        key = self.PREFIX + sid
        raw = self.storage.get(key)
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def delete(self, sid: str) -> None:
        key = self.PREFIX + sid
        self.storage.delete(key)

def build_auth_url(state: str, redirect_uri: str, scope: str = "openid profile email") -> str:
    params = {
        "client_id": FRONTEND_CLIENT,
        "response_type": "code",
        "scope": scope,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    return _auth_endpoint() + "?" + urllib.parse.urlencode(params)

def exchange_code_for_tokens(code: str, redirect_uri: str) -> Dict[str, Any]:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": FRONTEND_CLIENT,
        "redirect_uri": redirect_uri,
    }
    # public client: no client_secret
    r = requests.post(_token_endpoint(), data=data, timeout=5)
    r.raise_for_status()
    return r.json()

def refresh_tokens(refresh_token: str) -> Dict[str, Any]:
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": API_CLIENT,
        "client_secret": API_CLIENT_SECRET,
    }
    r = requests.post(_token_endpoint(), data=data, timeout=5)
    r.raise_for_status()
    return r.json()

# Helper to validate ID token minimally (signature validation omitted for local dev)
def parse_id_token(id_token: str) -> Dict[str, Any]:
    # ID token is JWT; for deterministic local dev we parse payload without verifying signature
    try:
        parts = id_token.split(".")
        if len(parts) < 2:
            return {}
        import base64
        payload = parts[1] + "=="
        decoded = base64.urlsafe_b64decode(payload.encode("utf-8"))
        return json.loads(decoded.decode("utf-8"))
    except Exception:
        return {}

# Flask/FastAPI style handlers will call these helpers
def start_login_redirect(request_base_url: str, state: str) -> str:
    """
    Build redirect URL to Keycloak authorization endpoint.
    request_base_url: e.g., http://localhost:8000
    state: opaque state to roundtrip
    """
    redirect_uri = urllib.parse.urljoin(request_base_url, REDIRECT_PATH)
    return build_auth_url(state=state, redirect_uri=redirect_uri)

def handle_oauth_callback(code: str, request_base_url: str, session_store: SessionStore) -> Dict[str, Any]:
    """
    Exchange code for tokens, create session, and return session info.
    """
    redirect_uri = urllib.parse.urljoin(request_base_url, REDIRECT_PATH)
    tokens = exchange_code_for_tokens(code, redirect_uri)
    id_token = tokens.get("id_token")
    refresh = tokens.get("refresh_token")
    access = tokens.get("access_token")
    claims = parse_id_token(id_token) if id_token else {}
    # create session payload
    session = {
        "id_token": id_token,
        "access_token": access,
        "refresh_token": refresh,
        "claims": claims,
        "created_at": int(time.time()),
    }
    sid = session_store.create(session)
    return {"sid": sid, "claims": claims, "expires_in": SESSION_TTL}

def logout_session(sid: str, session_store: SessionStore) -> None:
    session_store.delete(sid)
```

**Notes**
- `parse_id_token` intentionally does not verify signatures in local dev; production must verify signatures and use JWKS.
- `start_login_redirect` and `handle_oauth_callback` are helpers; the API will expose endpoints that call them and set cookies.

---

## Exact API endpoint modifications

Modify `tasker/api/app.py` to add the following endpoints and session handling. Insert the code snippets exactly where appropriate (near other auth endpoints). These snippets assume `container.session_store` is available and `SessionStore` from `tasker/auth/oauth.py` is used.

**Login redirect endpoint**

```python
from fastapi.responses import RedirectResponse
from tasker.auth.oauth import start_login_redirect
import secrets

@app.get("/auth/login")
def auth_login(request: Request):
    # build redirect to Keycloak
    base = os.getenv("TASKER_BASE_URL", "http://localhost:8000")
    state = secrets.token_urlsafe(16)
    url = start_login_redirect(base, state)
    return RedirectResponse(url)
```

**OAuth callback endpoint**

```python
from fastapi import Response
from tasker.auth.oauth import handle_oauth_callback, SESSION_COOKIE_NAME

@app.get("/auth/callback")
def auth_callback(code: Optional[str] = None, response: Response = None, request: Request = None, container = Depends(get_container)):
    if not code:
        return JSONResponse(status_code=400, content={"status": "error", "error": "missing code"})
    base = os.getenv("TASKER_BASE_URL", "http://localhost:8000")
    session_store = container.session_store
    try:
        info = handle_oauth_callback(code, base, session_store)
        sid = info["sid"]
        # set secure cookie (HttpOnly)
        response = JSONResponse(content={"status": "ok"})
        response.set_cookie(SESSION_COOKIE_NAME, sid, httponly=True, secure=False, max_age=int(os.getenv("TASKER_SESSION_TTL", "3600")))
        return response
    except Exception as exc:
        return JSONResponse(status_code=500, content={"status": "error", "error": str(exc)})
```

**Logout endpoint**

```python
from tasker.auth.oauth import logout_session, _logout_endpoint

@app.post("/auth/logout")
def auth_logout(request: Request, response: Response, container = Depends(get_container)):
    sid = request.cookies.get(os.getenv("TASKER_SESSION_COOKIE", "TASKER_SESSION"))
    if sid:
        container.session_store.delete(sid)
    # redirect to Keycloak logout to clear server session
    logout_url = _logout_endpoint() + "?redirect_uri=" + urllib.parse.quote(os.getenv("TASKER_BASE_URL", "http://localhost:8000"))
    resp = RedirectResponse(logout_url)
    resp.delete_cookie(os.getenv("TASKER_SESSION_COOKIE", "TASKER_SESSION"))
    return resp
```

**Session-based authentication in request handling**

Where the API previously resolved `user_id` from `Authorization` header, update the logic to also check for `TASKER_SESSION` cookie:

```python
def get_user_id_from_request(request: Request, container = Depends(get_container)) -> Optional[str]:
    # check Authorization header first
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1]
        user_id = container.auth.verify_token(token)
        if user_id:
            return user_id
    # fallback to session cookie
    sid = request.cookies.get(os.getenv("TASKER_SESSION_COOKIE", "TASKER_SESSION"))
    if sid:
        session = container.session_store.get(sid)
        if session:
            claims = session.get("claims", {})
            # Keycloak subject or preferred_username
            return claims.get("preferred_username") or claims.get("sub")
    return None
```

Replace existing dependency `get_user_id_from_token` with a dependency that calls `get_user_id_from_request`.

---

## Exact wiring modifications

Modify `tasker/cli/wiring.py` to instantiate `SessionStore` and include it in the container. Insert the following lines after storage creation:

```python
from tasker.auth.oauth import SessionStore

session_store = SessionStore(storage)
# include in Container return
return Container(..., session_store=session_store, ...)
```

---

## Frontend SSO helpers

Create `frontend/src/auth.js` with the exact content below. This file provides deterministic login/logout helpers that call backend endpoints.

```javascript
// frontend/src/auth.js
export function login() {
  // redirect to backend login endpoint which redirects to Keycloak
  window.location.href = (window.__TASKER_API_URL || "http://localhost:8000") + "/auth/login";
}

export function logout() {
  fetch((window.__TASKER_API_URL || "http://localhost:8000") + "/auth/logout", { method: "POST", credentials: "include" })
    .then(() => {
      // clear client-side state if any and reload
      window.location.reload();
    });
}

export async function whoami() {
  // call an API endpoint that returns current user info based on session cookie
  const r = await fetch((window.__TASKER_API_URL || "http://localhost:8000") + "/api/v1/whoami", { credentials: "include" });
  if (r.ok) {
    return r.json();
  }
  return null;
}
```

**Note**: Add a small API endpoint `/api/v1/whoami` in `tasker/api/app.py` that returns current user info using `get_user_id_from_request`.

---

## Frontend index update (example)

If `examples/board/index.html` exists, update it to include login/logout buttons and to call `whoami`. Example snippet to add:

```html
<script src="/static/auth.js"></script>
<button id="login">Login</button>
<button id="logout">Logout</button>
<script>
  document.getElementById("login").addEventListener("click", () => login());
  document.getElementById("logout").addEventListener("click", () => logout());
  async function init() {
    const me = await whoami();
    if (me && me.username) {
      document.body.insertAdjacentHTML('afterbegin', '<div>Signed in as ' + me.username + '</div>');
    }
  }
  init();
</script>
```

---

## Unit test for OAuth helpers

Create `tests/auth/test_oauth_unit.py` with the exact content below. This test mocks Keycloak token exchange.

```python
# tests/auth/test_oauth_unit.py
import json
from unittest.mock import patch, MagicMock
from tasker.auth.oauth import exchange_code_for_tokens, handle_oauth_callback, SessionStore
from tasker.infrastructure.memory_storage import MemoryStorage

@patch("tasker.auth.oauth.requests.post")
def test_exchange_code_for_tokens(mock_post):
    mock_post.return_value = MagicMock(status_code=200, json=lambda: {"access_token":"a","id_token":"b","refresh_token":"r"})
    tokens = exchange_code_for_tokens("code", "http://localhost:8000/auth/callback")
    assert "access_token" in tokens

def test_session_store_create_get_delete():
    storage = MemoryStorage()
    ss = SessionStore(storage)
    sid = ss.create({"foo":"bar"}, ttl=10)
    assert ss.get(sid)["foo"] == "bar"
    ss.delete(sid)
    assert ss.get(sid) is None
```

---

## Integration test for SSO flow

Create `tests/integration/test_sso_flow.py` with the exact content below. This test requires Keycloak and API running via `docker-compose.auth.yml` and `docker-compose.api.yml`. It performs a simplified flow by calling Keycloak token endpoint directly (authorization code exchange is simulated).

```python
# tests/integration/test_sso_flow.py
import os
import time
import requests
import pytest

pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")

def test_sso_session_cookie_and_api_access():
    _skip_if_not_integration()
    # Keycloak must be running and realm imported
    # Simulate resource owner password grant for test user to obtain tokens (Keycloak dev allows direct token endpoint)
    token_url = "http://localhost:8082/realms/tasker-dev/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": "tasker-frontend",
        "username": "reader",
        "password": "readertoken123",
        "scope": "openid"
    }
    r = requests.post(token_url, data=data, timeout=5)
    assert r.status_code == 200
    tokens = r.json()
    id_token = tokens.get("id_token")
    # Now create a session via backend helper endpoint (simulate callback)
    # Call backend endpoint to create session (this endpoint is test-only and not in production)
    backend_session_create = "http://localhost:8000/test/create_session"
    r2 = requests.post(backend_session_create, json={"id_token": id_token, "access_token": tokens.get("access_token"), "refresh_token": tokens.get("refresh_token")}, timeout=5)
    assert r2.status_code == 200
    # backend returns cookie
    assert "set-cookie" in r2.headers or r2.cookies
    # use cookie to call protected API endpoint
    cookies = r2.cookies
    r3 = requests.get("http://localhost:8000/api/v1/whoami", cookies=cookies, timeout=5)
    assert r3.status_code == 200
    j = r3.json()
    assert j.get("username") == "reader"
```

**Note**: For deterministic integration, add a test-only endpoint `/test/create_session` in `tasker/api/app.py` that accepts tokens and creates a session via `handle_oauth_callback` or directly via `SessionStore`. This endpoint must be guarded to run only when `TASKER_INTEGRATION=1`.

---

## Documentation to add

Create `tasker/auth/SSO.md` with the exact content below.

```
Single Sign-On (SSO) with Keycloak

Overview
- Local development SSO using Keycloak and OpenID Connect.
- Keycloak realm import file: auth/keycloak-realm.json
- Keycloak admin UI: http://localhost:8082 (admin: kcadmin / kcadminpass)

How it works
1. Frontend redirects to backend /auth/login.
2. Backend builds Keycloak authorization URL and redirects browser.
3. User authenticates in Keycloak and Keycloak redirects to /auth/callback with code.
4. Backend exchanges code for tokens, creates a server-side session, and sets TASKER_SESSION cookie.
5. API endpoints accept either Authorization: Bearer <token> or TASKER_SESSION cookie.

Environment variables
- TASKER_KEYCLOAK_URL default http://localhost:8082
- TASKER_KEYCLOAK_REALM default tasker-dev
- TASKER_KEYCLOAK_API_CLIENT_SECRET default tasker-api-secret
- TASKER_BASE_URL default http://localhost:8000
- TASKER_SESSION_COOKIE default TASKER_SESSION

Local dev steps
1. Start Keycloak:
   docker compose -f docker-compose.auth.yml up -d
2. Start API and frontend (compose stacks).
3. Open frontend at http://localhost:8080 and click Login.

Security notes
- The realm and client configuration in auth/keycloak-realm.json are for local development only.
- In production, validate ID token signatures using Keycloak JWKS and use HTTPS and secure cookies.
```

---

## Commands the agent must run exactly

```bash
git checkout -b feature/sso-keycloak
# create files as specified
python -m pip install -e .
# start Keycloak
docker compose -f docker-compose.auth.yml up -d
# start API and frontend stacks as appropriate
docker compose -f docker-compose.api.yml up -d
docker compose -f docker-compose.api.yml up -d tasker-board
# run unit tests
pytest tests/auth/test_oauth_unit.py -q
# run integration test only if TASKER_INTEGRATION=1
export TASKER_INTEGRATION=1
pytest tests/integration/test_sso_flow.py -q -m integration || true
# commit and push
git add auth/keycloak-realm.json docker-compose.auth.yml tasker/auth/oauth.py tasker/auth/SSO.md frontend/src/auth.js tests/auth tests/integration tasker/api/app.py tasker/cli/wiring.py README.md
git commit -m "feat(auth): add Keycloak SSO, session store, and frontend integration for local dev"
git push origin feature/sso-keycloak
```

---

## PR body exact text to paste

```
Summary:
- Added local Keycloak SSO support with realm import auth/keycloak-realm.json.
- Added docker-compose.auth.yml to run Keycloak in dev mode with deterministic credentials.
- Implemented OAuth2 helpers and SessionStore in tasker/auth/oauth.py.
- Integrated session cookie handling and login/callback/logout endpoints in tasker/api/app.py.
- Added frontend SSO helpers frontend/src/auth.js and updated board to show login/logout.
- Wired SessionStore into container via tasker/cli/wiring.py.
- Added unit tests tests/auth/test_oauth_unit.py and integration test tests/integration/test_sso_flow.py (skipped unless TASKER_INTEGRATION=1).
- Added documentation tasker/auth/SSO.md.

Verification steps executed by this agent:
1. Started Keycloak via docker compose and imported realm.
2. Started API and frontend stacks.
3. Ran unit tests for OAuth helpers.
4. Optionally ran integration SSO flow test with TASKER_INTEGRATION=1.

Files changed:
- auth/keycloak-realm.json
- docker-compose.auth.yml
- tasker/auth/oauth.py
- tasker/auth/SSO.md
- frontend/src/auth.js
- tasker/api/app.py
- tasker/cli/wiring.py
- tests/auth/test_oauth_unit.py
- tests/integration/test_sso_flow.py
- README.md

Notes:
- The Keycloak configuration and credentials are for local development only. Production deployments must use secure secrets, HTTPS, and proper token validation.
```

---

## Acceptance criteria (must be satisfied exactly)
- `auth/keycloak-realm.json` exists and defines realm `tasker-dev`, clients `tasker-frontend` and `tasker-api`, and users `admin` and `reader` with the specified credentials.
- `docker-compose.auth.yml` exists and starts Keycloak with realm import and healthcheck.
- `tasker/auth/oauth.py` exists and implements `SessionStore`, `start_login_redirect`, `handle_oauth_callback`, `refresh_tokens`, and `logout_session` as specified.
- `tasker/api/app.py` exposes `/auth/login`, `/auth/callback`, `/auth/logout`, and `/api/v1/whoami` (test helper) and accepts session cookie authentication.
- `tasker/cli/wiring.py` wires `session_store` into the container.
- `frontend/src/auth.js` exists and provides `login`, `logout`, and `whoami` helpers.
- Unit tests `tests/auth/test_oauth_unit.py` pass.
- Integration test `tests/integration/test_sso_flow.py` passes when `TASKER_INTEGRATION=1` and compose stacks are running.
- `tasker/auth/SSO.md` documents the flow and environment variables.
- Branch `feature/sso-keycloak` created and PR opened with the exact PR body above.

---

## Labels to apply on GitHub
- `auth`
- `sso`
- `infra`
- `integration-test`
- `medium-priority`

---

## Estimated effort
**Medium (M)** — expected to take **2–4 hours** depending on environment and Docker availability.