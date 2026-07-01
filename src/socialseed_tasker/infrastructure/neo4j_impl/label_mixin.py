from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from socialseed_tasker.domain.entities import Issue
from socialseed_tasker.infrastructure import neo4j_queries as queries
from socialseed_tasker.infrastructure.neo4j_impl.shared import _node_to_issue, _session


class LabelRepositoryMixin:
    """Label management operations."""

    def sync_labels_from_github(self, github_adapter) -> int:
        """Sync labels from GitHub repository."""
        from datetime import datetime, timezone
        from uuid import uuid4

        labels = github_adapter.list_labels() if github_adapter else []
        synced = 0

        with _session(self._driver) as session:
            for label in labels:
                session.run(
                    queries.CREATE_LABEL,
                    id=str(uuid4()),
                    name=label.get("name", ""),
                    color=label.get("color", ""),
                    description=label.get("description", ""),
                    createdAt=datetime.now(timezone.utc).isoformat(),
                    updatedAt=datetime.now(timezone.utc).isoformat(),
                )
                synced += 1

        return synced

    def get_all_labels(self) -> list[dict]:
        """Get all labels from Neo4j."""
        with _session(self._driver) as session:
            result = session.run(queries.GET_ALL_LABELS)
            return [dict(r["l"]) for r in result]

    def link_issue_to_labels(self, issue_id: str, label_names: list[str]) -> None:
        """Link an issue to labels."""
        with _session(self._driver) as session:
            for label_name in label_names:
                session.run(
                    queries.LINK_ISSUE_TO_LABEL,
                    issue_id=issue_id,
                    label_name=label_name,
                )

    def get_issues_by_labels(self, labels: list[str]) -> list[Issue]:
        """Get issues filtered by labels."""
        if not labels:
            return []

        with _session(self._driver) as session:
            result = session.run(
                queries.GET_ISSUES_BY_LABELS,
                labels=labels,
            )
            return [_node_to_issue(r["i"]) for r in result]
