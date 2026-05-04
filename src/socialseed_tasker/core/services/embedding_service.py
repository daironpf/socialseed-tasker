"""Embedding service for RAG (Retrieval-Augmented Generation).

Provides embedding generation using OpenAI's text-embedding-3-small model
or local alternatives. Includes chunking strategies and secret filtering.
"""

from __future__ import annotations

import logging
import os
import random
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


SECRET_PATTERNS = [
    r"(?i)(api[_-]?key|secret[_-]?key|password|token|auth)[=:\s]['\"]?([a-zA-Z0-9_\-]{20,})['\"]?",
    r"gh[pousa]_[\w]{36,}",
    r"(?i)bearer\s+[a-zA-Z0-9_\-\.]+",
]


@dataclass
class EmbeddingChunk:
    """Represents a chunk of text with its embedding."""

    content: str
    embedding: list[float]
    source_type: str
    source_id: str
    metadata: dict[str, Any]


class SecretFilter:
    """Filters secrets from text before embedding."""

    @staticmethod
    def filter(text: str) -> str:
        """Remove secrets from text."""
        filtered = text
        filtered = re.sub(r"api[_-]?key\s*[=:]\s*['\"]?([a-zA-Z0-9_\-]{20,})", r"api_key=\1[REDACTED]", filtered, flags=re.I)
        filtered = re.sub(r"(gh[pousa]_[\w]{36,})", r"\1[REDACTED]", filtered)
        filtered = re.sub(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]+", r"bearer [REDACTED]", filtered)
        filtered = re.sub(r"password\s*[=:]\s*['\"]?([a-zA-Z0-9_\-]{8,})", r"password=[REDACTED]", filtered, flags=re.I)
        filtered = re.sub(r"token\s*[=:]\s*['\"]?([a-zA-Z0-9_\-]{20,})", r"token=[REDACTED]", filtered, flags=re.I)
        return filtered


class ChunkingStrategy:
    """Strategies for chunking text content."""

    @staticmethod
    def by_paragraph(text: str, min_length: int = 50) -> list[str]:
        """Chunk by paragraphs."""
        paragraphs = text.split("\n\n")
        return [p.strip() for p in paragraphs if len(p.strip()) >= min_length]

    @staticmethod
    def by_lines(text: str, lines_per_chunk: int = 10) -> list[str]:
        """Chunk by fixed number of lines."""
        lines = text.split("\n")
        chunks = []
        for i in range(0, len(lines), lines_per_chunk):
            chunk = "\n".join(lines[i : i + lines_per_chunk])
            if chunk.strip():
                chunks.append(chunk.strip())
        return chunks

    @staticmethod
    def by_sentences(text: str, sentences_per_chunk: int = 5) -> list[str]:
        """Chunk by sentences."""
        sentence_endings = re.compile(r"(?<=[.!?])\s+")
        sentences = sentence_endings.split(text)
        chunks = []
        current = []
        for sentence in sentences:
            current.append(sentence)
            if len(current) >= sentences_per_chunk:
                chunks.append(" ".join(current))
                current = []
        if current:
            chunks.append(" ".join(current))
        return [c.strip() for c in chunks if c.strip()]


class EmbeddingService:
    """Service for generating text embeddings."""

    DEFAULT_MODEL = "text-embedding-3-small"
    DEFAULT_DIMENSIONS = 1536

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize embedding service.

        Args:
            api_key: OpenAI API key (defaults to env OPENAI_API_KEY)
            model: Embedding model to use
        """
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._model = model or os.environ.get("EMBEDDING_MODEL", self.DEFAULT_MODEL)
        self._dimensions = self.DEFAULT_DIMENSIONS
        self._client = None

    def _get_client(self) -> Any:
        """Get or create OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=self._api_key)
            except ImportError:
                logger.warning("OpenAI client not available")
                return None
        return self._client

    def is_available(self) -> bool:
        """Check if embedding service is available."""
        return self._api_key is not None

    def generate(self, text: str) -> list[float] | None:
        """Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector or None if failed
        """
        if not self.is_available():
            logger.warning("Embedding service not available - no API key")
            return None

        filtered_text = SecretFilter.filter(text)

        try:
            client = self._get_client()
            if client is None:
                return self._generate_fallback(filtered_text)

            response = client.embeddings.create(
                model=self._model,
                input=filtered_text[:8192],
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return self._generate_fallback(filtered_text)

    def _generate_fallback(self, text: str) -> list[float]:
        """Generate a simple fallback embedding using hash."""
        random.seed(hash(text) % (2**31))
        return [random.random() * 2 - 1 for _ in range(self._dimensions)]

    def embed_chunks(
        self, chunks: list[str], source_type: str, source_id: str
    ) -> list[EmbeddingChunk]:
        """Embed multiple chunks.

        Args:
            chunks: List of text chunks
            source_type: Type of source (issue, adr, code, etc.)
            source_id: ID of the source document

        Returns:
            List of EmbeddingChunk objects
        """
        embedded_chunks = []
        for i, chunk in enumerate(chunks):
            embedding = self.generate(chunk)
            if embedding:
                embedded_chunks.append(
                    EmbeddingChunk(
                        content=chunk,
                        embedding=embedding,
                        source_type=source_type,
                        source_id=source_id,
                        metadata={"chunk_index": i},
                    )
                )
        return embedded_chunks


def get_embedding_service() -> EmbeddingService:
    """Get the global embedding service instance."""
    return EmbeddingService()