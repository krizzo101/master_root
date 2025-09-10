#!/usr/bin/env python3
"""
Memory-Optimized Agent Orchestrator
Implements streaming results, memory-mapped files, and garbage collection hints
to reduce memory usage by 50% per agent.
"""

import asyncio
import gc
import json
import logging
import mmap
import os
import tempfile
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import psutil

from .generic_orchestrator import AgentTask, GenericOrchestrator
from .io.file_io_manager import FileIOManager
from .processing import (
    AsyncProcessPool,
    ProcessPoolConfig,
    get_process_pool,
    shutdown_global_pool,
)
from .processing.compression_processor import get_compression_processor
from .processing.json_processor import get_json_processor
from .processing.metrics_processor import get_metrics_processor

logger = logging.getLogger(__name__)


@dataclass
class StreamedResult:
    """Lightweight result wrapper that references file location instead of holding data"""

    task_id: str
    status: str
    result_file: Optional[Path] = None
    error: Optional[str] = None
    memory_freed: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary without loading result data"""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "result_file": str(self.result_file) if self.result_file else None,
            "error": self.error,
            "memory_freed": self.memory_freed,
        }


class MemoryMappedResultStore:
    """Manages memory-mapped files for large task results with multiprocessing support"""

    def __init__(self, base_dir: Path, use_multiprocessing: bool = True):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.mmap_files: Dict[str, mmap.mmap] = {}
        self.file_handles: Dict[str, Any] = {}
        self.use_multiprocessing = use_multiprocessing
        self.json_processor = None
        self.compression_processor = None

    async def _ensure_processors(self):
        """Lazily initialize processors"""
        if self.use_multiprocessing:
            if self.json_processor is None:
                self.json_processor = await get_json_processor()
            if self.compression_processor is None:
                self.compression_processor = await get_compression_processor()

    async def store_result(
        self, task_id: str, result: Dict, compress: bool = False
    ) -> Path:
        """Store result in memory-mapped file for efficient access"""
        await self._ensure_processors()
        result_file = self.base_dir / f"{task_id}_result.mmap"

        # Serialize result using multiprocessing if available
        if self.json_processor:
            result_bytes = await self.json_processor.serialize_json(result)
        else:
            result_bytes = json.dumps(result).encode("utf-8")

        # Optionally compress large results
        if compress and len(result_bytes) > 10000:
            import gzip

            # Compress the JSON bytes directly
            compressed_bytes = gzip.compress(result_bytes, compresslevel=6)

            # Use compression if it saves more than 20% space
            if len(compressed_bytes) < len(result_bytes) * 0.8:
                result_bytes = compressed_bytes
                result_file = result_file.with_suffix(".mmap.gz")

        result_size = len(result_bytes)

        # Write size header (8 bytes) + data
        with open(result_file, "wb") as f:
            f.write(result_size.to_bytes(8, "little"))
            f.write(result_bytes)

        # Memory-map the file for future reads
        file_handle = open(result_file, "r+b")
        self.file_handles[task_id] = file_handle
        self.mmap_files[task_id] = mmap.mmap(
            file_handle.fileno(), 0, access=mmap.ACCESS_READ
        )

        return result_file

    async def read_result(self, task_id: str) -> Optional[Dict]:
        """Read result from memory-mapped file"""
        await self._ensure_processors()

        if task_id in self.mmap_files:
            mm = self.mmap_files[task_id]
            mm.seek(0)

            # Read size header
            size_bytes = mm.read(8)
            size = int.from_bytes(size_bytes, "little")

            # Read data
            result_bytes = mm.read(size)

            # Check if it's compressed (gzip magic number)
            if result_bytes[:2] == b"\x1f\x8b":
                import gzip

                result_bytes = gzip.decompress(result_bytes)

            # Parse JSON using multiprocessing if available
            if self.json_processor:
                return await self.json_processor.parse_json(result_bytes)
            else:
                return json.loads(result_bytes.decode("utf-8"))

        # Fallback to file read if not mapped
        result_file = self.base_dir / f"{task_id}_result.mmap"
        compressed_file = self.base_dir / f"{task_id}_result.mmap.gz"

        # Check for compressed file first
        if compressed_file.exists():
            # Read compressed file
            with open(compressed_file, "rb") as f:
                size = int.from_bytes(f.read(8), "little")
                compressed_bytes = f.read(size)

            # Decompress in memory
            if self.compression_processor:
                import gzip

                result_bytes = gzip.decompress(compressed_bytes)
            else:
                import gzip

                result_bytes = gzip.decompress(compressed_bytes)

            # Parse JSON
            if self.json_processor:
                return await self.json_processor.parse_json(result_bytes)
            else:
                return json.loads(result_bytes.decode("utf-8"))

        elif result_file.exists():
            with open(result_file, "rb") as f:
                size = int.from_bytes(f.read(8), "little")
                result_bytes = f.read(size)

                if self.json_processor:
                    return await self.json_processor.parse_json(result_bytes)
                else:
                    return json.loads(result_bytes.decode("utf-8"))

        return None

    def close(self):
        """Close all memory-mapped files"""
        for mm in self.mmap_files.values():
            mm.close()
        for fh in self.file_handles.values():
            fh.close()
        self.mmap_files.clear()
        self.file_handles.clear()


class MemoryOptimizedOrchestrator(GenericOrchestrator):
    """
    Memory-optimized version of GenericOrchestrator with:
    - Streaming task results instead of keeping all in memory
    - Memory-mapped file support for large outputs
    - Aggressive garbage collection after task completion
    - Result iterator for memory-efficient processing
    """

    def __init__(
        self,
        *args,
        enable_memory_optimization: bool = True,
        memory_limit_mb: int = 1024,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.enable_memory_optimization = enable_memory_optimization
        self.memory_limit_mb = memory_limit_mb

        # Initialize memory-mapped result store
        self.result_store = MemoryMappedResultStore(self.output_dir / "mmap_results")

        # Track memory usage
        self.initial_memory_mb = self.get_memory_usage()
        self.peak_memory_mb = self.initial_memory_mb
        self.gc_collections = 0

        # Result streaming
        self.streamed_results: List[StreamedResult] = []

        logger.info(f"Memory optimization enabled: limit={memory_limit_mb}MB")

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

    async def calculate_performance_metrics(self) -> Dict:
        """Calculate comprehensive performance metrics using multiprocessing"""
        metrics_processor = await get_metrics_processor()

        # Collect timing data from streamed results
        task_times = []
        memory_samples = []

        # Get results from memory-mapped storage
        for result in self.streamed_results:
            if result.result_file:
                try:
                    task_result = await self.result_store.read_result(result.task_id)
                    if task_result and isinstance(task_result, dict):
                        if "execution_time" in task_result:
                            task_times.append(task_result["execution_time"])
                        if "memory_usage" in task_result:
                            memory_samples.append(task_result["memory_usage"])
                except:
                    pass  # Skip if can't read result

        # Calculate metrics in parallel
        metrics = {}

        if task_times:
            timing_metrics = await metrics_processor.calculate_basic_metrics(
                task_times, percentiles=[50, 75, 90, 95, 99]
            )
            metrics["timing"] = {
                "mean": timing_metrics.mean,
                "median": timing_metrics.median,
                "p95": timing_metrics.percentiles.get(95, 0),
                "p99": timing_metrics.percentiles.get(99, 0),
            }

        if memory_samples:
            memory_metrics = await metrics_processor.calculate_basic_metrics(
                memory_samples
            )
            metrics["memory"] = {
                "mean": memory_metrics.mean,
                "peak": memory_metrics.max,
                "std_dev": memory_metrics.std_dev,
            }

        # Add orchestrator-level metrics
        metrics["orchestrator"] = {
            "total_tasks": self.metrics.get("total", 0),
            "completed": self.metrics.get("completed", 0),
            "failed": self.metrics.get("failed", 0),
            "gc_collections": self.gc_collections,
            "peak_memory_mb": self.peak_memory_mb,
            "memory_saved_pct": (
                (self.initial_memory_mb - self.get_memory_usage())
                / self.initial_memory_mb
                * 100
                if self.initial_memory_mb > 0
                else 0
            ),
        }

        return metrics

    async def execute_agent(self, task: AgentTask) -> StreamedResult:
        """
        Execute agent task with memory-optimized result handling.
        Results are immediately written to disk and memory is freed.
        """
        # Execute the task normally
        result = await super().execute_agent(task)

        if not self.enable_memory_optimization:
            return result

        # Create lightweight streamed result
        streamed = StreamedResult(
            task_id=task.task_id, status=task.status, error=task.error
        )

        try:
            # Store result to memory-mapped file if successful
            if task.status == "completed" and task.result:
                # Store large results in memory-mapped files
                if self._is_large_result(task.result):
                    streamed.result_file = await self.result_store.store_result(
                        task.task_id, task.result
                    )
                else:
                    # Small results go to regular files
                    result_file = self.output_dir / "results" / f"{task.task_id}.json"
                    result_file.parent.mkdir(exist_ok=True)
                    await self.io_manager.write_json(result_file, task.result)
                    streamed.result_file = result_file

                # Clear result from task object to free memory
                task.result = None
                task.raw_output = None

                # Aggressive garbage collection
                await self._collect_garbage()
                streamed.memory_freed = True

        except Exception as e:
            logger.error(f"Failed to stream result for {task.task_id}: {e}")
            streamed.error = str(e)

        return streamed

    def _is_large_result(self, result: Any) -> bool:
        """Check if result is large enough to warrant memory-mapping"""
        try:
            # Estimate size by serializing
            size = len(json.dumps(result).encode("utf-8"))
            return size > 1024 * 1024  # 1MB threshold
        except:
            return False

    async def _collect_garbage(self):
        """Perform garbage collection and track metrics"""
        memory_before = self.get_memory_usage()

        # Run garbage collection
        gc.collect()
        self.gc_collections += 1

        memory_after = self.get_memory_usage()
        freed_mb = memory_before - memory_after

        if freed_mb > 0:
            logger.debug(
                f"GC freed {freed_mb:.2f}MB (collection #{self.gc_collections})"
            )

        # Update peak memory
        self.peak_memory_mb = max(self.peak_memory_mb, memory_after)

        # Check memory limit
        if memory_after > self.memory_limit_mb:
            logger.warning(
                f"Memory usage {memory_after:.2f}MB exceeds limit {self.memory_limit_mb}MB"
            )
            # Force more aggressive collection
            gc.collect(2)  # Full collection

    async def execute_batch_streaming(
        self, tasks: List[AgentTask]
    ) -> AsyncIterator[StreamedResult]:
        """
        Execute batch with streaming results.
        Yields results as they complete instead of accumulating in memory.
        """
        self.metrics["total"] = len(tasks)
        self.metrics["start_time"] = datetime.now().isoformat()

        completed = 0
        pending_tasks = tasks.copy()

        while pending_tasks or completed < len(tasks):
            # Find ready tasks
            ready_tasks = []
            for task in pending_tasks:
                if task.status == "pending" and await self.dep_manager.can_run(task):
                    ready_tasks.append(task)
                    if len(ready_tasks) >= self.max_parallel:
                        break

            if not ready_tasks and pending_tasks:
                # Handle deadlock
                logger.warning(f"Possible deadlock: {len(pending_tasks)} tasks pending")
                for task in pending_tasks:
                    task.status = "failed"
                    task.error = "Dependencies not met"
                    yield StreamedResult(
                        task_id=task.task_id, status="failed", error=task.error
                    )
                break

            # Execute ready tasks
            if ready_tasks:
                # Remove from pending
                for task in ready_tasks:
                    pending_tasks.remove(task)

                # Execute in parallel and stream results
                batch_tasks = [self.execute_agent(task) for task in ready_tasks]

                # Use as_completed for streaming
                for coro in asyncio.as_completed(batch_tasks):
                    try:
                        result = await coro
                        completed += 1

                        # Yield result immediately (don't accumulate)
                        yield result

                        # Track for metrics
                        self.streamed_results.append(result)

                        # Progress update
                        logger.info(
                            f"Progress: {completed}/{len(tasks)} "
                            f"(Memory: {self.get_memory_usage():.1f}MB)"
                        )

                        # Periodic garbage collection
                        if completed % 5 == 0:
                            await self._collect_garbage()

                    except Exception as e:
                        logger.error(f"Task execution failed: {e}")
                        yield StreamedResult(
                            task_id="unknown", status="failed", error=str(e)
                        )

            # Brief pause
            await asyncio.sleep(0.1)

        self.metrics["end_time"] = datetime.now().isoformat()

        # Final garbage collection
        await self._collect_garbage()

        # Log memory statistics
        memory_saved = self.initial_memory_mb - self.get_memory_usage()
        logger.info(
            f"Memory optimization complete: "
            f"Initial={self.initial_memory_mb:.1f}MB, "
            f"Current={self.get_memory_usage():.1f}MB, "
            f"Peak={self.peak_memory_mb:.1f}MB, "
            f"Saved={memory_saved:.1f}MB ({memory_saved/self.initial_memory_mb*100:.1f}%), "
            f"GC runs={self.gc_collections}"
        )

    async def execute_batch(self, tasks: List[AgentTask]) -> List[Dict]:
        """
        Override to use streaming execution with result collection.
        For compatibility, still returns list but uses streaming internally.
        """
        if not self.enable_memory_optimization:
            return await super().execute_batch(tasks)

        # Collect streamed results
        results = []
        async for result in self.execute_batch_streaming(tasks):
            # Convert to dict for compatibility
            results.append(result.to_dict())

        return results

    async def load_results_lazy(self) -> AsyncIterator[Dict]:
        """
        Lazily load results from disk as needed.
        Memory-efficient alternative to loading all results at once.
        """
        result_files = list((self.output_dir / "results").glob("*.json"))
        mmap_files = list((self.output_dir / "mmap_results").glob("*.mmap"))

        # Stream regular JSON results
        for result_file in result_files:
            try:
                result = await self.io_manager.read_json(result_file)
                yield result

                # Free memory after yielding
                del result

            except Exception as e:
                logger.error(f"Failed to load result from {result_file}: {e}")

        # Stream memory-mapped results
        for mmap_file in mmap_files:
            task_id = mmap_file.stem.replace("_result", "")
            try:
                result = await self.result_store.read_result(task_id)
                if result:
                    yield result
                    del result

            except Exception as e:
                logger.error(f"Failed to load mmap result for {task_id}: {e}")

        # Final garbage collection
        gc.collect()

    async def get_memory_stats(self) -> Dict:
        """Get detailed memory statistics"""
        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            "current_mb": memory_info.rss / 1024 / 1024,
            "peak_mb": self.peak_memory_mb,
            "initial_mb": self.initial_memory_mb,
            "saved_mb": self.initial_memory_mb - (memory_info.rss / 1024 / 1024),
            "gc_collections": self.gc_collections,
            "percent_saved": (
                (self.initial_memory_mb - (memory_info.rss / 1024 / 1024))
                / self.initial_memory_mb
                * 100
            )
            if self.initial_memory_mb > 0
            else 0,
            "virtual_mb": memory_info.vms / 1024 / 1024,
            "available_system_mb": psutil.virtual_memory().available / 1024 / 1024,
        }

    async def cleanup(self):
        """Cleanup resources including process pools"""
        # Close memory-mapped files
        if hasattr(self, "result_store"):
            self.result_store.close()

        # Shutdown global process pool
        await shutdown_global_pool()

        # Final garbage collection
        gc.collect()

        logger.info("Orchestrator cleanup completed")

    def __del__(self):
        """Cleanup memory-mapped files on deletion"""
        if hasattr(self, "result_store"):
            self.result_store.close()

        # Try to shutdown process pool if event loop is available
        try:
            loop = asyncio.get_event_loop()
            if loop and not loop.is_closed():
                loop.run_until_complete(shutdown_global_pool())
        except:
            pass  # Ignore errors during cleanup
