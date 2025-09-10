"""Comprehensive deduplication system with content hashing and intelligent merging.

This module provides advanced deduplication capabilities for the Unified Context System,
including exact duplicate detection, semantic similarity analysis, temporal clustering,
and intelligent merge strategies across all data sources.
"""

import asyncio
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID

import numpy as np
import structlog
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

from ..models.common import ContextItem, ContextRelationship

logger = structlog.get_logger(__name__)


@dataclass
class DeduplicationConfig:
    """Configuration for deduplication algorithms."""

    # Content hashing
    content_hash_algorithm: str = "sha256"
    normalize_content: bool = True

    # Semantic similarity
    embedding_similarity_threshold: float = 0.95
    content_similarity_threshold: float = 0.85

    # Temporal clustering
    temporal_window_minutes: int = 60
    temporal_cluster_epsilon: float = 0.3
    temporal_min_samples: int = 2

    # Merge strategies
    confidence_threshold: float = 0.8
    preserve_original_metadata: bool = True
    auto_merge_threshold: float = 0.95

    # Performance
    batch_size: int = 1000
    max_similarity_comparisons: int = 10000


@dataclass
class DuplicateGroup:
    """Represents a group of potential duplicates."""

    primary_item: ContextItem
    duplicates: List[ContextItem] = field(default_factory=list)
    similarity_scores: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0
    merge_strategy: str = "manual"
    temporal_cluster_id: Optional[str] = None

    @property
    def total_items(self) -> int:
        return len(self.duplicates) + 1

    @property
    def source_types(self) -> Set[str]:
        return {self.primary_item.source_type} | {
            item.source_type for item in self.duplicates
        }


@dataclass
class DeduplicationResult:
    """Result of deduplication process."""

    total_items: int = 0
    exact_duplicates: int = 0
    semantic_duplicates: int = 0
    temporal_clusters: int = 0
    merged_items: int = 0
    preserved_items: int = 0

    duplicate_groups: List[DuplicateGroup] = field(default_factory=list)
    processing_time_seconds: float = 0.0
    quality_score: float = 0.0


class ContentHasher:
    """Advanced content hashing for exact duplicate detection."""

    def __init__(self, config: DeduplicationConfig):
        self.config = config
        self.logger = logger.bind(component="content_hasher")

    def generate_content_hash(self, item: ContextItem) -> str:
        """Generate content hash for exact duplicate detection."""
        # Build canonical content representation
        content_parts = []

        # Core content
        if item.content:
            content = (
                self._normalize_content(item.content)
                if self.config.normalize_content
                else item.content
            )
            content_parts.append(f"content:{content}")

        # Structural elements for code items
        if item.source_type == "code":
            if item.function_name:
                content_parts.append(f"function:{item.function_name}")
            if item.class_name:
                content_parts.append(f"class:{item.class_name}")
            if item.file_path:
                content_parts.append(f"file:{item.file_path}")

        # Title for chat/documentation items
        if item.title and item.source_type in ["chat", "documentation"]:
            title = (
                self._normalize_content(item.title)
                if self.config.normalize_content
                else item.title
            )
            content_parts.append(f"title:{title}")

        # Create canonical string
        canonical_content = "|".join(sorted(content_parts))

        # Generate hash
        if self.config.content_hash_algorithm == "sha256":
            return hashlib.sha256(canonical_content.encode()).hexdigest()
        elif self.config.content_hash_algorithm == "md5":
            return hashlib.md5(canonical_content.encode()).hexdigest()
        else:
            raise ValueError(
                f"Unsupported hash algorithm: {self.config.content_hash_algorithm}"
            )

    def _normalize_content(self, content: str) -> str:
        """Normalize content for consistent hashing."""
        # Remove extra whitespace
        normalized = " ".join(content.split())

        # Convert to lowercase for case-insensitive comparison
        normalized = normalized.lower()

        # Remove common punctuation variations
        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")

        return normalized.strip()


class SemanticSimilarityDetector:
    """Semantic similarity detection using embeddings and content analysis."""

    def __init__(self, config: DeduplicationConfig):
        self.config = config
        self.logger = logger.bind(component="semantic_similarity")

    async def find_semantic_duplicates(
        self, items: List[ContextItem]
    ) -> List[Tuple[ContextItem, ContextItem, float]]:
        """Find semantically similar items using embedding similarity."""
        similar_pairs = []

        # Group by source type for more efficient comparison
        grouped_items = defaultdict(list)
        for item in items:
            if item.embedding:  # Only process items with embeddings
                grouped_items[item.source_type].append(item)

        # Process each source type group
        for source_type, source_items in grouped_items.items():
            if len(source_items) < 2:
                continue

            self.logger.info(
                "Processing semantic similarity",
                source_type=source_type,
                item_count=len(source_items),
            )

            # Convert embeddings to numpy array
            embeddings = np.array([item.embedding for item in source_items])

            # Compute pairwise cosine similarity
            similarity_matrix = cosine_similarity(embeddings)

            # Find similar pairs above threshold
            for i in range(len(source_items)):
                for j in range(i + 1, len(source_items)):
                    similarity_score = similarity_matrix[i][j]

                    if similarity_score >= self.config.embedding_similarity_threshold:
                        similar_pairs.append(
                            (source_items[i], source_items[j], similarity_score)
                        )

        return similar_pairs

    def calculate_content_similarity(
        self, item1: ContextItem, item2: ContextItem
    ) -> float:
        """Calculate content similarity using text analysis."""
        if not item1.content or not item2.content:
            return 0.0

        # Simple Jaccard similarity on word sets
        words1 = set(item1.content.lower().split())
        words2 = set(item2.content.lower().split())

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0


class TemporalClusterAnalyzer:
    """Temporal clustering for related events and activities."""

    def __init__(self, config: DeduplicationConfig):
        self.config = config
        self.logger = logger.bind(component="temporal_clustering")

    async def create_temporal_clusters(
        self, items: List[ContextItem]
    ) -> Dict[str, List[ContextItem]]:
        """Create temporal clusters of related items."""
        if not items:
            return {}

        # Sort items by timestamp
        sorted_items = sorted(items, key=lambda x: x.timestamp)

        # Group by source type and actor for initial clustering
        grouped_items = defaultdict(list)
        for item in sorted_items:
            key = f"{item.source_type}:{item.actor_id or 'unknown'}"
            grouped_items[key].append(item)

        clusters = {}

        for group_key, group_items in grouped_items.items():
            if len(group_items) < self.config.temporal_min_samples:
                continue

            # Extract timestamps as features
            timestamps = np.array(
                [item.timestamp.timestamp() for item in group_items]
            ).reshape(-1, 1)

            # Normalize timestamps to minutes
            timestamps = timestamps / 60

            # Apply DBSCAN clustering
            clustering = DBSCAN(
                eps=self.config.temporal_cluster_epsilon,
                min_samples=self.config.temporal_min_samples,
            ).fit(timestamps)

            # Group items by cluster
            for cluster_id in set(clustering.labels_):
                if cluster_id == -1:  # Noise points
                    continue

                cluster_key = f"{group_key}:cluster_{cluster_id}"
                cluster_items = [
                    group_items[i]
                    for i in range(len(group_items))
                    if clustering.labels_[i] == cluster_id
                ]

                if len(cluster_items) >= self.config.temporal_min_samples:
                    clusters[cluster_key] = cluster_items

        self.logger.info("Temporal clustering completed", cluster_count=len(clusters))
        return clusters


class IntelligentMerger:
    """Intelligent merging strategies for duplicate content."""

    def __init__(self, config: DeduplicationConfig):
        self.config = config
        self.logger = logger.bind(component="intelligent_merger")

    def create_merged_item(self, duplicate_group: DuplicateGroup) -> ContextItem:
        """Create intelligently merged item from duplicate group."""
        primary = duplicate_group.primary_item
        duplicates = duplicate_group.duplicates

        # Determine merge strategy
        if duplicate_group.confidence >= self.config.auto_merge_threshold:
            return self._auto_merge(primary, duplicates)
        else:
            return self._conservative_merge(primary, duplicates)

    def _auto_merge(
        self, primary: ContextItem, duplicates: List[ContextItem]
    ) -> ContextItem:
        """Automatic merge with high confidence."""
        merged = primary

        # Merge content (use longest/most complete)
        all_items = [primary] + duplicates
        best_content_item = max(all_items, key=lambda x: len(x.content or ""))

        if best_content_item != primary:
            merged.content = best_content_item.content
            merged.content_hash = best_content_item.content_hash

        # Merge metadata
        all_tags = set()
        all_metrics = {}

        for item in all_items:
            if item.tags:
                all_tags.update(item.tags)
            if item.metrics:
                all_metrics.update(item.metrics)

        merged.tags = list(all_tags)
        merged.metrics = all_metrics

        # Update source data to include merge information
        merged.source_data = merged.source_data or {}
        merged.source_data.update(
            {
                "merged_from": [item.source_id for item in duplicates],
                "merge_strategy": "auto",
                "merge_confidence": max(duplicate_group.similarity_scores.values()),
                "merged_at": datetime.utcnow().isoformat(),
            }
        )

        return merged

    def _conservative_merge(
        self, primary: ContextItem, duplicates: List[ContextItem]
    ) -> ContextItem:
        """Conservative merge preserving original data."""
        merged = primary

        # Only merge non-conflicting metadata
        merged.source_data = merged.source_data or {}
        merged.source_data.update(
            {
                "potential_duplicates": [item.source_id for item in duplicates],
                "merge_strategy": "conservative",
                "requires_review": True,
                "flagged_at": datetime.utcnow().isoformat(),
            }
        )

        return merged


class ComprehensiveDeduplicator:
    """Main deduplication system orchestrator."""

    def __init__(self, config: Optional[DeduplicationConfig] = None):
        self.config = config or DeduplicationConfig()
        self.content_hasher = ContentHasher(self.config)
        self.semantic_detector = SemanticSimilarityDetector(self.config)
        self.temporal_analyzer = TemporalClusterAnalyzer(self.config)
        self.merger = IntelligentMerger(self.config)
        self.logger = logger.bind(component="deduplicator")

    async def deduplicate_items(self, items: List[ContextItem]) -> DeduplicationResult:
        """Comprehensive deduplication of context items."""
        start_time = datetime.utcnow()
        result = DeduplicationResult(total_items=len(items))

        self.logger.info("Starting deduplication", item_count=len(items))

        try:
            # Step 1: Generate content hashes
            await self._generate_content_hashes(items)

            # Step 2: Find exact duplicates
            exact_duplicate_groups = self._find_exact_duplicates(items)
            result.exact_duplicates = sum(
                len(group.duplicates) for group in exact_duplicate_groups
            )

            # Step 3: Find semantic duplicates
            remaining_items = self._get_remaining_items(items, exact_duplicate_groups)
            semantic_pairs = await self.semantic_detector.find_semantic_duplicates(
                remaining_items
            )
            semantic_groups = self._create_semantic_groups(semantic_pairs)
            result.semantic_duplicates = sum(
                len(group.duplicates) for group in semantic_groups
            )

            # Step 4: Temporal clustering
            temporal_clusters = await self.temporal_analyzer.create_temporal_clusters(
                remaining_items
            )
            result.temporal_clusters = len(temporal_clusters)

            # Step 5: Combine all duplicate groups
            all_groups = exact_duplicate_groups + semantic_groups
            result.duplicate_groups = all_groups

            # Step 6: Apply intelligent merging
            merged_items = []
            for group in all_groups:
                if group.confidence >= self.config.confidence_threshold:
                    merged_item = self.merger.create_merged_item(group)
                    merged_items.append(merged_item)
                    result.merged_items += 1
                else:
                    result.preserved_items += group.total_items

            # Calculate quality metrics
            result.processing_time_seconds = (
                datetime.utcnow() - start_time
            ).total_seconds()
            result.quality_score = self._calculate_quality_score(result)

            self.logger.info(
                "Deduplication completed",
                exact_duplicates=result.exact_duplicates,
                semantic_duplicates=result.semantic_duplicates,
                merged_items=result.merged_items,
                processing_time=result.processing_time_seconds,
            )

            return result

        except Exception as e:
            self.logger.error("Deduplication failed", error=str(e))
            raise

    async def _generate_content_hashes(self, items: List[ContextItem]) -> None:
        """Generate content hashes for all items."""
        for item in items:
            if not item.content_hash:
                item.content_hash = self.content_hasher.generate_content_hash(item)

    def _find_exact_duplicates(self, items: List[ContextItem]) -> List[DuplicateGroup]:
        """Find exact duplicates based on content hash."""
        hash_groups = defaultdict(list)

        for item in items:
            if item.content_hash:
                hash_groups[item.content_hash].append(item)

        duplicate_groups = []
        for content_hash, grouped_items in hash_groups.items():
            if len(grouped_items) > 1:
                # Sort by timestamp to get primary item
                sorted_items = sorted(grouped_items, key=lambda x: x.timestamp)

                group = DuplicateGroup(
                    primary_item=sorted_items[0],
                    duplicates=sorted_items[1:],
                    similarity_scores={
                        item.source_id: 1.0 for item in sorted_items[1:]
                    },
                    confidence=1.0,
                    merge_strategy="exact_match",
                )
                duplicate_groups.append(group)

        return duplicate_groups

    def _get_remaining_items(
        self, all_items: List[ContextItem], exact_groups: List[DuplicateGroup]
    ) -> List[ContextItem]:
        """Get items not in exact duplicate groups."""
        processed_ids = set()
        for group in exact_groups:
            processed_ids.add(group.primary_item.source_id)
            for item in group.duplicates:
                processed_ids.add(item.source_id)

        return [item for item in all_items if item.source_id not in processed_ids]

    def _create_semantic_groups(
        self, semantic_pairs: List[Tuple[ContextItem, ContextItem, float]]
    ) -> List[DuplicateGroup]:
        """Create duplicate groups from semantic similarity pairs."""
        # Build similarity graph
        similarity_graph = defaultdict(list)
        for item1, item2, score in semantic_pairs:
            similarity_graph[item1.source_id].append((item2, score))
            similarity_graph[item2.source_id].append((item1, score))

        # Find connected components (simple approach)
        visited = set()
        groups = []

        for item1, item2, score in semantic_pairs:
            if item1.source_id in visited or item2.source_id in visited:
                continue

            # Create group with highest scoring item as primary
            primary = (
                item1 if score >= self.config.embedding_similarity_threshold else item2
            )
            duplicate = item2 if primary == item1 else item1

            group = DuplicateGroup(
                primary_item=primary,
                duplicates=[duplicate],
                similarity_scores={duplicate.source_id: score},
                confidence=score,
                merge_strategy="semantic_match",
            )

            groups.append(group)
            visited.add(item1.source_id)
            visited.add(item2.source_id)

        return groups

    def _calculate_quality_score(self, result: DeduplicationResult) -> float:
        """Calculate overall quality score for deduplication."""
        if result.total_items == 0:
            return 1.0

        # Factor in reduction ratio
        total_duplicates = result.exact_duplicates + result.semantic_duplicates
        reduction_ratio = total_duplicates / result.total_items

        # Factor in processing efficiency
        efficiency_score = min(1.0, 60.0 / result.processing_time_seconds)  # Target 60s

        # Combine metrics
        quality_score = (0.7 * reduction_ratio) + (0.3 * efficiency_score)
        return min(1.0, quality_score)


# Factory function for easy instantiation
def create_deduplicator(
    embedding_threshold: float = 0.95,
    temporal_window_minutes: int = 60,
    auto_merge_threshold: float = 0.95,
) -> ComprehensiveDeduplicator:
    """Create deduplicator with common configuration."""
    config = DeduplicationConfig(
        embedding_similarity_threshold=embedding_threshold,
        temporal_window_minutes=temporal_window_minutes,
        auto_merge_threshold=auto_merge_threshold,
    )
    return ComprehensiveDeduplicator(config)
