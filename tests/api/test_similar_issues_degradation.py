"""GET /ai/similar-issues/{id} degradation (issue #591).

The similarity queries used ``apoc.algo.similarity(...)`` but the stack's Neo4j
5.26 community image has no APOC plugin -> ``CypherSyntaxError: Unknown function
'apoc.algo.similarity'`` -> the handler (no try) let it propagate as an opaque
500 ``INTERNAL_ERROR``.

Decision (Opcion B): drop APOC — both queries (``FIND_SIMILAR_ISSUES`` and
``SEARCH_BY_EMBEDDING``) now compute cosine similarity natively with
``reduce()`` in Cypher, guarded by list-size equality and non-zero norms. The
handler additionally maps a residual ``CypherSyntaxError`` to a controlled 503
with a semantic code instead of a generic 500 (patron #589/#590).
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from neo4j.exceptions import CypherSyntaxError

from socialseed_tasker.infrastructure import neo4j_queries as queries
from socialseed_tasker.infrastructure.web_api.app import create_app


class _Repo:
    def __init__(self, results: list[dict] | None = None) -> None:
        self.results = results if results is not None else []
        self.explode = False

    def find_similar_issues(self, issue_id: str, threshold: float = 0.7, limit: int = 10) -> list[dict]:
        if self.explode:
            raise CypherSyntaxError("Unknown function 'apoc.algo.similarity' (line 7, column 13)")
        return self.results


def _client(repo: Any) -> TestClient:
    return TestClient(create_app(repository=repo, neo4j_driver=None))


def test_similar_issues_returns_200_with_results() -> None:
    rows = [{"issue_id": "b", "title": "Fix login", "score": 0.8123}]
    client = _client(_Repo(rows))

    resp = client.get("/api/v1/ai/similar-issues/a")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["error"] is None
    assert body["data"] == rows
    assert "request_id" in body["meta"]


def test_similar_issues_unknown_id_returns_200_empty() -> None:
    client = _client(_Repo([]))

    resp = client.get("/api/v1/ai/similar-issues/nonexistent")
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"] == []


def test_similar_issues_cypher_error_returns_503_not_500() -> None:
    repo = _Repo()
    repo.explode = True
    client = _client(repo)

    resp = client.get("/api/v1/ai/similar-issues/a")
    assert resp.status_code == 503, resp.text
    detail = resp.json()["detail"]
    assert detail.startswith("CYPHER_QUERY_UNAVAILABLE:")
    assert "Unknown function" in detail
    assert resp.status_code != 500


def test_similar_issues_without_repository_returns_503() -> None:
    client = TestClient(create_app(repository=None, neo4j_driver=None))

    resp = client.get("/api/v1/ai/similar-issues/a")
    assert resp.status_code == 503, resp.text
    assert "Neo4j not available" in resp.json()["detail"]


def test_similarity_queries_do_not_require_apoc() -> None:
    for name in ("FIND_SIMILAR_ISSUES", "SEARCH_BY_EMBEDDING"):
        query = getattr(queries, name)
        assert "apoc." not in query, f"{name} must not depend on the APOC plugin"
        assert "reduce(" in query, f"{name} must compute cosine natively with reduce()"
