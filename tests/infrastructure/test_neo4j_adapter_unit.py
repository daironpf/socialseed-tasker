"""Unit tests for Neo4jGraphAdapter using mocked driver."""

from unittest.mock import MagicMock, patch

from socialseed_tasker.application.ports import NodeRecord, QueryResult
from socialseed_tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter


def make_driver_mock(single_record=None, records=None):
    session = MagicMock()
    run = MagicMock()
    run.single.return_value = single_record
    if records is not None:
        run.__iter__.return_value = iter(records)
    session.run.return_value = run
    driver = MagicMock()
    driver.session.return_value.__enter__.return_value = session
    driver.session.return_value.__exit__.return_value = None
    return driver, session, run


@patch("socialseed_tasker.infrastructure.neo4j_adapter.GraphDatabase.driver")
def test_create_node_success(driver_factory_mock):
    driver, session, run = make_driver_mock(single_record={"id": "abc-123"})
    driver_factory_mock.return_value = driver
    adapter = Neo4jGraphAdapter()
    node_id = adapter.create_node("Test", {"k": "v"})
    assert node_id == "abc-123"


@patch("socialseed_tasker.infrastructure.neo4j_adapter.GraphDatabase.driver")
def test_get_node_not_found(driver_factory_mock):
    driver, session, run = make_driver_mock(single_record=None)
    driver_factory_mock.return_value = driver
    adapter = Neo4jGraphAdapter()
    assert adapter.get_node("999") is None


@patch("socialseed_tasker.infrastructure.neo4j_adapter.GraphDatabase.driver")
def test_get_node_found(driver_factory_mock):
    mock_rec = {"labels": ["Person"], "props": {"name": "Alice"}}
    driver, session, run = make_driver_mock(single_record=mock_rec)
    driver_factory_mock.return_value = driver
    adapter = Neo4jGraphAdapter()
    node = adapter.get_node("abc-123")
    assert isinstance(node, NodeRecord)
    assert node.id == "abc-123"
    assert node.labels == ["Person"]
    assert node.properties == {"name": "Alice"}


@patch("socialseed_tasker.infrastructure.neo4j_adapter.GraphDatabase.driver")
def test_run_cypher_returns_query_result(driver_factory_mock):
    mock_records = [{"n": {"name": "Alice"}}, {"n": {"name": "Bob"}}]
    driver, session, run = make_driver_mock(records=mock_records)
    driver_factory_mock.return_value = driver
    adapter = Neo4jGraphAdapter()
    result = adapter.run_cypher("MATCH (n) RETURN n")
    assert isinstance(result, QueryResult)
    assert len(result.records) == 2


@patch("socialseed_tasker.infrastructure.neo4j_adapter.GraphDatabase.driver")
def test_delete_node_no_op(driver_factory_mock):
    driver, session, run = make_driver_mock()
    driver_factory_mock.return_value = driver
    adapter = Neo4jGraphAdapter()
    adapter.delete_node("abc-123")
    assert True  # no exception means success


@patch("socialseed_tasker.infrastructure.neo4j_adapter.GraphDatabase.driver")
def test_close_releases_driver(driver_factory_mock):
    driver, session, run = make_driver_mock()
    driver_factory_mock.return_value = driver
    adapter = Neo4jGraphAdapter()
    adapter.close()
    driver.close.assert_called_once()
