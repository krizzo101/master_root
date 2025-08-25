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
    from apps.knowledge_system.hybrid_search import HybridSearch
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
        self.smart_enrichment = None

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

                # Initialize smart enrichment for automatic enrichment
                try:
                    from apps.knowledge_system.smart_enrichment import SmartEnrichment

                    self.smart_enrichment = SmartEnrichment(self.neo4j_driver)
                    logger.info("Smart enrichment initialized for automatic enrichment")
                except ImportError as ie:
                    logger.warning(f"Smart enrichment not available: {ie}")
                except Exception as e:
                    logger.warning(f"Smart enrichment initialization failed: {e}")
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
        superseded_ids = []

        # First try embedding-based similarity if available
        if self.embedding_service and self.neo4j_driver:
            try:
                # Generate embedding for new content
                embed_text = f"{knowledge_type}: {content}"
                logger.info(
                    f"Generating embedding for duplicate check: {embed_text[:50]}..."
                )
                new_embedding = self.embedding_service.generate_embedding(embed_text)
                logger.info(f"Generated embedding with {len(new_embedding)} dimensions")

                # Query for similar knowledge with embeddings
                query = """
                MATCH (k:Knowledge)
                WHERE k.knowledge_type = $knowledge_type
                AND (k.deprecated = false OR k.deprecated IS NULL)
                AND k.embedding IS NOT NULL
                RETURN k.knowledge_id as id,
                       k.content as content,
                       k.embedding as embedding,
                       k.confidence_score as confidence
                ORDER BY k.created_at DESC
                LIMIT 20
                """
                params = {"knowledge_type": knowledge_type}

                with self.neo4j_driver.session() as session:
                    result = session.run(query, params)
                    found_count = 0
                    for record in result:
                        found_count += 1
                        existing_embedding = record["embedding"]
                        if existing_embedding:
                            # Calculate cosine similarity
                            import numpy as np

                            # Convert to numpy arrays if needed
                            new_emb_array = np.array(new_embedding)
                            existing_emb_array = np.array(existing_embedding)

                            similarity = np.dot(new_emb_array, existing_emb_array) / (
                                np.linalg.norm(new_emb_array)
                                * np.linalg.norm(existing_emb_array)
                            )
                            logger.debug(
                                f"Similarity with {record['id'][:8]}: {similarity:.4f}"
                            )

                            # Lower threshold to 0.75 for better duplicate detection (was 0.85)
                            if similarity >= 0.75:
                                superseded_ids.append(record["id"])
                                logger.info(
                                    f"Found superseded knowledge via embedding (similarity={similarity:.2f}): {record['id'][:8]}..."
                                )
                    logger.info(
                        f"Checked {found_count} existing entries for duplicates"
                    )
            except Exception as e:
                logger.warning(f"Embedding-based superseding check failed: {e}")

        # Fallback to word-based similarity if no embeddings or no matches found
        if not superseded_ids and self.neo4j_driver:
            try:
                query = """
                MATCH (k:Knowledge)
                WHERE k.knowledge_type = $knowledge_type
                AND k.deprecated IS NULL
                AND any(tag IN $tags WHERE tag IN k.tags)
                RETURN k.knowledge_id as id, k.content as content
                LIMIT 10
                """
                params = {"knowledge_type": knowledge_type, "tags": tags}

                with self.neo4j_driver.session() as session:
                    result = session.run(query, params)
                    for record in result:
                        existing_content = record["content"]
                        # Lower threshold to 0.6 for better detection
                        if self._is_similar(content, existing_content, threshold=0.6):
                            superseded_ids.append(record["id"])
                            logger.info(
                                f"Found superseded knowledge via word similarity: {record['id'][:8]}..."
                            )
            except Exception as e:
                logger.warning(f"Word-based superseding check failed: {e}")

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
        
        logger.info(f"DEBUG: superseded_ids returned from find_superseded_knowledge: {superseded_ids}")
        
        if superseded_ids:
            structured.supersedes = superseded_ids
            logger.info(
                f"This knowledge supersedes {len(superseded_ids)} existing entries"
            )
        else:
            logger.info("DEBUG: No superseded entries found (superseded_ids is empty)")

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

                    # Apply automatic enrichment if available
                    if self.smart_enrichment:
                        logger.info(f"Starting automatic enrichment for {knowledge_id}")
                        try:
                            # Prepare entry dict for enrichment
                            entry_for_enrichment = {
                                "knowledge_id": knowledge_id,
                                "content": structured.content,
                                "summary": structured.summary,
                                "tags": structured.tags,
                                "knowledge_type": structured.knowledge_type,
                                "embedding": embedding,
                                "supersedes": superseded_ids,
                            }

                            # Get enrichments (now synchronous)
                            enrichments = self.smart_enrichment.enrich_on_storage(
                                entry_for_enrichment, session=session
                            )
                            logger.info(f"Got enrichments: {enrichments.keys()}")

                            # Apply enrichments
                            from apps.knowledge_system.smart_enrichment import (
                                apply_enrichments_to_storage,
                            )

                            result = apply_enrichments_to_storage(
                                self.neo4j_driver,
                                knowledge_id,
                                enrichments,
                                session=session,
                            )
                            logger.info(
                                f"Apply result: {result}, Applied enrichment: confidence={enrichments.get('confidence'):.2f}, quality={enrichments.get('quality_score'):.2f}"
                            )
                        except Exception as e:
                            logger.error(f"ENRICHMENT FAILED: {e}")
                            import traceback

                            logger.error(f"Traceback: {traceback.format_exc()}")

                    # Mark superseded entries
                    logger.info(
                        f"About to mark superseded entries. superseded_ids: {superseded_ids}"
                    )
                    if superseded_ids:
                        logger.info(
                            f"Marking {len(superseded_ids)} entries as superseded by {knowledge_id}"
                        )
                        
                        # First, verify these nodes exist
                        verify_query = """
                        MATCH (k:Knowledge)
                        WHERE k.knowledge_id IN $ids
                        RETURN k.knowledge_id as id, k.content as content
                        """
                        verify_result = session.run(verify_query, {"ids": superseded_ids})
                        existing_nodes = list(verify_result)
                        logger.info(f"Found {len(existing_nodes)} nodes to deprecate out of {len(superseded_ids)} IDs")
                        for node in existing_nodes:
                            logger.info(f"  - Node {node['id'][:8]}... exists with content: {node['content'][:50]}...")
                        
                        if not existing_nodes:
                            logger.error(f"WARNING: None of the superseded IDs exist in the database! IDs: {superseded_ids}")
                        
                        deprecate_query = """
                        MATCH (k:Knowledge)
                        WHERE k.knowledge_id IN $ids
                        SET k.deprecated = true,
                            k.deprecated_at = datetime(),
                            k.superseded_by = $new_id
                        RETURN count(k) as deprecated_count
                        """
                        result = session.run(
                            deprecate_query,
                            {"ids": superseded_ids, "new_id": knowledge_id},
                        )
                        deprecated_count = result.single()["deprecated_count"]
                        logger.info(
                            f"Successfully marked {deprecated_count} entries as deprecated"
                        )
                        
                        # Verify the deprecation actually worked
                        verify_deprecation = """
                        MATCH (k:Knowledge)
                        WHERE k.knowledge_id IN $ids
                        RETURN k.knowledge_id as id, k.deprecated as deprecated, k.superseded_by as superseded_by
                        """
                        verify_dep_result = session.run(verify_deprecation, {"ids": superseded_ids})
                        for record in verify_dep_result:
                            logger.info(f"Verification - ID: {record['id'][:8]}..., deprecated: {record['deprecated']}, superseded_by: {record['superseded_by'][:8] if record['superseded_by'] else 'None'}...")

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
    """Enhanced knowledge query with direct execution and hybrid search"""

    def __init__(self):
        self.neo4j_driver = None
        self.vector_search = None
        self.cache = None
        self.embedding_service = None
        self.hybrid_search = None

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
                self.hybrid_search = HybridSearch()
                logger.info("RAG query components initialized with hybrid search")
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
        min_confidence: float = 0.0,  # CHANGED: Show ALL knowledge by default
        limit: int = 5,
        direct_execute: bool = True,
    ) -> Dict[str, Any]:
        """
        Query knowledge with optional direct execution and semantic search support.
        """
        # Try hybrid search if available
        if query_type in ["semantic", "hybrid"] and query_text and self.hybrid_search:
            try:
                # Determine strategy based on query type
                strategy = "hybrid" if query_type == "hybrid" else "vector"

                # Use hybrid search
                search_results = self.hybrid_search.search(
                    query=query_text,
                    limit=limit,
                    strategy=strategy,
                    expand_depth=1,
                    filters={"knowledge_type": knowledge_type}
                    if knowledge_type
                    else None,
                )

                if search_results:
                    # Convert search results to knowledge format
                    knowledge_items = []
                    for result in search_results:
                        item = {
                            "id": result.knowledge_id,
                            "type": result.knowledge_type,
                            "content": result.content,
                            "source": result.source,
                            "confidence": result.combined_score,
                            "vector_score": result.vector_score,
                            "graph_score": result.graph_score,
                            "relationships": result.relationships,
                        }
                        knowledge_items.append(item)

                    return {
                        "success": True,
                        "query_type": query_type,
                        "knowledge": knowledge_items,
                        "count": len(knowledge_items),
                        "strategy": strategy,
                    }
            except Exception as e:
                logger.warning(f"Hybrid search failed, falling back to keyword: {e}")
                query_type = "search"  # Fall back to keyword search

        # Legacy semantic search via vector search
        elif query_type == "semantic" and query_text:
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
            # Split multi-word queries and search for ALL words
            query_words = query_text.split() if query_text else []

            if len(query_words) > 1:
                # For multi-word queries, require ALL words to be present
                where_clauses = []
                for i, word in enumerate(query_words):
                    where_clauses.append(
                        f"""
                    (toLower(k.content) CONTAINS toLower($word{i})
                    OR toLower(k.summary) CONTAINS toLower($word{i})
                    OR any(tag IN k.tags WHERE toLower(tag) CONTAINS toLower($word{i})))
                    """
                    )

                where_condition = " AND ".join(where_clauses)

                cypher = f"""
                MATCH (k:Knowledge)
                WHERE (k.deprecated = false OR k.deprecated IS NULL)
                AND ({where_condition})
                AND (k.confidence_score >= $min_confidence OR k.confidence_score IS NULL)
                RETURN k.knowledge_id as id,
                       k.knowledge_type as type,
                       k.content as content,
                       k.summary as summary,
                       k.tags as tags,
                       k.confidence as confidence,
                       k.quality_score as quality_score,
                       k.usage_count as usage_count,
                       k.success_rate as success_rate,
                       k.relationships as relationships,
                       k.created_at as created_at
                ORDER BY k.confidence DESC, k.usage_count DESC
                LIMIT $limit
                """

                # Build params with individual words
                params = {"min_confidence": min_confidence, "limit": limit}
                for i, word in enumerate(query_words):
                    params[f"word{i}"] = word
            else:
                # Single word or empty query
                cypher = """
                MATCH (k:Knowledge)
                WHERE (k.deprecated = false OR k.deprecated IS NULL)
                AND (toLower(k.content) CONTAINS toLower($query_text)
                OR toLower(k.summary) CONTAINS toLower($query_text)
                OR any(tag IN k.tags WHERE toLower(tag) CONTAINS toLower($query_text))
                OR toLower(k.knowledge_type) CONTAINS toLower($query_text))
                AND (k.confidence_score >= $min_confidence OR k.confidence_score IS NULL)
                RETURN k.knowledge_id as id,
                       k.knowledge_type as type,
                       k.content as content,
                       k.summary as summary,
                       k.tags as tags,
                       k.confidence as confidence,
                       k.quality_score as quality_score,
                       k.usage_count as usage_count,
                       k.success_rate as success_rate,
                       k.relationships as relationships,
                       k.created_at as created_at
                ORDER BY k.confidence DESC, k.usage_count DESC
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
            WHERE (k.deprecated = false OR k.deprecated IS NULL)
            AND (k.confidence_score >= $min_confidence OR k.confidence_score IS NULL)
            RETURN k.knowledge_id as id,
                   k.knowledge_type as type,
                   k.content as content,
                   k.summary as summary,
                   k.tags as tags,
                   k.confidence as confidence,
                   k.quality_score as quality_score,
                   k.usage_count as usage_count,
                   k.success_rate as success_rate,
                   k.relationships as relationships,
                   k.created_at as created_at
            ORDER BY COALESCE(k.updated_at, k.created_at, datetime()) DESC
            LIMIT $limit
            """
            params = {"min_confidence": min_confidence, "limit": limit}

        elif query_type == "by_type":
            cypher = """
            MATCH (k:Knowledge)
            WHERE k.deprecated = false
            AND k.knowledge_type = $knowledge_type
            AND k.confidence_score >= $min_confidence
            RETURN k.knowledge_id as id,
                   k.knowledge_type as type,
                   k.content as content,
                   k.summary as summary,
                   k.tags as tags,
                   k.confidence as confidence,
                   k.quality_score as quality_score,
                   k.usage_count as usage_count,
                   k.success_rate as success_rate,
                   k.relationships as relationships,
                   k.created_at as created_at
            ORDER BY k.confidence DESC
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
            RETURN k.knowledge_id as id,
                   k.knowledge_type as type,
                   k.content as content,
                   k.summary as summary,
                   k.tags as tags,
                   k.confidence as confidence,
                   k.quality_score as quality_score,
                   k.usage_count as usage_count,
                   k.success_rate as success_rate,
                   k.relationships as relationships,
                   k.created_at as created_at
            ORDER BY k.confidence DESC
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
                        # Now we're returning individual fields, not the whole node
                        item = {
                            "id": record.get("id"),
                            "type": record.get("type"),
                            "content": record.get("content"),
                            "summary": record.get("summary"),
                            "tags": record.get("tags", []),
                            "confidence": record.get("confidence"),
                            "quality_score": record.get("quality_score"),
                            "usage_count": record.get("usage_count", 0),
                            "success_rate": record.get("success_rate", 0.0),
                            "relationships": record.get("relationships", []),
                            "created_at": str(record.get("created_at"))
                            if record.get("created_at")
                            else None,
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
