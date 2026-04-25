"""Tests for policy engine."""

import pytest
from uuid import uuid4

from socialseed_tasker.core.project_analysis.policy import (
    Policy,
    PolicyEngine,
    PolicyRule,
    PolicyRuleType,
    PolicyValidationResult,
    PolicyViolation,
)


class TestPolicyRule:
    """Test cases for PolicyRule."""

    def test_create_forbidden_path_rule(self):
        rule = PolicyRule(
            rule_type=PolicyRuleType.FORBIDDEN_PATH,
            from_pattern="component.type:frontend",
            to_pattern="component.type:database",
            description="Frontend cannot directly depend on database",
        )
        assert rule.rule_type == PolicyRuleType.FORBIDDEN_PATH
        assert rule.from_pattern == "component.type:frontend"
        assert rule.to_pattern == "component.type:database"

    def test_create_max_depth_rule(self):
        rule = PolicyRule(
            rule_type=PolicyRuleType.MAX_DEPTH,
            max_depth=3,
            description="Max dependency depth is 3",
        )
        assert rule.rule_type == PolicyRuleType.MAX_DEPTH
        assert rule.max_depth == 3

    def test_create_forbidden_label_dependency_rule(self):
        rule = PolicyRule(
            rule_type=PolicyRuleType.FORBIDDEN_LABEL_DEPENDENCY,
            from_pattern="security,auth",
            to_pattern="test,docs",
            description="Security labels cannot depend on test labels",
        )
        assert rule.rule_type == PolicyRuleType.FORBIDDEN_LABEL_DEPENDENCY
        assert rule.from_pattern == "security,auth"

    def test_policy_rule_is_frozen(self):
        rule = PolicyRule(rule_type=PolicyRuleType.FORBIDDEN_PATH)
        with pytest.raises(Exception):
            rule.from_pattern = "modified"


class TestPolicy:
    """Test cases for Policy."""

    def test_create_policy_with_rules(self):
        rule = PolicyRule(
            rule_type=PolicyRuleType.FORBIDDEN_PATH,
            from_pattern="component.type:frontend",
            to_pattern="component.type:database",
        )
        policy = Policy(
            name="Architecture Policy",
            description="Enforce layered architecture",
            rules=[rule],
            is_active=True,
        )
        assert policy.name == "Architecture Policy"
        assert len(policy.rules) == 1
        assert policy.is_active is True

    def test_policy_is_frozen(self):
        policy = Policy(name="Test Policy")
        with pytest.raises(Exception):
            policy.name = "Modified"

    def test_policy_with_multiple_rules(self):
        rule1 = PolicyRule(
            rule_type=PolicyRuleType.FORBIDDEN_PATH,
            from_pattern="component.type:frontend",
            to_pattern="component.type:database",
        )
        rule2 = PolicyRule(
            rule_type=PolicyRuleType.FORBIDDEN_LABEL_DEPENDENCY,
            from_pattern="security",
            to_pattern="test",
        )
        policy = Policy(name="Test Policy", rules=[rule1, rule2])
        assert len(policy.rules) == 2


class TestPolicyEngine:
    """Test cases for PolicyEngine."""

    def test_create_engine_with_policies(self):
        policy = Policy(name="Test Policy")
        engine = PolicyEngine(policies=[policy])
        assert len(engine.list_policies()) == 1

    def test_add_policy(self):
        engine = PolicyEngine()
        policy = Policy(name="New Policy")
        engine.add_policy(policy)
        assert len(engine.list_policies()) == 1

    def test_remove_policy(self):
        policy = Policy(name="To Remove")
        engine = PolicyEngine(policies=[policy])
        engine.remove_policy(policy.id)
        assert len(engine.list_policies()) == 0

    def test_get_policy(self):
        policy = Policy(name="Test Policy")
        engine = PolicyEngine(policies=[policy])
        retrieved = engine.get_policy(policy.id)
        assert retrieved is not None
        assert retrieved.name == "Test Policy"

    def test_get_nonexistent_policy(self):
        engine = PolicyEngine()
        retrieved = engine.get_policy(uuid4())
        assert retrieved is None

    def test_list_active_policies_only(self):
        active_policy = Policy(name="Active", is_active=True)
        inactive_policy = Policy(name="Inactive", is_active=False)
        engine = PolicyEngine(policies=[active_policy, inactive_policy])
        assert len(engine.list_policies()) == 1

    def test_validate_dependency_with_no_policies(self):
        engine = PolicyEngine()
        result = engine.validate_dependency(
            from_component_name="frontend",
            from_component_type="frontend",
            from_labels=[],
            to_component_name="database",
            to_component_type="database",
            to_labels=[],
        )
        assert result.is_valid is True
        assert len(result.violations) == 0

    def test_validate_dependency_forbidden_path(self):
        policy = Policy(
            name="Layer Architecture",
            is_active=True,
            rules=[
                PolicyRule(
                    rule_type=PolicyRuleType.FORBIDDEN_PATH,
                    from_pattern="component.type:frontend",
                    to_pattern="component.type:database",
                )
            ],
        )
        engine = PolicyEngine(policies=[policy])
        result = engine.validate_dependency(
            from_component_name="web-app",
            from_component_type="frontend",
            from_labels=[],
            to_component_name="db",
            to_component_type="database",
            to_labels=[],
        )
        assert result.is_valid is False
        assert len(result.violations) == 1
        assert result.has_violations is True

    def test_validate_dependency_allowed_path(self):
        policy = Policy(
            name="Layer Architecture",
            is_active=True,
            rules=[
                PolicyRule(
                    rule_type=PolicyRuleType.FORBIDDEN_PATH,
                    from_pattern="component.type:frontend",
                    to_pattern="component.type:database",
                )
            ],
        )
        engine = PolicyEngine(policies=[policy])
        result = engine.validate_dependency(
            from_component_name="api-gateway",
            from_component_type="frontend",
            from_labels=[],
            to_component_name="backend",
            to_component_type="backend",
            to_labels=[],
        )
        assert result.is_valid is True

    def test_validate_dependency_by_component_name(self):
        policy = Policy(
            name="Component Restriction",
            is_active=True,
            rules=[
                PolicyRule(
                    rule_type=PolicyRuleType.FORBIDDEN_PATH,
                    from_pattern="component.name:frontend",
                    to_pattern="component.name:legacy",
                )
            ],
        )
        engine = PolicyEngine(policies=[policy])
        result = engine.validate_dependency(
            from_component_name="frontend",
            from_component_type="app",
            from_labels=[],
            to_component_name="legacy",
            to_component_type="system",
            to_labels=[],
        )
        assert result.is_valid is False

    def test_validate_dependency_by_label(self):
        policy = Policy(
            name="Label Restriction",
            is_active=True,
            rules=[
                PolicyRule(
                    rule_type=PolicyRuleType.FORBIDDEN_PATH,
                    from_pattern="label:security",
                    to_pattern="label:test",
                )
            ],
        )
        engine = PolicyEngine(policies=[policy])
        result = engine.validate_dependency(
            from_component_name="auth",
            from_component_type="service",
            from_labels=["security", "auth"],
            to_component_name="test-runner",
            to_component_type="tool",
            to_labels=["test", "ci"],
        )
        assert result.is_valid is False

    def test_validate_dependency_forbidden_label(self):
        policy = Policy(
            name="Label Dependency",
            is_active=True,
            rules=[
                PolicyRule(
                    rule_type=PolicyRuleType.FORBIDDEN_LABEL_DEPENDENCY,
                    from_pattern="security,auth",
                    to_pattern="test,docs",
                )
            ],
        )
        engine = PolicyEngine(policies=[policy])
        result = engine.validate_dependency(
            from_component_name="auth-service",
            from_component_type="service",
            from_labels=["security"],
            to_component_name="test-runner",
            to_component_type="tool",
            to_labels=["test"],
        )
        assert result.is_valid is False
        assert result.violations[0].rule_type == PolicyRuleType.FORBIDDEN_LABEL_DEPENDENCY

    def test_validate_dependency_allowed_label(self):
        policy = Policy(
            name="Label Dependency",
            is_active=True,
            rules=[
                PolicyRule(
                    rule_type=PolicyRuleType.FORBIDDEN_LABEL_DEPENDENCY,
                    from_pattern="security,auth",
                    to_pattern="test,docs",
                )
            ],
        )
        engine = PolicyEngine(policies=[policy])
        result = engine.validate_dependency(
            from_component_name="auth-service",
            from_component_type="service",
            from_labels=["security"],
            to_component_name="database",
            to_component_type="storage",
            to_labels=["database"],
        )
        assert result.is_valid is True


class TestPolicyValidationResult:
    """Test cases for PolicyValidationResult."""

    def test_valid_result_has_no_violations(self):
        result = PolicyValidationResult(is_valid=True, violations=[])
        assert result.has_violations is False

    def test_invalid_result_has_violations(self):
        violation = PolicyViolation(
            policy_id=uuid4(),
            policy_name="Test Policy",
            rule_type=PolicyRuleType.FORBIDDEN_PATH,
            message="Test violation",
        )
        result = PolicyValidationResult(is_valid=False, violations=[violation])
        assert result.has_violations is True
        assert len(result.violations) == 1
