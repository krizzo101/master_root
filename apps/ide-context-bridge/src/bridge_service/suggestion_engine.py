#!/usr/bin/env python3
"""
Suggestion Engine for IDE Context Bridge

Generates intelligent code suggestions based on context data and embeddings.
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from .context_manager import ContextManager
from .models import CursorPosition, QueryFilters, SearchResult, Suggestion

logger = logging.getLogger(__name__)


class SuggestionEngine:
    """
    Generates intelligent code suggestions using context data and embeddings.

    Integrates with:
    - Context database for semantic search
    - Embedding service for vector similarity
    - Chat history for conversational context
    - Code analysis for syntax-aware suggestions
    """

    def __init__(
        self, context_manager: ContextManager, embedding_service_url: str, config: Any
    ):
        """Initialize suggestion engine."""
        self.context_manager = context_manager
        self.embedding_service_url = embedding_service_url
        self.config = config

        # HTTP session for embedding service
        self.http_session: Optional[aiohttp.ClientSession] = None

        # Suggestion caches
        self.suggestion_cache: Dict[str, List[Suggestion]] = {}
        self.search_cache: Dict[str, List[SearchResult]] = {}

        # Performance tracking
        self.suggestion_count = 0
        self.search_count = 0
        self.cache_hits = 0

    async def initialize(self):
        """Initialize the suggestion engine."""
        try:
            # Initialize HTTP session
            self.http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )

            # Test embedding service connection
            await self._test_embedding_service()

            logger.info("Suggestion engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize suggestion engine: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources."""
        if self.http_session:
            await self.http_session.close()
        logger.info("Suggestion engine cleanup complete")

    async def generate_suggestions(
        self,
        session_id: str,
        file_path: str,
        cursor_position: CursorPosition,
        context: Optional[str] = None,
        suggestion_types: List[str] = None,
    ) -> List[Suggestion]:
        """
        Generate intelligent code suggestions for current context.

        Args:
            session_id: Session identifier
            file_path: Current file path
            cursor_position: Current cursor position
            context: Additional context string
            suggestion_types: Types of suggestions to generate

        Returns:
            List of code suggestions
        """
        start_time = time.time()

        try:
            if suggestion_types is None:
                suggestion_types = ["completion", "refactor", "documentation"]

            # Get current IDE context
            ide_context = await self.context_manager.get_context(session_id)
            if not ide_context:
                logger.warning(f"No IDE context found for session {session_id}")
                return []

            # Build context query
            query_parts = []
            if context:
                query_parts.append(context)

            if ide_context.active_file:
                query_parts.append(f"file:{ide_context.active_file}")

            if ide_context.language:
                query_parts.append(f"language:{ide_context.language}")

            query_text = " ".join(query_parts)

            # Check cache first
            cache_key = self._build_cache_key(
                session_id, file_path, cursor_position, query_text
            )
            if cache_key in self.suggestion_cache:
                self.cache_hits += 1
                return self.suggestion_cache[cache_key]

            suggestions = []

            # Generate different types of suggestions
            for suggestion_type in suggestion_types:
                type_suggestions = await self._generate_suggestions_by_type(
                    suggestion_type,
                    session_id,
                    file_path,
                    cursor_position,
                    query_text,
                    ide_context,
                )
                suggestions.extend(type_suggestions)

            # Sort by priority and confidence
            suggestions.sort(key=lambda s: (s.priority, s.confidence), reverse=True)

            # Limit results
            max_suggestions = getattr(self.config, "max_suggestions", 10)
            suggestions = suggestions[:max_suggestions]

            # Cache results
            self.suggestion_cache[cache_key] = suggestions
            self.suggestion_count += len(suggestions)

            duration = time.time() - start_time
            logger.info(f"Generated {len(suggestions)} suggestions in {duration:.3f}s")

            return suggestions

        except Exception as e:
            logger.error(f"Failed to generate suggestions: {e}")
            return []

    async def search_context(
        self,
        query: str,
        search_type: str = "hybrid",
        filters: Optional[QueryFilters] = None,
        max_results: int = 10,
    ) -> List[SearchResult]:
        """
        Search context items using semantic similarity.

        Args:
            query: Search query text
            search_type: Type of search (semantic, code, hybrid, chat_history)
            filters: Search filters
            max_results: Maximum number of results

        Returns:
            List of search results
        """
        start_time = time.time()

        try:
            # Check cache
            cache_key = f"{query}:{search_type}:{json.dumps(asdict(filters) if filters else {})}"
            if cache_key in self.search_cache:
                self.cache_hits += 1
                return self.search_cache[cache_key]

            # Generate query embedding if semantic search
            embedding = None
            if search_type in ["semantic", "hybrid"]:
                embedding = await self._get_embedding(query)

            # Search database
            results = await self._search_database(
                query, search_type, embedding, filters, max_results
            )

            # Convert to SearchResult objects
            search_results = []
            for result in results:
                search_result = SearchResult(
                    id=result.get("id", ""),
                    source_type=result.get("source_type", "unknown"),
                    entity_type=result.get("entity_type", "unknown"),
                    title=result.get("title", ""),
                    content=result.get("content", ""),
                    file_path=result.get("file_path"),
                    similarity=result.get("similarity", 0.0),
                    relevance_score=result.get("relevance_score", 0.0),
                    metadata=result.get("metadata", {}),
                )
                search_results.append(search_result)

            # Cache results
            self.search_cache[cache_key] = search_results
            self.search_count += 1

            duration = time.time() - start_time
            logger.info(
                f"Search returned {len(search_results)} results in {duration:.3f}s"
            )

            return search_results

        except Exception as e:
            logger.error(f"Context search failed: {e}")
            return []

    async def _generate_suggestions_by_type(
        self,
        suggestion_type: str,
        session_id: str,
        file_path: str,
        cursor_position: CursorPosition,
        query_text: str,
        ide_context: Any,
    ) -> List[Suggestion]:
        """Generate suggestions for a specific type."""
        if suggestion_type == "completion":
            return await self._generate_completion_suggestions(
                session_id, file_path, cursor_position, query_text, ide_context
            )
        elif suggestion_type == "refactor":
            return await self._generate_refactor_suggestions(
                session_id, file_path, cursor_position, query_text, ide_context
            )
        elif suggestion_type == "fix":
            return await self._generate_fix_suggestions(
                session_id, file_path, cursor_position, query_text, ide_context
            )
        elif suggestion_type == "documentation":
            return await self._generate_documentation_suggestions(
                session_id, file_path, cursor_position, query_text, ide_context
            )
        else:
            return []

    async def _generate_completion_suggestions(
        self,
        session_id: str,
        file_path: str,
        cursor_position: CursorPosition,
        query_text: str,
        ide_context: Any,
    ) -> List[Suggestion]:
        """Generate code completion suggestions."""
        suggestions = []

        try:
            # Search for similar code patterns
            search_results = await self.search_context(
                query=query_text, search_type="code", max_results=5
            )

            for i, result in enumerate(search_results):
                if result.source_type in ["code", "git", "chat"]:
                    suggestion = Suggestion(
                        type="completion",
                        priority=8 - i,  # Higher priority for better matches
                        confidence=result.similarity,
                        title=f"Code completion from {result.source_type}",
                        description=f"Based on similar pattern: {result.title[:100]}",
                        code_snippet=self._extract_code_snippet(result.content),
                        file_path=file_path,
                        line_range=[cursor_position.line, cursor_position.line + 1],
                        source_context_id=result.id,
                    )
                    suggestions.append(suggestion)

        except Exception as e:
            logger.error(f"Failed to generate completion suggestions: {e}")

        return suggestions

    async def _generate_refactor_suggestions(
        self,
        session_id: str,
        file_path: str,
        cursor_position: CursorPosition,
        query_text: str,
        ide_context: Any,
    ) -> List[Suggestion]:
        """Generate refactoring suggestions."""
        suggestions = []

        try:
            # Look for refactoring patterns in chat history
            search_results = await self.search_context(
                query=f"refactor {query_text}",
                search_type="chat_history",
                max_results=3,
            )

            for i, result in enumerate(search_results):
                suggestion = Suggestion(
                    type="refactor",
                    priority=6 - i,
                    confidence=result.relevance_score,
                    title=f"Refactoring suggestion",
                    description=f"Based on previous discussion: {result.title[:100]}",
                    code_snippet=self._extract_code_snippet(result.content),
                    file_path=file_path,
                    source_context_id=result.id,
                )
                suggestions.append(suggestion)

        except Exception as e:
            logger.error(f"Failed to generate refactor suggestions: {e}")

        return suggestions

    async def _generate_fix_suggestions(
        self,
        session_id: str,
        file_path: str,
        cursor_position: CursorPosition,
        query_text: str,
        ide_context: Any,
    ) -> List[Suggestion]:
        """Generate bug fix suggestions."""
        suggestions = []

        try:
            # Search for error-related discussions
            search_results = await self.search_context(
                query=f"error fix bug {query_text}", search_type="hybrid", max_results=3
            )

            for i, result in enumerate(search_results):
                suggestion = Suggestion(
                    type="fix",
                    priority=7 - i,
                    confidence=result.relevance_score,
                    title=f"Bug fix suggestion",
                    description=f"Based on similar issue: {result.title[:100]}",
                    code_snippet=self._extract_code_snippet(result.content),
                    file_path=file_path,
                    source_context_id=result.id,
                )
                suggestions.append(suggestion)

        except Exception as e:
            logger.error(f"Failed to generate fix suggestions: {e}")

        return suggestions

    async def _generate_documentation_suggestions(
        self,
        session_id: str,
        file_path: str,
        cursor_position: CursorPosition,
        query_text: str,
        ide_context: Any,
    ) -> List[Suggestion]:
        """Generate documentation suggestions."""
        suggestions = []

        try:
            # Search for documentation patterns
            search_results = await self.search_context(
                query=f"documentation comment docstring {query_text}",
                search_type="semantic",
                max_results=2,
            )

            for i, result in enumerate(search_results):
                suggestion = Suggestion(
                    type="documentation",
                    priority=5 - i,
                    confidence=result.similarity,
                    title=f"Documentation suggestion",
                    description=f"Add documentation based on: {result.title[:100]}",
                    code_snippet=self._generate_documentation_template(result.content),
                    file_path=file_path,
                    line_range=[cursor_position.line, cursor_position.line],
                    source_context_id=result.id,
                )
                suggestions.append(suggestion)

        except Exception as e:
            logger.error(f"Failed to generate documentation suggestions: {e}")

        return suggestions

    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding vector for text."""
        try:
            if not self.http_session:
                return None

            async with self.http_session.post(
                f"{self.embedding_service_url}/embed", json={"text": text}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("embedding")
                else:
                    logger.error(f"Embedding service returned status {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            return None

    async def _search_database(
        self,
        query: str,
        search_type: str,
        embedding: Optional[List[float]],
        filters: Optional[QueryFilters],
        max_results: int,
    ) -> List[Dict[str, Any]]:
        """Search the context database."""
        try:
            if not self.context_manager.db_pool:
                return []

            async with self.context_manager.db_pool.acquire() as conn:
                if search_type == "semantic" and embedding:
                    # Vector similarity search
                    query_sql = """
                        SELECT *, 1 - (embedding <=> $1::vector) as similarity,
                               1 - (embedding <=> $1::vector) as relevance_score
                        FROM context_items
                        WHERE embedding IS NOT NULL
                        ORDER BY embedding <=> $1::vector
                        LIMIT $2
                    """
                    rows = await conn.fetch(query_sql, embedding, max_results)

                elif search_type == "code":
                    # Text search with code focus
                    query_sql = """
                        SELECT *, ts_rank(search_vector, plainto_tsquery('english', $1)) as similarity,
                               ts_rank(search_vector, plainto_tsquery('english', $1)) as relevance_score
                        FROM context_items
                        WHERE search_vector @@ plainto_tsquery('english', $1)
                        AND (source_type IN ('git', 'code') OR entity_type LIKE '%function%' OR entity_type LIKE '%class%')
                        ORDER BY similarity DESC
                        LIMIT $2
                    """
                    rows = await conn.fetch(query_sql, query, max_results)

                elif search_type == "chat_history":
                    # Chat history search
                    query_sql = """
                        SELECT *, ts_rank(search_vector, plainto_tsquery('english', $1)) as similarity,
                               ts_rank(search_vector, plainto_tsquery('english', $1)) as relevance_score
                        FROM context_items
                        WHERE search_vector @@ plainto_tsquery('english', $1)
                        AND source_type = 'chat'
                        ORDER BY timestamp DESC, similarity DESC
                        LIMIT $2
                    """
                    rows = await conn.fetch(query_sql, query, max_results)

                else:  # hybrid or fallback
                    # Combined search
                    if embedding:
                        query_sql = """
                            SELECT *,
                                   GREATEST(
                                       1 - (embedding <=> $1::vector),
                                       ts_rank(search_vector, plainto_tsquery('english', $2))
                                   ) as similarity,
                                   (1 - (embedding <=> $1::vector) +
                                    ts_rank(search_vector, plainto_tsquery('english', $2))) / 2 as relevance_score
                            FROM context_items
                            WHERE (embedding IS NOT NULL OR search_vector @@ plainto_tsquery('english', $2))
                            ORDER BY similarity DESC
                            LIMIT $3
                        """
                        rows = await conn.fetch(
                            query_sql, embedding, query, max_results
                        )
                    else:
                        # Text search only
                        query_sql = """
                            SELECT *, ts_rank(search_vector, plainto_tsquery('english', $1)) as similarity,
                                   ts_rank(search_vector, plainto_tsquery('english', $1)) as relevance_score
                            FROM context_items
                            WHERE search_vector @@ plainto_tsquery('english', $1)
                            ORDER BY similarity DESC
                            LIMIT $2
                        """
                        rows = await conn.fetch(query_sql, query, max_results)

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Database search failed: {e}")
            return []

    def _build_cache_key(
        self,
        session_id: str,
        file_path: str,
        cursor_position: CursorPosition,
        query: str,
    ) -> str:
        """Build cache key for suggestions."""
        return f"{session_id}:{file_path}:{cursor_position.line}:{cursor_position.column}:{hash(query)}"

    def _extract_code_snippet(self, content: str, max_lines: int = 10) -> str:
        """Extract relevant code snippet from content."""
        lines = content.split("\n")

        # Look for code blocks
        code_start = -1
        for i, line in enumerate(lines):
            if any(
                marker in line
                for marker in [
                    "```",
                    "def ",
                    "class ",
                    "function ",
                    "const ",
                    "let ",
                    "var ",
                ]
            ):
                code_start = i
                break

        if code_start >= 0:
            # Extract code block
            code_lines = lines[code_start : code_start + max_lines]
            return "\n".join(code_lines).strip()
        else:
            # Return first few lines
            return "\n".join(lines[:max_lines]).strip()

    def _generate_documentation_template(self, content: str) -> str:
        """Generate documentation template based on content."""
        # Simple documentation template
        template = f'''"""
{content[:100]}...

TODO: Add detailed documentation
"""'''
        return template

    async def _test_embedding_service(self):
        """Test connection to embedding service."""
        try:
            if not self.http_session:
                return

            async with self.http_session.get(
                f"{self.embedding_service_url}/health"
            ) as response:
                if response.status != 200:
                    logger.warning(
                        f"Embedding service health check failed: {response.status}"
                    )
                else:
                    logger.info("Embedding service connection verified")

        except Exception as e:
            logger.warning(f"Could not connect to embedding service: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get suggestion engine statistics."""
        return {
            "suggestions_generated": self.suggestion_count,
            "searches_performed": self.search_count,
            "cache_hits": self.cache_hits,
            "cache_size": len(self.suggestion_cache) + len(self.search_cache),
            "embedding_service_url": self.embedding_service_url,
        }
