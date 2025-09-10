"""High-performance parallel embedding generation service for production-scale chat import."""

import asyncio
import hashlib
import json
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class EmbeddingRequest:
    """Represents a single embedding generation request."""

    text: str
    request_id: str
    priority: int = 0  # Higher priority processed first
    created_at: float = 0.0

    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""

    request_id: str
    embedding: Optional[List[float]]
    error: Optional[str]
    processing_time_ms: float
    cache_hit: bool = False


class LRUCache:
    """Thread-safe LRU cache for embeddings."""

    def __init__(self, maxsize: int = 10000):
        self.maxsize = maxsize
        self.cache = OrderedDict()
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[List[float]]:
        """Get embedding from cache."""
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                self.hits += 1
                return value
            else:
                self.misses += 1
                return None

    def put(self, key: str, value: List[float]) -> None:
        """Put embedding in cache."""
        with self.lock:
            if key in self.cache:
                # Update existing entry
                self.cache.pop(key)
            elif len(self.cache) >= self.maxsize:
                # Remove oldest entry
                self.cache.popitem(last=False)

            self.cache[key] = value

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests) if total_requests > 0 else 0.0

            return {
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "size": len(self.cache),
                "maxsize": self.maxsize,
            }

    def clear(self) -> None:
        """Clear the cache."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0


class EmbeddingServiceMetrics:
    """Performance metrics for embedding service."""

    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.cache_hits = 0
        self.total_processing_time = 0.0
        self.active_requests = 0
        self.queue_size_samples = []
        self.throughput_samples = []
        self.last_metric_time = time.time()
        self.lock = threading.RLock()

    def record_request(
        self, processing_time_ms: float, success: bool, cache_hit: bool = False
    ):
        """Record request completion metrics."""
        with self.lock:
            self.total_requests += 1
            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1

            if cache_hit:
                self.cache_hits += 1

            self.total_processing_time += processing_time_ms

    def record_queue_size(self, size: int):
        """Record queue size sample."""
        with self.lock:
            self.queue_size_samples.append(size)
            # Keep only recent samples
            if len(self.queue_size_samples) > 1000:
                self.queue_size_samples = self.queue_size_samples[-1000:]

    def record_throughput(self, requests_per_second: float):
        """Record throughput sample."""
        with self.lock:
            self.throughput_samples.append(requests_per_second)
            if len(self.throughput_samples) > 100:
                self.throughput_samples = self.throughput_samples[-100:]

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        with self.lock:
            avg_processing_time = (
                self.total_processing_time / self.successful_requests
                if self.successful_requests > 0
                else 0.0
            )

            success_rate = (
                self.successful_requests / self.total_requests
                if self.total_requests > 0
                else 0.0
            )

            cache_hit_rate = (
                self.cache_hits / self.total_requests
                if self.total_requests > 0
                else 0.0
            )

            avg_queue_size = (
                sum(self.queue_size_samples) / len(self.queue_size_samples)
                if self.queue_size_samples
                else 0.0
            )

            avg_throughput = (
                sum(self.throughput_samples) / len(self.throughput_samples)
                if self.throughput_samples
                else 0.0
            )

            return {
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "success_rate": success_rate,
                "cache_hit_rate": cache_hit_rate,
                "average_processing_time_ms": avg_processing_time,
                "average_queue_size": avg_queue_size,
                "average_throughput_rps": avg_throughput,
                "active_requests": self.active_requests,
            }


class ProductionEmbeddingService:
    """High-performance, production-ready embedding generation service."""

    def __init__(
        self,
        # Core configuration
        max_concurrent_requests: int = 50,
        max_queue_size: int = 10000,
        request_timeout_seconds: float = 30.0,
        # Service configuration
        service_type: str = "sentence_transformers",  # openai, sentence_transformers, hybrid
        model_name: str = "all-MiniLM-L6-v2",
        api_key: Optional[str] = None,
        api_endpoint: Optional[str] = None,
        # Performance tuning
        enable_caching: bool = True,
        cache_size: int = 50000,
        enable_batching: bool = True,
        batch_size: int = 32,
        batch_timeout_ms: float = 100.0,
        # Threading
        thread_pool_size: int = 10,
        enable_gpu: bool = True,
        # Quality and reliability
        enable_fallback: bool = True,
        fallback_service: str = "simple",
        max_retries: int = 3,
        retry_delay_ms: float = 500.0,
    ):
        self.max_concurrent_requests = max_concurrent_requests
        self.max_queue_size = max_queue_size
        self.request_timeout_seconds = request_timeout_seconds

        self.service_type = service_type
        self.model_name = model_name
        self.api_key = api_key
        self.api_endpoint = api_endpoint

        self.enable_caching = enable_caching
        self.enable_batching = enable_batching
        self.batch_size = batch_size
        self.batch_timeout_ms = batch_timeout_ms

        self.thread_pool_size = thread_pool_size
        self.enable_gpu = enable_gpu

        self.enable_fallback = enable_fallback
        self.fallback_service = fallback_service
        self.max_retries = max_retries
        self.retry_delay_ms = retry_delay_ms

        # Initialize components
        self.cache = LRUCache(cache_size) if enable_caching else None
        self.metrics = EmbeddingServiceMetrics()
        self.logger = logger.bind(component="parallel_embedding_service")

        # Request management
        self._request_queue: asyncio.Queue = None
        self._result_futures: Dict[str, asyncio.Future] = {}
        self._semaphore: asyncio.Semaphore = None
        self._thread_pool: ThreadPoolExecutor = None

        # Background tasks
        self._processor_task: Optional[asyncio.Task] = None
        self._batch_processor_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        self._running = False

        # Model instances (initialized lazily)
        self._embedding_models: Dict[str, Any] = {}
        self._model_lock = threading.RLock()

    async def initialize(self) -> None:
        """Initialize the embedding service."""
        try:
            self.logger.info(
                "Initializing parallel embedding service",
                service_type=self.service_type,
                max_concurrent=self.max_concurrent_requests,
                cache_enabled=self.enable_caching,
                batching_enabled=self.enable_batching,
            )

            # Initialize async components
            self._request_queue = asyncio.Queue(maxsize=self.max_queue_size)
            self._semaphore = asyncio.Semaphore(self.max_concurrent_requests)
            self._thread_pool = ThreadPoolExecutor(
                max_workers=self.thread_pool_size, thread_name_prefix="embedding_worker"
            )

            # Initialize models based on service type
            await self._initialize_models()

            # Start background tasks
            self._running = True
            self._processor_task = asyncio.create_task(self._request_processor_loop())

            if self.enable_batching:
                self._batch_processor_task = asyncio.create_task(
                    self._batch_processor_loop()
                )

            self._metrics_task = asyncio.create_task(self._metrics_collector_loop())

            self.logger.info("Parallel embedding service initialized successfully")

        except Exception as e:
            self.logger.error("Failed to initialize embedding service", error=str(e))
            raise

    async def _initialize_models(self) -> None:
        """Initialize embedding models based on configuration."""
        try:
            if self.service_type in ["sentence_transformers", "hybrid"]:
                await self._initialize_sentence_transformers()

            if self.service_type in ["openai", "hybrid"]:
                await self._initialize_openai_client()

            self.logger.info(
                "Embedding models initialized",
                service_type=self.service_type,
                models=list(self._embedding_models.keys()),
            )

        except Exception as e:
            self.logger.warning("Model initialization failed", error=str(e))
            if not self.enable_fallback:
                raise

    async def _initialize_sentence_transformers(self) -> None:
        """Initialize sentence-transformers model."""
        try:

            def load_model():
                import torch
                from sentence_transformers import SentenceTransformer

                # Configure device
                device = (
                    "cuda" if self.enable_gpu and torch.cuda.is_available() else "cpu"
                )

                model = SentenceTransformer(
                    self.model_name,
                    device=device,
                    cache_folder=None,  # Use default cache
                )

                # Optimize for production
                model.eval()
                if device == "cuda":
                    model.half()  # Use half precision for speed

                return model, device

            # Load model in thread pool to avoid blocking
            model, device = await asyncio.get_event_loop().run_in_executor(
                self._thread_pool, load_model
            )

            self._embedding_models["sentence_transformers"] = {
                "model": model,
                "device": device,
            }

            self.logger.info(
                "SentenceTransformers model loaded",
                model_name=self.model_name,
                device=device,
            )

        except ImportError:
            self.logger.warning("sentence-transformers not available")
            if not self.enable_fallback:
                raise
        except Exception as e:
            self.logger.error(
                "Failed to load sentence-transformers model", error=str(e)
            )
            if not self.enable_fallback:
                raise

    async def _initialize_openai_client(self) -> None:
        """Initialize OpenAI client."""
        try:
            if not self.api_key:
                raise ValueError("OpenAI API key required")

            import openai

            client = openai.AsyncOpenAI(
                api_key=self.api_key, base_url=self.api_endpoint
            )

            self._embedding_models["openai"] = {
                "client": client,
                "model": self.model_name or "text-embedding-3-small",
            }

            self.logger.info("OpenAI client initialized")

        except ImportError:
            self.logger.warning("OpenAI client not available")
            if not self.enable_fallback:
                raise
        except Exception as e:
            self.logger.error("Failed to initialize OpenAI client", error=str(e))
            if not self.enable_fallback:
                raise

    async def generate_embedding(
        self, text: str, priority: int = 0, timeout: Optional[float] = None
    ) -> Optional[List[float]]:
        """Generate embedding for a single text with high performance."""
        if not text or not text.strip():
            return None

        # Create request
        request_id = hashlib.md5(text.encode()).hexdigest()
        request = EmbeddingRequest(text=text, request_id=request_id, priority=priority)

        # Check cache first
        if self.cache:
            cached_embedding = self.cache.get(request_id)
            if cached_embedding:
                self.metrics.record_request(0.0, True, cache_hit=True)
                return cached_embedding

        # Submit request
        try:
            result = await self._submit_request(
                request, timeout or self.request_timeout_seconds
            )
            return result.embedding

        except Exception as e:
            self.logger.error(
                "Embedding generation failed", text_length=len(text), error=str(e)
            )
            return None

    async def generate_embeddings_batch(
        self, texts: List[str], priority: int = 0, timeout: Optional[float] = None
    ) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts with optimal batching."""
        if not texts:
            return []

        # Create requests
        requests = []
        cached_results = []

        for i, text in enumerate(texts):
            if not text or not text.strip():
                cached_results.append((i, None))
                continue

            request_id = hashlib.md5(text.encode()).hexdigest()

            # Check cache first
            if self.cache:
                cached_embedding = self.cache.get(request_id)
                if cached_embedding:
                    cached_results.append((i, cached_embedding))
                    self.metrics.record_request(0.0, True, cache_hit=True)
                    continue

            request = EmbeddingRequest(
                text=text,
                request_id=f"{request_id}_{i}",  # Unique ID for batch
                priority=priority,
            )
            requests.append((i, request))

        # Submit non-cached requests
        results = [None] * len(texts)

        # Fill cached results
        for idx, embedding in cached_results:
            results[idx] = embedding

        # Process remaining requests
        if requests:
            try:
                # Submit all requests concurrently
                tasks = []
                for idx, request in requests:
                    task = asyncio.create_task(
                        self._submit_request(
                            request, timeout or self.request_timeout_seconds
                        )
                    )
                    tasks.append((idx, task))

                # Wait for all requests
                for idx, task in tasks:
                    try:
                        result = await task
                        results[idx] = result.embedding
                    except Exception as e:
                        self.logger.warning(
                            "Batch request failed", index=idx, error=str(e)
                        )
                        results[idx] = None

            except Exception as e:
                self.logger.error("Batch embedding generation failed", error=str(e))

        return results

    async def _submit_request(
        self, request: EmbeddingRequest, timeout: float
    ) -> EmbeddingResult:
        """Submit a request and wait for result."""
        # Create future for result
        future = asyncio.Future()
        self._result_futures[request.request_id] = future

        try:
            # Add to queue
            await asyncio.wait_for(self._request_queue.put(request), timeout=timeout)

            # Wait for result
            result = await asyncio.wait_for(future, timeout=timeout)
            return result

        except asyncio.TimeoutError:
            self.logger.warning(
                "Request timeout", request_id=request.request_id, timeout=timeout
            )
            raise
        finally:
            # Clean up future
            if request.request_id in self._result_futures:
                del self._result_futures[request.request_id]

    async def _request_processor_loop(self) -> None:
        """Main request processing loop."""
        while self._running:
            try:
                # Get request from queue
                try:
                    request = await asyncio.wait_for(
                        self._request_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Process request with semaphore for concurrency control
                async with self._semaphore:
                    self.metrics.active_requests += 1
                    try:
                        await self._process_single_request(request)
                    finally:
                        self.metrics.active_requests -= 1

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Request processor error", error=str(e))
                await asyncio.sleep(1.0)

    async def _process_single_request(self, request: EmbeddingRequest) -> None:
        """Process a single embedding request."""
        start_time = time.time()

        try:
            # Generate embedding using best available service
            embedding = await self._generate_embedding_with_fallback(request.text)

            processing_time_ms = (time.time() - start_time) * 1000

            # Cache result
            if embedding and self.cache:
                cache_key = hashlib.md5(request.text.encode()).hexdigest()
                self.cache.put(cache_key, embedding)

            # Create result
            result = EmbeddingResult(
                request_id=request.request_id,
                embedding=embedding,
                error=None,
                processing_time_ms=processing_time_ms,
            )

            # Record metrics
            self.metrics.record_request(processing_time_ms, embedding is not None)

        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000

            result = EmbeddingResult(
                request_id=request.request_id,
                embedding=None,
                error=str(e),
                processing_time_ms=processing_time_ms,
            )

            self.metrics.record_request(processing_time_ms, False)

        # Deliver result
        if request.request_id in self._result_futures:
            future = self._result_futures[request.request_id]
            if not future.done():
                future.set_result(result)

    async def _generate_embedding_with_fallback(
        self, text: str
    ) -> Optional[List[float]]:
        """Generate embedding with fallback support."""
        # Try primary service
        try:
            if self.service_type == "openai" and "openai" in self._embedding_models:
                return await self._generate_openai_embedding(text)
            elif (
                self.service_type == "sentence_transformers"
                and "sentence_transformers" in self._embedding_models
            ):
                return await self._generate_sentence_transformers_embedding(text)
            elif self.service_type == "hybrid":
                # Try sentence-transformers first, then OpenAI
                if "sentence_transformers" in self._embedding_models:
                    return await self._generate_sentence_transformers_embedding(text)
                elif "openai" in self._embedding_models:
                    return await self._generate_openai_embedding(text)

        except Exception as e:
            self.logger.warning(
                "Primary embedding service failed",
                service_type=self.service_type,
                error=str(e),
            )

        # Try fallback if enabled
        if self.enable_fallback:
            try:
                if self.fallback_service == "simple":
                    return self._generate_simple_embedding(text)
                elif self.fallback_service in self._embedding_models:
                    # Try other available services
                    for service_name in self._embedding_models:
                        if service_name != self.service_type:
                            try:
                                if service_name == "openai":
                                    return await self._generate_openai_embedding(text)
                                elif service_name == "sentence_transformers":
                                    return await self._generate_sentence_transformers_embedding(
                                        text
                                    )
                            except:
                                continue

            except Exception as e:
                self.logger.warning("Fallback embedding service failed", error=str(e))

        return None

    async def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API."""
        openai_config = self._embedding_models["openai"]
        client = openai_config["client"]
        model = openai_config["model"]

        # Truncate text if too long
        if len(text) > 8000:  # Conservative limit
            text = text[:8000]

        response = await client.embeddings.create(input=text, model=model)

        return response.data[0].embedding

    async def _generate_sentence_transformers_embedding(self, text: str) -> List[float]:
        """Generate embedding using SentenceTransformers."""
        model_config = self._embedding_models["sentence_transformers"]
        model = model_config["model"]

        def encode_text():
            with self._model_lock:
                embedding = model.encode(text, convert_to_tensor=False)
                return embedding.tolist()

        # Run in thread pool to avoid blocking
        embedding = await asyncio.get_event_loop().run_in_executor(
            self._thread_pool, encode_text
        )

        return embedding

    def _generate_simple_embedding(
        self, text: str, dimensions: int = 384
    ) -> List[float]:
        """Generate simple hash-based embedding as fallback."""
        embeddings = []
        for i in range(dimensions // 32 + 1):
            hash_input = f"{text}_{i}"
            hash_bytes = hashlib.sha256(hash_input.encode()).digest()

            for j in range(0, len(hash_bytes), 4):
                if len(embeddings) >= dimensions:
                    break
                value = int.from_bytes(hash_bytes[j : j + 4], "big") / (2**31)
                embeddings.append(max(-1.0, min(1.0, value - 1.0)))

        return embeddings[:dimensions]

    async def _batch_processor_loop(self) -> None:
        """Process requests in batches for efficiency (future enhancement)."""
        # This could implement more sophisticated batching logic
        # For now, individual processing is sufficient
        while self._running:
            await asyncio.sleep(1.0)

    async def _metrics_collector_loop(self) -> None:
        """Collect performance metrics periodically."""
        while self._running:
            try:
                # Record queue size
                queue_size = self._request_queue.qsize() if self._request_queue else 0
                self.metrics.record_queue_size(queue_size)

                # Calculate and record throughput
                current_time = time.time()
                time_delta = current_time - self.metrics.last_metric_time
                if time_delta >= 10.0:  # Every 10 seconds
                    if hasattr(self.metrics, "_last_request_count"):
                        request_delta = (
                            self.metrics.total_requests
                            - self.metrics._last_request_count
                        )
                        throughput = request_delta / time_delta
                        self.metrics.record_throughput(throughput)

                    self.metrics._last_request_count = self.metrics.total_requests
                    self.metrics.last_metric_time = current_time

                await asyncio.sleep(5.0)  # Collect every 5 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Metrics collection error", error=str(e))
                await asyncio.sleep(5.0)

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        metrics = self.metrics.get_stats()

        if self.cache:
            metrics["cache"] = self.cache.get_stats()

        metrics["configuration"] = {
            "service_type": self.service_type,
            "max_concurrent_requests": self.max_concurrent_requests,
            "max_queue_size": self.max_queue_size,
            "enable_caching": self.enable_caching,
            "enable_batching": self.enable_batching,
            "thread_pool_size": self.thread_pool_size,
        }

        metrics["queue"] = {
            "size": self._request_queue.qsize() if self._request_queue else 0,
            "max_size": self.max_queue_size,
        }

        metrics["models"] = {
            "available_services": list(self._embedding_models.keys()),
            "primary_service": self.service_type,
            "fallback_enabled": self.enable_fallback,
        }

        return metrics

    async def health_check(self) -> Dict[str, Any]:
        """Perform service health check."""
        try:
            start_time = time.time()

            # Test embedding generation with small text
            test_embedding = await self.generate_embedding(
                "test", priority=999, timeout=5.0
            )

            response_time_ms = (time.time() - start_time) * 1000

            return {
                "status": "healthy" if test_embedding else "degraded",
                "response_time_ms": response_time_ms,
                "test_embedding_generated": test_embedding is not None,
                "queue_size": self._request_queue.qsize() if self._request_queue else 0,
                "active_requests": self.metrics.active_requests,
                "available_models": list(self._embedding_models.keys()),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "queue_size": self._request_queue.qsize() if self._request_queue else 0,
                "active_requests": self.metrics.active_requests,
            }

    async def shutdown(self) -> None:
        """Shutdown the embedding service gracefully."""
        self.logger.info("Shutting down parallel embedding service")

        self._running = False

        # Cancel background tasks
        for task in [
            self._processor_task,
            self._batch_processor_task,
            self._metrics_task,
        ]:
            if task and not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=5.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass

        # Shutdown thread pool
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True, timeout=10.0)

        # Clear resources
        self._embedding_models.clear()
        if self.cache:
            self.cache.clear()

        # Cancel remaining futures
        for future in self._result_futures.values():
            if not future.done():
                future.cancel()
        self._result_futures.clear()

        self.logger.info(
            "Parallel embedding service shutdown completed",
            total_requests_processed=self.metrics.total_requests,
            success_rate=self.metrics.successful_requests / self.metrics.total_requests
            if self.metrics.total_requests > 0
            else 0,
        )
