### Issue 323 — Add Deterministic API Contract Testing and Mock Server

**Descripción breve**  
Agregar un sistema determinista para **pruebas de contrato de API** (contract testing) y un **mock server** reproducible que permita validar compatibilidad entre consumidores y proveedores, generar mocks a partir de OpenAPI/JSON Schema, ejecutar pruebas de contrato en CI, y producir reportes y artefactos. Todo debe ser explícito: rutas, nombres de archivos, firmas de funciones, variables de entorno, comandos, tests, plantillas y cuerpo de PR listos para aplicar sin ambigüedades.

---

### Objetivos exactos
1. **Core de contract testing**: implementar un módulo `tools/contracts` que:
   - Compare respuestas reales del proveedor con contratos (OpenAPI/JSON Schema) de forma determinista.
   - Exponga `validate_response(schema: dict, response: dict) -> dict` que devuelve `{ok: bool, errors: list[str]}`.
   - Exporte `compare_contract(provider_url: str, contract_path: str, endpoints: list[str]) -> dict` que ejecuta validaciones y devuelve un resumen.
2. **Mock server**:
   - Añadir `tools/contracts/mock_server.py` que:
     - Carga un OpenAPI spec (YAML/JSON) y genera rutas mock deterministas (deterministic seed for example values).
     - Soporta overrides por ruta mediante `mocks/overrides/*.json`.
     - Expone CLI `mockctl.py` para `start`, `stop`, `status`, `list`.
3. **OpenAPI/Schema utilities**:
   - Añadir `tools/contracts/openapi.py` con helpers:
     - `load_spec(path: str) -> dict`
     - `extract_endpoints(spec: dict) -> list[dict]` (method, path, response_schema)
     - `generate_example(schema: dict, seed: int = 42) -> Any` (deterministic example generator).
4. **Test harness and CI**:
   - Añadir tests unitarios y de integración:
     - `tests/contracts/test_validate_unit.py`
     - `tests/contracts/test_mock_server_unit.py`
     - `tests/integration/test_contracts_integration.py` (marca `integration`) que arranca mock server y valida proveedor contra mock consumer expectations.
   - Añadir workflow `ci/contract-test.yml` que ejecuta contract tests on PR and on `push` to `main`.
5. **Reportes y artefactos**:
   - Contract runner debe escribir `contracts/report-<timestamp>.json` con resumen por endpoint: status, errors, response sample.
   - Añadir `tools/contracts/templates/report.j2` para generar HTML resumen opcional.
6. **Documentación**:
   - `tools/contracts/README.md` con instrucciones, ejemplos de uso, cómo añadir overrides y cómo integrar en CI.
7. **Wiring y uso local**:
   - Mock server debe poder arrancarse con `python tools/contracts/mockctl.py start --spec openapi.yaml --port 9000`.
   - Contract runner CLI `python tools/contracts/contractctl.py run --provider http://localhost:8000 --spec openapi.yaml --out reports/`.
8. **Branch y PR**:
   - Crear branch `feature/contract-testing-mock-server` y abrir PR con el PR body exacto provisto más abajo.

---

### Archivos a añadir o modificar (exactos)
- `tools/contracts/__init__.py` **(nuevo)**
- `tools/contracts/openapi.py` **(nuevo)**
- `tools/contracts/validator.py` **(nuevo)**
- `tools/contracts/mock_server.py` **(nuevo)**
- `tools/contracts/contractctl.py` **(nuevo, CLI)**
- `tools/contracts/mockctl.py` **(nuevo, CLI)**
- `tools/contracts/templates/report.j2` **(nuevo)**
- `tools/contracts/README.md` **(nuevo)**
- `tests/contracts/test_validate_unit.py` **(nuevo)**
- `tests/contracts/test_mock_server_unit.py` **(nuevo)**
- `tests/integration/test_contracts_integration.py` **(nuevo, integration)**
- `ci/contract-test.yml` **(nuevo)**

---

### Código exacto a añadir (fragmentos clave)

#### `tools/contracts/__init__.py`
```python
# tools/contracts/__init__.py
from .openapi import load_spec, extract_endpoints, generate_example
from .validator import validate_response, compare_contract
from .mock_server import MockServer

__all__ = ["load_spec", "extract_endpoints", "generate_example", "validate_response", "compare_contract", "MockServer"]
```

#### `tools/contracts/openapi.py`
```python
# tools/contracts/openapi.py
from __future__ import annotations
import json
import yaml
import hashlib
from typing import Dict, List, Any
import random

def load_spec(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as fh:
        txt = fh.read()
    try:
        return json.loads(txt)
    except Exception:
        return yaml.safe_load(txt)

def extract_endpoints(spec: Dict) -> List[Dict]:
    out = []
    paths = spec.get("paths", {})
    for p, methods in sorted(paths.items(), key=lambda x: x[0]):
        for m, info in sorted(methods.items(), key=lambda x: x[0]):
            responses = info.get("responses", {})
            # pick 200 or default first response
            resp_schema = None
            if "200" in responses:
                resp_schema = responses["200"].get("content", {}).get("application/json", {}).get("schema")
            else:
                for code in sorted(responses.keys()):
                    resp_schema = responses[code].get("content", {}).get("application/json", {}).get("schema")
                    if resp_schema:
                        break
            out.append({"method": m.upper(), "path": p, "operation": info.get("operationId"), "response_schema": resp_schema})
    return out

def _seed_from_path(path: str) -> int:
    h = hashlib.sha256(path.encode("utf-8")).hexdigest()
    return int(h[:8], 16)

def generate_example(schema: Dict, seed: int | None = None) -> Any:
    """
    Deterministic example generator for JSON Schema subset.
    """
    if schema is None:
        return {}
    s = seed or 42
    rnd = random.Random(s)
    t = schema.get("type")
    if t == "object":
        props = schema.get("properties", {})
        out = {}
        for k in sorted(props.keys()):
            out[k] = generate_example(props[k], seed=(s + int(hashlib.sha256(k.encode()).hexdigest()[:6], 16)))
        return out
    if t == "array":
        item = schema.get("items", {})
        return [generate_example(item, seed=s)]
    if t == "string":
        fmt = schema.get("format")
        if fmt == "date-time":
            return "2020-01-01T00:00:00Z"
        enum = schema.get("enum")
        if enum:
            return enum[0]
        return f"str-{rnd.randint(1,1000)}"
    if t == "integer":
        minimum = schema.get("minimum", 0)
        return int(minimum) + 1
    if t == "number":
        return float(schema.get("minimum", 0)) + 0.1
    if t == "boolean":
        return True
    return None
```

#### `tools/contracts/validator.py`
```python
# tools/contracts/validator.py
from __future__ import annotations
import json
import time
from typing import Dict, Any, List
from jsonschema import validate, ValidationError
import requests
from .openapi import load_spec, extract_endpoints, generate_example

def validate_response(schema: Dict, response: Dict) -> Dict:
    """
    Validate a JSON response against a JSON Schema.
    Returns dict: {"ok": bool, "errors": [str]}
    """
    if schema is None:
        return {"ok": True, "errors": []}
    try:
        validate(instance=response, schema=schema)
        return {"ok": True, "errors": []}
    except ValidationError as exc:
        return {"ok": False, "errors": [str(exc.message)]}

def compare_contract(provider_url: str, contract_path: str, endpoints: List[str] | None = None, timeout: int = 5) -> Dict:
    """
    For each endpoint in contract, perform a request to provider_url + path and validate response.
    endpoints: list of "METHOD path" strings to limit checks, e.g., ["GET /api/v1/health"]
    Returns summary dict with per-endpoint results and overall status.
    """
    spec = load_spec(contract_path)
    eps = extract_endpoints(spec)
    if endpoints:
        eps = [e for e in eps if f"{e['method']} {e['path']}" in endpoints]
    results = []
    for e in eps:
        url = provider_url.rstrip("/") + e["path"]
        method = e["method"].lower()
        # generate deterministic example request if needed (not for GET)
        try:
            r = getattr(requests, method)(url, timeout=timeout)
            try:
                body = r.json()
            except Exception:
                body = {}
            res = validate_response(e.get("response_schema"), body)
        except Exception as exc:
            res = {"ok": False, "errors": [str(exc)]}
        results.append({"method": e["method"], "path": e["path"], "ok": res["ok"], "errors": res["errors"]})
    overall = all(r["ok"] for r in results)
    report = {"provider": provider_url, "contract": contract_path, "timestamp": int(time.time()), "overall": overall, "results": results}
    return report
```

#### `tools/contracts/mock_server.py`
```python
# tools/contracts/mock_server.py
from __future__ import annotations
import threading
import uvicorn
from fastapi import FastAPI, Response
from typing import Dict, Any
import os, json
from .openapi import load_spec, extract_endpoints, generate_example

class MockServer:
    def __init__(self, spec_path: str, port: int = 9000, overrides_dir: str | None = None, seed: int = 42):
        self.spec_path = spec_path
        self.port = int(port)
        self.overrides_dir = overrides_dir
        self.seed = int(seed)
        self.app = FastAPI(title="Contract Mock Server")
        self._server_thread = None
        self._uvicorn_config = None
        self._setup_routes()

    def _load_override(self, method: str, path: str):
        if not self.overrides_dir:
            return None
        fname = f"{method}_{path.strip('/').replace('/','_')}.json"
        p = os.path.join(self.overrides_dir, fname)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as fh:
                return json.load(fh)
        return None

    def _setup_routes(self):
        spec = load_spec(self.spec_path)
        eps = extract_endpoints(spec)
        for e in eps:
            method = e["method"].lower()
            path = e["path"]
            schema = e.get("response_schema")
            example = generate_example(schema, seed=self.seed)
            override = self._load_override(e["method"], path)
            body = override if override is not None else example
            async def handler(response_body=body):
                return Response(content=json.dumps(response_body), media_type="application/json")
            # attach route
            self.app.add_api_route(path, handler, methods=[e["method"]])

    def start(self):
        if self._server_thread and self._server_thread.is_alive():
            return
        def run():
            uvicorn.run(self.app, host="0.0.0.0", port=self.port, log_level="warning")
        self._server_thread = threading.Thread(target=run, daemon=True)
        self._server_thread.start()

    def stop(self):
        # uvicorn server stop not trivial; rely on process termination in tests or CI
        pass
```

#### `tools/contracts/contractctl.py` (CLI)
```python
#!/usr/bin/env python3
# tools/contracts/contractctl.py
from __future__ import annotations
import argparse, os, json, time
from .validator import compare_contract
from .openapi import load_spec

def main(argv=None):
    p = argparse.ArgumentParser(prog="contractctl")
    sub = p.add_subparsers(dest="cmd")
    run = sub.add_parser("run")
    run.add_argument("--provider", required=True)
    run.add_argument("--spec", required=True)
    run.add_argument("--out", required=True)
    run.add_argument("--endpoints", nargs="*", default=[])
    args = p.parse_args(argv)
    if args.cmd == "run":
        report = compare_contract(args.provider, args.spec, endpoints=args.endpoints or None)
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print("wrote", args.out)
    else:
        p.print_help()

if __name__ == "__main__":
    main()
```

#### `tools/contracts/mockctl.py` (CLI)
```python
#!/usr/bin/env python3
# tools/contracts/mockctl.py
from __future__ import annotations
import argparse, os
from .mock_server import MockServer

def main(argv=None):
    p = argparse.ArgumentParser(prog="mockctl")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("start")
    s.add_argument("--spec", required=True)
    s.add_argument("--port", type=int, default=9000)
    s.add_argument("--overrides", default=None)
    s.add_argument("--seed", type=int, default=42)
    args = p.parse_args(argv)
    if args.cmd == "start":
        ms = MockServer(spec_path=args.spec, port=args.port, overrides_dir=args.overrides, seed=args.seed)
        ms.start()
        print(f"mock server started on port {args.port} (spec={args.spec})")
    else:
        p.print_help()

if __name__ == "__main__":
    main()
```

#### `tools/contracts/templates/report.j2`
```jinja
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Contract Report</title></head>
<body>
<h1>Contract Test Report</h1>
<p>Provider: {{ report.provider }}</p>
<p>Contract: {{ report.contract }}</p>
<p>Timestamp: {{ report.timestamp }}</p>
<h2>Summary: {{ "PASS" if report.overall else "FAIL" }}</h2>
{% for r in report.results %}
  <h3>{{ r.method }} {{ r.path }} — {{ "OK" if r.ok else "FAIL" }}</h3>
  {% if r.errors %}
    <ul>
    {% for e in r.errors %}
      <li>{{ e }}</li>
    {% endfor %}
    </ul>
  {% endif %}
{% endfor %}
</body>
</html>
```

---

### Tests exactos a añadir

#### `tests/contracts/test_validate_unit.py`
```python
# tests/contracts/test_validate_unit.py
from tools.contracts.validator import validate_response
def test_validate_simple_ok():
    schema = {"type":"object","properties":{"a":{"type":"integer"}}}
    resp = {"a": 1}
    r = validate_response(schema, resp)
    assert r["ok"]
def test_validate_simple_fail():
    schema = {"type":"object","properties":{"a":{"type":"integer"}}}
    resp = {"a": "x"}
    r = validate_response(schema, resp)
    assert not r["ok"]
```

#### `tests/contracts/test_mock_server_unit.py`
```python
# tests/contracts/test_mock_server_unit.py
import time
from tools.contracts.mock_server import MockServer
from tools.contracts.openapi import load_spec
def test_mock_server_start(tmp_path):
    # create minimal spec
    spec = {"openapi":"3.0.0","paths":{"/ping":{"get":{"responses":{"200":{"description":"ok","content":{"application/json":{"schema":{"type":"object","properties":{"pong":{"type":"string"}}}}}}}}}}}
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec))
    ms = MockServer(spec_path=str(p), port=9010, seed=123)
    ms.start()
    time.sleep(0.2)
    # call endpoint
    import requests
    r = requests.get("http://localhost:9010/ping", timeout=2)
    assert r.status_code == 200
    j = r.json()
    assert "pong" in j
```

#### `tests/integration/test_contracts_integration.py`
```python
# tests/integration/test_contracts_integration.py
import os, time, json, pytest, subprocess
pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")

def test_provider_against_mock(tmp_path):
    _skip_if_not_integration()
    # start mock server from spec tests/release/fixture-openapi.yaml (assumed present)
    spec = "tests/contracts/fixture-openapi.yaml"
    p = tmp_path / "report.json"
    # start mock server
    proc = subprocess.Popen(["python", "tools/contracts/mockctl.py", "start", "--spec", spec, "--port", "9100"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1)
    try:
        # run contract compare against mock provider
        out = subprocess.run(["python", "tools/contracts/contractctl.py", "run", "--provider", "http://localhost:9100", "--spec", spec, "--out", str(p)], check=True)
        rep = json.loads(p.read_text())
        assert rep["overall"] is True
    finally:
        proc.terminate()
```

---

### CI workflow `ci/contract-test.yml`
```yaml
name: Contract Tests
on:
  pull_request:
  push:
    branches: [ main ]
jobs:
  contract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install deps
        run: python -m pip install jsonschema requests pyyaml uvicorn fastapi
      - name: Run unit tests
        run: pytest tests/contracts -q
```

---

### Documentación exacta a añadir

#### `tools/contracts/README.md`
```
Contract Testing and Mock Server

Quickstart
- Start mock server:
  python tools/contracts/mockctl.py start --spec openapi.yaml --port 9000 --overrides mocks/overrides --seed 42

- Run contract tests against provider:
  python tools/contracts/contractctl.py run --provider http://localhost:8000 --spec openapi.yaml --out reports/report.json

Overrides
- Place JSON files in mocks/overrides named METHOD_path_to_route.json, e.g., GET_api_v1_items.json

CI
- Use ci/contract-test.yml to run unit tests on PRs.

Determinism
- Example generation uses deterministic seed; mock responses are stable across runs when seed and spec are unchanged.
```

---

### Comandos exactos que el agente debe ejecutar
```bash
git checkout -b feature/contract-testing-mock-server
# create files as specified
python -m pip install -e .
python -m pip install jsonschema requests pyyaml uvicorn fastapi
# run unit tests
pytest tests/contracts/test_validate_unit.py -q
pytest tests/contracts/test_mock_server_unit.py -q
# optional integration test (requires TASKER_INTEGRATION=1)
export TASKER_INTEGRATION=1
pytest tests/integration/test_contracts_integration.py -q -m integration || true
# commit and push
git add tools/contracts tests/contracts tests/integration ci/contract-test.yml
git commit -m "feat(contract): add deterministic API contract testing and mock server with CLI and CI"
git push origin feature/contract-testing-mock-server
```

---

### PR body exacto a pegar
```
Summary:
- Added deterministic API contract testing utilities and a mock server under tools/contracts.
- Implemented OpenAPI helpers, deterministic example generator, response validator and contract comparator.
- Added MockServer that generates deterministic mock responses from OpenAPI specs and supports overrides.
- Added CLIs contractctl.py and mockctl.py, templates for HTML reports and README.
- Added unit and integration tests and CI workflow ci/contract-test.yml.

Verification steps executed:
1. Installed package in editable mode and required dependencies.
2. Ran unit tests for validator and mock server.
3. Optionally ran integration test that starts mock server and validates contract.

Files changed:
- tools/contracts/*
- tests/contracts/*
- tests/integration/test_contracts_integration.py
- ci/contract-test.yml

Notes:
- Mock server uses deterministic seed to produce stable example responses.
- Use overrides for custom mock payloads per route.
```

---

### Criterios de aceptación
- `tools/contracts` existe con `openapi.py`, `validator.py`, `mock_server.py`, `contractctl.py`, `mockctl.py` y plantillas.
- `validate_response` y `compare_contract` funcionan y devuelven reportes JSON con per-endpoint results.
- `MockServer` can start and serve deterministic mock responses from an OpenAPI spec and supports overrides.
- Unit tests exist and pass; integration test runs when `TASKER_INTEGRATION=1`.
- CI workflow `ci/contract-test.yml` exists and runs contract unit tests on PRs.
- Branch `feature/contract-testing-mock-server` created and PR opened with the PR body above.

---

### Labels to apply on GitHub
- `testing`
- `contracts`
- `mock-server`
- `ci`
- `small-priority`

---

### Estimated effort
**Small–Medium (S–M)** — expected **1–3 hours** depending on existing OpenAPI fixtures and CI access.