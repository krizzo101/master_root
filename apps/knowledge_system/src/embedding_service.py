"""
Embedding Service for Knowledge Learning System

This module provides embedding generation capabilities using both OpenAI API
and local models for fallback and cost optimization.
"""

import asyncio
import hashlib
import json
import logging
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import numpy as np

# Optional imports with fallbacks
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI not available. Using local embeddings only.")

try:
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Sentence transformers not available.")


@dataclass
class EmbeddingConfig:
    """Configuration for embedding service"""
    primary_model: str = "text-embedding-3-small"
    fallback_model: str = "all-MiniLM-L6-v2"
    target_dimension: int = 512
    batch_size: int = 100
    max_tokens: int = 8000
    cache_embeddings: bool = True
    cache_dir: str = ".cache/embeddings"


class EmbeddingCache:
    """Simple file-based embedding cache"""
    
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text"""
        return hashlib.sha256(text.encode()).hexdigest()
    
    def get(self, text: str) -> Optional[List[float]]:
        """Retrieve embedding from cache"""
        cache_key = self._get_cache_key(text)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    return data['embedding']
            except Exception as e:
                logging.error(f"Cache read error: {e}")
        
        return None
    
    def set(self, text: str, embedding: List[float]):
        """Store embedding in cache"""
        cache_key = self._get_cache_key(text)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'text_preview': text[:100],
                    'embedding': embedding
                }, f)
        except Exception as e:
            logging.error(f"Cache write error: {e}")


class EmbeddingService:
    """
    Main embedding service with multi-model support and caching
    """
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self.cache = EmbeddingCache(self.config.cache_dir) if self.config.cache_embeddings else None
        
        # Initialize OpenAI client if available
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.openai_client = openai.AsyncOpenAI()
        else:
            self.openai_client = None
            logging.info("OpenAI client not initialized")
        
        # Initialize local model if available
        if TRANSFORMERS_AVAILABLE:
            try:
                self.local_model = SentenceTransformer(self.config.fallback_model)
                logging.info(f"Loaded local model: {self.config.fallback_model}")
            except Exception as e:
                logging.error(f"Failed to load local model: {e}")
                self.local_model = None
        else:
            self.local_model = None
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for embedding generation
        
        Args:
            text: Raw text content
            
        Returns:
            Preprocessed text
        """
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Truncate to token limit (rough approximation)
        # Assuming ~4 characters per token
        max_chars = self.config.max_tokens * 4
        if len(text) > max_chars:
            text = text[:max_chars]
        
        # Add context markers for better embedding
        if "def " in text or "class " in text:
            text = f"[CODE] {text}"
        elif "Error" in text or "Exception" in text:
            text = f"[ERROR] {text}"
        elif "workflow" in text.lower():
            text = f"[WORKFLOW] {text}"
        
        return text
    
    def reduce_dimensions(self, embedding: List[float], target_dim: int) -> List[float]:
        """
        Reduce embedding dimensions using PCA-like approach
        
        Args:
            embedding: Original embedding vector
            target_dim: Target dimension size
            
        Returns:
            Reduced dimension embedding
        """
        if len(embedding) <= target_dim:
            return embedding
        
        # Simple dimension reduction by averaging groups
        original_dim = len(embedding)
        chunk_size = original_dim // target_dim
        reduced = []
        
        for i in range(0, target_dim * chunk_size, chunk_size):
            chunk = embedding[i:i+chunk_size]
            reduced.append(sum(chunk) / len(chunk))
        
        return reduced
    
    def normalize_embedding(self, embedding: List[float]) -> List[float]:
        """
        Normalize embedding vector to unit length
        
        Args:
            embedding: Embedding vector
            
        Returns:
            Normalized embedding
        """
        norm = np.linalg.norm(embedding)
        if norm > 0:
            return (np.array(embedding) / norm).tolist()
        return embedding
    
    async def generate_embedding_openai(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding using OpenAI API
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        if not self.openai_client:
            return None
        
        try:
            response = await self.openai_client.embeddings.create(
                model=self.config.primary_model,
                input=text,
                dimensions=self.config.target_dimension
            )
            
            embedding = response.data[0].embedding
            return self.normalize_embedding(embedding)
            
        except Exception as e:
            logging.error(f"OpenAI embedding error: {e}")
            return None
    
    def generate_embedding_local(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding using local model
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        if not self.local_model:
            return None
        
        try:
            embedding = self.local_model.encode(text)
            embedding_list = embedding.tolist()
            
            # Reduce dimensions if needed
            if len(embedding_list) > self.config.target_dimension:
                embedding_list = self.reduce_dimensions(
                    embedding_list, 
                    self.config.target_dimension
                )
            
            return self.normalize_embedding(embedding_list)
            
        except Exception as e:
            logging.error(f"Local embedding error: {e}")
            return None
    
    async def generate_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Generate embedding for text with fallback and caching
        
        Args:
            text: Text to embed
            use_cache: Whether to use cache
            
        Returns:
            Embedding vector
        """
        # Check cache
        if use_cache and self.cache:
            cached = self.cache.get(text)
            if cached:
                return cached
        
        # Preprocess text
        processed_text = self.preprocess_text(text)
        
        # Try OpenAI first
        embedding = await self.generate_embedding_openai(processed_text)
        
        # Fallback to local model
        if embedding is None:
            embedding = self.generate_embedding_local(processed_text)
        
        # If all else fails, generate random embedding (for testing)
        if embedding is None:
            logging.warning("All embedding methods failed, using random")
            embedding = self.normalize_embedding(
                np.random.randn(self.config.target_dimension).tolist()
            )
        
        # Cache the result
        if use_cache and self.cache:
            self.cache.set(text, embedding)
        
        return embedding
    
    async def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i:i+self.config.batch_size]
            
            # Generate embeddings concurrently for batch
            batch_embeddings = await asyncio.gather(
                *[self.generate_embedding(text) for text in batch]
            )
            
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between 0 and 1
        """
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
        
        # Ensure result is between 0 and 1
        return max(0.0, min(1.0, (similarity + 1) / 2))


class ContentEmbedder:
    """
    Specialized embedder for different content types
    """
    
    def __init__(self, embedding_service: EmbeddingService):
        self.embedder = embedding_service
    
    async def embed_code_pattern(self, code: str, language: str, pattern_type: str) -> List[float]:
        """
        Generate embedding for code pattern
        
        Args:
            code: Code content
            language: Programming language
            pattern_type: Type of pattern
            
        Returns:
            Embedding vector
        """
        # Create enriched context for code
        context = f"Language: {language}\nPattern: {pattern_type}\n{code}"
        return await self.embedder.generate_embedding(context)
    
    async def embed_error_resolution(
        self, 
        error_type: str, 
        error_message: str, 
        resolution: str
    ) -> List[float]:
        """
        Generate embedding for error resolution
        
        Args:
            error_type: Type of error
            error_message: Error message
            resolution: Resolution steps
            
        Returns:
            Embedding vector
        """
        # Create structured error context
        context = f"Error: {error_type}\nMessage: {error_message}\nFix: {resolution}"
        return await self.embedder.generate_embedding(context)
    
    async def embed_workflow(self, workflow_name: str, steps: List[str]) -> List[float]:
        """
        Generate embedding for workflow
        
        Args:
            workflow_name: Name of workflow
            steps: Workflow steps
            
        Returns:
            Embedding vector
        """
        # Create workflow context
        steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
        context = f"Workflow: {workflow_name}\nSteps:\n{steps_text}"
        return await self.embedder.generate_embedding(context)


# Example usage
async def main():
    """Example usage of embedding service"""
    
    # Initialize service
    config = EmbeddingConfig()
    service = EmbeddingService(config)
    
    # Test single embedding
    text = "def calculate_fibonacci(n): return n if n <= 1 else calculate_fibonacci(n-1) + calculate_fibonacci(n-2)"
    embedding = await service.generate_embedding(text)
    print(f"Generated embedding with dimension: {len(embedding)}")
    
    # Test batch embeddings
    texts = [
        "Error: ImportError - No module named 'numpy'",
        "Workflow: Data Processing Pipeline",
        "SELECT * FROM users WHERE active = true"
    ]
    embeddings = await service.batch_generate_embeddings(texts)
    print(f"Generated {len(embeddings)} embeddings")
    
    # Test similarity
    similarity = service.calculate_similarity(embeddings[0], embeddings[1])
    print(f"Similarity between first two texts: {similarity:.4f}")


if __name__ == "__main__":
    asyncio.run(main())