Domain Test Suite

Purpose:
- Validate domain logic without infrastructure.
- Ensure deterministic behavior of impact analysis and agent context generation.
- Provide fast, isolated tests for autonomous agents.

Components:
- FakeGraphRepository: in-memory dependency graph.
- FakeIssueRepository: in-memory issue store.
- FakeParser: deterministic parser stub.

Tests:
- test_impact_analysis.py: validates dependency traversal and cycles.
- test_generate_agent_context_domain_only.py: validates context generation logic.
