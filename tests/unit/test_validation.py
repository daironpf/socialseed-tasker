"""Unit tests for validation module."""

import pytest

from socialseed_tasker.core.validation import (
    ComponentNameValidationError,
    IssueDescriptionValidationError,
    IssueTitleValidationError,
    sanitize_component_name,
    sanitize_input,
    sanitize_issue_description,
    sanitize_issue_title,
    validate_component_name,
    validate_issue_description,
    validate_issue_title,
)


class TestValidateComponentName:
    def test_valid_name(self):
        result = validate_component_name("auth-service")
        assert result == "auth-service"

    def test_valid_name_with_spaces(self):
        result = validate_component_name("auth service")
        assert result == "auth service"

    def test_valid_name_with_underscore(self):
        result = validate_component_name("auth_service")
        assert result == "auth_service"

    def test_empty_name_raises(self):
        with pytest.raises(ComponentNameValidationError):
            validate_component_name("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ComponentNameValidationError):
            validate_component_name("   ")

    def test_name_too_long_raises(self):
        long_name = "a" * 101
        with pytest.raises(ComponentNameValidationError):
            validate_component_name(long_name)

    def test_name_with_special_chars_raises(self):
        with pytest.raises(ComponentNameValidationError):
            validate_component_name("test<script>")


class TestValidateIssueTitle:
    def test_valid_title(self):
        result = validate_issue_title("Fix authentication bug")
        assert result == "Fix authentication bug"

    def test_valid_title_trims_whitespace(self):
        result = validate_issue_title("  Fix bug  ")
        assert result == "Fix bug"

    def test_empty_title_raises(self):
        with pytest.raises(IssueTitleValidationError):
            validate_issue_title("")

    def test_title_too_long_raises(self):
        long_title = "a" * 201
        with pytest.raises(IssueTitleValidationError):
            validate_issue_title(long_title)


class TestValidateIssueDescription:
    def test_valid_description(self):
        result = validate_issue_description("This is a description")
        assert result == "This is a description"

    def test_none_returns_empty(self):
        result = validate_issue_description(None)
        assert result == ""

    def test_description_too_long_raises(self):
        long_desc = "a" * 10001
        with pytest.raises(IssueDescriptionValidationError):
            validate_issue_description(long_desc)


class TestSanitizeInput:
    def test_sanitize_removes_html(self):
        result = sanitize_input("<script>alert('xss')</script>test")
        assert "<script>" not in result

    def test_sanitize_escapes_quotes(self):
        result = sanitize_input("test'quoted'text")
        assert "\\'" in result or '"' in result

    def test_sanitize_removes_control_chars(self):
        result = sanitize_input("test\x00text")
        assert "\x00" not in result

    def test_empty_returns_empty(self):
        result = sanitize_input("")
        assert result == ""


class TestSanitizeComponentName:
    def test_sanitize_escapes_quotes(self):
        result = sanitize_component_name("test'name")
        assert "\\'" in result

    def test_sanitize_removes_control_chars(self):
        result = sanitize_component_name("test\x00name")
        assert "\x00" not in result


class TestSanitizeIssueTitle:
    def test_sanitize_escapes_quotes(self):
        result = sanitize_issue_title("test'title")
        assert "\\'" in result

    def test_sanitize_trims(self):
        result = sanitize_issue_title("  test  ")
        assert result == "test"


class TestSanitizeIssueDescription:
    def test_sanitize_removes_html(self):
        result = sanitize_issue_description("<b>bold</b> text")
        assert "<b>" not in result

    def test_sanitize_escapes_quotes(self):
        result = sanitize_issue_description("test'quoted'text")
        assert "\\'" in result


class TestSanitizeEdgeCases:
    """Edge case tests for input sanitization."""

    def test_sanitize_empty_string(self):
        result = sanitize_input("")
        assert result == ""

    def test_sanitize_none_returns_empty(self):
        result = sanitize_input(None)
        assert result == ""

    def test_sanitize_whitespace_only(self):
        result = sanitize_input("   \t\n  ")
        assert "   \t\n  " in result or result == ""

    def test_sanitize_very_long_input(self):
        long_text = "a" * 2000
        result = sanitize_input(long_text)
        assert len(result) == 2000

    def test_sanitize_unicode_characters(self):
        result = sanitize_input("Hello 世界 🌍 émoji")
        assert "Hello" in result
        assert "世界" in result

    def test_sanitize_unicode_injection(self):
        result = sanitize_input("'; DROP TABLE users;--")
        assert "DROP TABLE" not in result or "'" in result

    def test_sanitize_xss_script_tag(self):
        result = sanitize_input("<script>alert('xss')</script>")
        assert "<script>" not in result

    def test_sanitize_xss_img_tag(self):
        result = sanitize_input('<img src=x onerror="alert(1)">')
        assert "<img" not in result

    def test_sanitize_xss_svg_tag(self):
        result = sanitize_input("<svg onload=alert(1)>")
        assert "<svg" not in result

    def test_sanitize_special_characters(self):
        result = sanitize_input("test!@#$%^&*()_+-=[]{}|;':\",./<>?")
        assert "test" in result

    def test_sanitize_neo4j_cypher_match(self):
        result = sanitize_input("MATCH (n) RETURN n")
        assert "MATCH" in result

    def test_sanitize_neo4j_cypher_detach_delete(self):
        result = sanitize_input("MATCH (n) DETACH DELETE n")
        assert "DELETE" in result

    def test_sanitize_neo4j_cypher_create(self):
        result = sanitize_input("CREATE (n:Label {prop: 'value'})")
        assert "CREATE" in result

    def test_sanitize_neo4j_cypher_merge(self):
        result = sanitize_input("MERGE (n:Label {prop: 'value'})")
        assert "MERGE" in result

    def test_sanitize_neo4j_cypher_unwind(self):
        result = sanitize_input("UNWIND [1,2,3] AS x RETURN x")
        assert "UNWIND" in result


class TestSanitizeComponentNameEdgeCases:
    """Edge case tests for component name sanitization."""

    def test_sanitize_component_empty(self):
        result = sanitize_component_name("")
        assert result == ""

    def test_sanitize_component_none(self):
        result = sanitize_component_name(None)
        assert result == ""

    def test_sanitize_component_whitespace_only(self):
        result = sanitize_component_name("   \t\n  ")
        assert result == ""

    def test_sanitize_component_very_long(self):
        long_name = "a" * 200
        result = sanitize_component_name(long_name)
        assert len(result) == 200

    def test_sanitize_component_unicode(self):
        result = sanitize_component_name("组件名称")
        assert "组件名称" in result

    def test_sanitize_component_special_chars(self):
        result = sanitize_component_name("name!@#$%^&*()")
        assert "name" in result


class TestSanitizeIssueTitleEdgeCases:
    """Edge case tests for issue title sanitization."""

    def test_sanitize_title_empty(self):
        result = sanitize_issue_title("")
        assert result == ""

    def test_sanitize_title_none(self):
        result = sanitize_issue_title(None)
        assert result == ""

    def test_sanitize_title_whitespace_only(self):
        result = sanitize_issue_title("   \t\n  ")
        assert result == ""

    def test_sanitize_title_very_long(self):
        long_title = "a" * 200
        result = sanitize_issue_title(long_title)
        assert len(result) == 200

    def test_sanitize_title_unicode(self):
        result = sanitize_issue_title("修复错误")
        assert "修复错误" in result


class TestSanitizeIssueDescriptionEdgeCases:
    """Edge case tests for issue description sanitization."""

    def test_sanitize_description_empty(self):
        result = sanitize_issue_description("")
        assert result == ""

    def test_sanitize_description_none(self):
        result = sanitize_issue_description(None)
        assert result == ""

    def test_sanitize_description_whitespace_only(self):
        result = sanitize_issue_description("   \t\n  ")
        assert result == ""

    def test_sanitize_description_very_long(self):
        long_desc = "a" * 5000
        result = sanitize_issue_description(long_desc)
        assert len(result) == 5000

    def test_sanitize_description_unicode(self):
        result = sanitize_issue_description("Descrição em português")
        assert "Descrição" in result

    def test_sanitize_description_xss_in_description(self):
        result = sanitize_issue_description("<div onclick='alert(1)'>Click me</div>")
        assert "<div" not in result
        assert "onclick" not in result
