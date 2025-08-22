#!/usr/bin/env python3
"""
Simple RAG implementation for knowledge system
Provides vector search, caching, and context augmentation
"""

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

# Third-party imports
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        PointStruct,
        VectorParams,
    )

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logging.warning(
        "Qdrant client not available. Install with: pip install qdrant-client"
    )

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis client not available. Install with: pip install redis")

logger = logging.getLogger(__name__)


class SimpleVectorSearch:
    """Simple Qdrant integration for vector search (~30 lines)"""

    def __init__(self, collection_name: str = "knowledge_vectors"):
        """Initialize connection to Qdrant"""
        if not QDRANT_AVAILABLE:
            raise ImportError("Qdrant client not installed")

        self.client = QdrantClient(host="localhost", port=6333)
        self.collection_name = collection_name
        self.vector_size = 384  # sentence-transformers dimension

        # Ensure collection exists
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size, distance=Distance.COSINE
                ),
            )
            logger.info(f"Created Qdrant collection: {self.collection_name}")

    def index_knowledge(
        self, knowledge_id: str, embedding: List[float], metadata: Dict[str, Any] = None
    ):
        """Index a knowledge entry with its embedding"""
        point = PointStruct(
            id=hashlib.md5(knowledge_id.encode(), usedforsecurity=False).hexdigest(),
            vector=embedding,
            payload={"knowledge_id": knowledge_id, **(metadata or {})},
        )

        self.client.upsert(collection_name=self.collection_name, points=[point])

    def search_similar(self, query_embedding: List[float], limit: int = 5) -> List[str]:
        """Search for similar knowledge entries"""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
        )

        return [hit.payload["knowledge_id"] for hit in results]


class SimpleCache:
    """Simple Redis caching for queries and embeddings (~40 lines)"""

    def __init__(self, host: str = "localhost", port: int = 6379, ttl: int = 3600):
        """Initialize Redis connection"""
        if not REDIS_AVAILABLE:
            self.client = None
            logger.warning("Redis not available, caching disabled")
            return

        try:
            self.client = redis.Redis(host=host, port=port, decode_responses=True)
            self.client.ping()
            self.ttl = ttl
            logger.info("Redis cache initialized")
        except Exception:
            self.client = None
            logger.warning("Could not connect to Redis, caching disabled")

    def _get_key(self, prefix: str, content: str) -> str:
        """Generate cache key"""
        return f"{prefix}:{hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()}"

    def get_cached_search(self, query: str) -> Optional[List[str]]:
        """Get cached search results"""
        if not self.client:
            return None

        key = self._get_key("search", query)
        result = self.client.get(key)
        return json.loads(result) if result else None

    def cache_search(self, query: str, results: List[str]):
        """Cache search results"""
        if not self.client:
            return

        key = self._get_key("search", query)
        self.client.setex(key, self.ttl, json.dumps(results))

    def get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding"""
        if not self.client:
            return None

        key = self._get_key("embed", text)
        result = self.client.get(key)
        return json.loads(result) if result else None

    def cache_embedding(self, text: str, embedding: List[float]):
        """Cache embedding"""
        if not self.client:
            return

        key = self._get_key("embed", text)
        self.client.setex(key, self.ttl, json.dumps(embedding))


class RAGContext:
    """Simple context augmentation for agents (~50 lines)"""

    def __init__(self):
        """Initialize RAG context manager"""
        self.cache = SimpleCache()
        self.vector_search = None

        # Initialize vector search if available
        if QDRANT_AVAILABLE:
            try:
                self.vector_search = SimpleVectorSearch()
                logger.info("Vector search initialized")
            except Exception as e:
                logger.warning(f"Could not initialize vector search: {e}")
                self.vector_search = None

    def get_relevant_context(self, query: str, max_items: int = 3) -> Optional[str]:
        """Get relevant knowledge for a query"""
        # Check cache first
        cached_results = self.cache.get_cached_search(query)
        if cached_results:
            logger.info(f"Cache hit for query: {query[:50]}...")
            return self._format_context(cached_results[:max_items])

        # Try semantic search if available
        if self.vector_search:
            try:
                # Would need embedding service here
                # For now, return None to indicate need for embedding
                logger.info("Vector search available but needs embedding service")
                return None
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")

        # Fallback: return None (could implement keyword search here)
        return None

    def _format_context(self, knowledge_ids: List[str]) -> str:
        """Format knowledge IDs into context string"""
        if not knowledge_ids:
            return None

        context_parts = ["Relevant knowledge:", "---"]

        for i, kid in enumerate(knowledge_ids, 1):
            context_parts.append(f"{i}. Knowledge ID: {kid}")

        return "\n".join(context_parts)

    def augment_prompt(self, original_prompt: str, max_context: int = 3) -> str:
        """Augment a prompt with relevant context"""
        context = self.get_relevant_context(original_prompt, max_context)

        if context:
            return f"{context}\n\nUser Query:\n{original_prompt}"

        return original_prompt


# Integration helper functions
def test_qdrant_connection() -> bool:
    """Test if Qdrant is accessible"""
    if not QDRANT_AVAILABLE:
        return False

    try:
        client = QdrantClient(host="localhost", port=6333)
        client.get_collections()
        return True
    except Exception:
        return False


def test_redis_connection() -> bool:
    """Test if Redis is accessible"""
    if not REDIS_AVAILABLE:
        return False

    try:
        client = redis.Redis(host="localhost", port=6379)
        client.ping()
        return True
    except Exception:
        return False


if __name__ == "__main__":
    # Test connections
    print("Testing infrastructure...")
    print(f"Qdrant available: {test_qdrant_connection()}")
    print(f"Redis available: {test_redis_connection()}")

    # Test components if available
    if test_redis_connection():
        cache = SimpleCache()
        cache.cache_search("test query", ["id1", "id2"])
        result = cache.get_cached_search("test query")
        print(f"Cache test: {result}")

    if test_qdrant_connection():
        vs = SimpleVectorSearch()
        # Would need real embedding to test properly
        test_embedding = [0.1] * 384
        vs.index_knowledge("test_id", test_embedding, {"type": "test"})
        print("Vector indexing test: OK")
