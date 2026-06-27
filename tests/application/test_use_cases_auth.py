from socialseed_tasker.application.use_cases import calculate_impact, generate_agent_context
from unittest.mock import MagicMock

def test_use_case_accepts_user_id():
    graph_repo = MagicMock()
    graph_repo.find_impact_set.return_value = []
    res = calculate_impact("x", 3, graph_repo, user_id="reader")
    assert res == []
