"""Tests for embedding service and RAG pipeline."""

from __future__ import annotations

import pytest
from socialseed_tasker.core.services.embedding_service import (
    SecretFilter,
    ChunkingStrategy,
    EmbeddingService,
    get_embedding_service,
)


class TestSecretFilter:
    """Tests for secret filtering."""

    def test_filters_github_token(self):
        """Test that GitHub tokens are filtered."""
        text = "token=ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        filtered = SecretFilter.filter(text)
        assert "ghp_" not in filtered
        assert "[REDACTED]" in filtered

    def test_preserves_normal_text(self):
        """Test that normal text is preserved."""
        text = "This is a normal test without secrets"
        filtered = SecretFilter.filter(text)
        assert filtered == text


class TestChunkingStrategy:
    """Tests for chunking strategies."""

    def test_by_paragraph(self):
        """Test paragraph chunking."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph with more content to pass the min length requirement."
        chunks = ChunkingStrategy.by_paragraph(text, min_length=10)
        assert len(chunks) >= 1

    def test_by_paragraph_min_length(self):
        """Test that short paragraphs are filtered."""
        text = "Short.\n\nThis is a much longer paragraph that should be included."
        chunks = ChunkingStrategy.by_paragraph(text, min_length=20)
        assert len(chunks) == 1

    def test_by_lines(self):
        """Test line chunking."""
        text = "line1\nline2\nline3\nline4\nline5\nline6"
        chunks = ChunkingStrategy.by_lines(text, lines_per_chunk=2)
        assert len(chunks) == 3

    def test_by_sentences(self):
        """Test sentence chunking."""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = ChunkingStrategy.by_sentences(text, sentences_per_chunk=2)
        assert len(chunks) == 2


class TestEmbeddingService:
    """Tests for embedding service."""

    def test_service_creation(self):
        """Test service can be created."""
        service = EmbeddingService(api_key=None)
        assert not service.is_available()

    def test_service_with_key(self):
        """Test service with API key."""
        service = EmbeddingService(api_key="test-key")
        assert service.is_available()

    def test_fallback_generation(self):
        """Test fallback embedding generation."""
        service = EmbeddingService(api_key=None)
        result = service._generate_fallback("test text")
        assert len(result) == 1536
        assert all(-1 <= x <= 1 for x in result)

    def test_fallback_deterministic(self):
        """Test fallback is deterministic for same text."""
        service = EmbeddingService(api_key=None)
        result1 = service._generate_fallback("same text")
        result2 = service._generate_fallback("same text")
        assert result1 == result2


class TestGetEmbeddingService:
    """Tests for get_embedding_service factory."""

    def test_returns_service(self):
        """Test that factory returns service instance."""
        service = get_embedding_service()
        assert isinstance(service, EmbeddingService)