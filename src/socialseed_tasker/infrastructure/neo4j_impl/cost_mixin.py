from __future__ import annotations

from socialseed_tasker.infrastructure import neo4j_queries as queries
from socialseed_tasker.infrastructure.neo4j_impl.shared import _session


class CostAnalyticsRepositoryMixin:
    """Cost analytics operations."""

    def get_cost_per_component(self) -> list[dict]:
        """Get cost breakdown by component for closed issues."""
        with _session(self._driver) as session:
            result = session.run(queries.GET_COST_PER_COMPONENT)
            return [
                {
                    "componentId": record["componentId"],
                    "component_name": record["component_name"],
                    "actual_cost": record.get("actual_cost", 0.0) or 0.0,
                    "avg_hourly_rate": record.get("avg_hourly_rate", 0.0) or 0.0,
                    "total_hours": record.get("total_hours", 0) or 0,
                    "issue_count": record.get("issue_count", 0) or 0,
                }
                for record in result
            ]

    def get_cost_per_epic(self) -> list[dict]:
        """Get cost breakdown by epic for closed issues."""
        with _session(self._driver) as session:
            result = session.run(queries.GET_COST_PER_EPIC)
            return [
                {
                    "epicId": record["epicId"],
                    "epic_name": record["epic_name"],
                    "actual_cost": record.get("actual_cost", 0.0) or 0.0,
                    "total_hours": record.get("total_hours", 0) or 0,
                    "issue_count": record.get("issue_count", 0) or 0,
                }
                for record in result
            ]

    def get_cost_per_project(self) -> list[dict]:
        """Get cost breakdown by project for closed issues."""
        with _session(self._driver) as session:
            result = session.run(queries.GET_COST_PER_PROJECT)
            return [
                {
                    "projectId": record["projectId"],
                    "project_name": record["project_name"],
                    "actual_cost": record.get("actual_cost", 0.0) or 0.0,
                    "total_hours": record.get("total_hours", 0) or 0,
                    "issue_count": record.get("issue_count", 0) or 0,
                }
                for record in result
            ]

    def get_cost_summary(self) -> dict:
        """Get overall cost summary."""
        with _session(self._driver) as session:
            result = session.run(queries.GET_COST_SUMMARY)
            record = result.single()
            if record is None:
                return {
                    "total_actual_cost": 0.0,
                    "total_hours": 0,
                    "total_issues_closed": 0,
                }
            return {
                "total_actual_cost": record.get("total_actual_cost", 0.0) or 0.0,
                "total_hours": record.get("total_hours", 0) or 0,
                "total_issues_closed": record.get("total_issues_closed", 0) or 0,
            }
