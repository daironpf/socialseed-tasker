"""Validation functions for input validation."""

import re

from socialseed_tasker.core.validation.exceptions import (
    ComponentNameValidationError,
    IssueDescriptionValidationError,
    IssueTitleValidationError,
)

COMPONENT_NAME_MAX_LENGTH = 100
COMPONENT_NAME_PATTERN = re.compile(r"^[\w\s\-]+$")

ISSUE_TITLE_MAX_LENGTH = 200

ISSUE_DESCRIPTION_MAX_LENGTH = 10000


def validate_component_name(name: str) -> str:
    """Validate component name.

    Args:
        name: The component name to validate.

    Returns:
        The validated component name.

    Raises:
        ComponentNameValidationError: If validation fails.
    """
    if not name or not name.strip():
        raise ComponentNameValidationError("Component name cannot be empty")

    name = name.strip()

    if len(name) > COMPONENT_NAME_MAX_LENGTH:
        raise ComponentNameValidationError(f"Component name cannot exceed {COMPONENT_NAME_MAX_LENGTH} characters")

    if not COMPONENT_NAME_PATTERN.match(name):
        raise ComponentNameValidationError(
            "Component name can only contain alphanumeric characters, dashes, underscores, and spaces"
        )

    return name


def validate_issue_title(title: str) -> str:
    """Validate issue title.

    Args:
        title: The issue title to validate.

    Returns:
        The validated issue title.

    Raises:
        IssueTitleValidationError: If validation fails.
    """
    if not title or not title.strip():
        raise IssueTitleValidationError("Issue title cannot be empty")

    title = title.strip()

    if len(title) > ISSUE_TITLE_MAX_LENGTH:
        raise IssueTitleValidationError(f"Issue title cannot exceed {ISSUE_TITLE_MAX_LENGTH} characters")

    return title


def validate_issue_description(description: str) -> str:
    """Validate issue description.

    Args:
        description: The issue description to validate.

    Returns:
        The validated issue description.

    Raises:
        IssueDescriptionValidationError: If validation fails.
    """
    if description is None:
        return ""

    description = description.strip() if isinstance(description, str) else str(description)

    if len(description) > ISSUE_DESCRIPTION_MAX_LENGTH:
        raise IssueDescriptionValidationError(
            f"Issue description cannot exceed {ISSUE_DESCRIPTION_MAX_LENGTH} characters"
        )

    return description
