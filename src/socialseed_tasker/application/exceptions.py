"""Application-level exceptions for port adapter failures."""


class GraphPortError(Exception):
    """Transient or permanent graph database error."""


class ParserError(Exception):
    """Parsing failed due to unreadable or invalid input."""


class GitError(Exception):
    """Git operation failed."""


class EmbeddingError(Exception):
    """Embedding generation failed."""


class StorageError(Exception):
    """Storage operation failed."""
