"""Unit tests for validators module."""

import pytest

from socialseed_tasker.core.validation.validators import (
    validate_component_name,
    validate_issue_title,
    validate_issue_description,
    COMPONENT_NAME_MAX_LENGTH,
    ISSUE_TITLE_MAX_LENGTH,
    ISSUE_DESCRIPTION_MAX_LENGTH,
)
from socialseed_tasker.core.validation.exceptions import (
    ComponentNameValidationError,
    IssueTitleValidationError,
    IssueDescriptionValidationError,
)


class TestValidateComponentName:
    """Tests for validate_component_name function."""

    def test_valid_component_name(self):
        """Test valid component name passes."""
        result = validate_component_name("Backend")
        assert result == "Backend"

    def test_valid_component_name_with_spaces(self):
        """Test component name with spaces passes."""
        result = validate_component_name("My Backend Component")
        assert result == "My Backend Component"

    def test_valid_component_name_with_dash(self):
        """Test component name with dash passes."""
        result = validate_component_name("my-component")
        assert result == "my-component"

    def test_valid_component_name_with_underscore(self):
        """Test component name with underscore passes."""
        result = validate_component_name("my_component")
        assert result == "my_component"

    def test_empty_name_raises_error(self):
        """Test empty name raises ComponentNameValidationError."""
        with pytest.raises(ComponentNameValidationError):
            validate_component_name("")

    def test_whitespace_only_raises_error(self):
        """Test whitespace-only name raises error."""
        with pytest.raises(ComponentNameValidationError):
            validate_component_name("   ")

    def test_name_exceeds_max_length_raises_error(self):
        """Test name exceeding max length raises error."""
        long_name = "a" * (COMPONENT_NAME_MAX_LENGTH + 1)
        with pytest.raises(ComponentNameValidationError):
            validate_component_name(long_name)

    def test_invalid_name_with_special_chars_raises_error(self):
        """Test name with special characters raises error."""
        with pytest.raises(ComponentNameValidationError):
            validate_component_name("test@component")

    def test_name_strips_whitespace(self):
        """Test name is stripped of leading/trailing whitespace."""
        result = validate_component_name("  Backend  ")
        assert result == "Backend"


class TestValidateIssueTitle:
    """Tests for validate_issue_title function."""

    def test_valid_title(self):
        """Test valid title passes."""
        result = validate_issue_title("Fix bug in login")
        assert result == "Fix bug in login"

    def test_empty_title_raises_error(self):
        """Test empty title raises IssueTitleValidationError."""
        with pytest.raises(IssueTitleValidationError):
            validate_issue_title("")

    def test_whitespace_only_raises_error(self):
        """Test whitespace-only title raises error."""
        with pytest.raises(IssueTitleValidationError):
            validate_issue_title("   ")

    def test_title_exceeds_max_length_raises_error(self):
        """Test title exceeding max length raises error."""
        long_title = "a" * (ISSUE_TITLE_MAX_LENGTH + 1)
        with pytest.raises(IssueTitleValidationError):
            validate_issue_title(long_title)

    def test_title_strips_whitespace(self):
        """Test title is stripped of whitespace."""
        result = validate_issue_title("  Fix bug  ")
        assert result == "Fix bug"


class TestValidateIssueDescription:
    """Tests for validate_issue_description function."""

    def test_valid_description(self):
        """Test valid description passes."""
        result = validate_issue_description("This is a description")
        assert result == "This is a description"

    def test_none_description_returns_empty(self):
        """Test None description returns empty string."""
        result = validate_issue_description(None)
        assert result == ""

    def test_empty_description_returns_empty(self):
        """Test empty description returns empty string."""
        result = validate_issue_description("")
        assert result == ""

    def test_description_exceeds_max_length_raises_error(self):
        """Test description exceeding max length raises error."""
        long_desc = "a" * (ISSUE_DESCRIPTION_MAX_LENGTH + 1)
        with pytest.raises(IssueDescriptionValidationError):
            validate_issue_description(long_desc)

    def test_description_strips_whitespace(self):
        """Test description is stripped."""
        result = validate_issue_description("  Some description  ")
        assert result == "Some description"

    def test_non_string_converted_to_string(self):
        """Test non-string is converted to string."""
        result = validate_issue_description(123)
        assert result == "123"


class TestValidationConstants:
    """Tests for validation constants."""

    def test_component_name_max_length(self):
        """Test component name max length is reasonable."""
        assert COMPONENT_NAME_MAX_LENGTH > 0
        assert COMPONENT_NAME_MAX_LENGTH <= 200

    def test_issue_title_max_length(self):
        """Test issue title max length is reasonable."""
        assert ISSUE_TITLE_MAX_LENGTH > 0
        assert ISSUE_TITLE_MAX_LENGTH <= 1000

    def test_issue_description_max_length(self):
        """Test issue description max length is reasonable."""
        assert ISSUE_DESCRIPTION_MAX_LENGTH > 0