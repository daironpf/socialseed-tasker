"""Tests for markdown transformer service."""

import pytest
from socialseed_tasker.core.services.markdown_transformer import (
    MarkdownTransformer,
    MarkdownTable,
    transform_root_cause_markdown,
    transform_impact_markdown,
    transform_dependencies_markdown,
    get_markdown_transformer,
)


class TestMarkdownTable:
    """Test cases for MarkdownTable class."""

    def test_empty_headers_returns_empty_string(self):
        """Should return empty string when no headers."""
        table = MarkdownTable(headers=[], rows=[])
        result = table.to_markdown()
        assert result == ""

    def test_single_row_table(self):
        """Should format single row table correctly."""
        table = MarkdownTable(
            headers=["Name", "Value"],
            rows=[["Test", "100"]],
        )
        result = table.to_markdown()
        assert "Name" in result
        assert "Value" in result
        assert "Test" in result
        assert "100" in result

    def test_multiple_rows(self):
        """Should format multiple rows correctly."""
        table = MarkdownTable(
            headers=["Col1", "Col2"],
            rows=[["A", "B"], ["C", "D"]],
        )
        result = table.to_markdown()
        lines = result.split("\n")
        assert len(lines) == 4


class TestMarkdownTransformerEscape:
    """Test cases for Markdown escaping."""

    def test_escape_asterisk(self):
        """Should escape asterisks."""
        result = MarkdownTransformer._escape("test*value")
        assert "\\*" in result

    def test_escape_backtick(self):
        """Should escape backticks."""
        result = MarkdownTransformer._escape("test`value")
        assert "\\`" in result

    def test_escape_underscore(self):
        """Should escape underscores."""
        result = MarkdownTransformer._escape("test_value")
        assert "\\_" in result

    def test_escape_brackets(self):
        """Should escape square brackets."""
        result = MarkdownTransformer._escape("[test]")
        assert "\\[" in result

    def test_handles_non_string(self):
        """Should convert non-string to string."""
        result = MarkdownTransformer._escape(123)
        assert result == "123"


class TestTransformRootCause:
    """Test cases for root cause transformation."""

    def test_empty_cause_returns_no_candidates_message(self):
        """Should return message when no causal links."""
        result = MarkdownTransformer.transform_root_cause([])
        assert "No root cause candidates found" in result

    def test_single_causal_link(self):
        """Should format single causal link."""
        causal_links = [
            {
                "issue": {
                    "issue_number": 123,
                    "title": "Fix authentication bug",
                },
                "score": 0.85,
                "reasons": ["Same component", "Closed recently"],
            }
        ]
        result = MarkdownTransformer.transform_root_cause(causal_links)
        assert "123" in result
        assert "0.85" in result
        assert "Same component" in result

    def test_multiple_causal_links(self):
        """Should format multiple causal links."""
        causal_links = [
            {
                "issue": {"issue_number": 1, "title": "Fix 1"},
                "score": 0.9,
                "reasons": ["Reason A"],
            },
            {
                "issue": {"issue_number": 2, "title": "Fix 2"},
                "score": 0.5,
                "reasons": ["Reason B"],
            },
        ]
        result = MarkdownTransformer.transform_root_cause(causal_links)
        assert "1" in result
        assert "2" in result

    def test_escapes_special_characters(self):
        """Should escape special Markdown characters in titles."""
        causal_links = [
            {
                "issue": {
                    "issue_number": 100,
                    "title": "Fix *critical* bug",
                },
                "score": 0.7,
                "reasons": ["Test"],
            }
        ]
        result = MarkdownTransformer.transform_root_cause(causal_links)
        assert "\\*" in result


class TestTransformImpact:
    """Test cases for impact analysis transformation."""

    def test_empty_impact_returns_no_data_message(self):
        """Should return message when no impact data."""
        result = MarkdownTransformer.transform_impact({})
        assert "No impact analysis data" in result

    def test_impact_with_affected_issues(self):
        """Should format impact with Mermaid diagram."""
        impact = {
            "issue_id": "123",
            "affected_issues": [
                {"issue_number": 124, "title": "Dep 1"},
                {"issue_number": 125, "title": "Dep 2"},
            ],
            "dependents": [],
            "risk_level": "high",
        }
        result = MarkdownTransformer.transform_impact(impact)
        assert "mermaid" in result
        assert "graph TD" in result
        assert "high" in result

    def test_impact_risk_critical(self):
        """Should show critical risk warning."""
        impact = {
            "issue_id": "1",
            "affected_issues": [{"issue_number": 2, "title": "Dep"}],
            "dependents": [],
            "risk_level": "critical",
        }
        result = MarkdownTransformer.transform_impact(impact)
        assert "critical" in result
        assert "Immediate action required" in result

    def test_impact_risk_high(self):
        """Should show high risk review suggestion."""
        impact = {
            "issue_id": "1",
            "affected_issues": [],
            "dependents": [{"issue_number": 2, "title": "Dep"}],
            "risk_level": "high",
        }
        result = MarkdownTransformer.transform_impact(impact)
        assert "high" in result
        assert "Review within 24h" in result


class TestTransformDependencies:
    """Test cases for dependency chain transformation."""

    def test_empty_dependencies_returns_no_deps_message(self):
        """Should return message when no dependencies."""
        result = MarkdownTransformer.transform_dependencies([])
        assert "No dependencies" in result

    def test_forward_direction(self):
        """Should format forward dependencies."""
        deps = [
            {"source_number": 1, "target_number": 2},
        ]
        result = MarkdownTransformer.transform_dependencies(deps, direction="forward")
        assert "mermaid" in result
        assert "graph LR" in result

    def test_backward_direction(self):
        """Should format backward dependencies."""
        deps = [
            {"source_number": 1, "target_number": 2},
        ]
        result = MarkdownTransformer.transform_dependencies(deps, direction="backward")
        assert "mermaid" in result
        assert "graph LR" in result


class TestTransformComponentImpact:
    """Test cases for component impact transformation."""

    def test_empty_component_impact(self):
        """Should handle empty component impact."""
        result = MarkdownTransformer.transform_component_impact({})
        assert "Component:" in result

    def test_with_statistics(self):
        """Should include statistics in output."""
        impact = {
            "component_id": "auth-service",
            "statistics": {
                "open_issues": 5,
                "total_dependencies": 10,
                "average_priority": "high",
            },
            "issues": [],
        }
        result = MarkdownTransformer.transform_component_impact(impact)
        assert "auth\\-service" in result
        assert "5" in result
        assert "10" in result

    def test_with_issues_list(self):
        """Should include issues table when present."""
        impact = {
            "component_id": "api",
            "statistics": {},
            "issues": [
                {"issue_number": 1, "title": "Bug 1", "priority": "high", "status": "open"},
                {"issue_number": 2, "title": "Bug 2", "priority": "medium", "status": "open"},
            ],
        }
        result = MarkdownTransformer.transform_component_impact(impact)
        assert "Issue" in result
        assert "Priority" in result
        assert "Status" in result


class TestTransformFullAnalysis:
    """Test cases for complete analysis transformation."""

    def test_empty_analysis_returns_no_data_message(self):
        """Should return message when no data."""
        result = MarkdownTransformer.transform_full_analysis()
        assert "No analysis data" in result

    def test_with_all_sections(self):
        """Should include all sections when provided."""
        root_cause = [{"issue": {"issue_number": 1, "title": "Fix"}, "score": 0.8, "reasons": ["Test"]}]
        impact = {"issue_id": "1", "affected_issues": [], "dependents": [], "risk_level": "low"}
        deps = [{"source_number": 1, "target_number": 2}]

        result = MarkdownTransformer.transform_full_analysis(
            root_cause=root_cause,
            impact=impact,
            dependencies=deps,
        )

        assert "Root Cause Analysis" in result
        assert "Impact Analysis" in result
        assert "Dependency Chain" in result

    def test_partial_analysis(self):
        """Should include only provided sections."""
        impact = {"issue_id": "1", "affected_issues": [], "dependents": [], "risk_level": "low"}

        result = MarkdownTransformer.transform_full_analysis(impact=impact)

        assert "Impact Analysis" in result
        assert "Root Cause Analysis" not in result


class TestStandaloneFunctions:
    """Test cases for standalone transform functions."""

    def test_transform_root_cause_markdown(self):
        """Should use standalone function."""
        result = transform_root_cause_markdown([])
        assert "No root cause" in result

    def test_transform_impact_markdown(self):
        """Should use standalone function."""
        result = transform_impact_markdown({})
        assert "No impact" in result

    def test_transform_dependencies_markdown(self):
        """Should use standalone function."""
        result = transform_dependencies_markdown([])
        assert "No dependencies" in result


class TestGetMarkdownTransformerSingleton:
    """Test cases for get_markdown_transformer singleton."""

    def test_returns_same_instance(self):
        """Should return the same instance on multiple calls."""
        transformer1 = get_markdown_transformer()
        transformer2 = get_markdown_transformer()
        assert transformer1 is transformer2
