"""Unit tests for RAG repository."""

import pytest
from unittest.mock import MagicMock


class TestRAGRepositoryInit:
    """Basic tests for RAG repository module."""

    def test_rag_queries_exist(self):
        """Test that RAG_QUERIES dictionary exists and has expected keys."""
        from socialseed_tasker.infrastructure.neo4j_rag_repository import RAG_QUERIES

        expected_keys = [
            "create_embedding_node",
            "create_vector_index",
            "search_similar_vector",
            "search_by_source",
            "delete_by_source",
            "count_embeddings",
            "get_stats",
        ]
        for key in expected_keys:
            assert key in RAG_QUERIES

    def test_rag_queries_contain_cypher(self):
        """Test that queries contain Cypher keywords."""
        from socialseed_tasker.infrastructure.neo4j_rag_repository import RAG_QUERIES

        assert "MERGE" in RAG_QUERIES["create_embedding_node"]
        assert "CALL db.index.vector" in RAG_QUERIES["search_similar_vector"]
        assert "MATCH" in RAG_QUERIES["search_by_source"]

    def test_rag_repository_class_exists(self):
        """Test RAGRepository class can be instantiated with mock."""
        from socialseed_tasker.infrastructure.neo4j_rag_repository import RAGRepository

        mock_driver = MagicMock()
        mock_driver.driver = MagicMock()
        mock_driver.database = "neo4j"

        repo = RAGRepository(mock_driver)
        assert repo is not None

    def test_rag_repository_has_embedding_service(self):
        """Test RAGRepository has embedding service."""
        from socialseed_tasker.infrastructure.neo4j_rag_repository import RAGRepository

        mock_driver = MagicMock()
        mock_driver.driver = MagicMock()
        mock_driver.database = "neo4j"

        repo = RAGRepository(mock_driver)
        assert hasattr(repo, "_embedding_service")


class TestReasoningRepositoryInit:
    """Basic tests for Reasoning repository module."""

    def test_reasoning_queries_exist(self):
        """Test that REASONING_QUERIES dictionary exists."""
        from socialseed_tasker.infrastructure.neo4j_reasoning_repository import REASONING_QUERIES

        expected_keys = [
            "create_reasoning",
            "get_reasoning_by_issue",
            "get_reasoning_history",
            "add_feedback",
            "get_feedback",
            "get_decision_stats",
            "delete_reasoning_by_issue",
            "clear_all_reasoning",
        ]
        for key in expected_keys:
            assert key in REASONING_QUERIES

    def test_reasoning_queries_contain_cypher(self):
        """Test that queries contain Cypher patterns."""
        from socialseed_tasker.infrastructure.neo4j_reasoning_repository import REASONING_QUERIES

        assert "MATCH" in REASONING_QUERIES["get_reasoning_by_issue"]
        assert "THOUGHT" in REASONING_QUERIES["create_reasoning"]
        assert "MERGE" in REASONING_QUERIES["add_feedback"]

    def test_reasoning_repository_class_exists(self):
        """Test ReasoningRepository class can be instantiated."""
        from socialseed_tasker.infrastructure.neo4j_reasoning_repository import ReasoningRepository

        mock_driver = MagicMock()
        mock_driver.driver = MagicMock()
        mock_driver.database = "neo4j"

        repo = ReasoningRepository(mock_driver)
        assert repo is not None