"""Wiring helper — builds the default Container with concrete adapters."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from socialseed_tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter
from socialseed_tasker.infrastructure.neo4j_graph_repository import Neo4jGraphRepository
from socialseed_tasker.infrastructure.neo4j_issue_repository import Neo4jIssueRepository
from socialseed_tasker.infrastructure.parser_adapter import TreeSitterParser
from socialseed_tasker.observability.exporter import start_exporter
from socialseed_tasker.observability.logging import get_logger
from socialseed_tasker.auth.auth import load_auth_provider
from socialseed_tasker.auth.rbac import RBAC

import socialseed_tasker.application as application_module


@dataclass
class Container:
    """Wiring container holding all adapter and repository instances."""

    graph: object
    parser: object
    issue_repo: object
    graph_repo: object
    embedding: object | None
    storage: object | None
    logger: object
    application: object
    auth: object
    rbac: object


def build_default_container() -> Container:
    """Construct and return a default Container wired to Neo4j + TreeSitter."""
    logger = get_logger("tasker")
    graph = Neo4jGraphAdapter()
    parser = TreeSitterParser()
    issue_repo = Neo4jIssueRepository(graph)
    graph_repo = Neo4jGraphRepository(graph)
    auth = load_auth_provider()
    rbac = RBAC()
    users_env = os.getenv("TASKER_AUTH_USERS")
    if users_env:
        try:
            users = json.loads(users_env)
            for uid, info in users.items():
                perms = info.get("permissions", [])
                for p in perms:
                    rbac.grant(uid, p)
        except Exception:
            pass
    if os.getenv("TASKER_METRICS_ENABLED") == "1":
        start_exporter()
    return Container(
        graph=graph,
        parser=parser,
        issue_repo=issue_repo,
        graph_repo=graph_repo,
        embedding=None,
        storage=None,
        logger=logger,
        application=application_module,
        auth=auth,
        rbac=rbac,
    )
