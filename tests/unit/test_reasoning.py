"""Unit tests for AI Reasoning feature."""

from __future__ import annotations

import pytest
from socialseed_tasker.core.task_management.entities import (
    DecisionType,
    ReasoningNode,
    ReasoningFeedback,
)


class TestDecisionType:
    """Tests for DecisionType enum."""

    def test_decision_types(self):
        """Test all decision types are defined."""
        assert DecisionType.SOLUTION_SELECTION.value == "solution_selection"
        assert DecisionType.ARCHITECTURE_CHOICE.value == "architecture_choice"
        assert DecisionType.PRIORITY_DECISION.value == "priority_decision"


class TestReasoningNode:
    """Tests for ReasoningNode entity."""

    def test_create_reasoning_node(self):
        """Test creating a reasoning node."""
        reasoning = ReasoningNode(
            thought="Using buffer strategy for async handling",
            confidence=0.85,
        )

        assert reasoning.thought == "Using buffer strategy for async handling"
        assert reasoning.confidence == 0.85
        assert reasoning.id is not None

    def test_confidence_bounds(self):
        """Test confidence must be between 0 and 1."""
        with pytest.raises(Exception):
            ReasoningNode(thought="test", confidence=1.5)

        with pytest.raises(Exception):
            ReasoningNode(thought="test", confidence=-0.5)

    def test_with_decision(self):
        """Test creating reasoning with decision."""
        reasoning = ReasoningNode(
            thought="Considering options",
            confidence=0.7,
            decision="choose option A",
            decision_type=DecisionType.SOLUTION_SELECTION,
        )

        assert reasoning.decision == "choose option A"
        assert reasoning.decision_type == DecisionType.SOLUTION_SELECTION

    def test_with_alternatives(self):
        """Test creating reasoning with alternatives."""
        reasoning = ReasoningNode(
            thought="Analyzing approaches",
            confidence=0.8,
            alternatives_considered=["option A", "option B", "option C"],
            rejected_reasons=["too complex", "out of scope"],
        )

        assert len(reasoning.alternatives_considered) == 3
        assert len(reasoning.rejected_reasons) == 2


class TestReasoningFeedback:
    """Tests for ReasoningFeedback entity."""

    def test_create_feedback(self):
        """Test creating feedback."""
        feedback = ReasoningFeedback(
            reasoning_id="550e8400-e29b-41d4-a716-446655440000",
            is_approved=True,
            feedback_text="Good decision",
        )

        assert feedback.is_approved is True
        assert feedback.feedback_text == "Good decision"
        assert feedback.id is not None

    def test_disapproval(self):
        """Test disapproval feedback."""
        feedback = ReasoningFeedback(
            reasoning_id="550e8400-e29b-41d4-a716-446655440000",
            is_approved=False,
        )

        assert feedback.is_approved is False