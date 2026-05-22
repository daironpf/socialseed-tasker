"""Wiring helper — builds the default Container with concrete adapters."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from socialseed_tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter
from socialseed_tasker.infrastructure.neo4j_graph_repository import Neo4jGraphRepository
from socialseed_tasker.infrastructure.neo4j_issue_repository import Neo4jIssueRepository
from socialseed_tasker.infrastructure.parser_adapter import TreeSitterParser

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


def build_default_container() -> Container:
    """Construct and return a default Container wired to Neo4j + TreeSitter."""
    logger = logging.getLogger("tasker")
    logger.setLevel(logging.INFO)
    graph = Neo4jGraphAdapter()
    parser = TreeSitterParser()
    issue_repo = Neo4jIssueRepository(graph)
    graph_repo = Neo4jGraphRepository(graph)
    return Container(
        graph=graph,
        parser=parser,
        issue_repo=issue_repo,
        graph_repo=graph_repo,
        embedding=None,
        storage=None,
        logger=logger,
        application=application_module,
    )
