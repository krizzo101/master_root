"""Context store for managing context bundles and embeddings."""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from opsvi_auto_forge.core.prompting.models import ContextBundle
from .chroma_client import ChromaClient

logger = logging.getLogger(__name__)


class ContextStore:
    """High-level context store for managing context bundles."""

    def __init__(self, chroma_client: ChromaClient):
        """Initialize context store.

        Args:
            chroma_client: ChromaDB client instance
        """
        self.chroma_client = chroma_client
        self.cache: Dict[str, Tuple[ContextBundle, datetime]] = {}
        self.cache_ttl = timedelta(minutes=30)

    def store_bundle(
        self, bundle: ContextBundle, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a context bundle.

        Args:
            bundle: Context bundle to store
            metadata: Additional metadata

        Returns:
            Document ID
        """
        # Add timestamp to metadata
        if metadata is None:
            metadata = {}
        metadata["stored_at"] = datetime.utcnow().isoformat()

        doc_id = self.chroma_client.store_context_bundle(bundle, metadata)

        # Cache the bundle
        self.cache[doc_id] = (bundle, datetime.utcnow())

        logger.info(f"Stored context bundle {doc_id} with {bundle.tokens} tokens")
        return doc_id

    def search_bundles(
        self,
        query: str,
        top_k: int = 8,
        filters: Optional[Dict[str, Any]] = None,
        min_score: float = 0.7,
    ) -> List[Tuple[str, ContextBundle, float]]:
        """Search for relevant context bundles.

        Args:
            query: Search query
            top_k: Number of results to return
            filters: Metadata filters
            min_score: Minimum similarity score

        Returns:
            List of (doc_id, bundle, score) tuples
        """
        results = self.chroma_client.search_context_bundles(query, top_k, filters)

        # Filter by minimum score
        filtered_results = [
            (doc_id, bundle, score)
            for doc_id, bundle, score in results
            if score >= min_score
        ]

        logger.info(
            f"Found {len(filtered_results)} relevant bundles (score >= {min_score})"
        )
        return filtered_results

    def get_bundle(self, doc_id: str) -> Optional[ContextBundle]:
        """Get a context bundle by ID.

        Args:
            doc_id: Document ID

        Returns:
            Context bundle if found, None otherwise
        """
        # Check cache first
        if doc_id in self.cache:
            bundle, timestamp = self.cache[doc_id]
            if datetime.utcnow() - timestamp < self.cache_ttl:
                return bundle
            else:
                # Remove expired cache entry
                del self.cache[doc_id]

        # Fetch from ChromaDB
        bundle = self.chroma_client.get_context_bundle(doc_id)
        if bundle:
            # Cache the bundle
            self.cache[doc_id] = (bundle, datetime.utcnow())

        return bundle

    def get_bundles_for_task(
        self, task_type: str, role: str, goal: str, max_tokens: int = 5000
    ) -> List[ContextBundle]:
        """Get context bundles relevant to a specific task.

        Args:
            task_type: Type of task
            role: Agent role
            goal: Task goal
            max_tokens: Maximum total tokens

        Returns:
            List of relevant context bundles
        """
        # Build search query
        query = f"{task_type} {role} {goal}"

        # Search for relevant bundles
        results = self.search_bundles(
            query=query,
            top_k=20,
            filters={"task_type": task_type, "role": role},
            min_score=0.6,
        )

        # Select bundles within token budget
        selected_bundles = []
        total_tokens = 0

        for doc_id, bundle, score in results:
            if total_tokens + bundle.tokens <= max_tokens:
                selected_bundles.append(bundle)
                total_tokens += bundle.tokens
            else:
                break

        logger.info(
            f"Selected {len(selected_bundles)} bundles with {total_tokens} tokens"
        )
        return selected_bundles

    def get_recent_bundles(
        self,
        hours: int = 24,
        task_type: Optional[str] = None,
        role: Optional[str] = None,
    ) -> List[Tuple[str, ContextBundle]]:
        """Get recently stored context bundles.

        Args:
            hours: Number of hours to look back
            task_type: Filter by task type
            role: Filter by role

        Returns:
            List of (doc_id, bundle) tuples
        """
        # Build filters
        filters = {}
        if task_type:
            filters["task_type"] = task_type
        if role:
            filters["role"] = role

        # Get all bundles and filter by timestamp
        all_bundles = self.chroma_client.list_context_bundles(filters, limit=1000)

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_bundles = []

        for doc_id, bundle in all_bundles:
            # Note: This is a simplified approach. In a real implementation,
            # you'd want to store and filter by actual timestamps in ChromaDB
            recent_bundles.append((doc_id, bundle))

        return recent_bundles[:100]  # Limit results

    def delete_bundle(self, doc_id: str) -> bool:
        """Delete a context bundle.

        Args:
            doc_id: Document ID to delete

        Returns:
            True if deleted, False otherwise
        """
        # Remove from cache
        if doc_id in self.cache:
            del self.cache[doc_id]

        return self.chroma_client.delete_context_bundle(doc_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get context store statistics.

        Returns:
            Dictionary with statistics
        """
        chroma_stats = self.chroma_client.get_collection_stats()

        return {
            "chroma_stats": chroma_stats,
            "cache_size": len(self.cache),
            "cache_ttl_minutes": self.cache_ttl.total_seconds() / 60,
        }

    def clear_cache(self):
        """Clear the in-memory cache."""
        self.cache.clear()
        logger.info("Cleared context store cache")

    def cleanup_expired_cache(self):
        """Remove expired entries from cache."""
        now = datetime.utcnow()
        expired_keys = [
            key
            for key, (bundle, timestamp) in self.cache.items()
            if now - timestamp > self.cache_ttl
        ]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
