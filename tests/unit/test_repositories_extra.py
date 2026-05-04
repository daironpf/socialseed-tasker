"""Unit tests for repositories module."""

import pytest
from unittest.mock import MagicMock, patch


class TestRepositoriesModule:
    """Tests for repositories module."""

    def test_neo4j_task_repository_exists(self):
        """Test Neo4jTaskRepository class exists."""
        from socialseed_tasker.storage.graph_database.repositories import Neo4jTaskRepository

        assert Neo4jTaskRepository is not None

    

    def test_queries_module_exists(self):
        """Test QUERIES module exists."""
        from socialseed_tasker.storage.graph_database import queries

        assert queries is not None


class TestRepositoryQueries:
    """Tests for repository queries."""

    


class TestNeo4jTaskRepositoryInit:
    """Tests for Neo4jTaskRepository initialization."""

    def test_can_instantiate_with_mock_driver(self):
        """Test Neo4jTaskRepository can be instantiated."""
        from socialseed_tasker.storage.graph_database.repositories import Neo4jTaskRepository

        mock_driver = MagicMock()
        mock_driver.driver = MagicMock()
        mock_driver.database = "neo4j"

        repo = Neo4jTaskRepository(mock_driver)
        assert repo is not None


class TestTaskRepositoryInterface:
    """Tests for TaskRepositoryInterface."""

    def test_interface_has_required_methods(self):
        """Test interface has all required methods."""
        from socialseed_tasker.core.task_management.actions import TaskRepositoryInterface
        import inspect

        methods = [m for m in dir(TaskRepositoryInterface) if not m.startswith('_')]
        expected = ['create_issue', 'get_issue', 'update_issue', 'close_issue', 
                    'delete_issue', 'list_issues', 'create_component', 'get_component',
                    'list_components', 'update_component', 'delete_component',
                    'add_dependency', 'get_dependencies', 'remove_dependency']

        for method in expected:
            assert method in methods, f"Missing method: {method}"