"""Validation exceptions for input validation and sanitization."""


class ValidationError(Exception):
    """Base exception for validation errors."""

    pass


class ComponentNameValidationError(ValidationError):
    """Raised when component name validation fails."""

    pass


class IssueTitleValidationError(ValidationError):
    """Raised when issue title validation fails."""

    pass


class IssueDescriptionValidationError(ValidationError):
    """Raised when issue description validation fails."""

    pass
