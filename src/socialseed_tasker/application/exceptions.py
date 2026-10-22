"""Application-level exceptions for port adapter failures."""


class GraphPortError(Exception):
    """Transient or permanent graph database error."""


class ParserError(Exception):
    """Parsing failed due to unreadable or invalid input."""


class GitError(Exception):
    """Git operation failed."""


class EmbeddingError(Exception):
    """Embedding generation failed."""


class AIServiceNotConfiguredError(Exception):
    """AI/embedding provider is not configured for this deployment."""


class StorageError(Exception):
    """Storage operation failed."""


class PermissionError(Exception):
    """Permission denied for the requested operation."""
