"""Integration tests for the thin CLI — runs against real Neo4j.

Requires TASKER_INTEGRATION=1 and Neo4j running via docker-compose.neo4j.yml.
"""

from __future__ import annotations

import json
import os
from io import StringIO

import pytest

pytestmark = pytest.mark.integration


def _skip_if_not_integration() -> None:
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration tests disabled; set TASKER_INTEGRATION=1 to enable")


def test_create_issue_and_calculate_impact_integration():
    """Create two issues, add a dependency, calculate impact via the thin CLI."""
    _skip_if_not_integration()

    from socialseed_tasker.cli.main import main

    with pytest.raises(SystemExit) as exc:
        main(["create-issue", "--id", "cli-a", "--title", "A"])
    assert exc.value.code == 0

    with pytest.raises(SystemExit) as exc:
        main(["create-issue", "--id", "cli-b", "--title", "B"])
    assert exc.value.code == 0

    with pytest.raises(SystemExit) as exc:
        main(["add-dependency", "--from", "cli-a", "--to", "cli-b"])
    assert exc.value.code == 0

    from io import StringIO

    with pytest.raises(SystemExit) as exc, StringIO() as buf:
        import sys
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            main(["calculate-impact", "--issue-id", "cli-b"])
        finally:
            sys.stdout = old_stdout
        output = buf.getvalue()

    assert exc.value.code == 0
    j = json.loads(output)
    assert "cli-a" in j.get("impact_set", [])

    # cleanup
    from socialseed_tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter
    from socialseed_tasker.infrastructure.neo4j_issue_repository import Neo4jIssueRepository

    g = Neo4jGraphAdapter()
    r = Neo4jIssueRepository(g)
    r.delete("cli-a")
    r.delete("cli-b")
    g.close()
