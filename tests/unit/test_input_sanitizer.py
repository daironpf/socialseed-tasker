"""Unit tests for input sanitizer module."""

import pytest

from socialseed_tasker.domain.input_sanitizer import (
    sanitize_input,
    sanitize_component_name,
    sanitize_issue_title,
    sanitize_issue_description,
    _escape_quotes,
    _remove_html_tags,
    _remove_control_characters,
)


class TestSanitizeInput:
    """Tests for sanitize_input function."""

    def test_empty_input_returns_empty(self):
        """Test empty input returns empty string."""
        assert sanitize_input("") == ""

    def test_none_input_returns_empty(self):
        """Test None input returns empty string."""
        assert sanitize_input(None) == ""

    def test_normal_text_unchanged(self):
        """Test normal text remains unchanged."""
        assert sanitize_input("Hello World") == "Hello World"

    def test_html_tags_removed(self):
        """Test HTML tags are removed."""
        result = sanitize_input("<script>alert('xss')</script>")
        assert "<script>" not in result

    def test_quotes_escaped(self):
        """Test quotes are escaped."""
        result = sanitize_input('Hello "World"')
        assert '\\"' in result

    def test_control_characters_removed(self):
        """Test control characters are removed."""
        result = sanitize_input("Hello\x00World")
        assert "\x00" not in result


class TestSanitizeComponentName:
    """Tests for sanitize_component_name function."""

    def test_empty_returns_empty(self):
        """Test empty input returns empty."""
        assert sanitize_component_name("") == ""

    def test_none_returns_empty(self):
        """Test None returns empty."""
        assert sanitize_component_name(None) == ""

    def test_normal_name_unchanged(self):
        """Test normal name remains unchanged."""
        assert sanitize_component_name("Backend") == "Backend"

    def test_whitespace_stripped(self):
        """Test whitespace is stripped."""
        assert sanitize_component_name("  Backend  ") == "Backend"

    def test_control_chars_removed(self):
        """Test control characters are removed."""
        result = sanitize_component_name("Backend\x00")
        assert "\x00" not in result


class TestSanitizeIssueTitle:
    """Tests for sanitize_issue_title function."""

    def test_empty_returns_empty(self):
        """Test empty returns empty."""
        assert sanitize_issue_title("") == ""

    def test_none_returns_empty(self):
        """Test None returns empty."""
        assert sanitize_issue_title(None) == ""

    def test_normal_title_unchanged(self):
        """Test normal title remains unchanged."""
        assert sanitize_issue_title("Fix bug") == "Fix bug"

    def test_whitespace_stripped(self):
        """Test whitespace is stripped."""
        assert sanitize_issue_title("  Fix bug  ") == "Fix bug"


class TestSanitizeIssueDescription:
    """Tests for sanitize_issue_description function."""

    def test_empty_returns_empty(self):
        """Test empty returns empty."""
        assert sanitize_issue_description("") == ""

    def test_none_returns_empty(self):
        """Test None returns empty."""
        assert sanitize_issue_description(None) == ""

    def test_normal_description_unchanged(self):
        """Test normal description remains unchanged."""
        assert sanitize_issue_description("This is a description") == "This is a description"

    def test_html_tags_removed(self):
        """Test HTML tags are removed."""
        result = sanitize_issue_description("<b>Bold</b> text")
        assert "<b>" not in result

    def test_whitespace_stripped(self):
        """Test whitespace is stripped."""
        assert sanitize_issue_description("  Description  ") == "Description"


class TestPrivateFunctions:
    """Tests for private sanitization functions."""

    def test_escape_quotes(self):
        """Test _escape_quotes escapes backslashes and quotes."""
        result = _escape_quotes('Hello "World"')
        assert "\\\\" in result or '\\"' in result

    def test_remove_html_tags(self):
        """Test _remove_html_tags removes HTML."""
        result = _remove_html_tags("<b>Bold</b>")
        assert result == "Bold"

    def test_remove_html_tags_with_attributes(self):
        """Test _remove_html_tags removes tags with attributes."""
        result = _remove_html_tags('<a href="http://test.com">Link</a>')
        assert "href" not in result

    def test_remove_control_characters(self):
        """Test _remove_control_characters removes control chars."""
        result = _remove_control_characters("Hello\x00World\x7f")
        assert "\x00" not in result
        assert "\x7f" not in result

    def test_remove_control_characters_preserves_newlines(self):
        """Test _remove_control_characters preserves newlines and tabs."""
        result = _remove_control_characters("Hello\nWorld\tTest")
        assert "\n" in result
        assert "\t" in result