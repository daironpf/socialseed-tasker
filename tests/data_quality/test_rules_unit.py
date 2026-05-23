from socialseed_tasker.data_quality.rules import RangeRule, SchemaRule, BaseRule

def test_range_rule():
    spec = {"id": "r1", "target": "value", "config": {"min": 0, "max": 10}}
    rr = RangeRule(spec)
    ok = rr.validate({"value": 5})
    assert ok["ok"]
    bad = rr.validate({"value": 20})
    assert not bad["ok"]


def test_range_rule_none_value():
    spec = {"id": "r1", "target": "value", "config": {"min": 0, "max": 10}}
    rr = RangeRule(spec)
    res = rr.validate({})
    assert res["ok"]


def test_range_rule_non_numeric():
    spec = {"id": "r1", "target": "value", "config": {"min": 0, "max": 10}}
    rr = RangeRule(spec)
    res = rr.validate({"value": "abc"})
    assert not res["ok"]
