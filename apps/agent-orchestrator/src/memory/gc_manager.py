#!/usr/bin/env python3
"""
Garbage Collection Manager for Agent Orchestrator
Implements intelligent garbage collection strategies to minimize memory usage
"""

import asyncio
import gc
import logging
import sys
import weakref
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import psutil

logger = logging.getLogger(__name__)


@dataclass
class GCStats:
    """Statistics for garbage collection operations"""

    collections_gen0: int = 0
    collections_gen1: int = 0
    collections_gen2: int = 0
    memory_freed_mb: float = 0
    total_collections: int = 0
    last_collection: Optional[datetime] = None
    peak_memory_mb: float = 0
    current_memory_mb: float = 0


class GarbageCollectionManager:
    """
    Intelligent garbage collection manager that:
    - Tracks memory usage patterns
    - Performs adaptive garbage collection
    - Clears caches and circular references
    - Provides memory usage insights
    """

    def __init__(
        self,
        target_memory_mb: int = 512,
        aggressive_threshold_mb: int = 768,
        collection_interval_sec: float = 30.0,
    ):
        self.target_memory_mb = target_memory_mb
        self.aggressive_threshold_mb = aggressive_threshold_mb
        self.collection_interval_sec = collection_interval_sec

        # Statistics
        self.stats = GCStats()
        self.process = psutil.Process()
        self.initial_memory_mb = self.get_memory_usage()
        self.stats.current_memory_mb = self.initial_memory_mb
        self.stats.peak_memory_mb = self.initial_memory_mb

        # Object tracking
        self.tracked_objects: Set[weakref.ref] = set()
        self.large_objects: weakref.WeakValueDictionary = weakref.WeakValueDictionary()

        # Collection control
        self.last_collection_time = datetime.now()
        self.collection_lock = asyncio.Lock()
        self.auto_collect_task: Optional[asyncio.Task] = None

        # Configure Python GC
        self._configure_gc()

        logger.info(
            f"GC Manager initialized: target={target_memory_mb}MB, "
            f"aggressive={aggressive_threshold_mb}MB"
        )

    def _configure_gc(self):
        """Configure Python garbage collector for optimal performance"""
        # Enable automatic garbage collection
        gc.enable()

        # Set thresholds for different generations
        # More frequent gen0 collections, less frequent gen2
        gc.set_threshold(700, 10, 10)  # Default is (700, 10, 10)

        # Enable debug flags for leak detection (optional)
        if logger.level <= logging.DEBUG:
            gc.set_debug(gc.DEBUG_STATS)

    def get_memory_usage(self) -> float:
        """Get current process memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024

    def track_object(self, obj: Any, size_estimate_mb: float = 0):
        """Track a large object for memory management"""
        try:
            # Create weak reference
            ref = weakref.ref(obj, self._on_object_deleted)
            self.tracked_objects.add(ref)

            # Track large objects separately
            if size_estimate_mb > 1:  # Objects larger than 1MB
                obj_id = id(obj)
                self.large_objects[obj_id] = obj
                logger.debug(
                    f"Tracking large object: {type(obj).__name__} (~{size_estimate_mb:.1f}MB)"
                )
        except TypeError:
            # Some objects can't be weakly referenced
            pass

    def _on_object_deleted(self, ref):
        """Callback when tracked object is deleted"""
        self.tracked_objects.discard(ref)

    async def collect_garbage(self, generation: int = -1) -> float:
        """
        Perform garbage collection and return memory freed.

        Args:
            generation: GC generation (-1 for auto, 0-2 for specific)

        Returns:
            Memory freed in MB
        """
        async with self.collection_lock:
            memory_before = self.get_memory_usage()

            # Clear any module-level caches
            self._clear_caches()

            # Determine collection generation
            if generation == -1:
                # Auto-select based on memory pressure
                if memory_before > self.aggressive_threshold_mb:
                    generation = 2  # Full collection
                elif memory_before > self.target_memory_mb:
                    generation = 1  # Medium collection
                else:
                    generation = 0  # Light collection

            # Perform collection
            logger.debug(
                f"Starting GC generation {generation} (memory: {memory_before:.1f}MB)"
            )

            if generation >= 0:
                collected = gc.collect(generation)
                self.stats.total_collections += 1

                if generation == 0:
                    self.stats.collections_gen0 += 1
                elif generation == 1:
                    self.stats.collections_gen1 += 1
                else:
                    self.stats.collections_gen2 += 1

                logger.debug(f"GC collected {collected} objects")

            # Force collection of large tracked objects if needed
            if memory_before > self.aggressive_threshold_mb:
                await self._force_collect_large_objects()

            # Update statistics
            memory_after = self.get_memory_usage()
            memory_freed = max(0, memory_before - memory_after)

            self.stats.memory_freed_mb += memory_freed
            self.stats.current_memory_mb = memory_after
            self.stats.peak_memory_mb = max(self.stats.peak_memory_mb, memory_after)
            self.stats.last_collection = datetime.now()

            if memory_freed > 0:
                logger.info(
                    f"GC freed {memory_freed:.1f}MB "
                    f"(gen{generation}: {memory_before:.1f}MB -> {memory_after:.1f}MB)"
                )

            return memory_freed

    def _clear_caches(self):
        """Clear various Python caches to free memory"""
        # Clear frame locals (safely)
        try:
            frame = sys._getframe()
            while frame:
                # Only clear if safe to do so
                if hasattr(frame, "f_locals"):
                    # Don't clear essential frames
                    frame_info = str(frame.f_code.co_filename)
                    if "gc_manager" not in frame_info and "asyncio" not in frame_info:
                        frame.f_locals.clear()
                frame = frame.f_back
        except:
            pass

        # Clear method caches (disabled - too dangerous)
        # for obj in gc.get_objects():
        #     try:
        #         if hasattr(obj, "__dict__") and hasattr(obj.__dict__, "clear"):
        #             # Clear instance dictionaries of large objects
        #             if sys.getsizeof(obj.__dict__) > 10000:  # 10KB threshold
        #                 obj.__dict__.clear()
        #     except:
        #         pass

        # Don't clear sys.modules - it breaks everything!
        # Instead, just clear linecache

        # Clear linecache (used by traceback)
        try:
            import linecache

            linecache.clearcache()
        except:
            pass

    async def _force_collect_large_objects(self):
        """Force collection of large tracked objects"""
        logger.debug("Force collecting large objects")

        # Clear references to large objects
        large_obj_ids = list(self.large_objects.keys())
        for obj_id in large_obj_ids:
            if obj_id in self.large_objects:
                del self.large_objects[obj_id]

        # Force immediate collection
        gc.collect(2)

        # Small delay to allow memory to be freed
        await asyncio.sleep(0.1)

    async def start_auto_collection(self):
        """Start automatic periodic garbage collection"""
        if self.auto_collect_task is None:
            self.auto_collect_task = asyncio.create_task(self._auto_collect_loop())
            logger.info("Started automatic garbage collection")

    async def stop_auto_collection(self):
        """Stop automatic garbage collection"""
        if self.auto_collect_task:
            self.auto_collect_task.cancel()
            try:
                await self.auto_collect_task
            except asyncio.CancelledError:
                pass
            self.auto_collect_task = None
            logger.info("Stopped automatic garbage collection")

    async def _auto_collect_loop(self):
        """Automatic collection loop"""
        while True:
            try:
                await asyncio.sleep(self.collection_interval_sec)

                # Check if collection is needed
                current_memory = self.get_memory_usage()
                time_since_last = (
                    datetime.now() - self.last_collection_time
                ).total_seconds()

                should_collect = (
                    current_memory > self.target_memory_mb
                    or time_since_last > self.collection_interval_sec * 2
                )

                if should_collect:
                    await self.collect_garbage()
                    self.last_collection_time = datetime.now()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto-collect loop: {e}")
                await asyncio.sleep(5)  # Brief pause on error

    async def optimize_memory(self) -> Dict[str, Any]:
        """
        Perform comprehensive memory optimization.

        Returns:
            Dictionary with optimization results
        """
        logger.info("Starting memory optimization")

        initial_memory = self.get_memory_usage()

        # Step 1: Clear caches
        self._clear_caches()

        # Step 2: Collect all generations
        await self.collect_garbage(0)
        await asyncio.sleep(0.1)
        await self.collect_garbage(1)
        await asyncio.sleep(0.1)
        await self.collect_garbage(2)

        # Step 3: Force collection of large objects
        await self._force_collect_large_objects()

        # Step 4: Final aggressive collection
        gc.collect(2)

        final_memory = self.get_memory_usage()
        memory_freed = initial_memory - final_memory

        results = {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_freed_mb": memory_freed,
            "percent_freed": (memory_freed / initial_memory * 100)
            if initial_memory > 0
            else 0,
            "total_collections": self.stats.total_collections,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"Memory optimization complete: freed {memory_freed:.1f}MB "
            f"({results['percent_freed']:.1f}%)"
        )

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get garbage collection statistics"""
        return {
            "current_memory_mb": self.get_memory_usage(),
            "initial_memory_mb": self.initial_memory_mb,
            "peak_memory_mb": self.stats.peak_memory_mb,
            "total_freed_mb": self.stats.memory_freed_mb,
            "collections": {
                "gen0": self.stats.collections_gen0,
                "gen1": self.stats.collections_gen1,
                "gen2": self.stats.collections_gen2,
                "total": self.stats.total_collections,
            },
            "last_collection": (
                self.stats.last_collection.isoformat()
                if self.stats.last_collection
                else None
            ),
            "tracked_objects": len(self.tracked_objects),
            "large_objects": len(self.large_objects),
            "gc_thresholds": gc.get_threshold(),
            "gc_counts": gc.get_count(),
        }

    def get_memory_report(self) -> str:
        """Generate a human-readable memory report"""
        stats = self.get_stats()

        report = [
            "=" * 60,
            "MEMORY REPORT",
            "=" * 60,
            f"Current Memory: {stats['current_memory_mb']:.1f} MB",
            f"Initial Memory: {stats['initial_memory_mb']:.1f} MB",
            f"Peak Memory: {stats['peak_memory_mb']:.1f} MB",
            f"Total Freed: {stats['total_freed_mb']:.1f} MB",
            "",
            "Collections:",
            f"  Generation 0: {stats['collections']['gen0']}",
            f"  Generation 1: {stats['collections']['gen1']}",
            f"  Generation 2: {stats['collections']['gen2']}",
            f"  Total: {stats['collections']['total']}",
            "",
            f"Tracked Objects: {stats['tracked_objects']}",
            f"Large Objects: {stats['large_objects']}",
            f"Last Collection: {stats['last_collection'] or 'Never'}",
            "=" * 60,
        ]

        return "\n".join(report)


class MemoryContextManager:
    """Context manager for memory-bounded operations"""

    def __init__(
        self, max_memory_mb: int, gc_manager: Optional[GarbageCollectionManager] = None
    ):
        self.max_memory_mb = max_memory_mb
        self.gc_manager = gc_manager or GarbageCollectionManager(
            target_memory_mb=max_memory_mb * 0.7
        )
        self.initial_memory = None

    async def __aenter__(self):
        self.initial_memory = self.gc_manager.get_memory_usage()
        await self.gc_manager.start_auto_collection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Stop auto collection
        await self.gc_manager.stop_auto_collection()

        # Perform final optimization
        await self.gc_manager.optimize_memory()

        # Check if memory limit was exceeded
        peak_memory = self.gc_manager.stats.peak_memory_mb
        if peak_memory > self.max_memory_mb:
            logger.warning(
                f"Memory limit exceeded: {peak_memory:.1f}MB > {self.max_memory_mb}MB"
            )

        # Log final stats
        final_memory = self.gc_manager.get_memory_usage()
        logger.info(
            f"Memory context complete: "
            f"{self.initial_memory:.1f}MB -> {final_memory:.1f}MB "
            f"(peak: {peak_memory:.1f}MB)"
        )
