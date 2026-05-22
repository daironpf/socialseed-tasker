"""Integration tests for Neo4jGraphAdapter.

These tests require a running Neo4j instance (via docker compose).
Run with: pytest tests/integration/test_neo4j_adapter_integration.py -v -m integration
"""

import os

import pytest

from socialseed_tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter

NEO4J_URI = os.getenv("TASKER_NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("TASKER_NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("TASKER_NEO4J_PASSWORD", "neoSocial")


@pytest.mark.integration
def test_create_get_delete_node_integration():
    adapter = Neo4jGraphAdapter(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    node_id = adapter.create_node("IntegrationTest", {"x": 1})
    assert isinstance(node_id, str)
    assert len(node_id) > 0

    node = adapter.get_node(node_id)
    assert node is not None
    assert "IntegrationTest" in node.labels

    adapter.delete_node(node_id)
    assert adapter.get_node(node_id) is None
    adapter.close()


@pytest.mark.integration
def test_run_cypher_integration():
    adapter = Neo4jGraphAdapter(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    result = adapter.run_cypher("RETURN 1 AS value")
    assert len(result.records) == 1
    assert result.records[0]["value"] == 1
    adapter.close()


@pytest.mark.integration
def test_get_node_not_found_integration():
    adapter = Neo4jGraphAdapter(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    assert adapter.get_node("non-existent-999") is None
    adapter.close()
