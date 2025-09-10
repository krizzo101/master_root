#!/usr/bin/env python3
"""
Multiprocessing Executor for CPU-intensive Operations
Provides async interface to ProcessPoolExecutor for CPU-bound tasks
"""

import asyncio
import bz2
import gzip
import hashlib
import json
import logging
import lzma
import os
import pickle
import statistics
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


# CPU-intensive functions that run in separate processes
def _parse_json_batch(json_strings: List[str]) -> List[Dict]:
    """Parse multiple JSON strings in a single process"""
    results = []
    for json_str in json_strings:
        try:
            results.append(json.loads(json_str))
        except json.JSONDecodeError as e:
            results.append({"error": str(e), "input": json_str[:100]})
    return results


def _compress_data(
    data: bytes, algorithm: str = "gzip", level: int = 6
) -> Tuple[bytes, int]:
    """Compress data using specified algorithm"""
    original_size = len(data)

    if algorithm == "gzip":
        compressed = gzip.compress(data, compresslevel=level)
    elif algorithm == "lzma":
        compressed = lzma.compress(data, preset=level)
    elif algorithm == "bz2":
        compressed = bz2.compress(data, compresslevel=level)
    else:
        raise ValueError(f"Unsupported compression algorithm: {algorithm}")

    compressed_size = len(compressed)
    return compressed, compressed_size


def _decompress_data(data: bytes, algorithm: str = "gzip") -> bytes:
    """Decompress data using specified algorithm"""
    if algorithm == "gzip":
        return gzip.decompress(data)
    elif algorithm == "lzma":
        return lzma.decompress(data)
    elif algorithm == "bz2":
        return bz2.decompress(data)
    else:
        raise ValueError(f"Unsupported compression algorithm: {algorithm}")


def _calculate_metrics_batch(data_sets: List[List[float]]) -> List[Dict[str, float]]:
    """Calculate statistical metrics for multiple datasets"""
    results = []
    for data in data_sets:
        if not data:
            results.append({})
            continue

        metrics = {
            "mean": statistics.mean(data),
            "median": statistics.median(data),
            "stdev": statistics.stdev(data) if len(data) > 1 else 0,
            "min": min(data),
            "max": max(data),
            "sum": sum(data),
            "count": len(data),
        }

        # Calculate percentiles
        sorted_data = sorted(data)
        n = len(sorted_data)
        metrics["p25"] = sorted_data[n // 4] if n > 0 else 0
        metrics["p75"] = sorted_data[3 * n // 4] if n > 0 else 0
        metrics["p95"] = sorted_data[int(0.95 * n)] if n > 0 else 0
        metrics["p99"] = sorted_data[int(0.99 * n)] if n > 0 else 0

        results.append(metrics)

    return results


def _compute_hashes(data: bytes) -> Dict[str, str]:
    """Compute multiple hash values for data integrity"""
    return {
        "md5": hashlib.md5(data).hexdigest(),
        "sha1": hashlib.sha1(data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "sha512": hashlib.sha512(data).hexdigest(),
    }


def _process_file_batch(file_paths: List[str], operation: str) -> List[Dict]:
    """Process multiple files with specified operation"""
    results = []

    for file_path in file_paths:
        try:
            path = Path(file_path)

            if operation == "checksum":
                with open(path, "rb") as f:
                    data = f.read()
                    hashes = _compute_hashes(data)
                    results.append(
                        {"file": file_path, "size": len(data), "hashes": hashes}
                    )

            elif operation == "compress":
                with open(path, "rb") as f:
                    data = f.read()
                    compressed, size = _compress_data(data, "gzip")

                    # Save compressed file
                    compressed_path = path.with_suffix(path.suffix + ".gz")
                    with open(compressed_path, "wb") as cf:
                        cf.write(compressed)

                    results.append(
                        {
                            "file": file_path,
                            "original_size": len(data),
                            "compressed_size": size,
                            "ratio": size / len(data) if data else 0,
                            "compressed_file": str(compressed_path),
                        }
                    )

            elif operation == "analyze":
                with open(path, "rb") as f:
                    data = f.read()

                results.append(
                    {
                        "file": file_path,
                        "size": len(data),
                        "lines": data.count(b"\n") if data else 0,
                        "is_text": all(b < 128 for b in data[:1000]) if data else False,
                    }
                )

        except Exception as e:
            results.append({"file": file_path, "error": str(e)})

    return results


@dataclass
class ProcessPoolConfig:
    """Configuration for ProcessPoolExecutor"""

    max_workers: Optional[int] = None  # None = cpu_count()
    chunk_size: int = 100  # Items per batch
    timeout: float = 30.0  # Seconds per task
    initializer: Optional[Callable] = None
    initargs: Tuple = ()


class AsyncProcessPool:
    """Async wrapper for ProcessPoolExecutor with batching support"""

    def __init__(self, config: Optional[ProcessPoolConfig] = None):
        self.config = config or ProcessPoolConfig()
        self.executor: Optional[ProcessPoolExecutor] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._shutdown = False

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()

    async def start(self):
        """Initialize the process pool"""
        if self.executor is None:
            self.loop = asyncio.get_event_loop()

            # Determine worker count
            max_workers = self.config.max_workers
            if max_workers is None:
                max_workers = min(os.cpu_count() or 4, 8)  # Cap at 8 workers

            self.executor = ProcessPoolExecutor(
                max_workers=max_workers,
                initializer=self.config.initializer,
                initargs=self.config.initargs,
            )

            logger.info(f"Started process pool with {max_workers} workers")

    async def shutdown(self, wait: bool = True):
        """Shutdown the process pool"""
        if self.executor and not self._shutdown:
            self._shutdown = True
            self.executor.shutdown(wait=wait)
            logger.info("Process pool shutdown complete")

    async def parse_json_batch(self, json_strings: List[str]) -> List[Dict]:
        """Parse multiple JSON strings using multiprocessing"""
        if not json_strings:
            return []

        # Split into chunks for parallel processing
        chunks = [
            json_strings[i : i + self.config.chunk_size]
            for i in range(0, len(json_strings), self.config.chunk_size)
        ]

        # Process chunks in parallel
        futures = []
        for chunk in chunks:
            future = self.loop.run_in_executor(self.executor, _parse_json_batch, chunk)
            futures.append(future)

        # Gather results
        results = []
        for future in asyncio.as_completed(futures):
            chunk_results = await future
            results.extend(chunk_results)

        return results

    async def compress_files(
        self,
        file_paths: List[Union[str, Path]],
        algorithm: str = "gzip",
        level: int = 6,
    ) -> List[Dict]:
        """Compress multiple files using multiprocessing"""
        if not file_paths:
            return []

        # Convert paths to strings
        paths = [str(p) for p in file_paths]

        # Split into chunks
        chunks = [
            paths[i : i + self.config.chunk_size]
            for i in range(0, len(paths), self.config.chunk_size)
        ]

        # Process in parallel
        futures = []
        for chunk in chunks:
            future = self.loop.run_in_executor(
                self.executor, _process_file_batch, chunk, "compress"
            )
            futures.append(future)

        # Gather results
        results = []
        for future in asyncio.as_completed(futures):
            chunk_results = await future
            results.extend(chunk_results)

        return results

    async def calculate_metrics(
        self, data_sets: List[List[float]]
    ) -> List[Dict[str, float]]:
        """Calculate metrics for multiple datasets using multiprocessing"""
        if not data_sets:
            return []

        # Split into chunks
        chunks = [
            data_sets[i : i + self.config.chunk_size]
            for i in range(0, len(data_sets), self.config.chunk_size)
        ]

        # Process in parallel
        futures = []
        for chunk in chunks:
            future = self.loop.run_in_executor(
                self.executor, _calculate_metrics_batch, chunk
            )
            futures.append(future)

        # Gather results
        results = []
        for future in asyncio.as_completed(futures):
            chunk_results = await future
            results.extend(chunk_results)

        return results

    async def compute_checksums(self, file_paths: List[Union[str, Path]]) -> List[Dict]:
        """Compute checksums for multiple files"""
        if not file_paths:
            return []

        # Convert paths to strings
        paths = [str(p) for p in file_paths]

        # Split into chunks
        chunks = [
            paths[i : i + self.config.chunk_size]
            for i in range(0, len(paths), self.config.chunk_size)
        ]

        # Process in parallel
        futures = []
        for chunk in chunks:
            future = self.loop.run_in_executor(
                self.executor, _process_file_batch, chunk, "checksum"
            )
            futures.append(future)

        # Gather results
        results = []
        for future in asyncio.as_completed(futures):
            chunk_results = await future
            results.extend(chunk_results)

        return results

    async def run_cpu_intensive(self, func: Callable, *args, **kwargs) -> Any:
        """Run any CPU-intensive function in process pool"""
        if not self.executor:
            await self.start()

        return await self.loop.run_in_executor(
            self.executor, partial(func, **kwargs), *args
        )


# Singleton instance for shared use
_global_pool: Optional[AsyncProcessPool] = None


async def get_process_pool() -> AsyncProcessPool:
    """Get or create global process pool"""
    global _global_pool
    if _global_pool is None:
        _global_pool = AsyncProcessPool()
        await _global_pool.start()
    return _global_pool


async def shutdown_global_pool():
    """Shutdown global process pool"""
    global _global_pool
    if _global_pool:
        await _global_pool.shutdown()
        _global_pool = None
