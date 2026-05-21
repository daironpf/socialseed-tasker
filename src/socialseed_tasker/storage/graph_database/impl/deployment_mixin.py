from __future__ import annotations

from socialseed_tasker.storage.graph_database import queries


class DeploymentRepositoryMixin:
    """Deployment operations."""

    def create_deployment(self, deployment) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                queries.CREATE_DEPLOYMENT,
                id=str(deployment.id),
                commit_sha=deployment.commit_sha,
                environment_name=deployment.environment_name.value,
                deployed_at=deployment.deployed_at.isoformat(),
                issue_ids=[str(i) for i in deployment.issue_ids],
                channel=deployment.channel,
                deployed_by=deployment.deployed_by,
            )

    def get_deployments(
        self,
        environment_name: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.GET_DEPLOYMENTS,
                environment_name=environment_name,
                limit=limit,
            )
            return [
                {
                    "id": record["d"]["id"],
                    "commit_sha": record["d"]["commit_sha"],
                    "environment_name": record["d"]["environment_name"],
                    "deployed_at": record["d"]["deployed_at"],
                    "issue_ids": record["d"].get("issue_ids", []),
                    "channel": record["d"].get("channel"),
                    "deployed_by": record["d"].get("deployed_by"),
                }
                for record in result
            ]

    def get_deployment_by_commit(self, commit_sha: str) -> dict | None:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_DEPLOYMENT_BY_COMMIT, commit_sha=commit_sha)
            record = result.single()
            if record is None:
                return None
            return {
                "id": record["d"]["id"],
                "commit_sha": record["d"]["commit_sha"],
                "environment_name": record["d"]["environment_name"],
                "deployed_at": record["d"]["deployed_at"],
                "issue_ids": record["d"].get("issue_ids", []),
            }

    def get_issue_deployments(self, issue_id: str) -> list[dict]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_ISSUES_DEPLOYMENTS, issue_id=issue_id)
            return [
                {
                    "id": record["d"]["id"],
                    "commit_sha": record["d"]["commit_sha"],
                    "environment_name": record["d"]["environment_name"],
                    "deployed_at": record["d"]["deployed_at"],
                    "channel": record["d"].get("channel"),
                }
                for record in result
            ]
