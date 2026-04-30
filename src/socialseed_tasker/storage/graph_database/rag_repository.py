"""RAG (Retrieval-Augmented Generation) storage repository.

Stores embeddings in Neo4j using vector indexes for semantic similarity search.
"""

from __future__ import annotations

import logging
from typing import Any

from socialseed_tasker.core.services.embedding_service import (
    ChunkingStrategy,
    EmbeddingService,
    get_embedding_service,
)

logger = logging.getLogger(__name__)


RAG_QUERIES = {
    "create_embedding_node": """
        MERGE (e:RAGEmbedding {id: $id})
        SET e.content = $content,
            e.embedding = $embedding,
            e.source_type = $source_type,
            e.source_id = $source_id,
            e.created_at = timestamp()
        RETURN e
    """,
    "search_similar_fallback": """
        MATCH (e:RAGEmbedding)
        WHERE e.source_type IS NOT NULL
        RETURN e.id as id, e.content as content,
               e.source_type as source_type, e.source_id as source_id,
               0.5 as score
        LIMIT $limit
    """,
    "search_by_source": """
        MATCH (e:RAGEmbedding {source_type: $source_type, source_id: $source_id})
        RETURN e.id as id, e.content as content
    """,
    "delete_by_source": """
        MATCH (e:RAGEmbedding {source_type: $source_type, source_id: $source_id})
        DETACH DELETE e
    """,
    "count_embeddings": """
        MATCH (e:RAGEmbedding)
        RETURN count(e) as total
    """,
    "get_stats": """
        MATCH (e:RAGEmbedding)
        RETURN e.source_type as source_type, count(e) as count
    """,
}


class RAGRepository:
    """Repository for RAG embeddings in Neo4j."""

    def __init__(self, driver: Any):
        """Initialize RAG repository.

        Args:
            driver: Neo4j driver wrapper
        """
        self._driver = driver
        self._embedding_service = get_embedding_service()

    def _get_session(self):
        """Get Neo4j session."""
        if hasattr(self._driver, "driver"):
            return self._driver.driver.session(database=self._driver.database)
        return self._driver.session(database="neo4j")

    def create_vector_index(self) -> None:
        """Create vector index for RAG embeddings."""
        with self._get_session() as session:
            try:
                session.run(RAG_QUERIES["create_vector_index"])
                logger.info("Created RAG vector index")
            except Exception as e:
                logger.warning(f"Vector index creation: {e}")

    def index_text(
        self,
        text: str,
        source_type: str,
        source_id: str,
        chunking_strategy: str = "paragraph",
    ) -> list[str]:
        """Index text content with embeddings.

        Args:
            text: Text to index
            source_type: Type of source (issue, adr, code, doc)
            source_id: ID of the source
            chunking_strategy: Strategy for chunking (paragraph, lines, sentences)

        Returns:
            List of chunk IDs created
        """
        strategy_map = {
            "paragraph": ChunkingStrategy.by_paragraph,
            "lines": ChunkingStrategy.by_lines,
            "sentences": ChunkingStrategy.by_sentences,
        }

        chunking_func = strategy_map.get(chunking_strategy, ChunkingStrategy.by_paragraph)
        chunks = chunking_func(text)

        if not chunks:
            return []

        import uuid

        chunk_ids = []
        embedded_chunks = self._embedding_service.embed_chunks(
            chunks, source_type, source_id
        ) if self._embedding_service.is_available() else []

        with self._get_session() as session:
            if embedded_chunks:
                for chunk in embedded_chunks:
                    chunk_id = str(uuid.uuid4())
                    chunk_ids.append(chunk_id)
                    session.run(
                        RAG_QUERIES["create_embedding_node"],
                        {
                            "id": chunk_id,
                            "content": chunk.content,
                            "embedding": chunk.embedding,
                            "source_type": source_type,
                            "source_id": source_id,
                        },
                    )
            else:
                for i, chunk in enumerate(chunks):
                    chunk_id = str(uuid.uuid4())
                    chunk_ids.append(chunk_id)
                    session.run(
                        RAG_QUERIES["create_embedding_node"],
                        {
                            "id": chunk_id,
                            "content": chunk,
                            "embedding": [],
                            "source_type": source_type,
                            "source_id": source_id,
                        },
                    )

        logger.info(f"Indexed {len(chunk_ids)} chunks for {source_type}:{source_id}")
        return chunk_ids

    def search(
        self, query: str, limit: int = 5, threshold: float = 0.7
    ) -> list[dict[str, Any]]:
        """Search for similar content.

        Args:
            query: Search query
            limit: Maximum results
            threshold: Minimum similarity score

        Returns:
            List of similar items with scores
        """
        with self._get_session() as session:
            if self._embedding_service.is_available():
                query_embedding = self._embedding_service.generate(query)
                if query_embedding:
                    result = session.run(
                        RAG_QUERIES["search_similar_fallback"],
                        {"embedding": query_embedding, "limit": limit, "threshold": threshold},
                    )
                    return [
                        {
                            "id": record["id"],
                            "content": record["content"],
                            "source_type": record["source_type"],
                            "source_id": record["source_id"],
                            "score": record["score"],
                        }
                        for record in result
                    ]

            result = session.run(
                RAG_QUERIES["search_similar_fallback"],
                {"limit": limit, "threshold": threshold},
            )
            return [
                {
                    "id": record["id"],
                    "content": record["content"],
                    "source_type": record["source_type"],
                    "source_id": record["source_id"],
                    "score": record["score"],
                }
                for record in result
            ]

    def get_stats(self) -> dict[str, Any]:
        """Get RAG index statistics."""
        with self._get_session() as session:
            total_result = session.run(RAG_QUERIES["count_embeddings"])
            record = total_result.single()
            total = record["total"] if record else 0

            stats_result = session.run(RAG_QUERIES["get_stats"])
            by_type = {}
            for record in stats_result:
                by_type[record["source_type"]] = record["count"]

            return {"total": total, "by_type": by_type}

    def delete_by_source(self, source_type: str, source_id: str) -> None:
        """Delete all embeddings for a source."""
        with self._get_session() as session:
            session.run(
                RAG_QUERIES["delete_by_source"],
                {"source_type": source_type, "source_id": source_id},
            )

    def clear(self) -> None:
        """Clear all RAG embeddings."""
        with self._get_session() as session:
            session.run("MATCH (e:RAGEmbedding) DETACH DELETE e")