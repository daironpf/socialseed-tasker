"""Issue #580: cost analytics Cypher must be valid and share one rate source.

The audit found every ``/cost-*`` query failing with two errors: a string
literal where Neo4j expects a Boolean (``CASE WHEN 'JUNIOR'`` → 22NB1) and an
orphan ``hours`` variable (the ``COLLECT({hours, tier})`` line aggregated it
away before the ``SUM``). The rate expression is now generated from
``domain.value_objects.HOURLY_RATES`` so the numbers exist in exactly one
place, and these tests pin both regressions.
"""

from __future__ import annotations

from socialseed_tasker.domain.value_objects import HOURLY_RATES
from socialseed_tasker.infrastructure import neo4j_queries as queries

COST_QUERIES = {
    "GET_COST_PER_COMPONENT": queries.GET_COST_PER_COMPONENT,
    "GET_COST_PER_EPIC": queries.GET_COST_PER_EPIC,
    "GET_COST_PER_PROJECT": queries.GET_COST_PER_PROJECT,
    "GET_COST_SUMMARY": queries.GET_COST_SUMMARY,
}


def test_cost_queries_use_simple_case_over_tier_variable() -> None:
    """``CASE WHEN '<literal>'`` is a Boolean type mismatch (Neo4j 22NB1)."""
    for name, query in COST_QUERIES.items():
        assert "CASE WHEN '" not in query, f"{name}: string literal where Boolean expected"
        assert "CASE tier WHEN" in query, f"{name}: expected simple CASE over the tier variable"


def test_cost_queries_share_single_rate_expression() -> None:
    for name, query in COST_QUERIES.items():
        assert queries._TIER_RATE_CASE in query, f"{name}: must use the shared rate CASE"


def test_rate_expression_covers_every_hourly_rate_tier() -> None:
    case = queries._TIER_RATE_CASE
    assert case.startswith("CASE tier ")
    assert case.endswith(" ELSE 0.0 END")
    for tier, rate in HOURLY_RATES.items():
        assert f"WHEN '{tier.value}' THEN {rate}" in case, f"missing rate for {tier.value}"


def test_cost_queries_keep_hours_in_scope() -> None:
    """The old COLLECT dropped ``hours`` from scope → ``Variable 'hours' not defined``."""
    for name, query in COST_QUERIES.items():
        assert "COLLECT(" not in query, f"{name}: aggregation must not discard per-issue rows"
        assert "issue_data" not in query, f"{name}: unused aggregate left behind"
        assert "AS hours" in query, f"{name}: hours must come from a WITH/MATCH binding"
