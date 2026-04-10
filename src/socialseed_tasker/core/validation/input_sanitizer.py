"""Input sanitization functions."""

import re


def sanitize_input(text: str) -> str:
    """Sanitize user input for safe storage.

    Removes dangerous characters and patterns that could cause
    issues with Neo4j queries or security vulnerabilities.

    Args:
        text: The input text to sanitize.

    Returns:
        The sanitized text.
    """
    if not text:
        return ""

    text = str(text)

    text = _escape_quotes(text)
    text = _remove_html_tags(text)
    text = _remove_control_characters(text)

    return text


def _escape_quotes(text: str) -> str:
    """Escape quotes to prevent injection."""
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")


def _remove_html_tags(text: str) -> str:
    """Remove HTML tags to prevent XSS attacks."""
    return re.sub(r"<[^>]*>", "", text)


def _remove_control_characters(text: str) -> str:
    """Remove control characters except newlines and tabs."""
    return re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)


def sanitize_component_name(name: str) -> str:
    """Sanitize component name.

    Args:
        name: The component name to sanitize.

    Returns:
        The sanitized component name.
    """
    if not name:
        return ""

    name = name.strip()
    name = _escape_quotes(name)
    name = _remove_control_characters(name)

    return name


def sanitize_issue_title(title: str) -> str:
    """Sanitize issue title.

    Args:
        title: The issue title to sanitize.

    Returns:
        The sanitized title.
    """
    if not title:
        return ""

    title = title.strip()
    title = _escape_quotes(title)
    title = _remove_control_characters(title)

    return title


def sanitize_issue_description(description: str) -> str:
    """Sanitize issue description.

    Args:
        description: The issue description to sanitize.

    Returns:
        The sanitized description.
    """
    if not description:
        return ""

    description = str(description)
    description = _escape_quotes(description)
    description = _remove_html_tags(description)
    description = _remove_control_characters(description)

    return description
