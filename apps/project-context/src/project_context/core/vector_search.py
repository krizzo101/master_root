#!/usr/bin/env python3
"""
Vector Search Integration for Project Context System

Provides semantic search capabilities using pgvector and embedding service.
Integrates with existing project context tools for intelligent code and chat analytics.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import asyncpg
import httpx
from project_context.config.settings import get_database_url

logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION
# ============================================

EMBEDDING_SERVICE_URL = "http://localhost:8001"
DEFAULT_SIMILARITY_THRESHOLD = 0.7
DEFAULT_MAX_RESULTS = 10

# ============================================
# DATA MODELS
# ============================================


@dataclass
class SearchResult:
    """Represents a search result with similarity score."""

    id: str
    source_type: str
    entity_type: str
    title: str
    content: str
    file_path: Optional[str]
    similarity: float
    metadata: Dict[str, Any] = None


@dataclass
class CodeSearchResult:
    """Represents a code search result."""

    id: str
    file_path: str
    element_type: str
    element_name: str
    signature: str
    docstring: str
    language: str
    similarity: float


@dataclass
class HybridSearchResult(SearchResult):
    """Hybrid search result with separate text and vector scores."""

    text_score: float
    vector_score: float
    combined_score: float


# ============================================
# VECTOR SEARCH CLIENT
# ============================================


class VectorSearchClient:
    """
    Client for performing vector-based semantic search operations.

    Integrates with the embedding service API and PostgreSQL pgvector functions
    to provide semantic search capabilities for the unified context system.
    """

    def __init__(
        self,
        embedding_service_url: str = EMBEDDING_SERVICE_URL,
        database_url: str = None,
    ):
        """
        Initialize the vector search client.

        Args:
            embedding_service_url: URL of the embedding service API
            database_url: PostgreSQL connection URL
        """
        self.embedding_service_url = embedding_service_url.rstrip("/")
        self.database_url = database_url or get_database_url()
        self.db_pool = None
        self._http_client = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    async def initialize(self):
        """Initialize database connection pool and HTTP client."""
        try:
            self.db_pool = await asyncpg.create_pool(
                self.database_url, min_size=1, max_size=5
            )
            self._http_client = httpx.AsyncClient(timeout=30.0)
            logger.info("Vector search client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize vector search client: {e}")
            raise

    async def cleanup(self):
        """Clean up resources."""
        if self.db_pool:
            await self.db_pool.close()
        if self._http_client:
            await self._http_client.aclose()

    async def _generate_embedding(
        self, text: str, model: str = "sentence-transformers"
    ) -> List[float]:
        """Generate embedding using the embedding service."""
        try:
            response = await self._http_client.post(
                f"{self.embedding_service_url}/embed",
                json={"text": text, "model": model},
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def semantic_search(
        self,
        query: str,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        max_results: int = DEFAULT_MAX_RESULTS,
        source_filter: Optional[str] = None,
        entity_filter: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Perform semantic search using vector similarity.

        Args:
            query: Search query text
            similarity_threshold: Minimum similarity score
            max_results: Maximum number of results
            source_filter: Filter by source type (e.g., 'chat', 'code', 'git')
            entity_filter: Filter by entity type (e.g., 'message', 'function')

        Returns:
            List of search results sorted by similarity
        """
        try:
            # Generate embedding for query
            query_embedding = await self._generate_embedding(query)

            # Execute search in database
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM find_similar_context($1, $2, $3, $4, $5)
                    """,
                    query_embedding,
                    similarity_threshold,
                    max_results,
                    source_filter,
                    entity_filter,
                )

            # Convert to SearchResult objects
            results = []
            for row in rows:
                result = SearchResult(
                    id=str(row["id"]),
                    source_type=row["source_type"],
                    entity_type=row["entity_type"],
                    title=row["title"] or "",
                    content=row["content"] or "",
                    file_path=row["file_path"],
                    similarity=float(row["similarity"]),
                )
                results.append(result)

            logger.info(
                f"Semantic search for '{query}' returned {len(results)} results"
            )
            return results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise

    async def code_search(
        self,
        query: str,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        max_results: int = DEFAULT_MAX_RESULTS,
        element_type_filter: Optional[str] = None,
        language_filter: Optional[str] = None,
    ) -> List[CodeSearchResult]:
        """
        Perform semantic search for code elements.

        Args:
            query: Code search query
            similarity_threshold: Minimum similarity score
            max_results: Maximum number of results
            element_type_filter: Filter by element type ('function', 'class', etc.)
            language_filter: Filter by programming language

        Returns:
            List of code search results sorted by similarity
        """
        try:
            # Generate embedding for query
            query_embedding = await self._generate_embedding(query)

            # Execute code search
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM find_similar_code($1, $2, $3, $4, $5)
                    """,
                    query_embedding,
                    similarity_threshold,
                    max_results,
                    element_type_filter,
                    language_filter,
                )

            # Convert to CodeSearchResult objects
            results = []
            for row in rows:
                result = CodeSearchResult(
                    id=str(row["id"]),
                    file_path=row["file_path"],
                    element_type=row["element_type"],
                    element_name=row["element_name"] or "",
                    signature=row["signature"] or "",
                    docstring=row["docstring"] or "",
                    language=row["language"] or "",
                    similarity=float(row["similarity"]),
                )
                results.append(result)

            logger.info(f"Code search for '{query}' returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Code search failed: {e}")
            raise

    async def hybrid_search(
        self,
        query: str,
        text_weight: float = 0.3,
        vector_weight: float = 0.7,
        similarity_threshold: float = 0.5,
        max_results: int = DEFAULT_MAX_RESULTS,
    ) -> List[HybridSearchResult]:
        """
        Perform hybrid search combining text and vector similarity.

        Args:
            query: Search query text
            text_weight: Weight for text search component (0-1)
            vector_weight: Weight for vector search component (0-1)
            similarity_threshold: Minimum combined similarity score
            max_results: Maximum number of results

        Returns:
            List of hybrid search results with combined scores
        """
        try:
            # Generate embedding for query
            query_embedding = await self._generate_embedding(query)

            # Execute hybrid search
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM hybrid_context_search($1, $2, $3, $4, $5, $6)
                    """,
                    query,
                    query_embedding,
                    text_weight,
                    vector_weight,
                    similarity_threshold,
                    max_results,
                )

            # Convert to HybridSearchResult objects
            results = []
            for row in rows:
                result = HybridSearchResult(
                    id=str(row["id"]),
                    source_type=row["source_type"],
                    entity_type=row["entity_type"],
                    title=row["title"] or "",
                    content=row["content"] or "",
                    file_path=row["file_path"],
                    similarity=float(row["combined_score"]),
                    text_score=float(row["text_score"]),
                    vector_score=float(row["vector_score"]),
                    combined_score=float(row["combined_score"]),
                )
                results.append(result)

            logger.info(f"Hybrid search for '{query}' returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise

    async def find_similar_to_context(
        self,
        context_item_id: str,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        max_results: int = DEFAULT_MAX_RESULTS,
        exclude_same_source: bool = True,
    ) -> List[SearchResult]:
        """
        Find items similar to a specific context item.

        Args:
            context_item_id: ID of the context item to find similarities for
            similarity_threshold: Minimum similarity score
            max_results: Maximum number of results
            exclude_same_source: Whether to exclude items from same source

        Returns:
            List of similar context items
        """
        try:
            # Get the embedding for the target context item
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT embedding, source_type FROM context_items
                    WHERE id = $1 AND embedding IS NOT NULL
                    """,
                    context_item_id,
                )

            if not row:
                raise ValueError(
                    f"Context item {context_item_id} not found or has no embedding"
                )

            target_embedding = row["embedding"]
            target_source = row["source_type"]

            # Find similar items
            async with self.db_pool.acquire() as conn:
                query_parts = [
                    """
                    SELECT
                        id,
                        source_type,
                        entity_type,
                        title,
                        content,
                        file_path,
                        (1 - (embedding <=> $1)) AS similarity
                    FROM context_items
                    WHERE id != $2
                      AND embedding IS NOT NULL
                      AND (1 - (embedding <=> $1)) >= $3
                    """
                ]
                params = [target_embedding, context_item_id, similarity_threshold]

                if exclude_same_source:
                    query_parts.append(" AND source_type != $4")
                    params.append(target_source)

                query_parts.append(" ORDER BY embedding <=> $1 LIMIT $5")
                params.append(max_results)

                rows = await conn.fetch("".join(query_parts), *params)

            # Convert to SearchResult objects
            results = []
            for row in rows:
                result = SearchResult(
                    id=str(row["id"]),
                    source_type=row["source_type"],
                    entity_type=row["entity_type"],
                    title=row["title"] or "",
                    content=row["content"] or "",
                    file_path=row["file_path"],
                    similarity=float(row["similarity"]),
                )
                results.append(result)

            logger.info(
                f"Found {len(results)} similar items to context {context_item_id}"
            )
            return results

        except Exception as e:
            logger.error(f"Similar context search failed: {e}")
            raise

    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get embedding coverage statistics."""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM embedding_stats")

            stats = [dict(row) for row in rows]
            total_items = sum(row["total_items"] for row in stats)
            total_embeddings = sum(row["items_with_embeddings"] for row in stats)

            return {
                "by_source_type": stats,
                "overall": {
                    "total_items": total_items,
                    "items_with_embeddings": total_embeddings,
                    "coverage_percentage": round(
                        100.0 * total_embeddings / total_items, 2
                    )
                    if total_items > 0
                    else 0,
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get embedding stats: {e}")
            raise


# ============================================
# HIGH-LEVEL SEARCH UTILITIES
# ============================================


async def search_related_context(
    query: str, search_type: str = "hybrid", max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    High-level function to search for related context items.

    Args:
        query: Search query
        search_type: Type of search ('semantic', 'hybrid', 'code')
        max_results: Maximum number of results

    Returns:
        List of search results as dictionaries
    """
    async with VectorSearchClient() as client:
        if search_type == "semantic":
            results = await client.semantic_search(query, max_results=max_results)
        elif search_type == "hybrid":
            results = await client.hybrid_search(query, max_results=max_results)
        elif search_type == "code":
            results = await client.code_search(query, max_results=max_results)
        else:
            raise ValueError(f"Unsupported search type: {search_type}")

        # Convert results to dictionaries
        return [
            {
                "id": result.id,
                "source_type": result.source_type,
                "entity_type": result.entity_type,
                "title": result.title,
                "content": result.content[:500] + "..."
                if len(result.content) > 500
                else result.content,
                "file_path": result.file_path,
                "similarity": result.similarity,
                **(
                    {
                        "text_score": result.text_score,
                        "vector_score": result.vector_score,
                    }
                    if hasattr(result, "text_score")
                    else {}
                ),
            }
            for result in results
        ]


async def find_context_clusters(
    similarity_threshold: float = 0.8, min_cluster_size: int = 3
) -> List[Dict[str, Any]]:
    """
    Find clusters of similar context items.

    Args:
        similarity_threshold: Minimum similarity for clustering
        min_cluster_size: Minimum items per cluster

    Returns:
        List of cluster information
    """
    async with VectorSearchClient() as client:
        async with client.db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM find_content_clusters($1, $2)",
                similarity_threshold,
                min_cluster_size,
            )

        return [dict(row) for row in rows]


# ============================================
# CHAT CONTEXT MATCHING
# ============================================


async def find_relevant_chat_history(
    current_context: str, max_results: int = 5, similarity_threshold: float = 0.6
) -> List[Dict[str, Any]]:
    """
    Find relevant chat history based on current context.

    Args:
        current_context: Current conversation context
        max_results: Maximum number of results
        similarity_threshold: Minimum similarity threshold

    Returns:
        List of relevant chat messages/sessions
    """
    async with VectorSearchClient() as client:
        results = await client.semantic_search(
            query=current_context,
            source_filter="chat",
            similarity_threshold=similarity_threshold,
            max_results=max_results,
        )

        return [
            {
                "id": result.id,
                "title": result.title,
                "content": result.content[:300] + "..."
                if len(result.content) > 300
                else result.content,
                "similarity": result.similarity,
                "file_path": result.file_path,
            }
            for result in results
        ]


# ============================================
# CODE SIMILARITY OPERATIONS
# ============================================


async def find_similar_code_patterns(
    code_snippet: str,
    language: Optional[str] = None,
    element_type: Optional[str] = None,
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """
    Find code patterns similar to a given code snippet.

    Args:
        code_snippet: Code to find similarities for
        language: Programming language filter
        element_type: Element type filter ('function', 'class', etc.)
        max_results: Maximum number of results

    Returns:
        List of similar code elements
    """
    async with VectorSearchClient() as client:
        results = await client.code_search(
            query=code_snippet,
            language_filter=language,
            element_type_filter=element_type,
            max_results=max_results,
        )

        return [
            {
                "id": result.id,
                "file_path": result.file_path,
                "element_name": result.element_name,
                "element_type": result.element_type,
                "signature": result.signature,
                "docstring": result.docstring[:200] + "..."
                if len(result.docstring) > 200
                else result.docstring,
                "language": result.language,
                "similarity": result.similarity,
            }
            for result in results
        ]


# ============================================
# EXAMPLE USAGE
# ============================================


async def main():
    """Example usage of vector search functionality."""
    try:
        # Initialize client
        async with VectorSearchClient() as client:
            # Test semantic search
            print("=== Semantic Search ===")
            results = await client.semantic_search(
                "error handling in Python", max_results=5
            )
            for result in results[:3]:
                print(f"- {result.title} (similarity: {result.similarity:.3f})")
                print(f"  Content: {result.content[:100]}...")
                print()

            # Test code search
            print("=== Code Search ===")
            code_results = await client.code_search(
                "async function database", max_results=5
            )
            for result in code_results[:3]:
                print(
                    f"- {result.element_name} in {result.file_path} (similarity: {result.similarity:.3f})"
                )
                print(f"  Signature: {result.signature}")
                print()

            # Test embedding stats
            print("=== Embedding Statistics ===")
            stats = await client.get_embedding_stats()
            print(f"Overall coverage: {stats['overall']['coverage_percentage']}%")
            for source_stat in stats["by_source_type"]:
                print(
                    f"- {source_stat['source_type']}: {source_stat['embedding_coverage_pct']}%"
                )

    except Exception as e:
        logger.error(f"Example failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
