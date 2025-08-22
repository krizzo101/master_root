#!/usr/bin/env python3
"""
Enhanced Knowledge Tools with Nano Agent Middleware and Direct Execution

This module provides complete knowledge management with:
- Nano agent for intelligent data transformation
- Auto-embedding generation
- Direct Neo4j execution via db MCP tool
- Knowledge superseding and deprecation
"""

import asyncio
import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# Add path for imports
sys.path.insert(0, "/home/opsvi/master_root")

# Import embedding service
from apps.knowledge_system.embedding_service import get_embedding_service

# Import nano agent
from apps.knowledge_system.knowledge_nano_agent import KnowledgeSchema, get_nano_agent

# Import Neo4j client for direct execution
try:
    from neo4j import GraphDatabase

    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("Neo4j driver not available. Will use db MCP tool fallback.")

# Import RAG components
try:
    from apps.knowledge_system.simple_rag import (
        RAGContext,
        SimpleCache,
        SimpleVectorSearch,
    )

    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logging.warning("RAG components not available")

logger = logging.getLogger(__name__)


class EnhancedKnowledgeStore:
    """
    Complete knowledge storage with nano agent transformation,
    embedding generation, and direct execution.
    """

    def __init__(self):
        """Initialize the enhanced knowledge store"""
        self.nano_agent = get_nano_agent()
        self.embedding_service = None
        self.neo4j_driver = None
        self.vector_search = None
        self.cache = None
        self.rag_context = None

        # Try to initialize embedding service
        try:
            self.embedding_service = get_embedding_service()
            logger.info("Embedding service initialized")
        except Exception as e:
            logger.warning(f"Embedding service not available: {e}")

        # Try to initialize Neo4j driver
        if NEO4J_AVAILABLE:
            try:
                uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
                user = os.getenv("NEO4J_USER", "neo4j")
                password = os.getenv("NEO4J_PASSWORD", "password")
                self.neo4j_driver = GraphDatabase.driver(uri, auth=(user, password))
                logger.info("Neo4j driver initialized for direct execution")
            except Exception as e:
                logger.warning(f"Neo4j driver initialization failed: {e}")

        # Initialize RAG components
        if RAG_AVAILABLE:
            try:
                self.vector_search = SimpleVectorSearch()
                self.cache = SimpleCache()
                self.rag_context = RAGContext()
                logger.info("RAG components initialized")
            except Exception as e:
                logger.warning(f"RAG initialization failed: {e}")

    def generate_knowledge_id(self, content: str, knowledge_type: str) -> str:
        """Generate a unique knowledge ID"""
        id_source = (
            f"{knowledge_type}:{content[:100]}:{datetime.now(timezone.utc).isoformat()}"
        )
        return hashlib.sha256(id_source.encode()).hexdigest()[:16]

    async def find_superseded_knowledge(
        self, content: str, knowledge_type: str, tags: List[str]
    ) -> List[str]:
        """
        Find existing knowledge that might be superseded by new entry.

        Returns list of knowledge IDs that should be marked as superseded.
        """
        # Query for similar knowledge
        query = """
        MATCH (k:Knowledge)
        WHERE k.knowledge_type = $knowledge_type
        AND k.deprecated IS NULL
        AND any(tag IN $tags WHERE tag IN k.tags)
        RETURN k.knowledge_id as id, k.content as content, k.confidence_score as confidence
        ORDER BY k.confidence_score DESC
        LIMIT 10
        """

        params = {"knowledge_type": knowledge_type, "tags": tags}

        superseded_ids = []

        try:
            if self.neo4j_driver:
                with self.neo4j_driver.session() as session:
                    result = session.run(query, params)
                    for record in result:
                        # Simple similarity check - could be enhanced
                        existing_content = record["content"]
                        if self._is_similar(content, existing_content):
                            superseded_ids.append(record["id"])
        except Exception as e:
            logger.warning(f"Could not check for superseded knowledge: {e}")

        return superseded_ids

    def _is_similar(self, content1: str, content2: str, threshold: float = 0.7) -> bool:
        """
        Check if two content strings are similar enough to be considered duplicates.
        Simple implementation - could use embeddings for better similarity.
        """
        # Simple word overlap similarity
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        if not words1 or not words2:
            return False

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        similarity = len(intersection) / len(union)
        return similarity >= threshold

    async def store(
        self,
        raw_input: str,
        hint_type: Optional[str] = None,
        hint_tags: Optional[List[str]] = None,
        direct_execute: bool = True,
    ) -> Dict[str, Any]:
        """
        Complete knowledge storage pipeline.

        Args:
            raw_input: Raw knowledge text
            hint_type: Optional knowledge type hint
            hint_tags: Optional tag hints
            direct_execute: Whether to execute directly or return query

        Returns:
            Result with knowledge_id and execution status
        """
        # Step 1: Transform with nano agent
        structured = await self.nano_agent.transform_knowledge(
            raw_input=raw_input, hint_type=hint_type, hint_tags=hint_tags
        )

        # Step 2: Generate knowledge ID
        knowledge_id = self.generate_knowledge_id(
            structured.content, structured.knowledge_type
        )

        # Step 3: Find potentially superseded knowledge
        superseded_ids = await self.find_superseded_knowledge(
            structured.content, structured.knowledge_type, structured.tags
        )

        if superseded_ids:
            structured.supersedes = superseded_ids
            logger.info(
                f"This knowledge supersedes {len(superseded_ids)} existing entries"
            )

        # Step 4: Generate embedding
        embedding = None
        embedding_model = None

        if self.embedding_service:
            try:
                # Prepare text for embedding
                embed_text = f"{structured.knowledge_type}: {structured.content}"
                if structured.tags:
                    embed_text += f" Tags: {', '.join(structured.tags)}"

                embedding = self.embedding_service.generate_embedding(embed_text)
                embedding_model = self.embedding_service.model_name
                logger.info(f"Generated embedding with {len(embedding)} dimensions")

                # Index in vector search if available
                if self.vector_search and embedding:
                    try:
                        metadata = {
                            "knowledge_type": structured.knowledge_type,
                            "tags": structured.tags,
                            "confidence": structured.confidence_score,
                        }
                        self.vector_search.index_knowledge(
                            knowledge_id, embedding, metadata
                        )
                        logger.info(
                            f"Indexed knowledge {knowledge_id} in vector search"
                        )
                    except Exception as e:
                        logger.warning(f"Vector indexing failed: {e}")

                # Cache the embedding if available
                if self.cache and embedding:
                    try:
                        self.cache.cache_embedding(embed_text, embedding)
                        logger.info("Cached embedding for future use")
                    except Exception as e:
                        logger.warning(f"Embedding caching failed: {e}")

            except Exception as e:
                logger.warning(f"Embedding generation failed: {e}")

        # Step 5: Build Cypher query
        if embedding:
            query = """
            MERGE (k:Knowledge {knowledge_id: $knowledge_id})
            ON CREATE SET
                k.knowledge_type = $knowledge_type,
                k.content = $content,
                k.summary = $summary,
                k.context = $context,
                k.tags = $tags,
                k.confidence_score = $confidence_score,
                k.usage_count = 0,
                k.success_rate = 0.0,
                k.deprecated = false,
                k.created_at = datetime(),
                k.updated_at = datetime(),
                k.embedding = $embedding,
                k.embedding_model = $embedding_model,
                k.embedding_generated_at = datetime()
            ON MATCH SET
                k.updated_at = datetime(),
                k.content = $content,
                k.summary = $summary,
                k.context = $context,
                k.tags = $tags,
                k.embedding = $embedding,
                k.embedding_model = $embedding_model,
                k.embedding_generated_at = datetime()
            RETURN k.knowledge_id as id
            """
        else:
            query = """
            MERGE (k:Knowledge {knowledge_id: $knowledge_id})
            ON CREATE SET
                k.knowledge_type = $knowledge_type,
                k.content = $content,
                k.summary = $summary,
                k.context = $context,
                k.tags = $tags,
                k.confidence_score = $confidence_score,
                k.usage_count = 0,
                k.success_rate = 0.0,
                k.deprecated = false,
                k.created_at = datetime(),
                k.updated_at = datetime()
            ON MATCH SET
                k.updated_at = datetime(),
                k.content = $content,
                k.summary = $summary,
                k.context = $context,
                k.tags = $tags
            RETURN k.knowledge_id as id
            """

        # Prepare parameters
        params = {
            "knowledge_id": knowledge_id,
            "knowledge_type": structured.knowledge_type,
            "content": structured.content,
            "summary": structured.summary,
            "context": structured.context,  # Already a string now
            "tags": structured.tags,
            "confidence_score": structured.confidence_score,
        }

        if embedding:
            params["embedding"] = embedding
            params["embedding_model"] = embedding_model

        # Step 6: Execute or return query
        if direct_execute and self.neo4j_driver:
            try:
                with self.neo4j_driver.session() as session:
                    # Store the main knowledge
                    result = session.run(query, params)

                    # Mark superseded entries
                    if superseded_ids:
                        deprecate_query = """
                        MATCH (k:Knowledge)
                        WHERE k.knowledge_id IN $ids
                        SET k.deprecated = true,
                            k.deprecated_at = datetime(),
                            k.superseded_by = $new_id
                        """
                        session.run(
                            deprecate_query,
                            {"ids": superseded_ids, "new_id": knowledge_id},
                        )

                    # Create relationships
                    if structured.related_to:
                        for related_id in structured.related_to:
                            rel_query = """
                            MATCH (k1:Knowledge {knowledge_id: $source_id})
                            MATCH (k2:Knowledge {knowledge_id: $target_id})
                            MERGE (k1)-[:RELATED_TO]->(k2)
                            """
                            session.run(
                                rel_query,
                                {"source_id": knowledge_id, "target_id": related_id},
                            )

                return {
                    "success": True,
                    "knowledge_id": knowledge_id,
                    "stored": True,
                    "embedding_generated": embedding is not None,
                    "superseded_count": len(superseded_ids),
                    "knowledge_type": structured.knowledge_type,
                    "tags": structured.tags,
                    "confidence": structured.confidence_score,
                }
            except Exception as e:
                logger.error(f"Direct execution failed: {e}")
                # Fall back to returning query

        # Return query for external execution
        return {
            "success": True,
            "knowledge_id": knowledge_id,
            "cypher_query": query,
            "params": params,
            "superseded_ids": superseded_ids,
            "instruction": "Execute via mcp__db__write_neo4j_cypher",
            "embedding_generated": embedding is not None,
        }

    def store_sync(
        self,
        raw_input: str,
        hint_type: Optional[str] = None,
        hint_tags: Optional[List[str]] = None,
        direct_execute: bool = True,
    ) -> Dict[str, Any]:
        """Synchronous wrapper for store method"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            self.store(raw_input, hint_type, hint_tags, direct_execute)
        )


class EnhancedKnowledgeQuery:
    """Enhanced knowledge query with direct execution and semantic search"""

    def __init__(self):
        self.neo4j_driver = None
        self.vector_search = None
        self.cache = None
        self.embedding_service = None

        if NEO4J_AVAILABLE:
            try:
                uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
                user = os.getenv("NEO4J_USER", "neo4j")
                password = os.getenv("NEO4J_PASSWORD", "password")
                self.neo4j_driver = GraphDatabase.driver(uri, auth=(user, password))
            except Exception as e:
                logger.warning(f"Neo4j driver initialization failed: {e}")

        # Initialize RAG components for semantic search
        if RAG_AVAILABLE:
            try:
                self.vector_search = SimpleVectorSearch()
                self.cache = SimpleCache()
                logger.info("RAG query components initialized")
            except Exception as e:
                logger.warning(f"RAG query initialization failed: {e}")

        # Initialize embedding service for semantic queries
        try:
            self.embedding_service = get_embedding_service()
        except Exception as e:
            logger.warning(f"Embedding service not available for queries: {e}")

    def query(
        self,
        query_type: str,
        query_text: Optional[str] = None,
        knowledge_type: Optional[str] = None,
        min_confidence: float = 0.7,
        limit: int = 5,
        direct_execute: bool = True,
    ) -> Dict[str, Any]:
        """
        Query knowledge with optional direct execution and semantic search support.
        """
        # Try semantic search first if available
        if query_type == "semantic" and query_text:
            # Check cache first
            if self.cache:
                cached_results = self.cache.get_cached_search(query_text)
                if cached_results:
                    logger.info(f"Cache hit for semantic search: {query_text[:50]}...")
                    # Fetch full knowledge from Neo4j
                    knowledge_ids = cached_results[:limit]
                    if knowledge_ids and direct_execute and self.neo4j_driver:
                        cypher = """
                        MATCH (k:Knowledge)
                        WHERE k.knowledge_id IN $knowledge_ids
                        AND k.deprecated = false
                        RETURN k
                        """
                        params = {"knowledge_ids": knowledge_ids}
                        try:
                            with self.neo4j_driver.session() as session:
                                result = session.run(cypher, params)
                                knowledge = [dict(record["k"]) for record in result]
                                return {
                                    "success": True,
                                    "query_type": "semantic_cached",
                                    "knowledge": knowledge,
                                    "count": len(knowledge),
                                }
                        except Exception as e:
                            logger.error(
                                f"Failed to fetch cached semantic results: {e}"
                            )

            # Generate embedding and search
            if self.embedding_service and self.vector_search:
                try:
                    # Get or generate embedding
                    embedding = None
                    if self.cache:
                        embedding = self.cache.get_cached_embedding(query_text)

                    if not embedding:
                        embedding = self.embedding_service.generate_embedding(
                            query_text
                        )
                        if self.cache and embedding:
                            self.cache.cache_embedding(query_text, embedding)

                    # Search in vector store
                    if embedding:
                        knowledge_ids = self.vector_search.search_similar(
                            embedding, limit
                        )

                        # Cache the results
                        if self.cache and knowledge_ids:
                            self.cache.cache_search(query_text, knowledge_ids)

                        # Fetch full knowledge from Neo4j
                        if knowledge_ids and direct_execute and self.neo4j_driver:
                            cypher = """
                            MATCH (k:Knowledge)
                            WHERE k.knowledge_id IN $knowledge_ids
                            AND k.deprecated = false
                            RETURN k
                            """
                            params = {"knowledge_ids": knowledge_ids}
                            try:
                                with self.neo4j_driver.session() as session:
                                    result = session.run(cypher, params)
                                    knowledge = [dict(record["k"]) for record in result]
                                    return {
                                        "success": True,
                                        "query_type": "semantic",
                                        "knowledge": knowledge,
                                        "count": len(knowledge),
                                    }
                            except Exception as e:
                                logger.error(
                                    f"Failed to fetch semantic search results: {e}"
                                )

                        return {
                            "success": True,
                            "query_type": "semantic",
                            "knowledge_ids": knowledge_ids,
                            "instruction": "Fetch via Neo4j with provided IDs",
                        }

                except Exception as e:
                    logger.warning(
                        f"Semantic search failed, falling back to keyword: {e}"
                    )
                    query_type = "search"  # Fall back to keyword search

        # Build query based on type
        if query_type == "search":
            cypher = """
            MATCH (k:Knowledge)
            WHERE k.deprecated = false
            AND (toLower(k.content) CONTAINS toLower($query_text)
            OR any(tag IN k.tags WHERE toLower(tag) CONTAINS toLower($query_text)))
            AND k.confidence_score >= $min_confidence
            RETURN k
            ORDER BY k.confidence_score DESC, k.usage_count DESC
            LIMIT $limit
            """
            params = {
                "query_text": query_text or "",
                "min_confidence": min_confidence,
                "limit": limit,
            }

        elif query_type == "recent":
            cypher = """
            MATCH (k:Knowledge)
            WHERE k.deprecated = false
            AND k.confidence_score >= $min_confidence
            RETURN k
            ORDER BY k.updated_at DESC
            LIMIT $limit
            """
            params = {"min_confidence": min_confidence, "limit": limit}

        elif query_type == "by_type":
            cypher = """
            MATCH (k:Knowledge)
            WHERE k.deprecated = false
            AND k.knowledge_type = $knowledge_type
            AND k.confidence_score >= $min_confidence
            RETURN k
            ORDER BY k.confidence_score DESC
            LIMIT $limit
            """
            params = {
                "knowledge_type": knowledge_type or "CODE_PATTERN",
                "min_confidence": min_confidence,
                "limit": limit,
            }

        else:
            cypher = """
            MATCH (k:Knowledge)
            WHERE k.deprecated = false
            AND k.confidence_score >= $min_confidence
            RETURN k
            ORDER BY k.confidence_score DESC
            LIMIT $limit
            """
            params = {"min_confidence": min_confidence, "limit": limit}

        # Execute or return query
        if direct_execute and self.neo4j_driver:
            try:
                with self.neo4j_driver.session() as session:
                    result = session.run(cypher, params)
                    knowledge_items = []
                    for record in result:
                        k = record["k"]
                        # Clean up the response (no embeddings)
                        item = {
                            "id": k.get("knowledge_id"),
                            "type": k.get("knowledge_type"),
                            "content": k.get("content"),
                            "summary": k.get("summary"),
                            "tags": k.get("tags", []),
                            "confidence": k.get("confidence_score"),
                            "usage_count": k.get("usage_count", 0),
                            "success_rate": k.get("success_rate", 0.0),
                        }
                        knowledge_items.append(item)

                    return {
                        "success": True,
                        "results": knowledge_items,
                        "count": len(knowledge_items),
                        "query_type": query_type,
                    }
            except Exception as e:
                logger.error(f"Direct query execution failed: {e}")

        # Return query for external execution
        return {
            "success": True,
            "cypher_query": cypher,
            "params": params,
            "instruction": "Execute via mcp__db__read_neo4j_cypher",
        }


# Singleton instances
_store = None
_query = None


def get_enhanced_store() -> EnhancedKnowledgeStore:
    """Get or create the enhanced store instance"""
    global _store
    if _store is None:
        _store = EnhancedKnowledgeStore()
    return _store


def get_enhanced_query() -> EnhancedKnowledgeQuery:
    """Get or create the enhanced query instance"""
    global _query
    if _query is None:
        _query = EnhancedKnowledgeQuery()
    return _query
