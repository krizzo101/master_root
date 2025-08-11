#!/usr/bin/env python3
"""
Semantic Graph Integration
Integrates vector embeddings with ArangoDB graph for semantic search
"""

import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib


class SemanticGraphIntegration:
    def __init__(self):
        self.embedding_cache = {}

    def create_semantic_search_collections(self) -> List[Dict]:
        """Create collections optimized for semantic search"""

        collections_to_create = [
            {
                "name": "research_concepts",
                "type": "document",
                "purpose": "Store research findings with embeddings",
                "indexes": [
                    {
                        "type": "fulltext",
                        "fields": [
                            "knowledge_content.title",
                            "knowledge_content.summary",
                        ],
                    },
                    {"type": "hash", "fields": ["knowledge_domain"]},
                    {"type": "skiplist", "fields": ["confidence_score"]},
                ],
            },
            {
                "name": "semantic_vectors",
                "type": "document",
                "purpose": "Store vector embeddings for similarity search",
                "indexes": [
                    {"type": "hash", "fields": ["concept_id"]},
                    {"type": "skiplist", "fields": ["vector_dimension"]},
                ],
            },
            {
                "name": "research_relationships",
                "type": "edge",
                "purpose": "Connect related research concepts",
                "indexes": [
                    {"type": "skiplist", "fields": ["semantic_similarity"]},
                    {"type": "hash", "fields": ["relationship_type"]},
                ],
            },
        ]

        return collections_to_create

    def create_arangosearch_view(self) -> Dict:
        """Create ArangoSearch view for full-text semantic search"""

        view_definition = {
            "name": "research_semantic_search",
            "type": "arangosearch",
            "properties": {
                "links": {
                    "research_concepts": {
                        "analyzers": ["text_en", "agent_memory_analyzer"],
                        "fields": {
                            "knowledge_content": {
                                "fields": {
                                    "title": {"analyzers": ["text_en"]},
                                    "summary": {
                                        "analyzers": [
                                            "text_en",
                                            "agent_memory_analyzer",
                                        ]
                                    },
                                    "key_insights": {"analyzers": ["text_en"]},
                                }
                            },
                            "knowledge_domain": {"analyzers": ["identity"]},
                            "concept_type": {"analyzers": ["identity"]},
                        },
                    },
                    "cognitive_concepts": {
                        "analyzers": ["text_en", "cognitive_concepts_analyzer"],
                        "fields": {
                            "knowledge_content": {
                                "fields": {
                                    "title": {"analyzers": ["text_en"]},
                                    "content": {
                                        "analyzers": [
                                            "text_en",
                                            "cognitive_concepts_analyzer",
                                        ]
                                    },
                                }
                            }
                        },
                    },
                }
            },
        }

        return view_definition

    def generate_embedding(
        self, text: str, model_type: str = "sentence_transformer"
    ) -> List[float]:
        """Generate vector embedding for text"""

        # Check cache first
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.embedding_cache:
            return self.embedding_cache[text_hash]

        # In production, would use actual embedding model
        if model_type == "sentence_transformer":
            embedding = self._sentence_transformer_embedding(text)
        else:
            embedding = self._simple_embedding(text)

        # Cache the result
        self.embedding_cache[text_hash] = embedding

        return embedding

    def _sentence_transformer_embedding(self, text: str) -> List[float]:
        """Generate embedding using sentence transformer (mock)"""
        # Would use: from sentence_transformers import SentenceTransformer
        # model = SentenceTransformer('all-MiniLM-L6-v2')
        # embedding = model.encode(text).tolist()

        # Mock implementation
        words = text.lower().split()
        embedding = []
        for i in range(384):  # Standard sentence transformer dimension
            val = sum(hash(word + str(i)) for word in words) % 1000 / 1000.0
            embedding.append(val)

        return embedding

    def _simple_embedding(self, text: str) -> List[float]:
        """Simple hash-based embedding for testing"""
        words = text.lower().split()
        embedding = []
        for i in range(128):
            val = sum(hash(word + str(i)) for word in words) % 1000 / 1000.0
            embedding.append(val)
        return embedding

    def store_concept_with_embedding(self, concept: Dict) -> Dict:
        """Store concept with generated embedding"""

        # Generate text for embedding
        title = concept.get("knowledge_content", {}).get("title", "")
        summary = concept.get("knowledge_content", {}).get("summary", "")
        insights = " ".join(
            concept.get("knowledge_content", {}).get("key_insights", [])
        )

        embedding_text = f"{title} {summary} {insights}"

        # Generate embedding
        embedding = self.generate_embedding(embedding_text)

        # Store embedding in concept
        concept["semantic_embedding"] = {
            "vector": embedding,
            "dimension": len(embedding),
            "model": "sentence_transformer_mock",
            "generated_at": datetime.now().isoformat(),
        }

        return concept

    def calculate_semantic_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """Calculate cosine similarity between embeddings"""

        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return float(similarity)

    def find_similar_concepts(
        self, query_embedding: List[float], threshold: float = 0.7
    ) -> str:
        """Generate AQL query to find similar concepts"""

        # This would be more sophisticated in production with vector indexes
        aql_query = f"""
        FOR concept IN research_concepts
        FILTER concept.semantic_embedding != null
        LET similarity = COSINE_SIMILARITY(@query_vector, concept.semantic_embedding.vector)
        FILTER similarity > @threshold
        SORT similarity DESC
        LIMIT 10
        RETURN {{
            concept: concept,
            similarity: similarity,
            title: concept.knowledge_content.title,
            domain: concept.knowledge_domain
        }}
        """

        return aql_query

    def create_semantic_relationships(
        self, concepts: List[Dict], similarity_threshold: float = 0.8
    ) -> List[Dict]:
        """Create relationships based on semantic similarity"""

        relationships = []

        for i, concept1 in enumerate(concepts):
            embedding1 = concept1.get("semantic_embedding", {}).get("vector", [])
            if not embedding1:
                continue

            for concept2 in concepts[i + 1 :]:
                embedding2 = concept2.get("semantic_embedding", {}).get("vector", [])
                if not embedding2:
                    continue

                similarity = self.calculate_semantic_similarity(embedding1, embedding2)

                if similarity > similarity_threshold:
                    relationship = {
                        "_from": f"research_concepts/{concept1['_key']}",
                        "_to": f"research_concepts/{concept2['_key']}",
                        "relationship_type": "semantically_similar",
                        "semantic_similarity": similarity,
                        "confidence": similarity,
                        "relationship_context": f"High semantic similarity ({similarity:.3f})",
                        "discovery_method": "vector_embedding_similarity",
                        "created": datetime.now().isoformat() + "Z",
                    }
                    relationships.append(relationship)

        return relationships

    def hybrid_search_query(
        self, search_term: str, domain_filter: Optional[str] = None
    ) -> str:
        """Generate hybrid search combining full-text and semantic search"""

        domain_filter_clause = ""
        if domain_filter:
            domain_filter_clause = (
                f"FILTER concept.knowledge_domain == '{domain_filter}'"
            )

        aql_query = f"""
        // Hybrid search: Full-text + Semantic
        LET fulltext_results = (
            FOR concept IN research_semantic_search
            SEARCH PHRASE(concept.knowledge_content.title, @search_term, "text_en") OR
                   PHRASE(concept.knowledge_content.summary, @search_term, "text_en")
            {domain_filter_clause}
            SORT BM25(concept) DESC
            LIMIT 20
            RETURN {{
                concept: concept,
                score: BM25(concept),
                match_type: "fulltext"
            }}
        )
        
        LET semantic_results = (
            FOR concept IN research_concepts
            FILTER concept.semantic_embedding != null
            {domain_filter_clause}
            LET query_embedding = EMBEDDING(@search_term)  // Would need custom function
            LET similarity = COSINE_SIMILARITY(query_embedding, concept.semantic_embedding.vector)
            FILTER similarity > 0.6
            SORT similarity DESC
            LIMIT 20
            RETURN {{
                concept: concept,
                score: similarity,
                match_type: "semantic"
            }}
        )
        
        // Combine and deduplicate results
        FOR result IN UNION(fulltext_results, semantic_results)
        COLLECT concept_id = result.concept._id INTO groups
        LET best_score = MAX(groups[*].result.score)
        LET match_types = UNIQUE(groups[*].result.match_type)
        SORT best_score DESC
        LIMIT 15
        RETURN {{
            concept: FIRST(groups).result.concept,
            combined_score: best_score,
            match_types: match_types,
            relevance: best_score > 0.8 ? "high" : best_score > 0.6 ? "medium" : "low"
        }}
        """

        return aql_query

    def research_knowledge_graph_query(
        self, starting_concept: str, max_depth: int = 3
    ) -> str:
        """Generate query to explore research knowledge graph"""

        aql_query = f"""
        // Research Knowledge Graph Traversal
        FOR concept IN research_concepts
        FILTER concept._key == @starting_concept OR 
               CONTAINS(LOWER(concept.knowledge_content.title), LOWER(@starting_concept))
        
        FOR v, e, p IN 1..{max_depth} ANY concept research_relationships
        
        // Calculate path relevance
        LET path_similarity = AVG(p.edges[*].semantic_similarity)
        LET path_length = LENGTH(p.edges)
        LET relevance_score = path_similarity * (1 / path_length)
        
        FILTER relevance_score > 0.5
        
        COLLECT path_vertices = p.vertices INTO groups
        LET avg_relevance = AVG(groups[*].relevance_score)
        
        SORT avg_relevance DESC
        LIMIT 10
        
        RETURN {{
            knowledge_path: path_vertices[*].knowledge_content.title,
            relationships: groups[0].p.edges[*].relationship_type,
            path_relevance: avg_relevance,
            domains: UNIQUE(path_vertices[*].knowledge_domain),
            insights: FLATTEN(path_vertices[*].knowledge_content.key_insights)
        }}
        """

        return aql_query


def create_complete_semantic_system():
    """Create complete semantic search and graph system"""

    semantic_integration = SemanticGraphIntegration()

    return {
        "semantic_system": semantic_integration,
        "collections": semantic_integration.create_semantic_search_collections(),
        "search_view": semantic_integration.create_arangosearch_view(),
        "capabilities": [
            "Vector embedding generation",
            "Semantic similarity calculation",
            "Hybrid full-text + semantic search",
            "Automatic relationship discovery",
            "Knowledge graph traversal",
            "Research caching and deduplication",
        ],
        "queries": {
            "hybrid_search": "semantic_integration.hybrid_search_query(term, domain)",
            "similar_concepts": "semantic_integration.find_similar_concepts(embedding)",
            "knowledge_graph": "semantic_integration.research_knowledge_graph_query(concept)",
        },
    }


if __name__ == "__main__":
    system = create_complete_semantic_system()
    print("Semantic Graph Integration System initialized")
    print(f"Collections to create: {len(system['collections'])}")
    print(f"Capabilities: {', '.join(system['capabilities'])}")
