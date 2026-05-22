"""Neo4j-backed implementation of IssueRepository.

Note: Neo4j 5.x does not support MAP values as node properties.
Metadata dicts are serialized to JSON strings for storage and
parsed back to dicts on read.
"""

from __future__ import annotations

import json

from socialseed_tasker.application.dtos import IssueDTO, IssueSummary
from socialseed_tasker.application.exceptions import GraphPortError
from socialseed_tasker.application.ports import GraphPort
from socialseed_tasker.application.repositories import IssueRepository


class Neo4jIssueRepository(IssueRepository):
    """Neo4j-backed implementation of IssueRepository.

    Implementation notes:
    - Issues are stored as nodes with label Issue and property 'id' (string).
    - Use parameterized Cypher queries only.
    - Map driver results to IssueDTO and IssueSummary.
    - Metadata dicts are stored as JSON strings (Neo4j 5.x compat).
    """

    def __init__(self, graph: GraphPort) -> None:
        self._graph = graph

    def save(self, issue: IssueDTO) -> None:
        try:
            cypher = (
                "MERGE (i:Issue {id: $id}) "
                "SET i.title = $title, i.description = $description, i.status = $status, "
                "i.metadata = $metadata"
            )
            self._graph.run_cypher(
                cypher,
                {
                    "id": issue.id,
                    "title": issue.title,
                    "description": issue.description,
                    "status": issue.status,
                    "metadata": json.dumps(dict(issue.metadata or {})),
                },
            )
        except Exception as exc:
            raise GraphPortError(f"Failed to save issue {issue.id}: {exc}") from exc

    def get(self, issue_id: str) -> IssueDTO | None:
        try:
            cypher = (
                "MATCH (i:Issue {id: $id}) "
                "RETURN i.id AS id, i.title AS title, i.description AS description, "
                "i.status AS status, i.metadata AS metadata"
            )
            res = self._graph.run_cypher(cypher, {"id": issue_id})
            if not res.records:
                return None
            r = res.records[0]
            raw = r.get("metadata") or "{}"
            metadata = json.loads(raw) if isinstance(raw, str) else raw
            return IssueDTO(
                id=str(r.get("id")),
                title=str(r.get("title") or ""),
                description=str(r.get("description") or ""),
                status=str(r.get("status") or ""),
                metadata=metadata,
            )
        except Exception as exc:
            raise GraphPortError(f"Failed to get issue {issue_id}: {exc}") from exc

    def list(self, status: str | None = None) -> list[IssueSummary]:
        try:
            if status:
                cypher = "MATCH (i:Issue {status: $status}) RETURN i.id AS id, i.title AS title, i.status AS status"
                res = self._graph.run_cypher(cypher, {"status": status})
            else:
                cypher = "MATCH (i:Issue) RETURN i.id AS id, i.title AS title, i.status AS status"
                res = self._graph.run_cypher(cypher, {})
            return [
                IssueSummary(id=str(r.get("id")), title=str(r.get("title") or ""), status=str(r.get("status") or ""))
                for r in res.records
            ]
        except Exception as exc:
            raise GraphPortError(f"Failed to list issues: {exc}") from exc

    def delete(self, issue_id: str) -> None:
        try:
            cypher = "MATCH (i:Issue {id: $id}) DETACH DELETE i"
            self._graph.run_cypher(cypher, {"id": issue_id})
        except Exception as exc:
            raise GraphPortError(f"Failed to delete issue {issue_id}: {exc}") from exc
