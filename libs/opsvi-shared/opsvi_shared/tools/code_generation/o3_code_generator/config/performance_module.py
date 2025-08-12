"""
performance_manager.py

Module PerformanceManager provides performance optimizations for the O3 code generator,
including response caching, parallel request handling, streaming support, and performance monitoring.
"""

from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock
import time

from src.tools.code_generation.o3_code_generator.utils.logger import O3Logger


class PerformanceManager:
    """
    Manages performance optimizations for O3 code generator:
    - In-memory response caching
    - Parallel request processing
    - Streaming support
    - Detailed performance metrics

    Attributes:
        max_workers (int): maximum number of worker threads in the pool
        cache_maxsize (int): maximum number of entries in the cache
        _executor (ThreadPoolExecutor): thread pool executor for concurrent tasks
        _cache (dict): thread-safe in-memory cache mapping keys to responses
        _cache_lock (Lock): lock for synchronizing cache access
        _metrics (dict): performance metrics (requests, hits, misses, total_latency)
        _metrics_lock (Lock): lock for synchronizing metrics updates
        logger: O3Logger instance for logging
    """

    __all__ = ["PerformanceManager"]

    def __init__(self, max_workers: int = 10, cache_maxsize: int = 128):
        """
        Initialize PerformanceManager.

        Args:
            max_workers (int): Maximum threads for concurrent execution (default: 10)
            cache_maxsize (int): Maximum cached responses (default: 128)
        """
        # Initialize logger
        logger_instance = O3Logger()
        self.logger = logger_instance.get_logger()

        # Thread pool for concurrent processing
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)

        # Simple in-memory cache with manual eviction policy (LRU approximated)
        self.cache_maxsize = cache_maxsize
        self._cache = {}
        self._cache_usage = []  # list of keys, most recent at end
        self._cache_lock = Lock()

        # Performance metrics
        self._metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_latency": 0.0,  # in seconds
        }
        self._metrics_lock = Lock()

        self.logger.log_info(
            "PerformanceManager initialized with %d workers and cache size %d",
            self.max_workers,
            self.cache_maxsize,
        )

    def _update_metrics(self, latency: float, cache_hit: bool):
        """
        Update performance metrics in a thread-safe manner.
        """
        with self._metrics_lock:
            self._metrics["total_requests"] += 1
            if cache_hit:
                self._metrics["cache_hits"] += 1
            else:
                self._metrics["cache_misses"] += 1
                self._metrics["total_latency"] += latency

    def _evict_if_needed(self):
        """
        Evict oldest cache entry if cache exceeds max size.
        """
        with self._cache_lock:
            while len(self._cache_usage) > self.cache_maxsize:
                old_key = self._cache_usage.pop(0)
                del self._cache[old_key]
                self.logger.log_debug("Evicted cache entry for key %s", old_key)

    def _make_key(self, input_data) -> str:
        """
        Create a unique key for the input data for caching purposes.
        """
        try:
            return str(hash(repr(input_data)))
        except Exception:
            return str(time.time())

    def clear_cache(self):
        """
        Clear the entire response cache.
        """
        with self._cache_lock:
            self._cache.clear()
            self._cache_usage.clear()
        self.logger.log_info("Cache cleared")

    def get_metrics(self) -> dict:
        """
        Retrieve a snapshot of current performance metrics, including average latency.

        Returns:
            dict: metrics with fields total_requests, cache_hits, cache_misses, average_latency
        """
        with self._metrics_lock:
            total = self._metrics["total_requests"]
            misses = self._metrics["cache_misses"]
            avg_latency = (
                (self._metrics["total_latency"] / misses) if misses > 0 else 0.0
            )
            metrics_snapshot = {
                "total_requests": total,
                "cache_hits": self._metrics["cache_hits"],
                "cache_misses": misses,
                "average_latency": avg_latency,
            }
        return metrics_snapshot

    def submit(
        self, input_data, generator_fn, callback=None, stream: bool = False
    ) -> Future:
        """
        Submit a code generation job for concurrent execution.

        Args:
            input_data: The input to pass into the generator function.
            generator_fn (callable): Function that generates response. If stream=True,
                                     it must return an iterator of chunks.
            callback (callable, optional): Function to call with the future when done.
            stream (bool): Whether to use streaming mode.

        Returns:
            concurrent.futures.Future: Future representing the pending result.
        """
        future = self._executor.submit(self._execute, input_data, generator_fn, stream)
        if callback:
            future.add_done_callback(callback)
        return future

    def _execute(self, input_data, generator_fn, stream: bool):
        """
        Internal method to handle execution, caching, streaming, and metrics.
        """
        key = self._make_key(input_data)
        # Check cache
        with self._cache_lock:
            if key in self._cache:
                cached = self._cache[key]
                # Move key to end to mark recent use
                try:
                    self._cache_usage.remove(key)
                except ValueError:
                    pass
                self._cache_usage.append(key)
                self.logger.log_info("Cache hit for key %s", key)
                self._update_metrics(latency=0.0, cache_hit=True)
                if stream:
                    # Yield entire cached response
                    for chunk in [cached]:
                        yield chunk
                    return
                else:
                    return cached
        # Cache miss
        self.logger.log_info("Cache miss for key %s", key)
        start = time.time()
        try:
            if stream:
                collected = []
                for chunk in generator_fn(input_data):
                    yield chunk
                    collected.append(chunk)
                result = "".join(collected)
            else:
                result = generator_fn(input_data)
        except Exception as ex:
            self.logger.log_error("Error during execution for key %s: %s", key, ex)
            raise
        finally:
            end = time.time()
            latency = end - start
            self._update_metrics(latency=latency, cache_hit=False)

        # Store in cache
        with self._cache_lock:
            self._cache[key] = result
            self._cache_usage.append(key)
            self._evict_if_needed()
            self.logger.log_debug("Cached response for key %s", key)

        if stream:
            # If stream mode, the generator has already yielded; end of method
            return
        else:
            return result
