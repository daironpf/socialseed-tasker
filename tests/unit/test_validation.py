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
