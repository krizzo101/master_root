#!/usr/bin/env python3
"""
Embedding Service for Knowledge System

Provides semantic search capabilities using sentence-transformers and Neo4j vector indexes.
Uses all-MiniLM-L6-v2 for fast, efficient embeddings (384 dimensions).
"""

import json
import hashlib
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import logging

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Warning: sentence-transformers not installed. Run: pip install sentence-transformers")
    SentenceTransformer = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating and managing embeddings for knowledge entries.
    
    Features:
    - Fast embedding generation with all-MiniLM-L6-v2 (384 dimensions)
    - Caching to avoid re-computing embeddings
    - Batch processing for efficiency
    - Neo4j vector index integration
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the embedding service.
        
        Args:
            model_name: Name of the sentence-transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self.embedding_cache = {}
        self.vector_dimension = 384  # all-MiniLM-L6-v2 produces 384-dim vectors
        
    def _ensure_model_loaded(self):
        """Lazy load the model when first needed."""
        if self.model is None:
            if SentenceTransformer is None:
                raise ImportError("sentence-transformers is required. Install with: pip install sentence-transformers")
            
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Model loaded successfully. Embedding dimension: {self.vector_dimension}")
    
    def generate_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            use_cache: Whether to use cached embeddings
            
        Returns:
            List of floats representing the embedding vector
        """
        self._ensure_model_loaded()
        
        # Check cache
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if use_cache and text_hash in self.embedding_cache:
            logger.debug(f"Using cached embedding for text hash: {text_hash}")
            return self.embedding_cache[text_hash]
        
        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        embedding_list = embedding.tolist()
        
        # Cache it
        if use_cache:
            self.embedding_cache[text_hash] = embedding_list
        
        return embedding_list
    
    def generate_embeddings_batch(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            use_cache: Whether to use cached embeddings
            
        Returns:
            List of embedding vectors
        """
        self._ensure_model_loaded()
        
        embeddings = []
        texts_to_encode = []
        text_indices = []
        
        # Check cache and prepare batch
        for i, text in enumerate(texts):
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if use_cache and text_hash in self.embedding_cache:
                embeddings.append(self.embedding_cache[text_hash])
            else:
                texts_to_encode.append(text)
                text_indices.append(i)
                embeddings.append(None)  # Placeholder
        
        # Batch encode uncached texts
        if texts_to_encode:
            logger.info(f"Generating embeddings for {len(texts_to_encode)} texts")
            new_embeddings = self.model.encode(texts_to_encode, convert_to_numpy=True)
            
            # Fill in the embeddings and update cache
            for idx, text, embedding in zip(text_indices, texts_to_encode, new_embeddings):
                embedding_list = embedding.tolist()
                embeddings[idx] = embedding_list
                
                if use_cache:
                    text_hash = hashlib.md5(text.encode()).hexdigest()
                    self.embedding_cache[text_hash] = embedding_list
        
        return embeddings
    
    def prepare_knowledge_text(self, knowledge_entry: Dict[str, Any]) -> str:
        """
        Prepare knowledge entry text for embedding.
        Combines relevant fields into a single searchable text.
        
        Args:
            knowledge_entry: Knowledge entry dictionary
            
        Returns:
            Combined text for embedding
        """
        parts = []
        
        # Add knowledge type as context
        if 'knowledge_type' in knowledge_entry:
            parts.append(f"Type: {knowledge_entry['knowledge_type']}")
        
        # Add main content
        if 'content' in knowledge_entry:
            parts.append(knowledge_entry['content'])
        
        # Add tags if present
        if 'tags' in knowledge_entry and knowledge_entry['tags']:
            if isinstance(knowledge_entry['tags'], str):
                # Parse JSON if stored as string
                try:
                    tags = json.loads(knowledge_entry['tags'])
                except:
                    tags = [knowledge_entry['tags']]
            else:
                tags = knowledge_entry['tags']
            parts.append(f"Tags: {', '.join(tags)}")
        
        # Add context preview if present
        if 'context' in knowledge_entry and knowledge_entry['context']:
            try:
                if isinstance(knowledge_entry['context'], str):
                    context = json.loads(knowledge_entry['context'])
                else:
                    context = knowledge_entry['context']
                
                # Add first few keys from context
                if isinstance(context, dict):
                    context_preview = []
                    for key, value in list(context.items())[:3]:
                        context_preview.append(f"{key}: {str(value)[:100]}")
                    if context_preview:
                        parts.append("Context: " + "; ".join(context_preview))
            except:
                pass
        
        return " ".join(parts)
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Compute cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    
    def find_similar_embeddings(
        self, 
        query_embedding: List[float], 
        candidate_embeddings: List[Tuple[str, List[float]]], 
        top_k: int = 5,
        min_similarity: float = 0.5
    ) -> List[Tuple[str, float]]:
        """
        Find most similar embeddings to a query.
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of (id, embedding) tuples
            top_k: Number of top results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of (id, similarity_score) tuples, sorted by similarity
        """
        similarities = []
        
        for candidate_id, candidate_embedding in candidate_embeddings:
            similarity = self.compute_similarity(query_embedding, candidate_embedding)
            if similarity >= min_similarity:
                similarities.append((candidate_id, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def create_neo4j_vector_index_query(self) -> Dict[str, Any]:
        """
        Generate Cypher query to create vector index in Neo4j.
        
        Returns:
            Dictionary with query and parameters
        """
        query = """
        CREATE VECTOR INDEX knowledge_embeddings IF NOT EXISTS
        FOR (k:Knowledge)
        ON k.embedding
        OPTIONS {
            indexConfig: {
                `vector.dimensions`: $dimensions,
                `vector.similarity_function`: 'cosine'
            }
        }
        """
        
        return {
            "query": query,
            "params": {"dimensions": self.vector_dimension}
        }
    
    def embed_knowledge_query(self, knowledge_id: str, embedding: List[float]) -> Dict[str, Any]:
        """
        Generate Cypher query to add embedding to a knowledge entry.
        
        Args:
            knowledge_id: ID of the knowledge entry
            embedding: Embedding vector
            
        Returns:
            Dictionary with query and parameters
        """
        query = """
        MATCH (k:Knowledge {knowledge_id: $knowledge_id})
        SET k.embedding = $embedding,
            k.embedding_generated_at = $generated_at,
            k.embedding_model = $model
        RETURN k.knowledge_id as id, k.content as content
        """
        
        return {
            "query": query,
            "params": {
                "knowledge_id": knowledge_id,
                "embedding": embedding,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "model": self.model_name
            }
        }
    
    def semantic_search_query(
        self, 
        query_embedding: List[float], 
        limit: int = 10,
        min_similarity: float = 0.5,
        knowledge_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate Cypher query for semantic search using vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold
            knowledge_type: Optional filter by knowledge type
            
        Returns:
            Dictionary with query and parameters
        """
        # Build the WHERE clause
        where_conditions = []
        if knowledge_type:
            where_conditions.append("k.knowledge_type = $knowledge_type")
        
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        query = f"""
        MATCH (k:Knowledge)
        {where_clause}
        WITH k, vector.similarity.cosine(k.embedding, $query_embedding) AS similarity
        WHERE similarity >= $min_similarity
        RETURN k.knowledge_id as id,
               k.knowledge_type as type,
               k.content as content,
               k.context as context,
               k.tags as tags,
               k.confidence_score as confidence,
               similarity
        ORDER BY similarity DESC
        LIMIT $limit
        """
        
        params = {
            "query_embedding": query_embedding,
            "min_similarity": min_similarity,
            "limit": limit
        }
        
        if knowledge_type:
            params["knowledge_type"] = knowledge_type
        
        return {
            "query": query,
            "params": params
        }
    
    def hybrid_search_query(
        self,
        text_query: str,
        query_embedding: List[float],
        limit: int = 10,
        text_weight: float = 0.3,
        vector_weight: float = 0.7,
        knowledge_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate Cypher query for hybrid search (text + vector).
        
        Args:
            text_query: Text search query
            query_embedding: Query embedding vector
            limit: Maximum number of results
            text_weight: Weight for text search (0-1)
            vector_weight: Weight for vector search (0-1)
            knowledge_type: Optional filter by knowledge type
            
        Returns:
            Dictionary with query and parameters
        """
        where_conditions = []
        if knowledge_type:
            where_conditions.append("k.knowledge_type = $knowledge_type")
        
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        query = f"""
        MATCH (k:Knowledge)
        {where_clause}
        WITH k,
             CASE 
                WHEN k.content CONTAINS $text_query THEN 1.0
                WHEN toLower(k.content) CONTAINS toLower($text_query) THEN 0.8
                ELSE 0.0
             END AS text_score,
             vector.similarity.cosine(k.embedding, $query_embedding) AS vector_score
        WITH k, 
             ($text_weight * text_score + $vector_weight * vector_score) AS combined_score,
             text_score,
             vector_score
        WHERE combined_score > 0
        RETURN k.knowledge_id as id,
               k.knowledge_type as type,
               k.content as content,
               k.context as context,
               k.tags as tags,
               k.confidence_score as confidence,
               text_score,
               vector_score,
               combined_score
        ORDER BY combined_score DESC
        LIMIT $limit
        """
        
        params = {
            "text_query": text_query,
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


# Singleton instance
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """Get or create the singleton embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


if __name__ == "__main__":
    # Test the embedding service
    service = get_embedding_service()
    
    # Test embedding generation
    test_text = "How to fix ImportError in Python when module is not found"
    print(f"Testing embedding generation for: {test_text}")
    
    embedding = service.generate_embedding(test_text)
    print(f"Generated embedding with {len(embedding)} dimensions")
    print(f"First 5 values: {embedding[:5]}")
    
    # Test similarity
    text2 = "Python import error module not found solution"
    embedding2 = service.generate_embedding(text2)
    
    similarity = service.compute_similarity(embedding, embedding2)
    print(f"\nSimilarity between the two texts: {similarity:.4f}")
    
    # Test knowledge text preparation
    knowledge_entry = {
        "knowledge_type": "ERROR_SOLUTION",
        "content": "Use pip install to fix missing module errors",
        "tags": ["python", "import", "error"],
        "context": {"error_type": "ImportError", "solution": "pip install"}
    }
    
    prepared_text = service.prepare_knowledge_text(knowledge_entry)
    print(f"\nPrepared knowledge text: {prepared_text}")