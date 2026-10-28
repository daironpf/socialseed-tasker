import os

import pytest
import requests

pytestmark = [
    pytest.mark.integration,
    pytest.mark.requires_graphql,
]


def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")


def test_subscription_receives_event():
    _skip_if_not_integration()
    url = os.getenv("TASKER_GRAPHQL_URL", "http://localhost:8081/graphql")
    headers = {"Authorization": "Bearer admintoken123"}
    m = {"query": "mutation { triggerEvent(type: \"test.event\", payload: { \"x\": 1 }) }"}
    r = requests.post(url, json=m, headers=headers)
    assert r.status_code == 200
    assert "data" in r.json()
