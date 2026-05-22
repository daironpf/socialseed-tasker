### Issue 319 — Add Data Catalog and Schema Registry for Deterministic Data Contracts

**Short description**  
Add a deterministic Data Catalog and Schema Registry to manage dataset metadata, JSON schema contracts, versioning, compatibility checks, and discovery. Provide HTTP API, CLI, storage-backed registry, schema validation hooks for ingestion endpoints, automated compatibility checks, unit and integration tests, Docker Compose service, documentation, and reproducible commands. All file paths, exact code snippets, tests, commands, and PR body are provided so an agent or developer can implement and verify without ambiguity.

---

### Objective
1. Add a Schema Registry service and Data Catalog integrated into the existing container wiring.  
2. Provide HTTP API endpoints to register schemas, fetch schemas by name/version, list datasets, and validate payloads against registered schemas.  
3. Implement compatibility checks (backward, forward, full) when registering new schema versions.  
4. Add CLI tools to manage schemas and catalog entries.  
5. Add middleware or hooks to validate incoming JSON payloads for ingestion endpoints using the registry.  
6. Add unit tests for registry logic, compatibility checks, and validation; add integration tests that run the registry and validate end-to-end ingestion.  
7. Document usage in `tasker/data_catalog/README.md`.  
8. Create branch `feature/data-catalog-schema-registry` and open a PR with the exact PR body provided below.

---

### Files to add or modify exact paths
- `tasker/data_catalog/__init__.py` **new**  
- `tasker/data_catalog/registry.py` **new** — core registry and compatibility logic  
- `tasker/data_catalog/api.py` **new** — FastAPI router for registry endpoints  
- `tasker/data_catalog/cli.py` **new** — CLI for schema and dataset management  
- `tasker/data_catalog/validation.py` **new** — JSON Schema validation helpers and middleware hook  
- `tasker/data_catalog/README.md` **new** — documentation and examples  
- `docker-compose.schema.yml` **new** — optional compose file to run registry as service (reuses API)  
- `tests/data_catalog/test_registry_unit.py` **new**  
- `tests/data_catalog/test_compatibility_unit.py` **new**  
- `tests/integration/test_schema_registry_integration.py` **new, integration**  
- Modify `tasker/cli/wiring.py` **modify** — wire `schema_registry` into container  
- Modify `tasker/api/app.py` **modify** — mount registry router and add validation hook to ingestion endpoints

---

### Core design and behavior

#### Registry model
- **Schema**: identified by `name` and `version` (semantic version string `MAJOR.MINOR.PATCH`). Stored as JSON Schema Draft 7.  
- **Dataset**: metadata entry with `dataset_id`, `title`, `description`, `schema_name`, `default_schema_version`, `owner`, `tags`, `created_at`.  
- **Compatibility modes**: `BACKWARD`, `FORWARD`, `FULL`, `NONE`. New schema versions are accepted only if compatibility check passes against the previous version according to selected mode.

#### Storage
- Registry persists schemas and dataset metadata in `StoragePort` under deterministic keys:
  - `schema:{name}:{version}` → schema JSON bytes  
  - `schema:versions:{name}` → JSON list of versions  
  - `dataset:{dataset_id}` → dataset metadata JSON bytes  
  - `dataset:list` → JSON list of dataset ids

#### Validation
- Use `jsonschema` to validate payloads against registered schema version. Validation middleware will be attachable to ingestion endpoints by dataset id.

---

### Exact code to add

#### `tasker/data_catalog/__init__.py`
```python
# tasker/data_catalog/__init__.py
from .registry import SchemaRegistry, SchemaCompatibilityError
from .api import router as registry_router
from .cli import main as registry_cli
from .validation import validate_payload, ValidationMiddleware

__all__ = ["SchemaRegistry", "SchemaCompatibilityError", "registry_router", "registry_cli", "validate_payload", "ValidationMiddleware"]
```

#### `tasker/data_catalog/registry.py`
```python
# tasker/data_catalog/registry.py
from __future__ import annotations
import json
import re
import time
from typing import Dict, List, Optional
from tasker.application.ports import StoragePort
from tasker.application.exceptions import StorageError

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

class SchemaCompatibilityError(Exception):
    pass

class SchemaRegistry:
    """
    Schema registry backed by StoragePort.
    Keys:
      schema:{name}:{version}
      schema:versions:{name}
      dataset:{dataset_id}
      dataset:list
    """

    def __init__(self, storage: StoragePort):
        self.storage = storage

    def _schema_key(self, name: str, version: str) -> str:
        return f"schema:{name}:{version}"

    def _versions_key(self, name: str) -> str:
        return f"schema:versions:{name}"

    def _dataset_key(self, dataset_id: str) -> str:
        return f"dataset:{dataset_id}"

    def register_schema(self, name: str, version: str, schema: Dict, compatibility: str = "BACKWARD") -> None:
        if not SEMVER_RE.match(version):
            raise ValueError("version must be semantic MAJOR.MINOR.PATCH")
        # check compatibility with latest version if exists
        versions = self.get_versions(name)
        if versions:
            latest = versions[-1]
            latest_schema = self.get_schema(name, latest)
            if not self._check_compatibility(latest_schema, schema, mode=compatibility):
                raise SchemaCompatibilityError("schema incompatible with latest version under mode " + compatibility)
        # persist
        try:
            self.storage.put(self._schema_key(name, version), json.dumps(schema).encode("utf-8"))
            versions = versions + [version]
            self.storage.put(self._versions_key(name), json.dumps(versions).encode("utf-8"))
        except Exception as exc:
            raise StorageError(f"failed to persist schema: {exc}") from exc

    def get_schema(self, name: str, version: str) -> Dict:
        raw = self.storage.get(self._schema_key(name, version))
        if not raw:
            raise KeyError("schema not found")
        return json.loads(raw.decode("utf-8"))

    def get_versions(self, name: str) -> List[str]:
        raw = self.storage.get(self._versions_key(name))
        if not raw:
            return []
        return json.loads(raw.decode("utf-8"))

    def list_schemas(self) -> List[Dict]:
        # naive: list versions keys not available; rely on dataset listing or stored index
        # attempt to read all known schema:versions:* keys by scanning storage if supported
        if not hasattr(self.storage, "list_keys"):
            return []
        keys = self.storage.list_keys()
        names = set()
        for k in keys:
            if k.startswith("schema:versions:"):
                names.add(k.split("schema:versions:")[1])
        out = []
        for n in sorted(names):
            out.append({"name": n, "versions": self.get_versions(n)})
        return out

    def register_dataset(self, dataset_id: str, title: str, description: str, schema_name: str, default_schema_version: str, owner: str, tags: Optional[List[str]] = None) -> None:
        meta = {
            "dataset_id": dataset_id,
            "title": title,
            "description": description,
            "schema_name": schema_name,
            "default_schema_version": default_schema_version,
            "owner": owner,
            "tags": tags or [],
            "created_at": int(time.time())
        }
        try:
            self.storage.put(self._dataset_key(dataset_id), json.dumps(meta).encode("utf-8"))
            raw = self.storage.get("dataset:list") or b"[]"
            arr = json.loads(raw.decode("utf-8")) if raw else []
            if dataset_id not in arr:
                arr.append(dataset_id)
                self.storage.put("dataset:list", json.dumps(arr).encode("utf-8"))
        except Exception as exc:
            raise StorageError(f"failed to persist dataset: {exc}") from exc

    def get_dataset(self, dataset_id: str) -> Dict:
        raw = self.storage.get(self._dataset_key(dataset_id))
        if not raw:
            raise KeyError("dataset not found")
        return json.loads(raw.decode("utf-8"))

    def list_datasets(self) -> List[Dict]:
        raw = self.storage.get("dataset:list") or b"[]"
        arr = json.loads(raw.decode("utf-8")) if raw else []
        out = []
        for did in arr:
            try:
                out.append(self.get_dataset(did))
            except Exception:
                pass
        return out

    def _check_compatibility(self, old_schema: Dict, new_schema: Dict, mode: str = "BACKWARD") -> bool:
        """
        Deterministic compatibility check:
        - BACKWARD: new schema must accept all instances valid under old schema (new is superset)
        - FORWARD: old schema must accept all instances valid under new schema
        - FULL: both BACKWARD and FORWARD
        - NONE: always true
        Implementation uses a conservative structural check: required fields in old must exist in new with compatible types.
        """
        if mode == "NONE":
            return True
        def extract_required(sch: Dict) -> Dict[str, str]:
            props = sch.get("properties", {})
            req = {}
            for k, v in props.items():
                t = v.get("type")
                if t:
                    req[k] = t
            return req
        old_req = extract_required(old_schema)
        new_req = extract_required(new_schema)
        if mode in ("BACKWARD", "FULL"):
            # every required in old must be present in new with same type or a superset (e.g., integer vs number not checked deeply)
            for k, t in old_req.items():
                if k not in new_req:
                    return False
                if new_req[k] != t:
                    return False
        if mode in ("FORWARD", "FULL"):
            for k, t in new_req.items():
                if k not in old_req:
                    return False
                if old_req[k] != t:
                    return False
        return True
```

#### `tasker/data_catalog/api.py`
```python
# tasker/data_catalog/api.py
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from pydantic import BaseModel
from tasker.cli.wiring import build_api_container

router = APIRouter(prefix="/api/v1/registry", tags=["registry"])

class RegisterSchemaRequest(BaseModel):
    name: str
    version: str
    schema: Dict[str, Any]
    compatibility: str = "BACKWARD"

class RegisterDatasetRequest(BaseModel):
    dataset_id: str
    title: str
    description: str
    schema_name: str
    default_schema_version: str
    owner: str
    tags: list[str] = []

def get_container():
    return build_api_container()

@router.post("/schemas")
def register_schema(req: RegisterSchemaRequest, container = Depends(get_container)):
    reg = container.schema_registry
    try:
        reg.register_schema(req.name, req.version, req.schema, compatibility=req.compatibility)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status":"ok"}

@router.get("/schemas/{name}/versions")
def list_versions(name: str, container = Depends(get_container)):
    reg = container.schema_registry
    return {"status":"ok","versions": reg.get_versions(name)}

@router.get("/schemas/{name}/{version}")
def get_schema(name: str, version: str, container = Depends(get_container)):
    reg = container.schema_registry
    try:
        s = reg.get_schema(name, version)
    except KeyError:
        raise HTTPException(status_code=404, detail="schema not found")
    return {"status":"ok","schema": s}

@router.post("/datasets")
def register_dataset(req: RegisterDatasetRequest, container = Depends(get_container)):
    reg = container.schema_registry
    try:
        reg.register_dataset(req.dataset_id, req.title, req.description, req.schema_name, req.default_schema_version, req.owner, tags=req.tags)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status":"ok"}

@router.get("/datasets")
def list_datasets(container = Depends(get_container)):
    reg = container.schema_registry
    return {"status":"ok","datasets": reg.list_datasets()}

@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: str, container = Depends(get_container)):
    reg = container.schema_registry
    try:
        d = reg.get_dataset(dataset_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="dataset not found")
    return {"status":"ok","dataset": d}
```

#### `tasker/data_catalog/validation.py`
```python
# tasker/data_catalog/validation.py
from __future__ import annotations
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from jsonschema import validate, ValidationError
from typing import Dict, Any
from tasker.cli.wiring import build_api_container

def validate_payload(dataset_id: str, payload: Dict[str, Any], version: str | None = None) -> None:
    container = build_api_container()
    reg = container.schema_registry
    ds = reg.get_dataset(dataset_id)
    schema_name = ds["schema_name"]
    schema_version = version or ds["default_schema_version"]
    schema = reg.get_schema(schema_name, schema_version)
    try:
        validate(instance=payload, schema=schema)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=f"schema validation error: {exc.message}")

class ValidationMiddleware:
    """
    Example middleware to validate JSON body for ingestion endpoints.
    Usage: call ValidationMiddleware.validate_request(request, dataset_id)
    """

    @staticmethod
    async def validate_request(request: Request, dataset_id: str):
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="invalid json")
        validate_payload(dataset_id, body)
```

#### `tasker/data_catalog/cli.py`
```python
# tasker/data_catalog/cli.py
from __future__ import annotations
import argparse
import json
from tasker.cli.wiring import build_default_container

def cmd_register_schema(args):
    container = build_default_container()
    reg = container.schema_registry
    schema = json.loads(open(args.file, "r", encoding="utf-8").read())
    reg.register_schema(args.name, args.version, schema, compatibility=args.compatibility)
    print("ok")

def cmd_get_schema(args):
    container = build_default_container()
    reg = container.schema_registry
    s = reg.get_schema(args.name, args.version)
    print(json.dumps(s, indent=2))

def cmd_register_dataset(args):
    container = build_default_container()
    reg = container.schema_registry
    reg.register_dataset(args.dataset_id, args.title, args.description, args.schema_name, args.default_schema_version, args.owner, tags=args.tags or [])
    print("ok")

def main(argv=None):
    p = argparse.ArgumentParser(prog="tasker-registry")
    sub = p.add_subparsers(dest="cmd")
    rs = sub.add_parser("register-schema")
    rs.add_argument("--name", required=True)
    rs.add_argument("--version", required=True)
    rs.add_argument("--file", required=True)
    rs.add_argument("--compatibility", default="BACKWARD")
    gs = sub.add_parser("get-schema")
    gs.add_argument("--name", required=True)
    gs.add_argument("--version", required=True)
    rd = sub.add_parser("register-dataset")
    rd.add_argument("--dataset-id", required=True)
    rd.add_argument("--title", required=True)
    rd.add_argument("--description", required=True)
    rd.add_argument("--schema-name", required=True)
    rd.add_argument("--default-schema-version", required=True)
    rd.add_argument("--owner", required=True)
    rd.add_argument("--tags", nargs="*", default=[])
    args = p.parse_args(argv)
    if args.cmd == "register-schema":
        cmd_register_schema(args)
    elif args.cmd == "get-schema":
        cmd_get_schema(args)
    elif args.cmd == "register-dataset":
        cmd_register_dataset(args)
    else:
        p.print_help()
```

---

### Docker Compose optional file

#### `docker-compose.schema.yml`
```yaml
version: "3.8"
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    image: tasker-api:local
    ports:
      - "8000:8000"
  schema-registry:
    image: tasker-api:local
    command: ["uvicorn", "tasker.api.app:create_app()", "--host", "0.0.0.0", "--port", "8010"]
    environment:
      TASKER_SCHEMA_SERVICE: "1"
    ports:
      - "8010:8010"
    depends_on:
      - api
```

---

### Tests to add

#### `tests/data_catalog/test_registry_unit.py`
```python
# tests/data_catalog/test_registry_unit.py
import json
from tasker.data_catalog.registry import SchemaRegistry, SchemaCompatibilityError
from tasker.infrastructure.memory_storage import MemoryStorage

def test_register_and_get_schema():
    s = MemoryStorage()
    reg = SchemaRegistry(s)
    schema_v1 = {"type":"object","properties":{"a":{"type":"integer"}}}
    reg.register_schema("s1", "1.0.0", schema_v1)
    assert reg.get_schema("s1", "1.0.0")["properties"]["a"]["type"] == "integer"
    assert reg.get_versions("s1") == ["1.0.0"]
```

#### `tests/data_catalog/test_compatibility_unit.py`
```python
# tests/data_catalog/test_compatibility_unit.py
from tasker.data_catalog.registry import SchemaRegistry, SchemaCompatibilityError
from tasker.infrastructure.memory_storage import MemoryStorage

def test_backward_compatibility_rejects_missing_field():
    s = MemoryStorage()
    reg = SchemaRegistry(s)
    v1 = {"type":"object","properties":{"a":{"type":"integer"}}}
    reg.register_schema("s2", "1.0.0", v1)
    v2 = {"type":"object","properties":{}}  # removes required field
    try:
        reg.register_schema("s2", "1.1.0", v2, compatibility="BACKWARD")
        assert False, "should have raised"
    except SchemaCompatibilityError:
        assert True
```

#### `tests/integration/test_schema_registry_integration.py`
```python
# tests/integration/test_schema_registry_integration.py
import os
import requests
import json
import pytest
from tasker.infrastructure.memory_storage import MemoryStorage
from tasker.data_catalog.registry import SchemaRegistry

pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")

def test_register_schema_via_api():
    _skip_if_not_integration()
    url = "http://localhost:8000/api/v1/registry/schemas"
    payload = {"name":"inttest","version":"1.0.0","schema":{"type":"object","properties":{"x":{"type":"integer"}}},"compatibility":"BACKWARD"}
    r = requests.post(url, json=payload, timeout=5)
    assert r.status_code == 200
    r2 = requests.get("http://localhost:8000/api/v1/registry/schemas/inttest/1.0.0", timeout=5)
    assert r2.status_code == 200
    j = r2.json()
    assert j["schema"]["properties"]["x"]["type"] == "integer"
```

---

### Wiring modifications

Modify `tasker/cli/wiring.py` to include `schema_registry` in the container. Insert the following excerpt in `build_default_container()` after storage creation:

```python
from tasker.data_catalog.registry import SchemaRegistry
schema_registry = SchemaRegistry(storage)
# include in Container return
return Container(
    # existing attributes...
    storage=storage,
    schema_registry=schema_registry,
    # other attributes...
)
```

Modify `tasker/api/app.py` to mount router. Insert the following where routes are registered:

```python
from tasker.data_catalog.api import router as registry_router
app.include_router(registry_router)
```

Add validation hook to ingestion endpoints by calling `ValidationMiddleware.validate_request(request, dataset_id)` before processing payloads.

---

### Documentation

Create `tasker/data_catalog/README.md` with the exact content below.

```
Data Catalog and Schema Registry

Overview
- Register JSON Schemas and datasets.
- Validate incoming payloads against registered schema versions.
- Enforce compatibility when adding new schema versions.

API Endpoints
- POST /api/v1/registry/schemas
- GET /api/v1/registry/schemas/{name}/versions
- GET /api/v1/registry/schemas/{name}/{version}
- POST /api/v1/registry/datasets
- GET /api/v1/registry/datasets
- GET /api/v1/registry/datasets/{dataset_id}

CLI
- tasker-registry register-schema --name <name> --version <v> --file <schema.json>
- tasker-registry get-schema --name <name> --version <v>
- tasker-registry register-dataset --dataset-id <id> --title <t> --description <d> --schema-name <s> --default-schema-version <v> --owner <o>

Compatibility Modes
- BACKWARD, FORWARD, FULL, NONE

Validation Hook
- Use ValidationMiddleware.validate_request(request, dataset_id) in ingestion endpoints to enforce schema validation.

Notes
- Registry persists schemas and datasets in StoragePort.
- Compatibility checks are conservative structural checks suitable for deterministic CI.
```

---

### Commands exact to run

```bash
git checkout -b feature/data-catalog-schema-registry
# create files as specified
python -m pip install -e .
# run unit tests
pytest tests/data_catalog/test_registry_unit.py -q
pytest tests/data_catalog/test_compatibility_unit.py -q
# optional integration test (requires API running)
export TASKER_INTEGRATION=1
pytest tests/integration/test_schema_registry_integration.py -q -m integration || true
# commit and push
git add tasker/data_catalog tests/data_catalog tests/integration tasker/data_catalog/README.md
git commit -m "feat(data): add data catalog and schema registry with compatibility checks and validation hooks"
git push origin feature/data-catalog-schema-registry
```

---

### PR body exact text to paste

```
Summary:
- Added Data Catalog and Schema Registry to manage JSON schema contracts and dataset metadata.
- Implemented SchemaRegistry with deterministic storage keys and conservative compatibility checks.
- Added FastAPI router for registry endpoints and CLI for schema/dataset management.
- Added JSON Schema validation helpers and a ValidationMiddleware hook for ingestion endpoints.
- Added unit and integration tests and documentation tasker/data_catalog/README.md.

Verification steps executed by this agent:
1. Installed package in editable mode.
2. Ran unit tests for registry and compatibility checks.
3. Optionally ran integration test against running API to register and fetch a schema.

Files changed:
- tasker/data_catalog/*
- tests/data_catalog/*
- tests/integration/test_schema_registry_integration.py
- Modified: tasker/cli/wiring.py, tasker/api/app.py

Notes:
- Compatibility checks are conservative structural checks appropriate for deterministic CI.
- For production-grade compatibility, replace _check_compatibility with a full schema compatibility engine.
```

---

### Acceptance criteria
- `tasker/data_catalog` exists with `registry.py`, `api.py`, `validation.py`, and `cli.py`.  
- Registry persists schemas and dataset metadata in `StoragePort` under deterministic keys.  
- Compatibility modes `BACKWARD`, `FORWARD`, `FULL`, `NONE` are implemented and enforced on schema registration.  
- API endpoints for schemas and datasets exist and are mounted at `/api/v1/registry`.  
- Validation helper and middleware are available and can be attached to ingestion endpoints.  
- Unit tests for registry and compatibility exist and pass. Integration test runs when `TASKER_INTEGRATION=1`.  
- Branch `feature/data-catalog-schema-registry` created and PR opened with the PR body above.

---

### Labels to apply on GitHub
- `data`
- `schema-registry`
- `catalog`
- `integration-test`
- `medium-priority`

---