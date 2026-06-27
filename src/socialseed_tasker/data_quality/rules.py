from __future__ import annotations
import json
from typing import Any, Dict, Callable, List, Optional
from socialseed_tasker.application.ports import StoragePort

class ValidationError(Exception):
    pass

class BaseRule:
    def __init__(self, spec: Dict[str, Any]):
        self.spec = spec
        self.id = spec["id"]
        self.name = spec.get("name", self.id)
        self.enabled = spec.get("enabled", True)

    def validate(self, record: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

class SchemaRule(BaseRule):
    def __init__(self, spec: Dict[str, Any], schema: Dict[str, Any]):
        super().__init__(spec)
        self.schema = schema
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
