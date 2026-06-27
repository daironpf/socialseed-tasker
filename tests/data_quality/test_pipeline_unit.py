from socialseed_tasker.data_quality.rules import RuleRegistry
from socialseed_tasker.data_quality.pipeline import DataQualityPipeline
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from socialseed_tasker.events.bus import EventBus

def test_pipeline_pre_post():
    storage = MemoryStorage()
    registry = RuleRegistry(storage)
    registry.add({"id": "r1", "name": "range", "kind": "range", "target": "value", "config": {"min": 0, "max": 10, "action": "reject"}})
    eb = EventBus()
    pipeline = DataQualityPipeline(storage, registry, eb)
    rec = {"value": 20}
    pre = pipeline.run_pre_ingest(rec, record_id="rec1")
    assert any(not r.ok for r in pre)
    post = pipeline.run_post_ingest(rec, record_id="rec1")
    assert len(post) >= 1
    raw = storage.get("dq:reports:rec1")
    assert raw is not None


def test_pipeline_emits_event_on_reject():
    storage = MemoryStorage()
    registry = RuleRegistry(storage)
    registry.add({"id": "r1", "name": "range", "kind": "range", "target": "value", "config": {"min": 0, "max": 10, "action": "reject"}})
    eb = EventBus()
    events = []
    def h(e):
        events.append(e)
    eb.subscribe("dq.failure", h)
    pipeline = DataQualityPipeline(storage, registry, eb)
    rec = {"value": 100}
    pre = pipeline.run_pre_ingest(rec, record_id="i1")
    assert any(not r.ok for r in pre)
    assert len(events) >= 1


def test_pipeline_metrics():
    storage = MemoryStorage()
    registry = RuleRegistry(storage)
    registry.add({"id": "r1", "name": "range", "kind": "range", "target": "value", "config": {"min": 0, "max": 10}})
    pipeline = DataQualityPipeline(storage, registry, EventBus())
    pipeline.run_pre_ingest({"value": 5}, record_id="a")
    pipeline.run_pre_ingest({"value": 20}, record_id="b")
    raw = storage.get("dq:metrics")
    import json
    m = json.loads(raw.decode("utf-8"))
    assert m["r1"]["checked"] == 2
    assert m["r1"]["failures"] == 1
