import os
import pytest
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from socialseed_tasker.data_quality.rules import RuleRegistry
from socialseed_tasker.data_quality.pipeline import DataQualityPipeline
from socialseed_tasker.events.bus import EventBus

pytestmark = pytest.mark.integration


def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")


def test_integration_rejects_and_emits_event():
    _skip_if_not_integration()
    storage = MemoryStorage()
    registry = RuleRegistry(storage)
    registry.add({"id": "r1", "name": "range", "kind": "range", "target": "value", "config": {"min": 0, "max": 10, "action": "reject"}})
    eb = EventBus()
    events = []
    def handler(e):
        events.append(e)
    eb.subscribe("dq.failure", handler)
    pipeline = DataQualityPipeline(storage, registry, eb)
    rec = {"value": 100}
    pre = pipeline.run_pre_ingest(rec, record_id="i1")
    assert any(not r.ok for r in pre)
    assert len(events) >= 1
