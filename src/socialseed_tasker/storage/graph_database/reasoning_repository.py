"""Reasoning repository for storing agent reasoning in Neo4j.

Pattern: (Agent)-[:THOUGHT]->(ReasoningNode)-[:DECIDED]->(Issue)
"""

from __future__ import annotations

import logging
from typing import Any

from socialseed_tasker.core.task_management.entities import (
    DecisionType,
    ReasoningFeedback,
    ReasoningNode,
)

logger = logging.getLogger(__name__)


REASONING_QUERIES = {
    "create_reasoning": """
        MERGE (i:Issue {id: $issue_id})
        MERGE (r:ReasoningNode {id: $id})
        SET r.thought = $thought,
            r.confidence = $confidence,
            r.alternatives_considered = $alternatives_considered,
            r.rejected_reasons = $rejected_reasons,
            r.decision = $decision,
            r.decision_type = $decision_type,
            r.created_at = timestamp()
        WITH r, i
        MERGE (a:Agent {id: $agent_id})
        SET a.name = $agent_name
        MERGE (a)-[:THOUGHT {timestamp: timestamp()}]->(r)
        MERGE (r)-[:DECIDED]->(i)
        RETURN r
    """,
    "get_reasoning_by_issue": """
        MATCH (a:Agent)-[:THOUGHT]->(r:ReasoningNode)-[:DECIDED]->(i:Issue {id: $issue_id})
        RETURN r.id as id, r.thought as thought, r.confidence as confidence,
               r.alternatives_considered as alternatives, r.rejected_reasons as rejected,
               r.decision as decision, r.decision_type as decision_type,
               r.created_at as created_at,
               a.id as agent_id, a.name as agent_name
        ORDER BY r.created_at DESC
        LIMIT $limit
    """,
    "get_reasoning_history": """
        MATCH (a:Agent)-[:THOUGHT]->(r:ReasoningNode)-[:DECIDED]->(i:Issue)
        RETURN r.id as id, r.thought as thought, r.confidence as confidence,
               r.decision as decision, r.decision_type as decision_type,
               r.created_at as created_at, i.id as issue_id, i.title as issue_title,
               a.id as agent_id, a.name as agent_name
        ORDER BY r.created_at DESC
        LIMIT $limit
    """,
    "add_feedback": """
        MERGE (f:ReasoningFeedback {id: $id})
        SET f.is_approved = $is_approved,
            f.feedback_text = $feedback_text,
            f.created_at = timestamp()
        WITH f
        MATCH (r:ReasoningNode {id: $reasoning_id})
        MERGE (f)-[:FEEDS_BACK]->(r)
        RETURN f
    """,
    "get_feedback": """
        MATCH (f:ReasoningFeedback)-[:FEEDS_BACK]->(r:ReasoningNode {id: $reasoning_id})
        RETURN f.id as id, f.is_approved as is_approved, 
               f.feedback_text as feedback_text, f.created_at as created_at
    """,
    "get_decision_stats": """
        MATCH (r:ReasoningNode)
        RETURN r.decision_type as decision_type, count(r) as count,
               avg(r.confidence) as avg_confidence
    """,
    "delete_reasoning_by_issue": """
        MATCH (a:Agent)-[t:THOUGHT]->(r:ReasoningNode)-[d:DECIDED]->(i:Issue {id: $issue_id})
        OPTIONAL MATCH (f:ReasoningFeedback)-[:FEEDS_BACK]->(r)
        DETACH DELETE r, f
    """,
    "clear_all_reasoning": """
        MATCH (r:ReasoningNode)
        OPTIONAL MATCH (f:ReasoningFeedback)-[:FEEDS_BACK]->(r)
        DETACH DELETE r, f
    """,
}


class ReasoningRepository:
    """Repository for storing and retrieving agent reasoning."""

    def __init__(self, driver: Any):
        """Initialize reasoning repository.

        Args:
            driver: Neo4j driver wrapper
        """
        self._driver = driver

    def _get_session(self):
        """Get Neo4j session."""
        if hasattr(self._driver, "driver"):
            return self._driver.driver.session(database=self._driver.database)
        return self._driver.session(database="neo4j")

    def log_reasoning(
        self,
        issue_id: str,
        agent_id: str,
        agent_name: str,
        reasoning: ReasoningNode,
    ) -> str:
        """Log agent reasoning for an issue.

        Args:
            issue_id: The issue being reasoned about
            agent_id: The agent making the decision
            agent_name: The agent's display name
            reasoning: The reasoning node

        Returns:
            Reasoning node ID
        """
        with self._get_session() as session:
            result = session.run(
                REASONING_QUERIES["create_reasoning"],
                {
                    "id": reasoning.id,
                    "issue_id": issue_id,
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "thought": reasoning.thought,
                    "confidence": reasoning.confidence,
                    "alternatives_considered": reasoning.alternatives_considered,
                    "rejected_reasons": reasoning.rejected_reasons,
                    "decision": reasoning.decision,
                    "decision_type": reasoning.decision_type.value,
                },
            )
            record = result.single()
            return record["r"]["id"] if record else None

    def get_reasoning_by_issue(
        self, issue_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get reasoning history for an issue.

        Args:
            issue_id: The issue ID
            limit: Maximum results

        Returns:
            List of reasoning entries
        """
        with self._get_session() as session:
            result = session.run(
                REASONING_QUERIES["get_reasoning_by_issue"],
                {"issue_id": issue_id, "limit": limit},
            )
            return [
                {
                    "id": record["id"],
                    "thought": record["thought"],
                    "confidence": record["confidence"],
                    "alternatives": record["alternatives"],
                    "rejected": record["rejected"],
                    "decision": record["decision"],
                    "decision_type": record["decision_type"],
                    "context": record["context"],
                    "created_at": record["created_at"],
                    "agent_id": record["agent_id"],
                    "agent_name": record["agent_name"],
                }
                for record in result
            ]

    def get_reasoning_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get global reasoning history.

        Args:
            limit: Maximum results

        Returns:
            List of all reasoning entries
        """
        with self._get_session() as session:
            result = session.run(
                REASONING_QUERIES["get_reasoning_history"],
                {"limit": limit},
            )
            return [
                {
                    "id": record["id"],
                    "thought": record["thought"],
                    "confidence": record["confidence"],
                    "decision": record["decision"],
                    "decision_type": record["decision_type"],
                    "created_at": record["created_at"],
                    "issue_id": record["issue_id"],
                    "issue_title": record["issue_title"],
                    "agent_id": record["agent_id"],
                    "agent_name": record["agent_name"],
                }
                for record in result
            ]

    def add_feedback(self, feedback: ReasoningFeedback, reasoning_id: str) -> str:
        """Add human feedback to reasoning.

        Args:
            feedback: The feedback
            reasoning_id: The reasoning being feedbacked

        Returns:
            Feedback ID
        """
        with self._get_session() as session:
            result = session.run(
                REASONING_QUERIES["add_feedback"],
                {
                    "id": feedback.id,
                    "reasoning_id": reasoning_id,
                    "is_approved": feedback.is_approved,
                    "feedback_text": feedback.feedback_text,
                },
            )
            record = result.single()
            return record["f"]["id"] if record else None

    def get_feedback(self, reasoning_id: str) -> list[dict[str, Any]]:
        """Get feedback for a reasoning.

        Args:
            reasoning_id: The reasoning ID

        Returns:
            List of feedback entries
        """
        with self._get_session() as session:
            result = session.run(
                REASONING_QUERIES["get_feedback"],
                {"reasoning_id": reasoning_id},
            )
            return [
                {
                    "id": record["id"],
                    "is_approved": record["is_approved"],
                    "feedback_text": record["feedback_text"],
                    "created_at": record["created_at"],
                }
                for record in result
            ]

    def get_decision_stats(self) -> dict[str, Any]:
        """Get decision statistics.

        Returns:
            Statistics by decision type
        """
        with self._get_session() as session:
            result = session.run(REASONING_QUERIES["get_decision_stats"])
            stats = {}
            for record in result:
                stats[record["decision_type"]] = {
                    "count": record["count"],
                    "avg_confidence": record["avg_confidence"],
                }
            return stats

    def delete_by_issue(self, issue_id: str) -> None:
        """Delete reasoning for an issue."""
        with self._get_session() as session:
            session.run(
                REASONING_QUERIES["delete_reasoning_by_issue"],
                {"issue_id": issue_id},
            )

    def clear_all(self) -> None:
        """Clear all reasoning data."""
        with self._get_session() as session:
            session.run(REASONING_QUERIES["clear_all_reasoning"])