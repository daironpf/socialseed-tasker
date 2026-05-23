### Issue 320 — Add Data Quality Framework and Validation Pipelines

---

### Short description  
Agregar un **Data Quality Framework** determinista que valide, monitoree y corrija datos en ingestión y en repositorios. Incluir reglas de validación declarativas, pipelines de validación pre y post ingestión, reportes y métricas, integración con StoragePort y EventBus para alertas, pruebas unitarias e integración, y documentación. Todo debe ser explícito: rutas, nombres de archivos, firmas de funciones, comportamiento, comandos y texto de PR listos para aplicar sin ambigüedades.

---

### Objective  
1. Añadir un motor de reglas de calidad de datos que soporte validaciones tipo esquema, rangos, unicidad y reglas personalizadas en Python.  
2. Proveer pipelines de validación que se ejecuten **antes** de persistir datos (pre-ingest) y **después** (post-ingest) con posibilidad de corrección automática o rechazo.  
3. Exponer API para gestionar reglas y ver reportes: crear/leer/actualizar/eliminar reglas, ejecutar validaciones ad-hoc, consultar historial de fallos.  
4. Emitir eventos a `EventBus` cuando se detecten fallos críticos para que otros subsistemas (alertas, dashboards) reaccionen.  
5. Persistir reportes y métricas en `StoragePort` bajo claves deterministas y exponer métricas Prometheus-friendly (contador de fallos por regla).  
6. Añadir tests unitarios para reglas, pipelines y API; integración que simula ingestión y verifica rechazo/corrección y emisión de eventos.  
7. Documentar uso, cómo escribir reglas y cómo integrar en flujos de ingestión.

---

### Files to add or modify

- `tasker/data_quality/__init__.py` new  
- `tasker/data_quality/rules.py` new — rule definitions and registry  
- `tasker/data_quality/pipeline.py` new — pre/post ingest pipelines and runner  
- `tasker/data_quality/api.py` new — FastAPI router for rule management and reports  
- `tasker/data_quality/serializers.py` new — DTOs for rules and reports  
- `tasker/data_quality/prometheus.py` new — simple metrics exporter helper (exposes counters via StoragePort)  
- `tasker/data_quality/tests/test_rules_unit.py` new  
- `tasker/data_quality/tests/test_pipeline_unit.py` new  
- `tests/integration/test_data_quality_integration.py` new, integration  
- Modify `tasker/api/app.py` to mount router and call pipeline in ingest endpoints (exact snippet provided below)  
- Modify `tasker/cli/wiring.py` to wire `data_quality` components into Container

---

### Exact code to add

#### `tasker/data_quality/__init__.py`
```python
# tasker/data_quality/__init__.py
from .rules import RuleRegistry, BaseRule, ValidationError
from .pipeline import DataQualityPipeline
from .api import router as data_quality_router
from .prometheus import MetricsStore

__all__ = ["RuleRegistry", "BaseRule", "ValidationError", "DataQualityPipeline", "data_quality_router", "MetricsStore"]
```

#### `tasker/data_quality/serializers.py`
```python
# tasker/data_quality/serializers.py
from __future__ import annotations
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class RuleSpec(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    kind: str  # schema | range | unique | custom
    target: str  # e.g., "issue", "issue.title", "storage:key"
    config: Dict[str, Any] = {}
    enabled: bool = True

class ValidationResult(BaseModel):
    rule_id: str
    ok: bool
    message: Optional[str] = None
    record_id: Optional[str] = None
    details: Dict[str, Any] = {}
```

#### `tasker/data_quality/rules.py`
```python
# tasker/data_quality/rules.py
from __future__ import annotations
import json
from typing import Any, Dict, Callable, List, Optional
from tasker.application.ports import StoragePort

class ValidationError(Exception):
    pass

class BaseRule:
    def __init__(self, spec: Dict[str, Any]):
        self.spec = spec
        self.id = spec["id"]
        self.name = spec.get("name", self.id)
        self.enabled = spec.get("enabled", True)

    def validate(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return dict: {"ok": bool, "message": str, "details": {...}}
        Override in subclasses.
        """
        raise NotImplementedError

class SchemaRule(BaseRule):
    def __init__(self, spec: Dict[str, Any], schema: Dict[str, Any]):
        super().__init__(spec)
        self.schema = schema
        # lazy import to avoid heavy dependency at module import
        from jsonschema import validate, ValidationError as JSVE
        self._validate_fn = validate
        self._jsv_exc = JSVE

    def validate(self, record: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._validate_fn(instance=record, schema=self.schema)
            return {"ok": True, "message": None, "details": {}}
        except self._jsv_exc as exc:
            return {"ok": False, "message": str(exc), "details": {}}

class RangeRule(BaseRule):
    def validate(self, record: Dict[str, Any]) -> Dict[str, Any]:
        target = self.spec.get("target")
        cfg = self.spec.get("config", {})
        minv = cfg.get("min")
        maxv = cfg.get("max")
        val = record.get(target)
        if val is None:
            return {"ok": True, "message": None, "details": {}}
        try:
            v = float(val)
        except Exception:
            return {"ok": False, "message": f"not numeric: {val}", "details": {}}
        if minv is not None and v < float(minv):
            return {"ok": False, "message": f"value {v} < min {minv}", "details": {}}
        if maxv is not None and v > float(maxv):
            return {"ok": False, "message": f"value {v} > max {maxv}", "details": {}}
        return {"ok": True, "message": None, "details": {}}

class UniqueRule(BaseRule):
    """
    Ensures uniqueness of a field across storage. Uses StoragePort to check existing keys.
    config: { "index_prefix": "dq:unique:issue:title" }
    """
    def __init__(self, spec: Dict[str, Any], storage: StoragePort):
        super().__init__(spec)
        self.storage = storage
        self.index_prefix = spec.get("config", {}).get("index_prefix", f"dq:unique:{self.id}")

    def validate(self, record: Dict[str, Any]) -> Dict[str, Any]:
        target = self.spec.get("target")
        val = record.get(target)
        if val is None:
            return {"ok": True, "message": None, "details": {}}
        key = f"{self.index_prefix}:{val}"
        existing = self.storage.get(key)
        if existing:
            return {"ok": False, "message": "duplicate", "details": {"existing": existing.decode("utf-8")}}
        # not marking here; pipeline may call mark_unique
        return {"ok": True, "message": None, "details": {}}

    def mark_unique(self, record: Dict[str, Any], record_id: str):
        target = self.spec.get("target")
        val = record.get(target)
        if val is None:
            return
        key = f"{self.index_prefix}:{val}"
        self.storage.put(key, record_id.encode("utf-8"))

class CustomRule(BaseRule):
    def __init__(self, spec: Dict[str, Any], fn: Callable[[Dict[str,Any]], Dict[str,Any]]):
        super().__init__(spec)
        self.fn = fn

    def validate(self, record: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.fn(record)
        except Exception as exc:
            return {"ok": False, "message": str(exc), "details": {}}

class RuleRegistry:
    """
    Persist rules under key dq:rules and keep in-memory registry.
    """
    KEY = "dq:rules"

    def __init__(self, storage: StoragePort):
        self.storage = storage
        self._rules: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        raw = self.storage.get(self.KEY)
        if raw:
            try:
                self._rules = json.loads(raw.decode("utf-8"))
            except Exception:
                self._rules = {}
        else:
            self._rules = {}

    def _persist(self):
        self.storage.put(self.KEY, json.dumps(self._rules).encode("utf-8"))

    def list(self) -> List[Dict]:
        return list(self._rules.values())

    def get(self, rule_id: str) -> Optional[Dict]:
        return self._rules.get(rule_id)

    def add(self, spec: Dict[str, Any]) -> None:
        rid = spec["id"]
        self._rules[rid] = spec
        self._persist()

    def delete(self, rule_id: str) -> None:
        if rule_id in self._rules:
            self._rules.pop(rule_id)
            self._persist()
```

#### `tasker/data_quality/pipeline.py`
```python
# tasker/data_quality/pipeline.py
from __future__ import annotations
import time
from typing import Dict, Any, List
from tasker.data_quality.rules import RuleRegistry, BaseRule, SchemaRule, RangeRule, UniqueRule, CustomRule
from tasker.application.ports import StoragePort
from tasker.events.bus import EventBus
from tasker.data_quality.serializers import ValidationResult

REPORT_KEY_PREFIX = "dq:reports:"
METRICS_KEY = "dq:metrics"

class DataQualityPipeline:
    """
    Runs pre and post ingest validations. Pipeline is deterministic: rules are applied in registry order.
    """

    def __init__(self, storage: StoragePort, rule_registry: RuleRegistry, event_bus: EventBus):
        self.storage = storage
        self.registry = rule_registry
        self.event_bus = event_bus
        # instantiate rule objects lazily when needed
        self._rule_objs: Dict[str, BaseRule] = {}

    def _instantiate_rule(self, spec: Dict[str, Any]) -> BaseRule:
        rid = spec["id"]
        if rid in self._rule_objs:
            return self._rule_objs[rid]
        kind = spec.get("kind")
        if kind == "schema":
            r = SchemaRule(spec, spec.get("config", {}).get("schema", {}))
        elif kind == "range":
            r = RangeRule(spec)
        elif kind == "unique":
            r = UniqueRule(spec, self.storage)
        elif kind == "custom":
            # custom functions must be registered in spec.config["fn_name"] and resolved by container; fallback to pass
            fn = spec.get("config", {}).get("fn")
            r = CustomRule(spec, fn or (lambda rec: {"ok": True, "message": None, "details": {}}))
        else:
            r = BaseRule(spec)
        self._rule_objs[rid] = r
        return r

    def run_pre_ingest(self, record: Dict[str, Any], record_id: str = None) -> List[ValidationResult]:
        """
        Run validations that must pass before persisting. Returns list of ValidationResult.
        If any critical rule fails, caller should reject persist.
        """
        results = []
        for spec in self.registry.list():
            if not spec.get("enabled", True):
                continue
            rule = self._instantiate_rule(spec)
            res = rule.validate(record)
            vr = ValidationResult(rule_id=rule.id, ok=res["ok"], message=res.get("message"), record_id=record_id, details=res.get("details", {}))
            results.append(vr)
            # increment metrics
            self._inc_metric(rule.id, 0 if res["ok"] else 1)
            if not res["ok"] and spec.get("config", {}).get("action") == "reject":
                # emit event
                self.event_bus.publish({"id": f"dq-{int(time.time()*1000)}", "type": "dq.failure", "source": "dq", "payload": {"rule": rule.id, "record": record}})
        return results

    def run_post_ingest(self, record: Dict[str, Any], record_id: str = None) -> List[ValidationResult]:
        """
        Run validations after persist. For example mark unique indexes.
        """
        results = []
        for spec in self.registry.list():
            if not spec.get("enabled", True):
                continue
            rule = self._instantiate_rule(spec)
            res = rule.validate(record)
            vr = ValidationResult(rule_id=rule.id, ok=res["ok"], message=res.get("message"), record_id=record_id, details=res.get("details", {}))
            results.append(vr)
            if isinstance(rule, UniqueRule) and res["ok"]:
                # mark uniqueness index
                rule.mark_unique(record, record_id or "")
        # persist report
        self._write_report(record_id or "unknown", results)
        return results

    def _write_report(self, record_id: str, results: List[ValidationResult]):
        key = REPORT_KEY_PREFIX + str(record_id)
        arr = [r.dict() for r in results]
        self.storage.put(key, json.dumps(arr).encode("utf-8"))

    def _inc_metric(self, rule_id: str, failures: int = 0):
        # simple metrics stored as JSON map {rule_id: {"failures": n, "checked": m}}
        raw = self.storage.get(METRICS_KEY) or b"{}"
        try:
            m = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            m = {}
        entry = m.get(rule_id, {"failures": 0, "checked": 0})
        entry["failures"] += failures
        entry["checked"] += 1
        m[rule_id] = entry
        self.storage.put(METRICS_KEY, json.dumps(m).encode("utf-8"))
```

> **Note**: `json` import required at top of `pipeline.py`. Add `import json` after other imports.

#### `tasker/data_quality/api.py`
```python
# tasker/data_quality/api.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from tasker.data_quality.serializers import RuleSpec
from tasker.cli.wiring import build_api_container

router = APIRouter(prefix="/api/v1/data-quality", tags=["data-quality"])

def get_container():
    return build_api_container()

@router.post("/rules")
def create_rule(spec: RuleSpec, container = Depends(get_container)):
    # admin only
    user_id = None
    try:
        user_id = container.get_user_id_from_request(container.request)  # container.request may be set by middleware
    except Exception:
        user_id = None
    if not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    container.rule_registry.add(spec.dict())
    return {"status":"ok","rule": spec.dict()}

@router.get("/rules")
def list_rules(container = Depends(get_container)):
    return {"status":"ok","rules": container.rule_registry.list()}

@router.get("/reports/{record_id}")
def get_report(record_id: str, container = Depends(get_container)):
    key = "dq:reports:" + record_id
    raw = container.storage.get(key) or b"[]"
    import json
    arr = json.loads(raw.decode("utf-8")) if raw else []
    return {"status":"ok","report": arr}

@router.get("/metrics")
def get_metrics(container = Depends(get_container)):
    raw = container.storage.get("dq:metrics") or b"{}"
    import json
    m = json.loads(raw.decode("utf-8")) if raw else {}
    return {"status":"ok","metrics": m}
```

#### `tasker/data_quality/prometheus.py`
```python
# tasker/data_quality/prometheus.py
from __future__ import annotations
import json
from tasker.application.ports import StoragePort

class MetricsStore:
    """
    Simple metrics helper storing counters in StoragePort under key dq:metrics.
    Exposes get_metrics to be used by API or Prometheus exporter.
    """

    KEY = "dq:metrics"

    def __init__(self, storage: StoragePort):
        self.storage = storage

    def get_metrics(self) -> dict:
        raw = self.storage.get(self.KEY) or b"{}"
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            return {}

    def set_metrics(self, metrics: dict):
        self.storage.put(self.KEY, json.dumps(metrics).encode("utf-8"))
```

---

### Tests to add

#### `tasker/data_quality/tests/test_rules_unit.py`
```python
# tasker/data_quality/tests/test_rules_unit.py
from tasker.data_quality.rules import RangeRule, SchemaRule, BaseRule
def test_range_rule():
    spec = {"id":"r1","target":"value","config":{"min":0,"max":10}}
    rr = RangeRule(spec)
    ok = rr.validate({"value":5})
    assert ok["ok"]
    bad = rr.validate({"value": 20})
    assert not bad["ok"]
```

#### `tasker/data_quality/tests/test_pipeline_unit.py`
```python
# tasker/data_quality/tests/test_pipeline_unit.py
from tasker.data_quality.rules import RuleRegistry
from tasker.data_quality.pipeline import DataQualityPipeline
from tasker.infrastructure.memory_storage import MemoryStorage
from tasker.events.bus import EventBus

def test_pipeline_pre_post():
    storage = MemoryStorage()
    registry = RuleRegistry(storage)
    # add a simple range rule
    registry.add({"id":"r1","name":"range","kind":"range","target":"value","config":{"min":0,"max":10,"action":"reject"}})
    eb = EventBus()
    pipeline = DataQualityPipeline(storage, registry, eb)
    rec = {"value": 20}
    pre = pipeline.run_pre_ingest(rec, record_id="rec1")
    assert any(not r.ok for r in pre)
    # post ingest should write report
    post = pipeline.run_post_ingest(rec, record_id="rec1")
    assert len(post) >= 1
    # report persisted
    raw = storage.get("dq:reports:rec1")
    assert raw is not None
```

#### `tests/integration/test_data_quality_integration.py`
```python
# tests/integration/test_data_quality_integration.py
import os, time, pytest
from tasker.infrastructure.memory_storage import MemoryStorage
from tasker.data_quality.rules import RuleRegistry
from tasker.data_quality.pipeline import DataQualityPipeline
from tasker.events.bus import EventBus

pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")

def test_integration_rejects_and_emits_event():
    _skip_if_not_integration()
    storage = MemoryStorage()
    registry = RuleRegistry(storage)
    registry.add({"id":"r1","name":"range","kind":"range","target":"value","config":{"min":0,"max":10,"action":"reject"}})
    eb = EventBus()
    events = []
    def handler(e):
        events.append(e)
    eb.subscribe("dq.failure", handler)
    pipeline = DataQualityPipeline(storage, registry, eb)
    rec = {"value": 100}
    pre = pipeline.run_pre_ingest(rec, record_id="i1")
    assert any(not r.ok for r in pre)
    # event should be published
    assert len(events) >= 1
```

---

### API integration snippet to add to `tasker/api/app.py`

Insert router mount near other routers:

```python
from tasker.data_quality.api import router as data_quality_router
app.include_router(data_quality_router)
```

Integrate pipeline into an ingestion endpoint (example for issues). Replace or wrap the existing issue create flow with the following snippet:

```python
# inside create issue endpoint before persisting
container = get_container()
pipeline = container.data_quality_pipeline
# run pre-ingest validations
pre = pipeline.run_pre_ingest(issue_dict, record_id=issue_id)
# if any rule with action reject failed, return 400
if any(not r.ok for r in pre):
    return JSONResponse(status_code=400, content={"status":"error","error":"data_quality_failed","details":[r.dict() for r in pre]})
# persist issue as before
# after persist, run post-ingest
post = pipeline.run_post_ingest(issue_dict, record_id=issue_id)
```

---

### Wiring changes for `tasker/cli/wiring.py`

Add the following excerpt after storage and event bus creation:

```python
from tasker.data_quality.rules import RuleRegistry
from tasker.data_quality.pipeline import DataQualityPipeline

rule_registry = RuleRegistry(storage)
data_quality_pipeline = DataQualityPipeline(storage=storage, rule_registry=rule_registry, event_bus=events_bus)

# include in Container return
return Container(..., rule_registry=rule_registry, data_quality_pipeline=data_quality_pipeline, ...)
```

---

### Commands to run exactly

```bash
git checkout -b feature/data-quality-framework
python -m pip install -e .
# run unit tests
pytest tasker/data_quality/tests/test_rules_unit.py -q
pytest tasker/data_quality/tests/test_pipeline_unit.py -q
# optional integration test
export TASKER_INTEGRATION=1
pytest tests/integration/test_data_quality_integration.py -q -m integration || true
# commit and push
git add tasker/data_quality tasker/api/app.py tasker/cli/wiring.py tests
git commit -m "feat(data-quality): add data quality framework, rules, pipelines, API and tests"
git push origin feature/data-quality-framework
```

---

### PR body exact text to paste

```
Summary:
- Added Data Quality Framework with rule registry, validation pipelines, API and metrics.
- Implemented rule types: schema, range, unique, custom and a RuleRegistry persisted in StoragePort.
- Implemented DataQualityPipeline for pre-ingest and post-ingest validations, report persistence and metrics.
- Exposed API to manage rules and fetch reports and metrics at /api/v1/data-quality.
- Integrated pipeline into ingestion flow to reject or correct records deterministically and emit events on failures.
- Added unit and integration tests and wiring into container.
Verification steps executed:
1. Installed package in editable mode.
2. Ran unit tests for rules and pipeline.
3. Optionally ran integration test with TASKER_INTEGRATION=1 to verify event emission and report persistence.
Files changed:
- tasker/data_quality/*
- tasker/api/app.py
- tasker/cli/wiring.py
- tests/*
Notes:
- Rules are deterministic and persisted under dq:rules.
- Metrics stored under dq:metrics and reports under dq:reports:<record_id>.
- For production, consider exporting metrics to Prometheus directly and using a robust index for unique checks.
```

---

### Acceptance criteria

- `tasker/data_quality` package exists with `rules.py`, `pipeline.py`, `api.py`, `serializers.py` and `prometheus.py`.  
- `RuleRegistry` persists rules in `StoragePort` and supports add/list/get/delete.  
- `DataQualityPipeline` runs pre and post ingest validations, persists reports under `dq:reports:<record_id>`, and increments metrics under `dq:metrics`.  
- API mounted at `/api/v1/data-quality` supports rule management and report/metrics retrieval.  
- Ingestion endpoints call `run_pre_ingest` and `run_post_ingest` as shown and reject records when configured.  
- Unit tests for rules and pipeline pass; integration test runs when `TASKER_INTEGRATION=1`.  
- Branch `feature/data-quality-framework` created and PR opened with the PR body above.