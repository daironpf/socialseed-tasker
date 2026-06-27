import pytest
from unittest.mock import patch, MagicMock
from socialseed_tasker.workers.tasks import parse_and_index_files, batch_embed_and_store, run_graph_analysis

@patch("socialseed_tasker.workers.tasks.create_celery")
def test_parse_and_index_files_calls_parser(mock_create):
    with patch("socialseed_tasker.workers.tasks.build_default_container") as mock_build:
        parser = MagicMock()
        parser.parse_file.return_value = {"type": "root", "children": []}
        parser.extract_symbols.return_value = []
        mock_build.return_value = MagicMock(parser=parser)
        res = parse_and_index_files(["/no/such/file.py"])
        assert "parsed" in res

def test_batch_embed_and_store_persists(tmp_path):
    docs = [{"id": "d1", "text": "hello"}]
    res = batch_embed_and_store(docs, "testkey")
    assert res.get("stored") == 1

@patch("socialseed_tasker.workers.tasks.Neo4jGraphAdapter")
def test_run_graph_analysis_calls_repo(mock_graph):
    mock_graph.return_value = MagicMock()
    with patch("socialseed_tasker.workers.tasks.Neo4jGraphRepository") as mock_repo_cls:
        mock_repo = MagicMock()
        mock_repo.find_impact_set.return_value = ["a", "b"]
        mock_repo_cls.return_value = mock_repo
        res = run_graph_analysis("issue-x", 2)
        assert "impact_set" in res
