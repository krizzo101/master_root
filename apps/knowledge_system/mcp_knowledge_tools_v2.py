#!/usr/bin/env python3
"""
Enhanced Knowledge Tools with Semantic Search
Extends the original tools to include embedding-based search capabilities.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from embedding_service import get_embedding_service


class SemanticSearchTool:
    """Tool for semantic search using embeddings."""
    
    @staticmethod
    def execute(
        query_text: str,
        search_type: str = "semantic",  # semantic, hybrid, or keyword
        limit: int = 10,
        min_similarity: float = 0.5,
        knowledge_type: Optional[str] = None,
        text_weight: float = 0.3,
        vector_weight: float = 0.7
    ) -> Dict[str, Any]:
        """
        Execute semantic or hybrid search.
        
        Args:
            query_text: The search query
            search_type: Type of search (semantic, hybrid, keyword)
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold for semantic search
            knowledge_type: Optional filter by knowledge type
            text_weight: Weight for text search in hybrid mode
            vector_weight: Weight for vector search in hybrid mode
            
        Returns:
            Dictionary with Cypher query and parameters
        """
        embedding_service = get_embedding_service()
        
        if search_type == "keyword":
            # Pure keyword search (no embeddings)
            where_conditions = []
            if knowledge_type:
                where_conditions.append("k.knowledge_type = $knowledge_type")
            
            where_conditions.append("""
                (toLower(k.content) CONTAINS toLower($query_text) OR
                 toLower(k.context) CONTAINS toLower($query_text) OR
                 ANY(tag IN k.tags WHERE toLower(tag) CONTAINS toLower($query_text)))
            """)
            
            where_clause = f"WHERE {' AND '.join(where_conditions)}"
            
            query = f"""
            MATCH (k:Knowledge)
            {where_clause}
            RETURN k.knowledge_id as id,
                   k.knowledge_type as type,
                   k.content as content,
                   k.context as context,
                   k.tags as tags,
                   k.confidence_score as confidence,
                   1.0 as relevance
            ORDER BY k.confidence_score DESC, k.usage_count DESC
            LIMIT $limit
            """
            
            params = {
                "query_text": query_text,
                "limit": limit
            }
            if knowledge_type:
                params["knowledge_type"] = knowledge_type
                
        elif search_type == "semantic":
            # Pure semantic search using embeddings
            query_embedding = embedding_service.generate_embedding(query_text)
            
            where_conditions = []
            if knowledge_type:
                where_conditions.append("k.knowledge_type = $knowledge_type")
            
            # Only search entries with embeddings
            where_conditions.append("k.embedding IS NOT NULL")
            
            where_clause = f"WHERE {' AND '.join(where_conditions)}"
            
            # Neo4j 5.x vector search syntax
            if knowledge_type:
                query = f"""
                CALL db.index.vector.queryNodes(
                    'knowledge_embeddings',
                    $limit * 2,
                    $query_embedding
                ) YIELD node as k, score
                WHERE score >= $min_similarity AND k.knowledge_type = $knowledge_type
                RETURN k.knowledge_id as id,
                       k.knowledge_type as type,
                       k.content as content,
                       k.context as context,
                       k.tags as tags,
                       k.confidence_score as confidence,
                       score as relevance
                ORDER BY score DESC
                LIMIT $limit
                """
            else:
                query = f"""
                CALL db.index.vector.queryNodes(
                    'knowledge_embeddings',
                    $limit,
                    $query_embedding
                ) YIELD node as k, score
                WHERE score >= $min_similarity
                RETURN k.knowledge_id as id,
                       k.knowledge_type as type,
                       k.content as content,
                       k.context as context,
                       k.tags as tags,
                       k.confidence_score as confidence,
                       score as relevance
                ORDER BY score DESC
                """
            
            params = {
                "query_embedding": query_embedding,
                "min_similarity": min_similarity,
                "limit": limit
            }
            if knowledge_type:
                params["knowledge_type"] = knowledge_type
                
        else:  # hybrid search
            # Combine keyword and semantic search
            query_embedding = embedding_service.generate_embedding(query_text)
            
            where_conditions = []
            if knowledge_type:
                where_conditions.append("k.knowledge_type = $knowledge_type")
            
            where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
            
            # Neo4j doesn't support vector.similarity.cosine in older versions, 
            # so we'll use the index for vector search and combine with text
            query = f"""
            // Get semantic matches
            CALL db.index.vector.queryNodes(
                'knowledge_embeddings',
                $limit * 2,
                $query_embedding
            ) YIELD node as k1, score as vector_score
            WITH collect({{node: k1, vector_score: vector_score}}) as semantic_results
            
            // Get keyword matches
            MATCH (k2:Knowledge)
            {where_clause.replace('k.', 'k2.')}
            WHERE toLower(k2.content) CONTAINS toLower($query_text) OR
                  toLower(k2.context) CONTAINS toLower($query_text) OR
                  ANY(tag IN k2.tags WHERE toLower(tag) CONTAINS toLower($query_text))
            WITH semantic_results, collect(k2) as keyword_results
            
            // Combine results
            UNWIND semantic_results + keyword_results as result
            WITH CASE 
                   WHEN result.node IS NOT NULL THEN result.node
                   ELSE result
                 END as k,
                 CASE
                   WHEN result.vector_score IS NOT NULL THEN result.vector_score
                   ELSE 0.0
                 END as vector_score,
                 CASE
                   WHEN result.node IS NULL AND 
                        (toLower(result.content) CONTAINS toLower($query_text) OR
                         toLower(result.context) CONTAINS toLower($query_text))
                   THEN 1.0
                   ELSE 0.0
                 END as text_score
            
            WITH k, 
                 MAX(vector_score) as vector_score,
                 MAX(text_score) as text_score,
                 ($text_weight * MAX(text_score) + $vector_weight * MAX(vector_score)) as combined_score
            WHERE combined_score > 0
            RETURN DISTINCT
                   k.knowledge_id as id,
                   k.knowledge_type as type,
                   k.content as content,
                   k.context as context,
                   k.tags as tags,
                   k.confidence_score as confidence,
                   combined_score as relevance,
                   vector_score,
                   text_score
            ORDER BY combined_score DESC
            LIMIT $limit
            """
            
            params = {
                "query_text": query_text,
                "query_embedding": query_embedding,
                "text_weight": text_weight,
                "vector_weight": vector_weight,
                "limit": limit
            }
            if knowledge_type:
                params["knowledge_type"] = knowledge_type
        
        return {
            "query": query,
            "params": params
        }


class EnhancedKnowledgeStoreTool:
    """Enhanced knowledge storage that automatically generates embeddings."""
    
    @staticmethod
    def execute(
        knowledge_type: str,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        confidence_score: float = 0.8,
        knowledge_id: Optional[str] = None,
        generate_embedding: bool = True
    ) -> Dict[str, Any]:
        """
        Store knowledge with automatic embedding generation.
        
        Args:
            knowledge_type: Type of knowledge
            content: The knowledge content
            context: Optional context dictionary
            tags: Optional tags
            confidence_score: Confidence score (0-1)
            knowledge_id: Optional ID (will generate if not provided)
            generate_embedding: Whether to generate embedding immediately
            
        Returns:
            Dictionary with Cypher query and parameters
        """
        # Generate ID if not provided
        if not knowledge_id:
            content_hash = hashlib.md5(f"{knowledge_type}:{content}".encode()).hexdigest()
            knowledge_id = f"{knowledge_type.lower()}_{content_hash[:8]}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        # Serialize complex objects
        context_json = json.dumps(context) if context else "{}"
        tags_json = json.dumps(tags) if tags else "[]"
        
        # Generate embedding if requested
        embedding = None
        if generate_embedding:
            embedding_service = get_embedding_service()
            knowledge_dict = {
                "knowledge_type": knowledge_type,
                "content": content,
                "context": context,
                "tags": tags
            }
            prepared_text = embedding_service.prepare_knowledge_text(knowledge_dict)
            embedding = embedding_service.generate_embedding(prepared_text)
        
        # Build the query
        if embedding:
            query = """
            CREATE (k:Knowledge {
                knowledge_id: $knowledge_id,
                knowledge_type: $knowledge_type,
                content: $content,
                context: $context,
                tags: $tags,
                confidence_score: $confidence_score,
                created_at: $created_at,
                updated_at: $updated_at,
                usage_count: 0,
                success_count: 0,
                failure_count: 0,
                embedding: $embedding,
                embedding_model: $embedding_model,
                embedding_generated_at: $embedding_generated_at
            })
            RETURN k.knowledge_id as id
            """
            
            params = {
                "knowledge_id": knowledge_id,
                "knowledge_type": knowledge_type,
                "content": content,
                "context": context_json,
                "tags": tags_json,
                "confidence_score": confidence_score,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "embedding": embedding,
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "embedding_generated_at": datetime.now(timezone.utc).isoformat()
            }
        else:
            query = """
            CREATE (k:Knowledge {
                knowledge_id: $knowledge_id,
                knowledge_type: $knowledge_type,
                content: $content,
                context: $context,
                tags: $tags,
                confidence_score: $confidence_score,
                created_at: $created_at,
                updated_at: $updated_at,
                usage_count: 0,
                success_count: 0,
                failure_count: 0
            })
            RETURN k.knowledge_id as id
            """
            
            params = {
                "knowledge_id": knowledge_id,
                "knowledge_type": knowledge_type,
                "content": content,
                "context": context_json,
                "tags": tags_json,
                "confidence_score": confidence_score,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        
        return {
            "query": query,
            "params": params,
            "knowledge_id": knowledge_id
        }


class SimilarKnowledgeTool:
    """Find similar knowledge entries using embeddings."""
    
    @staticmethod
    def execute(
        knowledge_id: str,
        limit: int = 5,
        min_similarity: float = 0.7
    ) -> Dict[str, Any]:
        """
        Find knowledge similar to a given entry.
        
        Args:
            knowledge_id: ID of the reference knowledge
            limit: Maximum number of similar entries
            min_similarity: Minimum similarity threshold
            
        Returns:
            Dictionary with Cypher query and parameters
        """
        # First need to get the embedding of the reference knowledge
        query = """
        MATCH (ref:Knowledge {knowledge_id: $knowledge_id})
        WHERE ref.embedding IS NOT NULL
        CALL db.index.vector.queryNodes(
            'knowledge_embeddings',
            $limit + 1,  // +1 to exclude self
            ref.embedding
        ) YIELD node as k, score
        WHERE k.knowledge_id <> $knowledge_id AND score >= $min_similarity
        RETURN k.knowledge_id as id,
               k.knowledge_type as type,
               k.content as content,
               k.confidence_score as confidence,
               score as similarity
        ORDER BY score DESC
        LIMIT $limit
        """
        
        return {
            "query": query,
            "params": {
                "knowledge_id": knowledge_id,
                "limit": limit,
                "min_similarity": min_similarity
            }
        }


class KnowledgeClusteringTool:
    """Discover knowledge clusters using embeddings."""
    
    @staticmethod
    def execute(
        similarity_threshold: float = 0.8,
        min_cluster_size: int = 2
    ) -> Dict[str, Any]:
        """
        Find clusters of similar knowledge.
        
        Args:
            similarity_threshold: Minimum similarity to be in same cluster
            min_cluster_size: Minimum size for a cluster
            
        Returns:
            Dictionary with Cypher query and parameters
        """
        # This is a simplified clustering approach using similarity threshold
        query = """
        MATCH (k1:Knowledge)
        WHERE k1.embedding IS NOT NULL
        MATCH (k2:Knowledge)
        WHERE k2.embedding IS NOT NULL AND k1.knowledge_id < k2.knowledge_id
        WITH k1, k2, 
             gds.similarity.cosine(k1.embedding, k2.embedding) as similarity
        WHERE similarity >= $similarity_threshold
        WITH k1, collect(k2) as similar_nodes
        WHERE size(similar_nodes) >= $min_cluster_size - 1
        RETURN k1.knowledge_id as cluster_center,
               k1.content as center_content,
               [k IN similar_nodes | {id: k.knowledge_id, content: k.content}] as cluster_members,
               size(similar_nodes) + 1 as cluster_size
        ORDER BY cluster_size DESC
        """
        
        return {
            "query": query,
            "params": {
                "similarity_threshold": similarity_threshold,
                "min_cluster_size": min_cluster_size
            }
        }


if __name__ == "__main__":
    # Test the enhanced tools
    print("Testing Enhanced Knowledge Tools with Semantic Search")
    print("-" * 50)
    
    # Test semantic search
    result = SemanticSearchTool.execute(
        query_text="How to fix Python import errors",
        search_type="semantic",
        limit=5
    )
    print(f"Semantic search query generated with {len(result['params']['query_embedding'])} dim embedding")
    
    # Test enhanced storage with embedding
    result = EnhancedKnowledgeStoreTool.execute(
        knowledge_type="ERROR_SOLUTION",
        content="Use virtual environments to avoid package conflicts",
        tags=["python", "venv", "packages"],
        generate_embedding=True
    )
    print(f"Storage query with embedding: {result['knowledge_id']}")
    
    print("\nEnhanced tools ready for integration!")