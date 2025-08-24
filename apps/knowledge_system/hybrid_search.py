#!/usr/bin/env python3
"""
Hybrid Search System - Combines vector similarity with graph traversal
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from neo4j import GraphDatabase
from qdrant_client import QdrantClient

from apps.knowledge_system.embedding_service import get_embedding_service
from apps.knowledge_system.simple_rag import SimpleCache

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Unified search result with combined scoring"""

    knowledge_id: str
    content: str
    source: str
    knowledge_type: str
    vector_score: float
    graph_score: float
    combined_score: float
    relationships: Dict[str, List[str]]  # relationship_type -> [connected_ids]
    metadata: Dict[str, Any]


class HybridSearch:
    """
    Advanced search combining vector similarity and graph traversal

    Search strategies:
    1. Vector-first: Find similar by embedding, expand via graph
    2. Graph-first: Start from known nodes, traverse relationships
    3. Hybrid: Combine both approaches with weighted scoring
    """

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_auth: tuple = ("neo4j", "password"),
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "knowledge_vectors",
    ):
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=neo4j_auth)
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = collection_name
        self.embedding_service = get_embedding_service()
        self.cache = SimpleCache()

        # Scoring weights
        self.vector_weight = 0.6
        self.graph_weight = 0.4

    def search(
        self,
        query: str,
        limit: int = 10,
        strategy: str = "hybrid",
        expand_depth: int = 1,
        filters: Optional[Dict] = None,
    ) -> List[SearchResult]:
        """
        Main search interface

        Args:
            query: Search query text
            limit: Maximum results to return
            strategy: "vector", "graph", or "hybrid"
            expand_depth: How many hops to traverse in graph
            filters: Optional filters (knowledge_type, tags, etc.)
        """

        if strategy == "vector":
            return self._vector_search(query, limit, expand_depth, filters)
        elif strategy == "graph":
            return self._graph_search(query, limit, expand_depth, filters)
        else:  # hybrid
            return self._hybrid_search(query, limit, expand_depth, filters)

    def _vector_search(
        self, query: str, limit: int, expand_depth: int, filters: Optional[Dict]
    ) -> List[SearchResult]:
        """Vector similarity search with optional graph expansion"""

        # Generate query embedding
        embedding = self.embedding_service.generate_embedding(query)

        # Search in Qdrant
        search_results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            limit=limit * 2,  # Get more for filtering
            query_filter=self._build_qdrant_filter(filters) if filters else None,
        )

        results = []
        with self.neo4j_driver.session() as session:
            for hit in search_results[:limit]:
                knowledge_id = hit.payload.get("knowledge_id")

                # Get full knowledge from Neo4j
                result = session.run(
                    """
                    MATCH (k:Knowledge {knowledge_id: $kid})
                    RETURN k
                """,
                    kid=knowledge_id,
                )

                record = result.single()
                if record:
                    node = record["k"]

                    # Get relationships and calculate graph score if expanding
                    relationships = {}
                    graph_score = 0.0

                    if expand_depth > 0:
                        relationships = self._get_relationships(
                            session, knowledge_id, expand_depth
                        )
                        # Calculate graph score based on relationship density
                        # More relationships = higher graph importance
                        total_relationships = sum(
                            len(v) for v in relationships.values()
                        )
                        if total_relationships > 0:
                            # Normalize by relationship types and count
                            graph_score = min(1.0, total_relationships / 10.0)

                    results.append(
                        SearchResult(
                            knowledge_id=knowledge_id,
                            content=node.get("content", ""),
                            source=node.get("source", ""),
                            knowledge_type=node.get("knowledge_type", ""),
                            vector_score=hit.score,
                            graph_score=graph_score,
                            combined_score=hit.score * (1 - self.graph_weight)
                            + graph_score * self.graph_weight
                            if graph_score > 0
                            else hit.score,
                            relationships=relationships,
                            metadata=dict(node),
                        )
                    )

        return results

    def _graph_search(
        self, query: str, limit: int, expand_depth: int, filters: Optional[Dict]
    ) -> List[SearchResult]:
        """Graph traversal search starting from seed nodes"""

        results = []
        with self.neo4j_driver.session() as session:
            # Find seed nodes based on text match
            query_parts = query.lower().split()

            cypher = """
                MATCH (k:Knowledge)
                WHERE k.direct_ingestion = true
                AND any(part IN $query_parts WHERE toLower(k.content) CONTAINS part)
            """

            if filters:
                if "knowledge_type" in filters:
                    cypher += " AND k.knowledge_type = $knowledge_type"
                if "tags" in filters:
                    cypher += " AND any(tag IN $tags WHERE tag IN k.tags)"

            cypher += """
                WITH k,
                     SIZE([part IN $query_parts WHERE toLower(k.content) CONTAINS part]) as match_count
                ORDER BY match_count DESC
                LIMIT $seed_limit
                RETURN k, match_count
            """

            params = {"query_parts": query_parts, "seed_limit": min(10, limit)}
            if filters:
                params.update(filters)

            result = session.run(cypher, params)

            # Expand from seed nodes
            seen_ids = set()
            for record in result:
                node = record["k"]
                knowledge_id = node["knowledge_id"]

                if knowledge_id not in seen_ids:
                    seen_ids.add(knowledge_id)

                    # Get expanded network
                    expanded = self._expand_from_node(
                        session, knowledge_id, expand_depth
                    )

                    # Calculate graph scores based on distance
                    for exp_node, distance in expanded:
                        if exp_node["knowledge_id"] not in seen_ids:
                            seen_ids.add(exp_node["knowledge_id"])

                            # Graph score decreases with distance
                            graph_score = 1.0 / (1 + distance)

                            results.append(
                                SearchResult(
                                    knowledge_id=exp_node["knowledge_id"],
                                    content=exp_node.get("content", ""),
                                    source=exp_node.get("source", ""),
                                    knowledge_type=exp_node.get("knowledge_type", ""),
                                    vector_score=0.0,
                                    graph_score=graph_score,
                                    combined_score=graph_score,
                                    relationships=self._get_relationships(
                                        session, exp_node["knowledge_id"], 1
                                    ),
                                    metadata=dict(exp_node),
                                )
                            )

        # Sort by score and limit
        results.sort(key=lambda x: x.combined_score, reverse=True)
        return results[:limit]

    def _hybrid_search(
        self, query: str, limit: int, expand_depth: int, filters: Optional[Dict]
    ) -> List[SearchResult]:
        """Combined vector and graph search with score fusion"""

        # Get results from both strategies
        # Get vector results WITH graph expansion
        vector_results = self._vector_search(query, limit, expand_depth, filters)
        # Get pure graph traversal results
        graph_results = self._graph_search(query, limit, expand_depth, filters)

        # Combine and re-score
        combined = {}

        # Add vector results
        for vr in vector_results:
            combined[vr.knowledge_id] = vr
            vr.combined_score = vr.vector_score * self.vector_weight

        # Merge graph results
        for gr in graph_results:
            if gr.knowledge_id in combined:
                # Update existing with graph score
                existing = combined[gr.knowledge_id]
                existing.graph_score = gr.graph_score
                existing.combined_score = (
                    existing.vector_score * self.vector_weight
                    + gr.graph_score * self.graph_weight
                )
                existing.relationships = gr.relationships
            else:
                # Add new result
                gr.combined_score = gr.graph_score * self.graph_weight
                combined[gr.knowledge_id] = gr

        # If we want graph expansion on vector results
        if expand_depth > 0:
            with self.neo4j_driver.session() as session:
                for kid in list(combined.keys())[: limit // 2]:  # Expand top half
                    expanded = self._expand_from_node(session, kid, expand_depth)

                    for exp_node, distance in expanded:
                        exp_id = exp_node["knowledge_id"]
                        if exp_id not in combined:
                            # Calculate vector similarity for expanded nodes
                            embedding = self.embedding_service.generate_embedding(
                                exp_node.get("content", "")[:500]
                            )
                            query_embedding = self.embedding_service.generate_embedding(
                                query
                            )

                            # Cosine similarity
                            vector_score = np.dot(embedding, query_embedding) / (
                                np.linalg.norm(embedding)
                                * np.linalg.norm(query_embedding)
                            )

                            graph_score = 0.5 / (1 + distance)  # Reduced for indirect

                            combined[exp_id] = SearchResult(
                                knowledge_id=exp_id,
                                content=exp_node.get("content", ""),
                                source=exp_node.get("source", ""),
                                knowledge_type=exp_node.get("knowledge_type", ""),
                                vector_score=vector_score,
                                graph_score=graph_score,
                                combined_score=(
                                    vector_score * self.vector_weight
                                    + graph_score * self.graph_weight
                                ),
                                relationships={},
                                metadata=dict(exp_node),
                            )

        # Sort by combined score
        results = sorted(
            combined.values(), key=lambda x: x.combined_score, reverse=True
        )
        return results[:limit]

    def _expand_from_node(
        self, session, knowledge_id: str, max_depth: int
    ) -> List[Tuple[Dict, int]]:
        """Expand from a node via relationships"""

        if max_depth == 0:
            return []

        # Build cypher with literal depth value
        cypher = f"""
            MATCH path = (k:Knowledge {{knowledge_id: $kid}})-[*1..{max_depth}]-(related:Knowledge)
            WHERE related.direct_ingestion = true
            RETURN DISTINCT related, length(path) as distance
            ORDER BY distance
            LIMIT 20
        """

        result = session.run(cypher, kid=knowledge_id)
        return [(record["related"], record["distance"]) for record in result]

    def _get_relationships(
        self, session, knowledge_id: str, depth: int
    ) -> Dict[str, List[str]]:
        """Get relationships for a node"""

        relationships = defaultdict(list)

        cypher = """
            MATCH (k:Knowledge {knowledge_id: $kid})-[r]-(related:Knowledge)
            WHERE related.direct_ingestion = true
            RETURN type(r) as rel_type, related.knowledge_id as related_id
            LIMIT 50
        """

        result = session.run(cypher, kid=knowledge_id)
        for record in result:
            relationships[record["rel_type"]].append(record["related_id"])

        return dict(relationships)

    def _build_qdrant_filter(self, filters: Dict) -> Dict:
        """Build Qdrant filter from search filters"""
        conditions = []

        if "knowledge_type" in filters:
            conditions.append(
                {"key": "knowledge_type", "match": {"value": filters["knowledge_type"]}}
            )

        if "tags" in filters:
            conditions.append({"key": "tags", "match": {"any": filters["tags"]}})

        if conditions:
            return {"must": conditions}
        return {}

    def get_context_window(
        self, knowledge_id: str, window_size: int = 2
    ) -> List[SearchResult]:
        """Get surrounding context for a knowledge chunk"""

        results = []
        with self.neo4j_driver.session() as session:
            # Get previous and next chunks
            cypher = f"""
                MATCH path = (k:Knowledge {{knowledge_id: $kid}})-[:NEXT_CHUNK*0..{window_size}]-(related:Knowledge)
                RETURN related, length(path) as distance
                ORDER BY distance
            """

            result = session.run(cypher, kid=knowledge_id)

            for record in result:
                node = record["related"]
                distance = record["distance"]

                results.append(
                    SearchResult(
                        knowledge_id=node["knowledge_id"],
                        content=node.get("content", ""),
                        source=node.get("source", ""),
                        knowledge_type=node.get("knowledge_type", ""),
                        vector_score=0.0,
                        graph_score=1.0 / (1 + distance),
                        combined_score=1.0 / (1 + distance),
                        relationships={},
                        metadata=dict(node),
                    )
                )

        return sorted(results, key=lambda x: x.combined_score, reverse=True)

    def close(self):
        """Clean up connections"""
        self.neo4j_driver.close()


# Example usage
if __name__ == "__main__":
    hybrid = HybridSearch()

    # Test different strategies
    queries = [
        ("OpenAI streaming API", "hybrid"),
        ("error handling", "graph"),
        ("authentication", "vector"),
    ]

    for query, strategy in queries:
        print(f"\nQuery: '{query}' using {strategy} strategy")
        print("=" * 60)

        results = hybrid.search(query, limit=3, strategy=strategy, expand_depth=1)

        for i, result in enumerate(results, 1):
            print(f"{i}. {result.source}")
            print(f"   Type: {result.knowledge_type}")
            print(
                f"   Scores: vector={result.vector_score:.3f}, "
                f"graph={result.graph_score:.3f}, "
                f"combined={result.combined_score:.3f}"
            )
            if result.relationships:
                print(f"   Relationships: {list(result.relationships.keys())}")

    hybrid.close()
