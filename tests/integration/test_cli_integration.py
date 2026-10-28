"""Integration tests for the thin CLI — runs against real Neo4j.

Requires TASKER_INTEGRATION=1 and Neo4j running via compose/infra/neo4j.yml.
"""

from __future__ import annotations

import json
import os
import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.requires_neo4j,
]


def _skip_if_not_integration() -> None:
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration tests disabled; set TASKER_INTEGRATION=1 to enable")


def test_create_issue_and_calculate_impact_integration(monkeypatch, capsys):
    """Create two issues, add a dependency, calculate impact via the thin CLI."""
    _skip_if_not_integration()
    monkeypatch.setenv("TASKER_AUTH_TOKEN", os.getenv("TASKER_TEST_TOKEN", "admintoken123"))

    from socialseed_tasker.cli.main import main

    main(["create-issue", "--id", "cli-a", "--title", "A"])
    main(["create-issue", "--id", "cli-b", "--title", "B"])
    main(["add-dependency", "--from", "cli-a", "--to", "cli-b"])

    capsys.readouterr()
    main(["calculate-impact", "--issue-id", "cli-b"])
    j = json.loads(capsys.readouterr().out)
    assert "cli-a" in j.get("impact_set", [])

    # cleanup
    from socialseed_tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter
    from socialseed_tasker.infrastructure.neo4j_issue_repository import Neo4jIssueRepository

    g = Neo4jGraphAdapter()
    r = Neo4jIssueRepository(g)
    r.delete("cli-a")
    r.delete("cli-b")
    g.close()
