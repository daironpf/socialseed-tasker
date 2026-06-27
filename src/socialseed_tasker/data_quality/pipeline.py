from __future__ import annotations
import json
import time
from typing import Dict, Any, List
from socialseed_tasker.data_quality.rules import RuleRegistry, BaseRule, SchemaRule, RangeRule, UniqueRule, CustomRule
from socialseed_tasker.application.ports import StoragePort
from socialseed_tasker.events.bus import EventBus
from socialseed_tasker.events.serializers import EventDTO
from socialseed_tasker.data_quality.serializers import ValidationResult

REPORT_KEY_PREFIX = "dq:reports:"
METRICS_KEY = "dq:metrics"

class DataQualityPipeline:
    def __init__(self, storage: StoragePort, rule_registry: RuleRegistry, event_bus: EventBus):
        self.storage = storage
        self.registry = rule_registry
        self.event_bus = event_bus
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
            fn = spec.get("config", {}).get("fn")
            r = CustomRule(spec, fn or (lambda rec: {"ok": True, "message": None, "details": {}}))
        else:
            r = BaseRule(spec)
        self._rule_objs[rid] = r
        return r

    def run_pre_ingest(self, record: Dict[str, Any], record_id: str = None) -> List[ValidationResult]:
        results = []
        for spec in self.registry.list():
            if not spec.get("enabled", True):
                continue
            rule = self._instantiate_rule(spec)
            res = rule.validate(record)
            vr = ValidationResult(rule_id=rule.id, ok=res["ok"], message=res.get("message"), record_id=record_id, details=res.get("details", {}))
            results.append(vr)
            self._inc_metric(rule.id, 0 if res["ok"] else 1)
            if not res["ok"] and spec.get("config", {}).get("action") == "reject":
                self.event_bus.publish(EventDTO.from_dict({
                    "id": f"dq-{int(time.time()*1000)}",
                    "type": "dq.failure",
                    "source": "dq",
                    "payload": {"rule": rule.id, "record": record},
                }))
        return results

    def run_post_ingest(self, record: Dict[str, Any], record_id: str = None) -> List[ValidationResult]:
        results = []
        for spec in self.registry.list():
            if not spec.get("enabled", True):
                continue
            rule = self._instantiate_rule(spec)
            res = rule.validate(record)
            vr = ValidationResult(rule_id=rule.id, ok=res["ok"], message=res.get("message"), record_id=record_id, details=res.get("details", {}))
            results.append(vr)
            if isinstance(rule, UniqueRule) and res["ok"]:
                rule.mark_unique(record, record_id or "")
        self._write_report(record_id or "unknown", results)
        return results

    def _write_report(self, record_id: str, results: List[ValidationResult]):
        key = REPORT_KEY_PREFIX + str(record_id)
        arr = [r.model_dump() for r in results]
        self.storage.put(key, json.dumps(arr).encode("utf-8"))

    def _inc_metric(self, rule_id: str, failures: int = 0):
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
