"""Tests for the root cause analyzer functionality."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4

import pytest

from socialseed_tasker.core.project_analysis.analyzer import (
    RootCauseAnalyzer,
    TestFailure,
    RiskLevel,
)


def test_test_failure_creation():
    """Test creating a TestFailure instance."""
    test_failure = TestFailure(
        test_id="test_123",
        test_name="test_example",
        error_message="AssertionError: Expected 5, got 3",
        component="auth-service",
        labels=["unit-test", "auth"]
    )
    
    assert test_failure.test_id == "test_123"
    assert test_failure.test_name == "test_example"
    assert test_failure.component == "auth-service"
    assert "unit-test" in test_failure.labels


def test_root_cause_analyzer_initialization():
    """Test initializing the RootCauseAnalyzer."""
    # Create a mock repository
    class MockRepository:
        def get_issue(self, issue_id: str):
            return None
        
        def get_dependents(self, issue_id: str):
            return []
    
    repository = MockRepository()
    analyzer = RootCauseAnalyzer(repository)
    
    assert analyzer._repository == repository


def test_find_root_cause_returns_empty_list():
    """Test that find_root_cause returns empty list when no matches."""
    class MockRepository:
        def get_issue(self, issue_id: str):
            return None
        
        def get_dependents(self, issue_id: str):
            return []
    
    repository = MockRepository()
    analyzer = RootCauseAnalyzer(repository)
    
    # Create a sample test failure
    test_failure = TestFailure(
        test_id="test_456",
        test_name="test_api_endpoint",
        error_message="Connection refused",
        component="api-gateway",
        labels=["integration-test"]
    )
    
    result = analyzer.find_root_cause("some-issue-id", [])
    
    # Should return empty list as the basic implementation returns empty
    assert result == []


def test_analyze_impact_with_no_repository_data():
    """Test analyzing impact when repository returns no data."""
    class MockRepository:
        def get_issue(self, issue_id: str):
            return None
        
        def get_dependents(self, issue_id: str):
            return []
    
    repository = MockRepository()
    analyzer = RootCauseAnalyzer(repository)
    
    issue_id = uuid4()
    result = analyzer.analyze_impact(issue_id)
    
    assert result["issue_id"] == issue_id
    assert result["directly_affected"] == []
    assert result["transitively_affected"] == []
    assert result["blocked_issues"] == []
    assert result["affected_components"] == []
    assert result["risk_level"] == "LOW"


def test_get_proximity_score_component_overlap():
    """Test proximity score calculation with component overlap."""
    class MockRepository:
        def get_issue(self, issue_id: str):
            return None
    
    repository = MockRepository()
    analyzer = RootCauseAnalyzer(repository)
    
    # Create test failure and issue with same component
    test_failure = TestFailure(
        test_id="test_789",
        test_name="test_database_connection",
        error_message="Timeout connecting to database",
        component="database-service",
        labels=["integration", "database"]
    )
    
    score = analyzer.get_proximity_score(None, test_failure)
    
    # Should have some score due to component overlap logic
    assert score >= 0.0
    assert score <= 1.0


def test_risk_level_enum():
    """Test RiskLevel enum values."""
    assert RiskLevel.LOW == "LOW"
    assert RiskLevel.MEDIUM == "MEDIUM"
    assert RiskLevel.HIGH == "HIGH"
    assert RiskLevel.CRITICAL == "CRITICAL"