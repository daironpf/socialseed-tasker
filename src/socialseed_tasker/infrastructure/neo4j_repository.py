"""Neo4j repository implementations.

Implements TaskRepositoryInterface using Neo4j as the persistence engine.
Uses the synchronous Neo4j driver for simplicity and reliability.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from socialseed_tasker.application.actions import TaskRepositoryInterface
from socialseed_tasker.infrastructure.neo4j_impl.component_mixin import ComponentRepositoryMixin
from socialseed_tasker.infrastructure.neo4j_impl.constraint_mixin import ConstraintRepositoryMixin
from socialseed_tasker.infrastructure.neo4j_impl.cost_mixin import CostAnalyticsRepositoryMixin
from socialseed_tasker.infrastructure.neo4j_impl.deployment_mixin import DeploymentRepositoryMixin
from socialseed_tasker.infrastructure.neo4j_impl.epic_mixin import EpicRepositoryMixin
from socialseed_tasker.infrastructure.neo4j_impl.issue_mixin import IssueRepositoryMixin
from socialseed_tasker.infrastructure.neo4j_impl.label_mixin import LabelRepositoryMixin
from socialseed_tasker.infrastructure.neo4j_impl.vector_mixin import VectorSearchRepositoryMixin

if TYPE_CHECKING:
    from socialseed_tasker.infrastructure.neo4j_driver import Neo4jDriver


class Neo4jTaskRepository(
    ComponentRepositoryMixin,
    IssueRepositoryMixin,
    ConstraintRepositoryMixin,
    EpicRepositoryMixin,
    LabelRepositoryMixin,
    CostAnalyticsRepositoryMixin,
    DeploymentRepositoryMixin,
    VectorSearchRepositoryMixin,
    TaskRepositoryInterface,
):
    """Neo4j implementation of TaskRepositoryInterface.

    Intent: Persist issues and components in a Neo4j graph database.
    Business Value: Enables efficient graph traversals for dependency
    analysis, root-cause tracing, and impact assessment.
    """

    def __init__(self, driver: Neo4jDriver) -> None:
        self._driver = driver
