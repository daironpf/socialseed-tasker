"""RAG (Retrieval-Augmented Generation) storage repository.

Stores embeddings in Neo4j using vector indexes for semantic similarity search.
"""

from __future__ import annotations

import logging
from typing import Any

from socialseed_tasker.infrastructure.embedding_service import (
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
            e.sourceType = $source_type,
            e.sourceId = $source_id,
            e.createdAt = timestamp()
        RETURN e
    """,
    "create_vector_index": """
        CREATE VECTOR INDEX rag_index IF NOT EXISTS
        FOR (e:RAGEmbedding) ON e.embedding
        OPTIONS {
            indexConfig: {
                `vector.dimensions`: 1536,
                `vector.similarity_function`: 'cosine'
            }
        }
    """,
    "search_similar_vector": """
        CALL db.index.vector.searchNodes('rag_index', $limit, $embedding)
        YIELD node, score
        RETURN node.id as id, node.content as content,
               node.sourceType as source_type, node.sourceId as source_id,
               score
        ORDER BY score DESC
    """,
    "search_by_source": """
        MATCH (e:RAGEmbedding {sourceType: $source_type, sourceId: $source_id})
        RETURN e.id as id, e.content as content
    """,
    "delete_by_source": """
        MATCH (e:RAGEmbedding {sourceType: $source_type, sourceId: $source_id})
        DETACH DELETE e
    """,
    "count_embeddings": """
        MATCH (e:RAGEmbedding)
        RETURN count(e) as total
    """,
    "get_stats": """
        MATCH (e:RAGEmbedding)
        RETURN e.sourceType as source_type, count(e) as count
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
        """Search for similar content using vector similarity.

        Args:
            query: Search query
            limit: Maximum results
            threshold: Minimum similarity score

        Returns:
            List of similar items with scores
        """
        if not self._embedding_service.is_available():
            logger.warning("Embedding service not available")
            return []

        query_embedding = self._embedding_service.generate(query)
        if query_embedding is None:
            return []

        try:
            with self._get_session() as session:
                result = session.run(
                    RAG_QUERIES["search_similar_vector"],
                    {"embedding": query_embedding, "limit": limit},
                )
                return [
                    {
                        "id": record["id"],
                        "content": record["content"],
                        "sourceType": record["sourceType"],
                        "sourceId": record["sourceId"],
                        "score": record["score"],
                    }
                    for record in result
                    if record["score"] >= threshold
                ]
        except Exception as e:
            logger.warning(f"Vector search failed: {e}, using fallback")
            return self._fallback_search(query_embedding, limit, threshold)

    def _fallback_search(self, query_embedding: list[float], limit: int, threshold: float) -> list[dict[str, Any]]:
        """Fallback search computing cosine similarity in Python."""
        with self._get_session() as session:
            result = session.run(
                "MATCH (e:RAGEmbedding) WHERE size(e.embedding) > 0 "
                "RETURN e.id as id, e.content as content, "
                "e.sourceType as source_type, e.sourceId as source_id, e.embedding as embedding",
            )

            import math

            def cosine_similarity(a: list[float], b: list[float]) -> float:
                dot = sum(x * y for x, y in zip(a, b))
                mag_a = math.sqrt(sum(x * x for x in a))
                mag_b = math.sqrt(sum(x * x for x in b))
                return dot / (mag_a * mag_b) if mag_a and mag_b else 0

            results = []
            for record in result:
                emb = record["embedding"]
                if emb and len(emb) > 0:
                    score = cosine_similarity(query_embedding, emb)
                    if score >= threshold:
                        results.append({
                            "id": record["id"],
                            "content": record["content"],
                            "sourceType": record["sourceType"],
                            "sourceId": record["sourceId"],
                            "score": score,
                        })

            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:limit]

    def get_stats(self) -> dict[str, Any]:
        """Get RAG index statistics."""
        with self._get_session() as session:
            total_result = session.run(RAG_QUERIES["count_embeddings"])
            record = total_result.single()
            total = record["total"] if record else 0

            stats_result = session.run(RAG_QUERIES["get_stats"])
            by_type = {}
            for record in stats_result:
                by_type[record["sourceType"]] = record["count"]

            return {"total": total, "by_type": by_type}

    def delete_by_source(self, source_type: str, source_id: str) -> None:
        """Delete all embeddings for a source."""
        with self._get_session() as session:
            session.run(
                RAG_QUERIES["delete_by_source"],
                {"source_type": source_type, "source_id": source_id},
            )

    def get_context_for_issue(self, issue_id: str) -> list[dict]:
        """Build RAG context for an Issue by following AFFECTS relationship.
        
        Retrieves CodeSymbols and CodeFiles affected by this issue
        to provide targeted context for the AI agent.
        """
        with self._get_session() as session:
            result = session.run("""
                MATCH (i:Issue {id: $issue_id})
                OPTIONAL MATCH (i)-[:AFFECTS]->(s:CodeSymbol)
                OPTIONAL MATCH (i)-[:AFFECTS]->(f:CodeFile)
                RETURN coalesce(s.id, f.id) as source_id,
                       coalesce(s.name, f.name) as source_name,
                       coalesce(labels(s)[0], labels(f)[0]) as source_type
            """, issue_id=issue_id)
            return [dict(r) for r in result]

    def get_embeddings_by_symbol(self, symbol_id: str) -> list[dict]:
        """Get all RAG embeddings linked to a CodeSymbol."""
        with self._get_session() as session:
            result = session.run("""
                MATCH (s:CodeSymbol {id: $symbol_id})-[:HAS_VECTOR]->(e:RAGEmbedding)
                RETURN e.id as id, e.content as content, e.sourceType as source_type
            """, symbol_id=symbol_id)
            return [dict(r) for r in result]

    def clear(self) -> None:
        """Clear all RAG embeddings."""
        with self._get_session() as session:
            session.run("MATCH (e:RAGEmbedding) DETACH DELETE e")

    def create_native_embedding(
        self, node_label: str, node_id: str, content: str
    ) -> dict[str, Any]:
        """Store embedding directly on the source node.

        This is the optimized approach - store the embedding
        directly on Issue/Symbol/Reasoning nodes instead of
        creating separate RAGEmbedding nodes.
        """
        embedding = self._embedding_service.generate(content)
        if embedding is None:
            return {"error": "Failed to encode content"}

        label_map = {
            "issue": "Issue",
            "symbol": "CodeSymbol",
            "reasoning": "ReasoningNode",
            "policy": "Policy",
        }
        neo_label = label_map.get(node_label.lower(), node_label.capitalize())

        with self._get_session() as session:
            query = f"""
            MATCH (n:{neo_label} {{id: $id}})
            SET n.embedding = $embedding
            RETURN n.id as id
            """
            result = session.run(
                query,
                {"id": node_id, "embedding": embedding},
            )
            record = result.single()
            if record:
                return {"success": True, "node_id": node_id}
            return {"error": "Node not found"}

    def search_native(
        self, node_label: str, query_text: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Search using embeddings stored directly on nodes."""
        embedding = self._embedding_service.generate(query_text)
        if embedding is None:
            return []

        label_map = {
            "issue": "Issue",
            "symbol": "CodeSymbol",
            "reasoning": "ReasoningNode",
            "policy": "Policy",
        }
        neo_label = label_map.get(node_label.lower(), node_label.capitalize())

        with self._get_session() as session:
            cypher = f"""
            MATCH (n:{neo_label})
            WHERE n.embedding IS NOT NULL
            RETURN n.id as id, n.name as title, n.title as issue_title,
                   vector.similarity.cosine(n.embedding, $embedding) as score
            ORDER BY score DESC
            LIMIT toInteger($limit)
            """
            result = session.run(
                cypher,
                {"embedding": embedding, "limit": limit},
            )
            return [
                {"id": r["id"], "title": r.get("issue_title") or r.get("title"), "score": r["score"]}
                for r in result
            ]

    def get_stats_native(self) -> dict[str, int]:
        """Get stats for natively stored embeddings."""
        counts = {}
        for label in ["Issue", "CodeSymbol", "ReasoningNode", "Policy"]:
            with self._get_session() as session:
                result = session.run(
                    f"MATCH (n:{label}) WHERE n.embedding IS NOT NULL RETURN count(n) as count"
                )
                record = result.single()
                counts[label] = record["count"] if record else 0
        return counts