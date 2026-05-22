"""Domain-level tests for impact analysis — no infrastructure, pure in-memory fakes."""

from __future__ import annotations

from socialseed_tasker.application.dtos import DependencyEdge
from socialseed_tasker.application.use_cases import calculate_impact
from tests.domain.fake_graph_repo import FakeGraphRepository


def test_impact_simple_chain() -> None:
    g = FakeGraphRepository()
    g.add_dependency(DependencyEdge(from_issue_id="a", to_issue_id="b", relation="DEPENDS_ON"))
    g.add_dependency(DependencyEdge(from_issue_id="b", to_issue_id="c", relation="DEPENDS_ON"))
    impact = calculate_impact("c", 5, g)
    assert impact == ["a", "b"]


def test_impact_cycle() -> None:
    g = FakeGraphRepository()
    g.add_dependency(DependencyEdge(from_issue_id="a", to_issue_id="b", relation="DEPENDS_ON"))
    g.add_dependency(DependencyEdge(from_issue_id="b", to_issue_id="a", relation="DEPENDS_ON"))
    impact = calculate_impact("a", 5, g)
    # In a cycle a→b→a both are transitively dependent on "a"
    assert sorted(impact) == ["a", "b"]


def test_impact_missing_issue() -> None:
    g = FakeGraphRepository()
    impact = calculate_impact("x", 5, g)
    assert impact == []
