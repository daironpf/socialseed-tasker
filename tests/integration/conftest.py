"""Live-infrastructure tests (opt-in).

These tests talk to real services on localhost (Neo4j, Redis, PostgreSQL...)
and some of them DESTROY development data: test_neo4j_repository wipes the
entire graph on every fixture teardown (``MATCH (n) DETACH DELETE n``), which
emptied the local Neo4j on every gate run.

They are therefore skipped by default. To run them explicitly you need a
DISPOSABLE stack (not a development database):

    TASKER_INTEGRATION=1 pytest tests/integration -v
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[Any]) -> None:
    if os.getenv("TASKER_INTEGRATION", "false").lower() in {"1", "true", "yes"}:
        return
    skip = pytest.mark.skip(
        reason="live infra test: set TASKER_INTEGRATION=1 (needs disposable databases)"
    )
    for item in items:
        # This hook is session-wide: only skip items collected from this directory.
        path = Path(str(getattr(item, "path", "") or item.fspath))
        if "integration" in path.parts:
            item.add_marker(skip)
