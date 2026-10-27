"""Authenticated smoke test of the live API operations described by OpenAPI.

Writes use a unique run prefix and are cleaned up after the scan. Destructive
or resource-intensive endpoints are explicitly skipped.
"""
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from contextlib import suppress

import psycopg
import redis

BASE = os.getenv("TASKER_SMOKE_BASE_URL", "http://127.0.0.1:8888").rstrip("/")
REDIS_URL = os.getenv("TASKER_SMOKE_REDIS_URL", "redis://127.0.0.1:6379/0")
DATABASE_URL = os.getenv("TASKER_SMOKE_DATABASE_URL")
SMOKE = f"TASKER-SMOKE-{uuid.uuid4().hex[:10]}"
SMOKE_L = SMOKE.lower()

API_KEY = os.environ["TASKER_SMOKE_LOGIN_KEY"]
X_KEY = os.environ["TASKER_API_KEY"]
JWT = None  # se llena en login()
REFRESH_TOKEN = None
MIN_INTERVAL = float(os.getenv("TASKER_SMOKE_INTERVAL_SECONDS", "1.05"))
_last_call = [0.0]


def _throttle():
    wait = MIN_INTERVAL - (time.time() - _last_call[0])
    if wait > 0:
        time.sleep(wait)
    _last_call[0] = time.time()


def login():
    """POST /auth/login con la API key admin -> JWT (para endpoints que exigen claims)."""
    global JWT, REFRESH_TOKEN
    body = json.dumps({"api_key": API_KEY}).encode()
    req = urllib.request.Request(
        BASE + "/api/v1/auth/login", data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": SMOKE,
            "X-API-Key": X_KEY,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=7.5) as resp:
            data = json.loads(resp.read())
        JWT = data.get("access_token")
        if not isinstance(JWT, str) or not JWT:
            raise RuntimeError("Login response is missing an access_token")
        REFRESH_TOKEN = data.get("refresh_token")
        if not isinstance(REFRESH_TOKEN, str) or not REFRESH_TOKEN:
            raise RuntimeError("Login response is missing a refresh_token")
        print(f"[login] ok user={data.get('user', {}).get('username')} jwt={bool(JWT)}")
    except urllib.error.HTTPError as e:
        print(f"[login] FAIL {e.code}")
        raise

SKIP = {
    ("POST", "/api/v1"): "endpoint has no safe, reversible smoke contract",
    ("POST", "/api/v1/projects"): "persistent project creation has no DELETE route",
    ("POST", "/api/v1/projects/users"): "may create a graph user without safe scoped cleanup",
    ("POST", "/api/v1/reasoning/log"): "creates a Neo4j Agent node without a scoped delete route",
    ("POST", "/api/v1/reasoning/{reasoning_id}/feedback"): "creates persistent feedback without a delete route",
    ("POST", "/api/v1/admin/reset"): "DESTRUCTIVO (vacia la BD real)",
    ("POST", "/api/v1/setup/initialize"): "DESTRUCTIVO (inicializacion)",
    ("POST", "/api/v1/privacy/delete"): "DESTRUCTIVO (eliminacion de datos de cuenta)",
    ("POST", "/api/v1/privacy/export"): "creates a potentially sensitive export artifact",
    ("POST", "/api/v1/notifications/mark-all-read"): "changes all admin notification state",
    ("POST", "/api/v1/notifications/clear-all"): "DESTRUCTIVO (borra todas las notificaciones)",
    ("POST", "/api/v1/auth/logout"): "invalidates the JWT required by the rest of the smoke",
    ("POST", "/api/v1/auth/exchange"): "OAuth credential exchange is not a smoke operation",
    ("POST", "/api/v1/sync/force"): "starts an external synchronization job",
    ("POST", "/api/v1/labels/sync"): "may call GitHub and mutate remote labels",
    ("POST", "/api/v1/webhooks/github"): "processes externally signed GitHub events",
    ("POST", "/api/v1/webhooks/receive"): "processes arbitrary webhook payloads",
    ("POST", "/api/v1/webhooks/test-failure"): "intentionally triggers webhook failure handling",
    ("POST", "/api/v1/secrets/rotate"): "changes live secret material",
    ("POST", "/api/v1/secrets/rotate/run"): "rotates live secrets",
    ("POST", "/api/v1/ai/issues/{issue_id}/embed"): "may incur provider cost and mutate embeddings",
    ("POST", "/api/v1/ai/search-similar-solutions"): "may incur provider cost",
    ("POST", "/api/v1/ai/backfill-embeddings"): "PESADO (backfill de embeddings)",
    ("POST", "/api/v1/auto-healing/runs"): "starts an autonomous remediation run",
    ("POST", "/api/v1/agent-skills/import-url"): "fetches external URLs and creates persistent skills",
    ("POST", "/api/v1/agent-skills/import"): "creates persistent skills from uploaded files",
    ("POST", "/api/v1/mcp/tool-calls"): "creates tool-call records without a delete route",
    ("DELETE", "/api/v1/reasoning"): "DESTRUCTIVO (borra todos los reasoning logs)",
    ("DELETE", "/api/v1/rag"): "DESTRUCTIVO (borra indice RAG)",
    ("DELETE", "/api/v1/code-graph"): "DESTRUCTIVO (borra code graph)",
    ("POST", "/api/v1/code-graph/scan"): "PESADO (escaneo del repo)",
    ("POST", "/api/v1/rag/index"): "PESADO (indexa documentos)",
    ("POST", "/api/v1/issues/{issue_id}/link-github"): "may mutate a remote GitHub issue",
    ("POST", "/api/v1/issues/{issue_id}/unlink-github"): "may mutate a remote GitHub issue",
    ("POST", "/api/v1/issues/{issue_id}/github-sync"): "starts external GitHub synchronization",
    ("POST", "/api/v1/issues/{issue_id}/github-sync/resolve"): "may mutate a remote GitHub issue",
    ("POST", "/api/v1/issues/{issue_id}/mirror-root-cause"): "may post to a remote GitHub issue",
    ("POST", "/api/v1/issues/{issue_id}/mirror-impact"): "may post to a remote GitHub issue",
    ("POST", "/api/v1/issues/{issue_id}/dependencies"): "seed phase already tests dependency creation",
    ("POST", "/api/v1/issues/{issue_id}/start-agent"): "starts a background agent run",
    ("POST", "/api/v1/issues/{issue_id}/agent/start"): "starts a background agent run",
    ("POST", "/api/v1/issues/{issue_id}/agent/finish"): "changes agent execution state",
    ("POST", "/api/v1/issues/{issue_id}/agent/heartbeat"): "changes agent execution state",
    ("POST", "/api/v1/issues/{issue_id}/stop-agent"): "changes agent execution state",
    ("POST", "/api/v1/agents/{agent_id}/runs"): "starts an agent workflow",
    ("POST", "/api/v1/agents/register"): "persists a Neo4j agent without a safe delete route",
    ("POST", "/api/v1/models/{model_name}/infer"): "model inference may incur provider cost",
    ("GET", "/api/v1/auth/oauth/{provider}/callback"): "OAuth callback requires a real provider authorization state",
    ("DELETE", "/api/v1/components/{component_id}"): (
        "seed component is linked to smoke issues and is cleaned after them"
    ),
}
SSE = ("/stream",)

spec_request = urllib.request.Request(
    BASE + "/openapi.json",
    headers={"X-API-Key": X_KEY},
)
spec = json.load(urllib.request.urlopen(spec_request, timeout=7.5))
schemas = spec.get("components", {}).get("schemas", {})


def deref(ref):
    target = schemas.get(ref.rsplit("/", 1)[-1])
    if target is None:
        raise ValueError(f"OpenAPI reference not found: {ref}")
    return target


def example(sch, name="x", depth=0):
    if depth > 12:
        raise ValueError(f"OpenAPI schema recursion limit reached for {name}")
    if not isinstance(sch, dict):
        raise ValueError(f"Invalid OpenAPI schema for {name}")
    if "$ref" in sch:
        return example(deref(sch["$ref"]), name, depth + 1)
    if "allOf" in sch:
        out = {}
        for sub in sch["allOf"]:
            ex = example(sub, name, depth + 1)
            if isinstance(ex, dict):
                out.update(ex)
            else:
                raise ValueError(f"Unsupported allOf schema for {name}")
        out.update(_obj(sch, name, depth + 1))
        return out
    for key in ("oneOf", "anyOf"):
        if key in sch and sch[key]:
            branches = [
                b for b in sch[key]
                if not (
                    isinstance(b, dict)
                    and (b.get("type") == "null" or b.get("nullable") is True)
                )
            ] or sch[key]
            for branch in branches:
                try:
                    return example(branch, name, depth + 1)
                except ValueError:
                    continue
            raise ValueError(f"No supported {key} branch for {name}")
    if "enum" in sch:
        if not sch["enum"]:
            raise ValueError(f"Empty enum for {name}")
        return sch["enum"][0]
    if "const" in sch:
        return sch["const"]
    if "default" in sch:
        return sch["default"]
    if "example" in sch:
        return sch["example"]
    t = sch.get("type")
    if isinstance(t, list):
        types = [item for item in t if item != "null"]
        if not types:
            return None
        t = types[0]
    if t == "object" or "properties" in sch:
        return _obj(sch, name, depth + 1)
    if t == "array":
        item = sch.get("items")
        if not isinstance(item, dict):
            raise ValueError(f"Array schema missing items for {name}")
        value = example(item, name, depth + 1)
        return [value] * max(1, sch.get("minItems", 1))
    if t == "integer":
        return max(1, int(sch.get("minimum", 1)))
    if t == "number":
        return max(1.0, float(sch.get("minimum", 1)))
    if t == "boolean":
        return True
    if t == "string":
        fmt = sch.get("format", "")
        if fmt == "email":
            value = f"{SMOKE_L}@example.com"
        if fmt == "uuid":
            value = str(uuid.uuid5(uuid.NAMESPACE_URL, SMOKE + name))
        elif fmt == "date-time":
            value = "2026-10-26T12:00:00Z"
        elif fmt == "date":
            value = "2026-10-26"
        elif fmt == "email":
            pass
        elif fmt in ("uri", "url"):
            value = f"https://example.invalid/{SMOKE_L}"
        elif "password" in name.lower() or "secret" in name.lower():
            value = f"{SMOKE_L}-secret-value"
        else:
            slug = re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-") or "x"
            value = f"{SMOKE_L}-{slug}"
        value = value[: sch.get("maxLength", 200)]
        return value.ljust(sch.get("minLength", 1), "x")
    raise ValueError(f"Unsupported OpenAPI type {t!r} for {name}")


def _obj(sch, name, depth=0):
    out = {}
    properties = sch.get("properties", {})
    required = sch.get("required", [])
    for k in required:
        if k not in properties:
            raise ValueError(f"Required property {k} missing in schema for {name}")
        out[k] = example(properties[k], k, depth + 1)
    return out


def call(method, path, body=None, timeout=7.5, stream=False):
    # Los endpoints de chat/notificaciones validan claims JWT ademas del
    # middleware; ademas flags/tenants/data-quality exigen verify_token (JWT).
    bearer = JWT
    headers = {
        "Accept": "application/json",
        "User-Agent": SMOKE,
        "X-API-Key": X_KEY,
        "Authorization": f"Bearer {bearer}",
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"

    for attempt in (1, 2, 3):
        _throttle()
        req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
        t0 = time.time()
        try:
            resp = urllib.request.urlopen(req, timeout=timeout)
            status = resp.status
            hdrs = dict(resp.headers)
            if stream:
                with suppress(TimeoutError):
                    resp.read(512)
                raw = b""
            else:
                raw = resp.read()
            resp.close()
        except urllib.error.HTTPError as e:
            status = e.code
            hdrs = dict(e.headers)
            raw = e.read()
        except TimeoutError:
            return {"status": None, "note": "timeout", "ms": int((time.time() - t0) * 1000), "body": ""}
        except Exception as e:  # noqa: BLE001
            return {"status": None, "note": type(e).__name__, "ms": int((time.time() - t0) * 1000), "body": ""}

        if status == 429 and attempt < 3:
            try:
                time.sleep(int(hdrs.get("Retry-After", "2")) + 1)
            except ValueError:
                time.sleep(3)
            continue

        try:
            parsed = json.loads(raw.decode("utf-8")) if raw else None
        except Exception:  # noqa: BLE001
            parsed = None
        return {
            "status": status,
            "note": "",
            "ms": int((time.time() - t0) * 1000),
            "body": "",
            "json": parsed,
        }
    return {"status": status, "note": "429 after retries", "ms": 0, "body": "", "json": None}


def unwrap(res):
    """Obtiene el payload util de una respuesta con envoltorio tipico."""
    if not isinstance(res, dict):
        return None
    j = res.get("json")
    if isinstance(j, dict) and "data" in j:
        return j["data"]
    if isinstance(j, dict) and len(j) == 1:
        only = next(iter(j.values()))
        if isinstance(only, list):
            return only
    return j


def is_smoke(value):
    return SMOKE.upper() in str(value or "").upper()


# --- entidades base creadas explicitamente (y luego limpiadas) -------------

created = {"issues": [], "other_deletes": []}
ids = {}


def first_id(res, *keys):
    data = unwrap(res)
    if isinstance(data, dict):
        for k in keys:
            if k in data:
                return data[k]
        if "id" in data:
            return data["id"]
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0].get("id")
    return None


def step(label, method, path, body=None, timeout=8):
    r = call(method, path, body, timeout=timeout)
    print(f"[seed] {label}: {method} {path} -> {r['status']}")
    return r


print("=== LOGIN ===")
login()

print("=== FASE 1: crear entidades base ===")
r = step("component", "POST", "/api/v1/components",
         {"name": f"{SMOKE} component", "description": "smoke"})
ids["component_id"] = first_id(r, "id")

r = step("issue", "POST", "/api/v1/issues",
         {"title": f"{SMOKE} probe issue", "description": "real backend smoke test",
          "priority": "LOW", "status": "OPEN", "component_id": ids.get("component_id")})
ids["issue_id"] = first_id(r, "id", "issue_id")
created["issues"].append(ids["issue_id"])

r = step("issue2", "POST", "/api/v1/issues",
         {"title": f"{SMOKE} probe issue 2", "priority": "LOW",
          "component_id": ids.get("component_id")})
ids["issue2_id"] = first_id(r, "id")
created["issues"].append(ids["issue2_id"])

r = step("batch", "POST", "/api/v1/issues/batch",
         {"issues": [{"title": f"{SMOKE} batch a", "priority": "LOW",
                      "component_id": ids.get("component_id")},
                     {"title": f"{SMOKE} batch b", "priority": "LOW",
                      "component_id": ids.get("component_id")}]})
batch = unwrap(r)
if isinstance(batch, list):
    for it in batch:
        if isinstance(it, dict) and it.get("id"):
            created["issues"].append(it["id"])
elif isinstance(batch, dict):
    for it in batch.get("issues", batch.get("created", [])) or []:
        if isinstance(it, dict) and it.get("id"):
            created["issues"].append(it["id"])

r = step("user", "POST", "/api/v1/users",
         {"username": f"{SMOKE_L}-user", "email": f"{SMOKE_L}@example.com",
          "role": "developer", "type": "human"})
ids["user_id"] = first_id(r, "id")

r = step("agent-profile", "POST", "/api/v1/agents/profiles",
         {"username": f"{SMOKE_L}-agent", "email": f"{SMOKE_L}-agent@example.com"})
ids["agent_id"] = first_id(r, "id", "agent_id")

r = step("policy", "POST", "/api/v1/policies",
         {"name": f"{SMOKE} policy", "description": "smoke"})
ids["policy_id"] = first_id(r, "id")

r = step("epic", "POST", "/api/v1/epics",
         {"name": f"{SMOKE} epic", "description": "smoke"})
ids["epic_id"] = first_id(r, "id", "epic_id")

r = step("objective", "POST", "/api/v1/objectives",
         {"name": f"{SMOKE} objective", "description": "smoke"})
ids["objective_id"] = first_id(r, "id", "objective_id")

r = step("workflow", "POST", "/api/v1/workflows",
         {"slug": f"{SMOKE_L}-wf", "name": f"{SMOKE} workflow",
          "steps": [], "description": "smoke"})
ids["slug"] = first_id(r, "slug", "id") or f"{SMOKE_L}-wf"

r = step("secret", "POST", "/api/v1/secrets",
         {"name": f"{SMOKE_L}-secret",
          "value": base64.b64encode(f"{SMOKE_L}-value".encode()).decode()})
ids["secret_name"] = first_id(r, "name", "id") or f"{SMOKE_L}-secret"

r = step("commit", "POST", "/api/v1/commits",
         {"sha": uuid.uuid4().hex + uuid.uuid4().hex[:8],
          "message": f"{SMOKE} commit", "author_name": SMOKE_L})
ids["sha"] = first_id(r, "sha", "id")

r = step("conversation", "POST", "/api/v1/chat/conversations",
         {"participantIds": ["admin", ids.get("user_id") or "admin"],
          "type": "direct", "title": f"{SMOKE} conversation"})
ids["conversation_id"] = first_id(r, "id", "conversation_id")

r = step("tenant", "POST", "/api/v1/admin/tenants",
         {"name": f"{SMOKE} tenant"})
ids["tenant_id"] = first_id(r, "id")

r = step("flag", "POST", "/api/v1/admin/flags",
         {"name": f"{SMOKE_L}-flag", "enabled": True})
ids["flag_name"] = first_id(r, "name", "id") or f"{SMOKE_L}-flag"

r = step("subscription", "POST", "/api/v1/webhooks/subscriptions",
         {"url": "https://example.invalid/smoke", "events": ["push"]})
ids["sid"] = first_id(r, "id", "sid")

r = step("dataset", "POST", "/api/v1/registry/datasets",
         {"dataset_id": f"{SMOKE_L}-dataset", "title": SMOKE,
          "description": "smoke", "schema_name": "default",
          "default_schema_version": "1", "owner": SMOKE_L})
ids["dataset_id"] = first_id(r, "dataset_id", "id") or f"{SMOKE_L}-dataset"

r = step("registry-schema", "POST", "/api/v1/registry/schemas",
         {"name": f"{SMOKE_L}-schema", "version": "1.0.0",
          "schema": {"type": "object", "properties": {"probe": {"type": "string"}}}})
ids["schema_name"] = first_id(r, "name", "id") or f"{SMOKE_L}-schema"

r = step("dq-rule", "POST", "/api/v1/data-quality/rules",
         {"id": f"{SMOKE_L}-dq", "name": f"{SMOKE_L}-dq",
          "kind": "not_empty", "target": "title"})
ids["dq_rule"] = first_id(r, "id") or f"{SMOKE_L}-dq"

r = step("skill", "POST", "/api/v1/skills",
         {"name": f"{SMOKE_L}-skill", "description": "smoke"})
ids["skill_id"] = first_id(r, "id")

r = step("agent-skill", "POST", "/api/v1/agent-skills",
         {"name": f"{SMOKE_L}-as", "behavior": "assist"})
ids["agent_skill_id"] = first_id(r, "id", "name")

r = step("dependency", "POST", f"/api/v1/issues/{ids.get('issue_id') or SMOKE_L}/dependencies",
         {"depends_on_id": ids.get("issue2_id") or f"{SMOKE_L}-issue2"})
ids["dep_id"] = first_id(r, "id")

r = step("comment", "POST", f"/api/v1/issues/{ids.get('issue_id') or SMOKE_L}/comments",
         {"text": f"{SMOKE} comment", "author": SMOKE_L})
ids["comment_id"] = first_id(r, "id")

r = step("notification-ish", "GET", "/api/v1/notifications")
# No usar IDs reales de notificaciones en rutas que mutan: placeholders smoke.

r = step("mcp-session", "POST", "/api/v1/mcp/sessions",
         {"clientName": f"{SMOKE_L}-client"})
ids["session_id"] = first_id(r, "id", "session_id")

r = step("mcp-server", "POST", "/api/v1/mcp/servers",
         {"name": f"{SMOKE_L}-mcp", "url": "http://127.0.0.1:9/smoke"})
ids["mcp_server_id"] = first_id(r, "id", "name")

print(f"ids={json.dumps(ids, indent=None)}")

# --- FASE 2: recorrer todas las rutas --------------------------------------

print("=== FASE 2: leer IDs reales para GETs (solo lectura) ===")
ids_read = dict(ids)
for key, path, pick in (
    ("issue_id", "/api/v1/issues", lambda d: d.get("id")),
    ("component_id", "/api/v1/components", lambda d: d.get("id")),
    ("policy_id", "/api/v1/policies", lambda d: d.get("id")),
    ("epic_id", "/api/v1/epics", lambda d: d.get("id")),
    ("objective_id", "/api/v1/objectives", lambda d: d.get("id")),
    ("agent_id", "/api/v1/agents", lambda d: d.get("id") or d.get("agent_id")),
    ("user_id", "/api/v1/users", lambda d: d.get("id")),
):
    r = call("GET", path)
    items = unwrap(r)
    if isinstance(items, list):
        real = [x for x in items if isinstance(x, dict)
                and not str(x.get("title") or x.get("name") or x.get("username") or "").startswith(SMOKE)]
        if real and pick(real[0]):
            ids_read[key] = pick(real[0])
print("ids_read:", json.dumps({k: ids_read.get(k) for k in ("issue_id", "component_id")}))

# Limpieza directa de POSTs sin listado (se ejecuta tras la fase 2).
POST_DELETE = {
    "/api/v1/secrets": "/api/v1/secrets/{}",
    "/api/v1/commits": "/api/v1/commits/{}",
    "/api/v1/workflows": "/api/v1/workflows/{}",
    "/api/v1/deployments": "/api/v1/deployments/{}",
    "/api/v1/registry/schemas": "/api/v1/registry/schemas/{}",
    "/api/v1/data-quality/rules": "/api/v1/data-quality/rules/{}",
    "/api/v1/mcp/sessions": "/api/v1/mcp/sessions/{}",
    "/api/v1/agent-skills": "/api/v1/agent-skills/{}",
}
POST_ID_KEYS = {
    "/api/v1/secrets": ("name", "id"),
    "/api/v1/commits": ("sha", "id"),
    "/api/v1/workflows": ("slug", "id"),
    "/api/v1/registry/schemas": ("name", "id"),
    "/api/v1/data-quality/rules": ("id",),
}
cleanup_urls = []


def fill_path(path, read_only):
    src = ids_read if read_only else ids

    def sub(m):
        p = m.group(1)
        if p in src and src[p]:
            return str(src[p])
        if p in ids and ids[p]:
            return str(ids[p])
        return f"{SMOKE_L}-{p}"

    return re.sub(r"\{([^}]+)\}", sub, path)


ops = []
for path, methods in spec["paths"].items():
    for method in methods:
        if method in ("get", "post", "put", "patch", "delete"):
            ops.append((method.upper(), path, methods[method]))
# Los DELETE van al final; reasoning debe borrarse antes que su issue asociado.
ops.sort(key=lambda o: (
    0 if o[0] != "DELETE" else
    1 if o[1] == "/api/v1/reasoning/issue/{issue_id}" else
    2
))

# Overrides for operation constraints that OpenAPI cannot express.
BODY_OVERRIDE = {
    ("POST", "/api/v1/issues"): lambda b: {
        **(b or {}), "title": f"{SMOKE} operation issue",
        "description": "smoke operation",
        "priority": "LOW",
        "component_id": ids.get("component_id") or f"{SMOKE_L}-component",
    },
    ("POST", "/api/v1/commits"): lambda b: {**(b or {}),
                                            "sha": uuid.uuid4().hex + uuid.uuid4().hex[:8]},
    ("POST", "/api/v1/deployments"): lambda b: {
        **(b or {}), "commit_sha": uuid.uuid4().hex + uuid.uuid4().hex[:8],
    },
    ("POST", "/api/v1/epics"): lambda b: {
        **(b or {}), "name": f"{SMOKE} epic operation",
        "description": "smoke operation",
    },
    ("POST", "/api/v1/objectives"): lambda b: {
        **(b or {}), "name": f"{SMOKE} objective operation",
        "description": "smoke operation",
    },
    ("POST", "/api/v1/users"): lambda b: {
        **(b or {}), "username": f"{SMOKE_L}-user-operation",
        "email": f"{SMOKE_L}-operation@example.com", "role": "developer",
        "type": "human",
    },
    ("POST", "/api/v1/secrets"): lambda b: {
        **(b or {}), "name": f"{SMOKE_L}-secret-operation",
        "value": base64.b64encode(f"{SMOKE_L}-secret".encode()).decode(),
    },
    ("POST", "/api/v1/chat/conversations"): lambda b: {
        **(b or {}),
        "participantIds": ["admin", ids.get("user_id") or SMOKE_L],
        "type": "direct", "title": f"{SMOKE} conversation operation",
    },
    ("POST", "/api/v1/chat/conversations/{conversation_id}/messages"): lambda b: {
        **(b or {}), "text": f"{SMOKE} message", "type": "text",
    },
    ("POST", "/api/v1/registry/schemas"): lambda b: {
        **(b or {}), "name": f"{SMOKE_L}-schema-operation",
        "version": "1.0.0",
        "schema": {"type": "object", "properties": {"probe": {"type": "string"}}},
    },
    ("POST", "/api/v1/data-quality/rules"): lambda b: {
        **(b or {}), "id": f"{SMOKE_L}-dq-operation",
        "name": f"{SMOKE_L}-dq-operation", "kind": "not_empty", "target": "issues",
    },
    ("POST", "/api/v1/admin/flags"): lambda b: {
        **(b or {}), "name": f"{SMOKE_L}-flag-operation", "value": True,
    },
    ("PATCH", "/api/v1/components/{component_id}"): lambda b: {
        **(b or {}), "description": "smoke update",
    },
    ("PATCH", "/api/v1/epics/{epic_id}"): lambda b: {
        **(b or {}), "description": "smoke update",
    },
    ("PATCH", "/api/v1/objectives/{objective_id}"): lambda b: {
        **(b or {}), "description": "smoke update",
    },
    ("POST", "/api/v1/components/{component_id}/dependencies"): lambda b: {
        **(b or {}), "depends_on_id": f"{SMOKE_L}-missing-component",
    },
    ("POST", "/api/v1/reasoning/log"): lambda b: {
        **(b or {}), "issue_id": ids.get("issue_id") or f"{SMOKE_L}-issue",
        "agent_id": f"{SMOKE_L}-reasoning-agent",
        "agent_name": f"{SMOKE} reasoning agent",
    },
    ("PUT", "/api/v1/users/{user_id}"): lambda b: {"role": "DEVELOPER"},
}
QUERY_OVERRIDE = {
    ("GET", "/api/v1/users/{user_id}/issues"): {"kind": "assigned"},
}

RESULTS = []
for M, path, op in ops:
    key = (M, path)
    if key in SKIP:
        RESULTS.append({"m": M, "p": path, "status": None, "verdict": "SKIP",
                        "note": SKIP[key]})
        continue

    read_only = M == "GET"
    real_path = fill_path(path, read_only)
    if key == ("POST", "/api/v1/issues/{issue_id}/close") and ids.get("issue2_id"):
        real_path = f"/api/v1/issues/{ids['issue2_id']}/close"
    body = None
    if M in ("POST", "PUT", "PATCH", "DELETE"):
        if (M, path) == ("POST", "/api/v1/auth/login"):
            body = {"api_key": API_KEY}
        else:
            rb = op.get("requestBody", {})
            media = rb.get("content", {})
            json_schema = media.get("application/json", {}).get("schema")
            if json_schema is not None:
                try:
                    body = example(json_schema, op.get("operationId", "body"))
                except ValueError as exc:
                    RESULTS.append({
                        "m": M, "p": path, "status": None, "verdict": "SKIP",
                        "note": f"unsupported request schema: {exc}",
                    })
                    continue
            elif rb.get("required"):
                RESULTS.append({
                    "m": M, "p": path, "status": None, "verdict": "SKIP",
                    "note": "required request body has no application/json schema",
                })
                continue
        if body is not None and (M, path) in BODY_OVERRIDE:
            body = BODY_OVERRIDE[(M, path)](body)

    query = {}
    for prm in op.get("parameters", []):
        if prm.get("in") == "query" and prm.get("required"):
            query[prm["name"]] = example(prm.get("schema", {}), prm["name"])
    if (M, path) in QUERY_OVERRIDE:
        query.update(QUERY_OVERRIDE[(M, path)])
    if query:
        qs = urllib.parse.urlencode(query)
        real_path = real_path + ("&" if "?" in real_path else "?") + qs

    is_sse = any(real_path.endswith(s) for s in SSE)
    r = call(M, real_path, body, timeout=3 if is_sse else 7.5, stream=is_sse)
    st = r["status"]
    if st is None:
        verdict = "TIMEOUT"
    elif st < 400:
        verdict = "PASS"
    elif st in (401, 403, 404):
        verdict = "GRACE"
    else:
        verdict = "ERR" if st >= 500 else "4XX"
    RESULTS.append({"m": M, "p": path, "status": st,
                    "verdict": verdict, "note": r["note"], "ms": r["ms"]})

    if M == "POST" and path == "/api/v1/issues" and st and st < 400:
        issue_id = first_id(r, "id", "issue_id")
        if issue_id and issue_id not in created["issues"]:
            created["issues"].append(issue_id)

    # Registrar creaciones POST sin endpoint de listado para limpieza directa.
    if M == "POST" and st and st < 400:
        if path in POST_DELETE:
            rid = first_id(r, *POST_ID_KEYS.get(path, ("id",)))
            if not rid and isinstance(body, dict):
                rid = next(
                    (body.get(key) for key in POST_ID_KEYS.get(path, ("id",)) if body.get(key)),
                    None,
                )
            if rid:
                cleanup_urls.append(POST_DELETE[path].format(rid))
        elif path.endswith("/runs"):
            rid = first_id(r, "id", "run_id")
            if rid:
                cleanup_urls.append(f"/api/v1/runs/{rid}")

# --- FASE 3: limpiar entidades SMOKE777 ------------------------------------


print("=== FASE 3: limpieza ===")
cleaned = {}
cleanup_errors = []


def list_items(list_path, response):
    items = unwrap(response)
    if isinstance(items, dict):
        lists = [value for value in items.values() if isinstance(value, list)]
        if len(lists) == 1:
            items = lists[0]
        elif list_path == "/api/v1/admin/flags" and isinstance(items.get("flags"), dict):
            items = [{"name": name} for name in items["flags"]]
    return items


def list_records(list_path):
    operation = spec.get("paths", {}).get(list_path, {}).get("get", {})
    query_names = {
        parameter.get("name")
        for parameter in operation.get("parameters", [])
        if parameter.get("in") == "query"
    }
    limit = 100
    page = 1
    records = []
    seen_pages = set()

    for _ in range(100):
        query = {}
        if "page" in query_names:
            query["page"] = page
        if "limit" in query_names:
            query["limit"] = limit
        path = f"{list_path}?{urllib.parse.urlencode(query)}" if query else list_path
        response = call("GET", path)
        items = list_items(list_path, response)
        if not isinstance(items, list):
            message = (
                f"ERROR: {list_path} returned status {response['status']} "
                "with no list payload"
            )
            cleanup_errors.append(message)
            return None
        if not items:
            break

        fingerprint = json.dumps(items, sort_keys=True, default=str)
        if fingerprint in seen_pages:
            message = f"ERROR: {list_path} repeated page {page}; cleanup is incomplete"
            cleanup_errors.append(message)
            return None
        seen_pages.add(fingerprint)
        records.extend(items)

        payload = response.get("json")
        meta = payload.get("meta", {}) if isinstance(payload, dict) else {}
        pagination = meta.get("pagination", {}) if isinstance(meta, dict) else {}
        has_next = pagination.get("has_next") if isinstance(pagination, dict) else None
        if has_next is False:
            break
        if has_next is True:
            if "page" not in query_names:
                message = f"ERROR: {list_path} reports more pages but has no page parameter"
                cleanup_errors.append(message)
                return None
            page += 1
            continue
        if "page" in query_names and len(items) >= limit:
            page += 1
            continue
        break
    else:
        message = f"ERROR: {list_path} exceeded the 100-page cleanup limit"
        cleanup_errors.append(message)
        return None

    return records


def list_delete(list_path, delete_path_tpl, id_key, matcher):
    items = list_records(list_path)
    if items is None:
        return "ERROR"
    n = 0
    for it in items:
        if not isinstance(it, dict):
            continue
        if matcher(it):
            iid = it.get(id_key) or it.get("id")
            if not iid:
                message = f"ERROR: {list_path} returned a tagged record without an id"
                cleanup_errors.append(message)
                continue
            path = delete_path_tpl.format(urllib.parse.quote(str(iid), safe=""))
            d = call("DELETE", path)
            if d["status"] and (d["status"] < 400 or d["status"] == 404):
                n += 1
            else:
                message = f"ERROR: DELETE {path} returned status {d['status']}"
                cleanup_errors.append(message)

    if n:
        remaining = list_records(list_path)
        if remaining is None:
            return n
        remaining_count = sum(
            1 for it in remaining if isinstance(it, dict) and matcher(it)
        )
        if remaining_count:
            message = (
                f"ERROR: {list_path} still has {remaining_count} tagged "
                "record(s) after cleanup"
            )
            cleanup_errors.append(message)
    return n


# Limpieza directa de POSTs sin listado.
direct_ok = 0
for u in cleanup_urls:
    d = call("DELETE", u)
    if d["status"] and (d["status"] < 400 or d["status"] == 404):
        direct_ok += 1
    else:
        cleanup_errors.append(f"ERROR: DELETE {u} returned status {d['status']}")
cleaned["direct"] = f"{direct_ok}/{len(cleanup_urls)}"

# Reasoning nodes are linked to issues, so remove them before deleting issues.
reasoning_url = (
    f"/api/v1/reasoning/issue/{ids['issue_id']}" if ids.get("issue_id") else None
)
if reasoning_url:
    reasoning_delete = call("DELETE", reasoning_url)
    cleaned["reasoning"] = reasoning_delete["status"]
    if not reasoning_delete["status"] or reasoning_delete["status"] >= 400:
        cleanup_errors.append(
            f"ERROR: DELETE {reasoning_url} returned status {reasoning_delete['status']}"
        )

# Listados con prefijo smoke (incluye batch y autocreaciones de la fase 2).
cleaned["issues"] = list_delete(
    "/api/v1/issues", "/api/v1/issues/{}", "id",
    lambda it: is_smoke(it.get("title")),
)
cleaned["agent_profiles"] = list_delete(
    "/api/v1/agents/profiles", "/api/v1/agents/profiles/{}", "id",
    lambda it: is_smoke(it.get("name")) or is_smoke(it.get("username")),
)
cleaned["skills"] = list_delete(
    "/api/v1/skills", "/api/v1/skills/{}", "id",
    lambda it: is_smoke(it.get("name")),
)
cleaned["agent_skills"] = list_delete(
    "/api/v1/agent-skills", "/api/v1/agent-skills/{}", "id",
    lambda it: is_smoke(it.get("name")),
)
cleaned["users"] = list_delete(
    "/api/v1/users", "/api/v1/users/{}", "id",
    lambda it: is_smoke(it.get("username")) or is_smoke(it.get("email")),
)
cleaned["agents"] = list_delete(
    "/api/v1/agents", "/api/v1/agents/{}", "agent_id",
    lambda it: is_smoke(it.get("name")) or is_smoke(it.get("username")),
)
cleaned["policies"] = list_delete(
    "/api/v1/policies", "/api/v1/policies/{}", "id",
    lambda it: is_smoke(it.get("name")),
)
cleaned["epics"] = list_delete(
    "/api/v1/epics", "/api/v1/epics/{}", "epic_id",
    lambda it: is_smoke(it.get("title")) or is_smoke(it.get("name")),
)
cleaned["objectives"] = list_delete(
    "/api/v1/objectives", "/api/v1/objectives/{}", "objective_id",
    lambda it: is_smoke(it.get("title")) or is_smoke(it.get("name")),
)
cleaned["conversations"] = list_delete(
    "/api/v1/chat/conversations", "/api/v1/chat/conversations/{}", "conversation_id",
    lambda it: is_smoke(it.get("title")),
)
cleaned["tenants"] = list_delete(
    "/api/v1/admin/tenants", "/api/v1/admin/tenants/{}", "tenant_id",
    lambda it: is_smoke(it.get("name")),
)
cleaned["flags"] = list_delete(
    "/api/v1/admin/flags", "/api/v1/admin/flags/{}", "name",
    lambda it: is_smoke(it.get("name")),
)
cleaned["subscriptions"] = list_delete(
    "/api/v1/webhooks/subscriptions", "/api/v1/webhooks/subscriptions/{}", "sid",
    lambda it: is_smoke(it.get("url")),
)
cleaned["datasets"] = list_delete(
    "/api/v1/registry/datasets", "/api/v1/registry/datasets/{}", "dataset_id",
    lambda it: is_smoke(it.get("name")) or is_smoke(it.get("dataset_id"))
    or is_smoke(it.get("title")),
)
cleaned["mcp_sessions"] = list_delete(
    "/api/v1/mcp/sessions", "/api/v1/mcp/sessions/{}", "id",
    lambda it: is_smoke(it.get("clientName")),
)
cleaned["mcp_servers"] = list_delete(
    "/api/v1/mcp/servers", "/api/v1/mcp/servers/{}", "id",
    lambda it: is_smoke(it.get("name")),
)
cleaned["components"] = list_delete(
    "/api/v1/components", "/api/v1/components/{}", "id",
    lambda it: is_smoke(it.get("name")),
)
# Eliminaciones explicitas de la fase 1.
for label, url in (
    ("workflow", f"/api/v1/workflows/{ids['slug']}" if ids.get("slug") else None),
    ("secret", f"/api/v1/secrets/{ids['secret_name']}" if ids.get("secret_name") else None),
    ("commit", f"/api/v1/commits/{ids['sha']}" if ids.get("sha") else None),
    ("mcp_session", f"/api/v1/mcp/sessions/{ids['session_id']}" if ids.get("session_id") else None),
    ("agent_skill", f"/api/v1/agent-skills/{ids['agent_skill_id']}" if ids.get("agent_skill_id") else None),
    ("conversation", f"/api/v1/chat/conversations/{ids['conversation_id']}" if ids.get("conversation_id") else None),
    ("mcp_server", f"/api/v1/mcp/servers/{ids['mcp_server_name']}" if ids.get("mcp_server_name") else None),
    ("data_quality_rule", f"/api/v1/data-quality/rules/{ids['dq_rule']}" if ids.get("dq_rule") else None),
    ("skill", f"/api/v1/skills/{ids['skill_id']}" if ids.get("skill_id") else None),
    ("registry_schema", f"/api/v1/registry/schemas/{ids['schema_name']}" if ids.get("schema_name") else None),
):
    if url:
        cleaned[label] = call("DELETE", url)["status"]

logout = call("POST", "/api/v1/auth/logout", {"refresh_token": REFRESH_TOKEN})
cleaned["auth_session"] = logout["status"]
if not logout["status"] or logout["status"] >= 400:
    cleanup_errors.append(
        f"ERROR: logout returned status {logout['status']} for smoke auth session"
    )

# Limpiar solo artefactos Redis asociados a IDs de issues o sesión de este run.
try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    report_keys = [
        f"dq:reports:{issue_id}"
        for issue_id in dict.fromkeys(created["issues"])
    ]
    cleaned["dq_reports"] = redis_client.delete(*report_keys) if report_keys else 0

    smoke_session_keys = []
    for session_key in redis_client.scan_iter(match="session:*"):
        raw_session = redis_client.get(session_key)
        if not raw_session:
            continue
        try:
            session = json.loads(raw_session)
        except json.JSONDecodeError as exc:
            cleanup_errors.append(
                f"ERROR: invalid JSON in auth session {session_key}: {exc}"
            )
            continue
        if isinstance(session, dict) and session.get("user_agent") == SMOKE:
            smoke_session_keys.append(session_key)

    cleaned["auth_sessions"] = (
        redis_client.delete(*smoke_session_keys) if smoke_session_keys else 0
    )
    remaining_reports = [key for key in report_keys if redis_client.exists(key)]
    if remaining_reports:
        cleanup_errors.append(
            f"ERROR: {len(remaining_reports)} smoke data-quality report(s) remain"
        )
    if any(
        isinstance((session := json.loads(raw)), dict)
        and session.get("user_agent") == SMOKE
        for key in redis_client.scan_iter(match="session:*")
        if (raw := redis_client.get(key))
    ):
        cleanup_errors.append("ERROR: smoke auth session remains in Redis")
except (redis.RedisError, OSError, ValueError) as exc:
    cleaned["redis"] = "ERROR"
    cleanup_errors.append(f"ERROR: Redis cleanup failed: {type(exc).__name__}")

if not DATABASE_URL:
    cleaned["auth_audit_logs"] = "ERROR"
    cleanup_errors.append("ERROR: TASKER_SMOKE_DATABASE_URL is required for audit-log cleanup")
else:
    try:
        with psycopg.connect(DATABASE_URL) as connection, connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM session_logs WHERE user_agent = %s",
                (SMOKE,),
            )
            cleaned["auth_audit_logs"] = cursor.rowcount
            cursor.execute(
                "SELECT count(*) FROM session_logs WHERE user_agent = %s",
                (SMOKE,),
            )
            if cursor.fetchone()[0]:
                cleanup_errors.append("ERROR: smoke auth audit log remains in PostgreSQL")
    except (psycopg.Error, OSError, ValueError) as exc:
        cleaned["auth_audit_logs"] = "ERROR"
        cleanup_errors.append(
            f"ERROR: PostgreSQL audit-log cleanup failed: {type(exc).__name__}"
        )

# --- reporte ----------------------------------------------------------------

counts = {}
for r in RESULTS:
    counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

print("\n=== RESUMEN ===")
print("total:", len(RESULTS), counts)
print("limpieza:", json.dumps(cleaned, default=str))

_out_dir = os.getenv(
    "TASKER_SMOKE_OUTPUT_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "artifacts", "smoke")),
)
os.makedirs(_out_dir, exist_ok=True)
_out = os.path.join(_out_dir, f"{SMOKE_L}-results.json")
with open(_out, "w", encoding="utf-8") as fh:
    json.dump({
        "run_id": SMOKE,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "api_base": BASE,
        "openapi_version": spec.get("openapi"),
        "openapi_path_count": len(spec.get("paths", {})),
        "operation_count": len(ops),
        "counts": counts,
        "cleanup": cleaned,
        "cleanup_errors": cleanup_errors,
        "results": RESULTS,
    }, fh, ensure_ascii=False, indent=2)
print("results ->", _out)

print("\n=== NO-PASS ===")
for r in RESULTS:
    if r["verdict"] not in ("PASS", "GRACE"):
        line = f'{r["verdict"]:8} {r["m"]:6} {r["p"]} -> {r["status"]} {r.get("note","")}'
        print(line)

print("\n=== 5xx (posibles bugs reales) ===")
for r in RESULTS:
    if r["status"] and r["status"] >= 500:
        print(f'{r["status"]} {r["m"]} {r["p"]}')

print("\n=== PASS por verbo ===")
byverb = {}
for r in RESULTS:
    byverb.setdefault(r["m"], {"PASS": 0, "GRACE": 0, "otro": 0})
    if r["verdict"] == "PASS":
        byverb[r["m"]]["PASS"] += 1
    elif r["verdict"] == "GRACE":
        byverb[r["m"]]["GRACE"] += 1
    else:
        byverb[r["m"]]["otro"] += 1
for v, c in sorted(byverb.items()):
    print(v, c)

if counts.get("ERR", 0) or counts.get("TIMEOUT", 0) or cleanup_errors:
    sys.exit(1)
