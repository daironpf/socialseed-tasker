"""Tests for constraint domain models and validation."""

from __future__ import annotations

from uuid import uuid4

import pytest

from socialseed_tasker.core.task_management.constraints import (
    ArchitectureConstraint,
    Constraint,
    ConstraintCategory,
    ConstraintConfig,
    ConstraintLevel,
    ConstraintStatus,
    ConstraintValidationResult,
    ConstraintViolation,
    DependencyConstraint,
    NamingConstraint,
    PatternConstraint,
    TechnologyConstraint,
)


class TestConstraintCategory:
    """Tests for ConstraintCategory enum."""

    def test_category_values(self):
        assert ConstraintCategory.ARCHITECTURE.value == "architecture"
        assert ConstraintCategory.TECHNOLOGY.value == "technology"
        assert ConstraintCategory.NAMING.value == "naming"
        assert ConstraintCategory.PATTERNS.value == "patterns"
        assert ConstraintCategory.DEPENDENCIES.value == "dependencies"


class TestConstraintLevel:
    """Tests for ConstraintLevel enum."""

    def test_level_values(self):
        assert ConstraintLevel.HARD.value == "hard"
        assert ConstraintLevel.SOFT.value == "soft"


class TestConstraintStatus:
    """Tests for ConstraintStatus enum."""

    def test_status_values(self):
        assert ConstraintStatus.ACTIVE.value == "active"
        assert ConstraintStatus.INACTIVE.value == "inactive"
        assert ConstraintStatus.VIOLATED.value == "violated"
        assert ConstraintStatus.COMPLIANT.value == "compliant"


class TestArchitectureConstraint:
    """Tests for ArchitectureConstraint model."""

    def test_create_required_pattern(self):
        constraint = ArchitectureConstraint(
            pattern=r"^class.*\(.*\):$",
            required=True,
            description="Classes should follow camelCase naming",
        )
        assert constraint.pattern == r"^class.*\(.*\):$"
        assert constraint.required is True

    def test_create_forbidden_pattern(self):
        constraint = ArchitectureConstraint(
            pattern=r"global_",
            required=False,
            description="No global variables",
        )
        assert constraint.pattern == r"global_"
        assert constraint.required is False


class TestTechnologyConstraint:
    """Tests for TechnologyConstraint model."""

    def test_create_required_technology(self):
        constraint = TechnologyConstraint(
            service="api-gateway",
            technology="Redis",
            required=True,
            description="API Gateway must use Redis for caching",
        )
        assert constraint.service == "api-gateway"
        assert constraint.technology == "Redis"
        assert constraint.required is True

    def test_create_forbidden_technology(self):
        constraint = TechnologyConstraint(
            service="*",
            technology="DynamoDB",
            required=False,
            description="No DynamoDB allowed",
        )
        assert constraint.service == "*"
        assert constraint.technology == "DynamoDB"
        assert constraint.required is False


class TestNamingConstraint:
    """Tests for NamingConstraint model."""

    def test_create_prefix_constraint(self):
        constraint = NamingConstraint(
            target="classes",
            pattern="^[A-Z][a-z]+$",
            description="Class names should be PascalCase",
        )
        assert constraint.target == "classes"
        assert constraint.pattern == "^[A-Z][a-z]+$"


class TestPatternConstraint:
    """Tests for PatternConstraint model."""

    def test_create_required_pattern(self):
        constraint = PatternConstraint(
            pattern="repository_pattern",
            required=True,
            path="/src/repositories",
            description="Repository pattern required",
        )
        assert constraint.pattern == "repository_pattern"
        assert constraint.required is True
        assert constraint.path == "/src/repositories"

    def test_create_pattern_with_multiple_paths(self):
        constraint = PatternConstraint(
            pattern="test_pattern",
            required=True,
            paths=["/tests/unit", "/tests/integration"],
        )
        assert constraint.paths == ["/tests/unit", "/tests/integration"]


class TestDependencyConstraint:
    """Tests for DependencyConstraint model."""

    def test_create_layer_rule(self):
        constraint = DependencyConstraint(
            from_layer="presentation",
            to_layer="data",
            rule_type="layer_rule",
            description="Presentation layer can only depend on domain",
        )
        assert constraint.from_layer == "presentation"
        assert constraint.to_layer == "data"
        assert constraint.rule_type == "layer_rule"

    def test_create_max_depth_rule(self):
        constraint = DependencyConstraint(
            from_layer="*",
            to_layer="*",
            rule_type="max_depth",
            max_depth=3,
            description="Maximum dependency depth of 3",
        )
        assert constraint.max_depth == 3


class TestConstraint:
    """Tests for Constraint model."""

    def test_create_minimal_constraint(self):
        constraint = Constraint(
            category=ConstraintCategory.ARCHITECTURE,
            level=ConstraintLevel.HARD,
        )
        assert constraint.category == ConstraintCategory.ARCHITECTURE
        assert constraint.level == ConstraintLevel.HARD
        assert constraint.required is True
        assert constraint.status == ConstraintStatus.INACTIVE

    def test_create_full_constraint(self):
        constraint = Constraint(
            category=ConstraintCategory.TECHNOLOGY,
            level=ConstraintLevel.SOFT,
            pattern="Redis",
            service="cache-layer",
            description="Must use Redis for caching",
            status=ConstraintStatus.ACTIVE,
        )
        assert constraint.pattern == "Redis"
        assert constraint.service == "cache-layer"
        assert constraint.description == "Must use Redis for caching"
        assert constraint.status == ConstraintStatus.ACTIVE

    def test_constraint_is_frozen(self):
        constraint = Constraint(
            category=ConstraintCategory.ARCHITECTURE,
            level=ConstraintLevel.HARD,
        )
        with pytest.raises(Exception):
            constraint.description = "changed"

    def test_from_dict_minimal(self):
        data = {"category": "architecture", "level": "hard"}
        constraint = Constraint.from_dict(data)
        assert constraint.category == ConstraintCategory.ARCHITECTURE
        assert constraint.level == ConstraintLevel.HARD

    def test_from_dict_full(self):
        data = {
            "category": "technology",
            "level": "soft",
            "pattern": "DynamoDB",
            "service": "storage",
            "target": "classes",
            "from_layer": "layer1",
            "to_layer": "layer2",
            "rule_type": "layer_rule",
            "max_depth": 5,
            "required": False,
            "description": "Test constraint",
        }
        constraint = Constraint.from_dict(data)
        assert constraint.category == ConstraintCategory.TECHNOLOGY
        assert constraint.level == ConstraintLevel.SOFT
        assert constraint.pattern == "DynamoDB"
        assert constraint.service == "storage"
        assert constraint.max_depth == 5
        assert constraint.required is False
        assert constraint.description == "Test constraint"


class TestConstraintViolation:
    """Tests for ConstraintViolation model."""

    def test_create_violation(self):
        violation = ConstraintViolation(
            constraint_id=uuid4(),
            constraint_description="No global variables allowed",
            level=ConstraintLevel.HARD,
            category=ConstraintCategory.ARCHITECTURE,
            affected_resource="global_config.py",
            message="Global variable found in {resource}",
            suggestion="Use class attributes or dependency injection",
        )
        assert violation.constraint_description == "No global variables allowed"
        assert violation.level == ConstraintLevel.HARD
        assert violation.suggestion == "Use class attributes or dependency injection"


class TestConstraintValidationResult:
    """Tests for ConstraintValidationResult model."""

    def test_valid_result_no_violations(self):
        result = ConstraintValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.has_violations is False
        assert len(result.violations) == 0
        assert len(result.hard_violations) == 0
        assert len(result.soft_violations) == 0

    def test_valid_result_with_violations(self):
        violation = ConstraintViolation(
            constraint_id=uuid4(),
            constraint_description="Test violation",
            level=ConstraintLevel.HARD,
            category=ConstraintCategory.ARCHITECTURE,
            affected_resource="test.py",
            message="Test violation message",
        )
        result = ConstraintValidationResult(
            is_valid=False,
            violations=[violation],
        )
        assert result.is_valid is False
        assert result.has_violations is True
        assert len(result.violations) == 1
        assert len(result.hard_violations) == 1
        assert len(result.soft_violations) == 0

    def test_result_with_mixed_violations(self):
        hard_violation = ConstraintViolation(
            constraint_id=uuid4(),
            constraint_description="Hard violation",
            level=ConstraintLevel.HARD,
            category=ConstraintCategory.TECHNOLOGY,
            affected_resource="test.py",
            message="Hard violation",
        )
        soft_violation = ConstraintViolation(
            constraint_id=uuid4(),
            constraint_description="Soft violation",
            level=ConstraintLevel.SOFT,
            category=ConstraintCategory.NAMING,
            affected_resource="test.py",
            message="Soft violation",
        )
        result = ConstraintValidationResult(
            is_valid=False,
            violations=[hard_violation, soft_violation],
        )
        assert result.has_violations is True
        assert len(result.hard_violations) == 1
        assert len(result.soft_violations) == 1


class TestConstraintConfig:
    """Tests for ConstraintConfig model."""

    def test_create_empty_config(self):
        config = ConstraintConfig()
        assert len(config.architecture) == 0
        assert len(config.technology) == 0
        assert len(config.to_constraints()) == 0

    def test_to_constraints_with_active_constraints(self):
        config = ConstraintConfig(
            active_constraints=[
                {
                    "category": "architecture",
                    "level": "hard",
                    "pattern": "test_pattern",
                },
                {
                    "category": "technology",
                    "level": "soft",
                    "service": "api",
                    "technology": "Redis",
                },
            ]
        )
        constraints = config.to_constraints()
        assert len(constraints) == 2
        assert constraints[0].category == ConstraintCategory.ARCHITECTURE
        assert constraints[1].category == ConstraintCategory.TECHNOLOGY


class TestConstraintEdgeCases:
    """Edge case tests for constraint validation scenarios."""

    def test_constraint_with_empty_pattern(self):
        constraint = Constraint(
            category=ConstraintCategory.PATTERNS,
            level=ConstraintLevel.SOFT,
            pattern="",
        )
        assert constraint.pattern == ""

    def test_constraint_with_empty_description(self):
        constraint = Constraint(
            category=ConstraintCategory.NAMING,
            level=ConstraintLevel.HARD,
            description="",
        )
        assert constraint.description == ""

    def test_constraint_with_none_max_depth(self):
        constraint = DependencyConstraint(
            from_layer="a",
            to_layer="b",
            rule_type="max_depth",
            max_depth=None,
        )
        assert constraint.max_depth is None

    def test_validation_result_with_empty_violations_list(self):
        result = ConstraintValidationResult(
            is_valid=True,
            violations=[],
        )
        assert result.has_violations is False
        assert len(result.hard_violations) == 0
        assert len(result.soft_violations) == 0

    def test_config_with_empty_active_constraints(self):
        config = ConstraintConfig(active_constraints=[])
        constraints = config.to_constraints()
        assert len(constraints) == 0


class TestConstraintCombinations:
    """Tests for constraint rule combination scenarios."""

    def test_multiple_constraints_different_categories(self):
        constraints = [
            Constraint(
                id=uuid4(),
                category=ConstraintCategory.ARCHITECTURE,
                level=ConstraintLevel.HARD,
                pattern="layered",
                description="Layered architecture",
            ),
            Constraint(
                id=uuid4(),
                category=ConstraintCategory.TECHNOLOGY,
                level=ConstraintLevel.HARD,
                service="api",
                technology="Redis",
                description="Use Redis for caching",
            ),
            Constraint(
                id=uuid4(),
                category=ConstraintCategory.NAMING,
                level=ConstraintLevel.SOFT,
                target="classes",
                pattern="PascalCase",
                description="Class naming convention",
            ),
        ]
        assert len(constraints) == 3
        assert constraints[0].category == ConstraintCategory.ARCHITECTURE
        assert constraints[1].category == ConstraintCategory.TECHNOLOGY
        assert constraints[2].category == ConstraintCategory.NAMING

    def test_multiple_constraints_same_category(self):
        constraints = [
            Constraint(
                id=uuid4(),
                category=ConstraintCategory.ARCHITECTURE,
                level=ConstraintLevel.HARD,
                pattern="pattern1",
                description="Pattern 1",
            ),
            Constraint(
                id=uuid4(),
                category=ConstraintCategory.ARCHITECTURE,
                level=ConstraintLevel.SOFT,
                pattern="pattern2",
                description="Pattern 2",
            ),
        ]
        assert len(constraints) == 2
        assert all(c.category == ConstraintCategory.ARCHITECTURE for c in constraints)

    def test_validation_result_with_many_violations(self):
        violations = [
            ConstraintViolation(
                constraint_id=uuid4(),
                constraint_description=f"Violation {i}",
                level=ConstraintLevel.HARD if i % 2 == 0 else ConstraintLevel.SOFT,
                category=ConstraintCategory.ARCHITECTURE,
                affected_resource=f"file_{i}.py",
                message=f"Violation message {i}",
            )
            for i in range(10)
        ]
        result = ConstraintValidationResult(
            is_valid=False,
            violations=violations,
        )
        assert len(result.violations) == 10
        assert len(result.hard_violations) == 5
        assert len(result.soft_violations) == 5