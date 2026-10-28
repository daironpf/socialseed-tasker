"""Live-infrastructure tests (opt-in).

These tests talk to real services and some of them DESTROY data:
``test_neo4j_repository`` wipes the entire graph on every fixture teardown
(``MATCH (n) DETACH DELETE n``). Run them only against a DISPOSABLE stack, never
against a development database.

They are skipped by default. Each test declares its external prerequisite with a
marker so it can be selected on its own:

    self_contained      no external service (in-memory stores, mocks, local servers)
    requires_neo4j      disposable Neo4j        TASKER_NEO4J_URI/USER/PASSWORD
    requires_redis      disposable Redis        TASKER_REDIS_URL
    requires_api        FastAPI service         TASKER_API_URL
    requires_board      tasker-board            TASKER_BOARD_URL
    requires_graphql    GraphQL service         TASKER_GRAPHQL_URL
    requires_graphviz   graphviz service        TASKER_GRAPHVIZ_URL
    requires_jaeger     Jaeger UI/API           TASKER_JAEGER_URL
    requires_grafana    Grafana + Prometheus    TASKER_GRAFANA_URL/TASKER_PROM_URL
    requires_sso        Keycloak realm          TASKER_KEYCLOAK_URL
    requires_celery     Celery worker + broker  TASKER_CELERY_BROKER_URL
    requires_chaos      destructive chaos run   TASKER_CHAOS=1
    requires_treesitter compiled grammar        TASKER_TREESITTER_PYTHON_SO

Opt in with ``TASKER_INTEGRATION=1`` and select a group:

    TASKER_INTEGRATION=1 pytest -m self_contained
    TASKER_INTEGRATION=1 pytest -m requires_neo4j
    TASKER_INTEGRATION=1 pytest -m "requires_api and not requires_chaos"

See ``docs/INTEGRATION_TESTS.md`` for the inventory, ports and CI jobs.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest


def _integration_enabled() -> bool:
    return os.getenv("TASKER_INTEGRATION", "false").lower() in {"1", "true", "yes"}


def pytest_collection_modifyitems(config: pytest.Config, items: list[Any]) -> None:
    if _integration_enabled():
        return
    skip = pytest.mark.skip(
        reason=(
            "live infra test: set TASKER_INTEGRATION=1 and select a group "
            "(see docs/INTEGRATION_TESTS.md)"
        )
    )
    for item in items:
        # This hook is session-wide: only skip integration tests, either by marker
        # (files outside this directory) or by collection path (safety net).
        path = Path(str(getattr(item, "path", "") or item.fspath))
        if item.get_closest_marker("integration") or "integration" in path.parts:
            item.add_marker(skip)
