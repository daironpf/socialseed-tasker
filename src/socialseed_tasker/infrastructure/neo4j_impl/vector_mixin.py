from __future__ import annotations

from contextlib import contextmanager

from socialseed_tasker.infrastructure import neo4j_queries


class VectorSearchRepositoryMixin:
    """Vector search and data management operations."""

    def search_by_embedding(self, embedding: list[float], threshold: float = 0.7, limit: int = 10) -> list[dict]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.SEARCH_BY_EMBEDDING,
                embedding=embedding,
                threshold=threshold,
                limit=limit,
            )
            return [
                {
                    "issue_id": record["issue_id"],
                    "title": record["title"],
                    "score": record["score"],
                }
                for record in result
            ]

    def find_similar_issues(self, issue_id: str, threshold: float = 0.7, limit: int = 10) -> list[dict]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.FIND_SIMILAR_ISSUES,
                issue_id=issue_id,
                threshold=threshold,
                limit=limit,
            )
            return [
                {
                    "issue_id": record["issue_id"],
                    "title": record["title"],
                    "score": record["score"],
                }
                for record in result
            ]

    def update_issue_embedding(self, issue_id: str, embedding: list[float]) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                queries.UPDATE_ISSUE_EMBEDDING,
                id=issue_id,
                embedding=embedding,
            )

    @contextmanager
    def transaction(self):  # type: ignore[misc]
        """Execute a block of operations as a logical unit.

        Note: Each repository method manages its own Neo4j session internally.
        This context manager exists to satisfy the TaskRepositoryInterface contract
        and to allow future refactoring toward explicit transaction passing.
        Currently behaves as a logical grouping marker (no-op yield).
        """
        yield

    def reset_data(self, scope: str = "all") -> dict[str, int]:
        """Reset data in the repository."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result: dict[str, int] = {}

            if scope in ("all", "issues"):
                res = session.run("MATCH (i:Issue) DETACH DELETE i RETURN count(*) as count")
                record = res.single()
                result["issues_deleted"] = record["count"] if record else 0

            if scope in ("all", "components"):
                res = session.run("MATCH (c:Component) DETACH DELETE c RETURN count(*) as count")
                record = res.single()
                result["components_deleted"] = record["count"] if record else 0

            return result
