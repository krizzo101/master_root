"""Adaptive batch processing system for optimal chat import performance."""

import asyncio
import math
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import psutil
import structlog

from .performance_cache import PerformanceCacheManager

logger = structlog.get_logger(__name__)


@dataclass
class BatchMetrics:
    """Metrics for batch processing performance analysis."""

    batch_size: int
    processing_time: float
    items_per_second: float
    memory_usage_mb: float
    cpu_utilization: float
    error_count: int
    embedding_time: float
    database_time: float
    entity_extraction_time: float


class AdaptiveBatchSizer:
    """Dynamic batch size optimization based on system performance and data complexity."""

    def __init__(
        self,
        initial_batch_size: int = 50,
        min_batch_size: int = 10,
        max_batch_size: int = 2000,
        target_processing_time: float = 30.0,
        adjustment_factor: float = 1.2,
    ):
        """Initialize adaptive batch sizer."""
        self.current_batch_size = initial_batch_size
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.target_processing_time = target_processing_time
        self.adjustment_factor = adjustment_factor

        # Performance tracking
        self.batch_history = deque(maxlen=20)
        self.complexity_cache = {}
        self.system_performance_history = deque(maxlen=10)

    def calculate_content_complexity(self, items: List[Dict[str, Any]]) -> float:
        """Calculate content complexity score for adaptive batch sizing."""
        if not items:
            return 1.0

        total_complexity = 0.0

        for item in items:
            complexity = 1.0
            content = item.get("content", "") or ""

            # Length factor
            if len(content) > 5000:
                complexity *= 2.0
            elif len(content) > 1000:
                complexity *= 1.5

            # Code content increases complexity
            if (
                "```" in content
                or "function" in content.lower()
                or "class " in content.lower()
            ):
                complexity *= 1.8

            # Multiple URLs increase complexity
            url_count = content.count("http")
            if url_count > 3:
                complexity *= 1.5
            elif url_count > 1:
                complexity *= 1.2

            # JSON/structured data
            if content.strip().startswith("{") or content.strip().startswith("["):
                complexity *= 1.3

            # Entity-rich content (many @ mentions, # issues, etc.)
            entity_indicators = (
                content.count("@") + content.count("#") + content.count("$")
            )
            if entity_indicators > 10:
                complexity *= 1.4

            total_complexity += complexity

        return total_complexity / len(items)

    def get_system_performance_factor(self) -> float:
        """Get current system performance factor for batch size adjustment."""
        try:
            # CPU utilization
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory utilization
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Calculate performance factor
            performance_factor = 1.0

            # Reduce batch size if CPU is heavily loaded
            if cpu_percent > 80:
                performance_factor *= 0.6
            elif cpu_percent > 60:
                performance_factor *= 0.8

            # Reduce batch size if memory is heavily used
            if memory_percent > 85:
                performance_factor *= 0.5
            elif memory_percent > 70:
                performance_factor *= 0.7

            # Store for historical analysis
            self.system_performance_history.append(
                {
                    "timestamp": time.time(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "performance_factor": performance_factor,
                }
            )

            return performance_factor

        except Exception as e:
            logger.warning("Failed to get system performance", error=str(e))
            return 1.0

    def calculate_optimal_batch_size(
        self, items: List[Dict[str, Any]], recent_metrics: Optional[BatchMetrics] = None
    ) -> int:
        """Calculate optimal batch size based on content complexity and system performance."""

        # Base calculation factors
        content_complexity = self.calculate_content_complexity(items)
        system_factor = self.get_system_performance_factor()

        # Adjust based on recent performance
        performance_adjustment = 1.0
        if recent_metrics:
            # If processing took too long, reduce batch size
            if recent_metrics.processing_time > self.target_processing_time:
                performance_adjustment = (
                    self.target_processing_time / recent_metrics.processing_time
                )
            # If processing was very fast, we can increase batch size
            elif recent_metrics.processing_time < self.target_processing_time * 0.5:
                performance_adjustment = min(
                    1.5, self.target_processing_time / recent_metrics.processing_time
                )

        # Calculate new batch size
        adjustment_multiplier = (
            system_factor
            * performance_adjustment
            * (1.0 / content_complexity)  # Inverse relationship with complexity
        )

        new_batch_size = int(self.current_batch_size * adjustment_multiplier)

        # Apply constraints
        new_batch_size = max(
            self.min_batch_size, min(self.max_batch_size, new_batch_size)
        )

        # Gradual adjustment to avoid wild swings
        if new_batch_size != self.current_batch_size:
            change_ratio = new_batch_size / self.current_batch_size
            if change_ratio > self.adjustment_factor:
                new_batch_size = int(self.current_batch_size * self.adjustment_factor)
            elif change_ratio < (1 / self.adjustment_factor):
                new_batch_size = int(self.current_batch_size / self.adjustment_factor)

        self.current_batch_size = new_batch_size

        logger.debug(
            "Calculated optimal batch size",
            batch_size=new_batch_size,
            content_complexity=content_complexity,
            system_factor=system_factor,
            performance_adjustment=performance_adjustment,
        )

        return new_batch_size

    def record_batch_performance(self, metrics: BatchMetrics):
        """Record batch performance for future optimization."""
        self.batch_history.append(metrics)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for monitoring."""
        if not self.batch_history:
            return {"status": "no_data"}

        recent_metrics = list(self.batch_history)

        avg_processing_time = sum(m.processing_time for m in recent_metrics) / len(
            recent_metrics
        )
        avg_items_per_second = sum(m.items_per_second for m in recent_metrics) / len(
            recent_metrics
        )
        avg_batch_size = sum(m.batch_size for m in recent_metrics) / len(recent_metrics)

        return {
            "current_batch_size": self.current_batch_size,
            "avg_processing_time": avg_processing_time,
            "avg_items_per_second": avg_items_per_second,
            "avg_batch_size": avg_batch_size,
            "batch_history_size": len(recent_metrics),
            "target_processing_time": self.target_processing_time,
        }


class ParallelEmbeddingProcessor:
    """High-performance parallel embedding generation with intelligent queueing."""

    def __init__(
        self,
        max_concurrent: int = 20,
        queue_size: int = 1000,
        cache_manager: Optional[PerformanceCacheManager] = None,
    ):
        """Initialize parallel embedding processor."""
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue = asyncio.Queue(maxsize=queue_size)
        self.cache_manager = cache_manager

        # Performance tracking
        self.embeddings_generated = 0
        self.cache_hits = 0
        self.total_embedding_time = 0.0
        self.active_tasks = 0

    async def generate_embeddings_batch(
        self, texts: List[str], model: str = "default"
    ) -> List[Optional[List[float]]]:
        """Generate embeddings for a batch of texts in parallel."""
        if not texts:
            return []

        start_time = time.time()

        # Create tasks for parallel processing
        tasks = []
        for text in texts:
            task = asyncio.create_task(
                self._generate_single_embedding_cached(text, model)
            )
            tasks.append(task)

        # Wait for all embeddings to complete
        embeddings = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions and None results
        results = []
        for i, embedding in enumerate(embeddings):
            if isinstance(embedding, Exception):
                logger.warning(
                    "Embedding generation failed",
                    text_preview=texts[i][:50],
                    error=str(embedding),
                )
                results.append(None)
            else:
                results.append(embedding)

        duration = time.time() - start_time
        self.total_embedding_time += duration

        logger.debug(
            "Batch embedding generation completed",
            batch_size=len(texts),
            duration=duration,
            successful=sum(1 for r in results if r is not None),
        )

        return results

    async def _generate_single_embedding_cached(
        self, text: str, model: str
    ) -> Optional[List[float]]:
        """Generate single embedding with caching and concurrency control."""
        if not text or not text.strip():
            return None

        # Check cache first
        if self.cache_manager:
            cached_embedding = await self.cache_manager.embedding_cache.get(text, model)
            if cached_embedding:
                self.cache_hits += 1
                return cached_embedding

        # Generate embedding with concurrency control
        async with self.semaphore:
            self.active_tasks += 1
            try:
                # This would call the actual embedding service
                # For now, simulate with a simple hash-based embedding
                embedding = await self._simulate_embedding_generation(text)

                # Cache the result
                if embedding and self.cache_manager:
                    await self.cache_manager.embedding_cache.set(text, embedding, model)

                self.embeddings_generated += 1
                return embedding

            except Exception as e:
                logger.error(
                    "Embedding generation failed", text_preview=text[:50], error=str(e)
                )
                return None
            finally:
                self.active_tasks -= 1

    async def _simulate_embedding_generation(self, text: str) -> List[float]:
        """Simulate embedding generation (replace with actual service call)."""
        # Simulate processing time
        await asyncio.sleep(0.1)

        # Generate simple hash-based embedding for simulation
        import hashlib

        hash_bytes = hashlib.sha256(text.encode()).digest()
        embedding = []

        for i in range(0, min(len(hash_bytes), 128), 4):
            value = int.from_bytes(hash_bytes[i : i + 4], "big") / (2**31)
            embedding.append(max(-1.0, min(1.0, value - 1.0)))

        # Pad to standard size
        while len(embedding) < 384:
            embedding.append(0.0)

        return embedding[:384]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get embedding processor performance statistics."""
        avg_time_per_embedding = self.total_embedding_time / max(
            1, self.embeddings_generated
        )

        return {
            "embeddings_generated": self.embeddings_generated,
            "cache_hits": self.cache_hits,
            "cache_hit_rate_pct": (
                self.cache_hits / max(1, self.embeddings_generated + self.cache_hits)
            )
            * 100,
            "total_embedding_time": self.total_embedding_time,
            "avg_time_per_embedding": avg_time_per_embedding,
            "active_tasks": self.active_tasks,
            "max_concurrent": self.max_concurrent,
        }


class EnhancedBatchProcessor:
    """Main batch processor combining adaptive sizing, parallel processing, and caching."""

    def __init__(
        self,
        cache_manager: Optional[PerformanceCacheManager] = None,
        initial_batch_size: int = 100,
        max_parallel_batches: int = 4,
    ):
        """Initialize enhanced batch processor."""
        self.cache_manager = cache_manager
        self.batch_sizer = AdaptiveBatchSizer(initial_batch_size=initial_batch_size)
        self.embedding_processor = ParallelEmbeddingProcessor(
            cache_manager=cache_manager
        )
        self.max_parallel_batches = max_parallel_batches

        # Processing statistics
        self.total_items_processed = 0
        self.total_processing_time = 0.0
        self.batch_count = 0
        self.error_count = 0

    async def process_chat_items(
        self, items: List[Dict[str, Any]], chat_adapter: Any
    ) -> Dict[str, Any]:
        """Process chat items with adaptive batching and parallel optimization."""
        if not items:
            return {"processed": 0, "errors": 0}

        start_time = time.time()
        processed_count = 0
        error_count = 0

        # Split into adaptive batches
        batches = []
        current_index = 0

        while current_index < len(items):
            # Calculate optimal batch size for current subset
            remaining_items = items[current_index:]
            sample_size = min(50, len(remaining_items))
            sample_items = remaining_items[:sample_size]

            batch_size = self.batch_sizer.calculate_optimal_batch_size(sample_items)
            batch = items[current_index : current_index + batch_size]
            batches.append(batch)
            current_index += batch_size

        # Process batches in parallel with controlled concurrency
        semaphore = asyncio.Semaphore(self.max_parallel_batches)

        async def process_single_batch(
            batch: List[Dict[str, Any]]
        ) -> Tuple[int, int, BatchMetrics]:
            async with semaphore:
                return await self._process_batch_with_metrics(batch, chat_adapter)

        # Execute all batches
        batch_results = await asyncio.gather(
            *[process_single_batch(batch) for batch in batches], return_exceptions=True
        )

        # Aggregate results and collect metrics
        batch_metrics_list = []
        for result in batch_results:
            if isinstance(result, Exception):
                error_count += 1
                logger.error("Batch processing failed", error=str(result))
            else:
                batch_processed, batch_errors, batch_metrics = result
                processed_count += batch_processed
                error_count += batch_errors
                batch_metrics_list.append(batch_metrics)

                # Record performance for adaptive sizing
                self.batch_sizer.record_batch_performance(batch_metrics)

        # Update overall statistics
        total_duration = time.time() - start_time
        self.total_items_processed += processed_count
        self.total_processing_time += total_duration
        self.batch_count += len(batches)
        self.error_count += error_count

        return {
            "processed": processed_count,
            "errors": error_count,
            "batches": len(batches),
            "total_duration": total_duration,
            "items_per_second": processed_count / max(0.1, total_duration),
            "batch_metrics": batch_metrics_list,
            "adaptive_batch_summary": self.batch_sizer.get_performance_summary(),
        }

    async def _process_batch_with_metrics(
        self, batch: List[Dict[str, Any]], chat_adapter: Any
    ) -> Tuple[int, int, BatchMetrics]:
        """Process a single batch and collect detailed metrics."""
        batch_start = time.time()
        processed = 0
        errors = 0

        # Track memory before processing
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        try:
            # Entity extraction phase
            entity_start = time.time()
            for item in batch:
                if item.get("content"):
                    # This would call the entity extraction
                    pass  # Placeholder
            entity_time = time.time() - entity_start

            # Embedding generation phase
            embedding_start = time.time()
            texts = [item.get("content", "") for item in batch if item.get("content")]
            if texts:
                embeddings = await self.embedding_processor.generate_embeddings_batch(
                    texts
                )
                # Assign embeddings back to items
                embedding_idx = 0
                for item in batch:
                    if item.get("content"):
                        if (
                            embedding_idx < len(embeddings)
                            and embeddings[embedding_idx]
                        ):
                            item["embedding"] = embeddings[embedding_idx]
                        embedding_idx += 1
            embedding_time = time.time() - embedding_start

            # Database storage phase (simulated)
            db_start = time.time()
            # This would call the database insertion
            processed = len(batch)
            db_time = time.time() - db_start

        except Exception as e:
            logger.error("Batch processing failed", error=str(e))
            errors = len(batch)
            entity_time = 0
            embedding_time = 0
            db_time = 0

        # Calculate final metrics
        total_time = time.time() - batch_start
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        cpu_percent = psutil.cpu_percent()

        metrics = BatchMetrics(
            batch_size=len(batch),
            processing_time=total_time,
            items_per_second=processed / max(0.1, total_time),
            memory_usage_mb=memory_after - memory_before,
            cpu_utilization=cpu_percent,
            error_count=errors,
            embedding_time=embedding_time,
            database_time=db_time,
            entity_extraction_time=entity_time,
        )

        return processed, errors, metrics

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        avg_processing_time = self.total_processing_time / max(1, self.batch_count)
        overall_items_per_second = self.total_items_processed / max(
            0.1, self.total_processing_time
        )

        return {
            "total_items_processed": self.total_items_processed,
            "total_processing_time": self.total_processing_time,
            "total_batches": self.batch_count,
            "total_errors": self.error_count,
            "avg_processing_time_per_batch": avg_processing_time,
            "overall_items_per_second": overall_items_per_second,
            "error_rate_pct": (self.error_count / max(1, self.total_items_processed))
            * 100,
            "batch_sizer_stats": self.batch_sizer.get_performance_summary(),
            "embedding_processor_stats": self.embedding_processor.get_performance_stats(),
        }


# Factory function
async def create_enhanced_batch_processor(
    cache_manager: Optional[PerformanceCacheManager] = None, **kwargs
) -> EnhancedBatchProcessor:
    """Create and initialize enhanced batch processor."""
    processor = EnhancedBatchProcessor(cache_manager=cache_manager, **kwargs)
    logger.info("Enhanced batch processor created")
    return processor
