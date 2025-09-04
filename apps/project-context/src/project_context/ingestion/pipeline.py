"""Main ingestion pipeline coordinator."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

import structlog

from ..models.common import (
    BatchProcessingResult,
    ContextItem,
    ContextRelationship,
    PipelineStatus,
)
from .base_adapter import AdapterStatus, BaseAdapter, BatchMode, CircuitBreakerOpenError
from .database import DatabaseConnectionPool, IngestionDatabase
from .registry import AdapterRegistry
from .transformers import DataTransformer

logger = structlog.get_logger(__name__)


class PipelineConfig:
    """Configuration for the ingestion pipeline."""

    def __init__(
        self,
        # Core configuration
        max_concurrent_adapters: int = 10,
        batch_commit_size: int = 1000,
        health_check_interval: int = 60,
        metrics_collection_interval: int = 30,
        auto_restart_failed_adapters: bool = True,
        adapter_failure_backoff_seconds: int = 300,
        pipeline_shutdown_timeout_seconds: int = 60,
        # Database configuration
        database_url: str = "postgresql://opsvi@localhost:5432/unified_context",
        database_pool_min: int = 5,
        database_pool_max: int = 20,
        database_command_timeout: int = 60,
        # Retry configuration
        max_retry_attempts: int = 3,
        retry_base_delay: float = 1.0,
        retry_max_delay: float = 60.0,
        retry_exponential_base: float = 2.0,
        # Relationship detection
        enable_relationship_detection: bool = True,
        relationship_context_window_size: int = 100,
        relationship_batch_size: int = 50,
        # Performance tuning
        enable_memory_monitoring: bool = True,
        max_pipeline_memory_mb: int = 2048,
        gc_interval_seconds: int = 300,
        # Quality assurance
        enable_duplicate_detection: bool = True,
        enable_content_validation: bool = True,
        min_content_length: int = 1,
        max_content_length: int = 1000000,
    ):
        # Core settings
        self.max_concurrent_adapters = max_concurrent_adapters
        self.batch_commit_size = batch_commit_size
        self.health_check_interval = health_check_interval
        self.metrics_collection_interval = metrics_collection_interval
        self.auto_restart_failed_adapters = auto_restart_failed_adapters
        self.adapter_failure_backoff_seconds = adapter_failure_backoff_seconds
        self.pipeline_shutdown_timeout_seconds = pipeline_shutdown_timeout_seconds

        # Database settings
        self.database_url = database_url
        self.database_pool_min = database_pool_min
        self.database_pool_max = database_pool_max
        self.database_command_timeout = database_command_timeout

        # Retry settings
        self.max_retry_attempts = max_retry_attempts
        self.retry_base_delay = retry_base_delay
        self.retry_max_delay = retry_max_delay
        self.retry_exponential_base = retry_exponential_base

        # Relationship detection
        self.enable_relationship_detection = enable_relationship_detection
        self.relationship_context_window_size = relationship_context_window_size
        self.relationship_batch_size = relationship_batch_size

        # Performance settings
        self.enable_memory_monitoring = enable_memory_monitoring
        self.max_pipeline_memory_mb = max_pipeline_memory_mb
        self.gc_interval_seconds = gc_interval_seconds

        # Quality settings
        self.enable_duplicate_detection = enable_duplicate_detection
        self.enable_content_validation = enable_content_validation
        self.min_content_length = min_content_length
        self.max_content_length = max_content_length


class PipelineMetrics:
    """Pipeline-wide metrics."""

    def __init__(self):
        self.total_items_ingested = 0
        self.total_items_failed = 0
        self.total_batches_processed = 0
        self.adapters_running = 0
        self.adapters_failed = 0
        self.average_pipeline_throughput = 0.0
        self.peak_pipeline_throughput = 0.0
        self.total_processing_time_seconds = 0.0
        self.pipeline_uptime_seconds = 0.0
        self.last_activity = datetime.utcnow()


class IngestionPipeline:
    """Main coordinator for the ingestion pipeline.

    Manages multiple adapters, coordinates batch processing, handles failures,
    and provides monitoring capabilities.
    """

    def __init__(
        self,
        registry: AdapterRegistry,
        transformer: DataTransformer,
        config: Optional[PipelineConfig] = None,
    ):
        """Initialize pipeline.

        Args:
            registry: Adapter registry for plugin management
            transformer: Data transformation utilities
            config: Pipeline configuration
        """
        self.registry = registry
        self.transformer = transformer
        self.config = config or PipelineConfig()
        self.metrics = PipelineMetrics()

        # Database integration
        self.db_pool: Optional[DatabaseConnectionPool] = None
        self.database: Optional[IngestionDatabase] = None

        # Adapter management
        self._active_adapters: Dict[str, BaseAdapter] = {}
        self._adapter_tasks: Dict[str, asyncio.Task] = {}
        self._failed_adapters: Dict[str, datetime] = {}

        # Pipeline state
        self._running = False
        self._start_time: Optional[datetime] = None
        self._shutdown_event = asyncio.Event()

        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        self._gc_task: Optional[asyncio.Task] = None
        self._relationship_detection_task: Optional[asyncio.Task] = None

        # Context window for relationship detection
        self._recent_items: List[ContextItem] = []
        self._recent_items_lock = asyncio.Lock()

        # Retry tracking
        self._retry_queues: Dict[str, List[Tuple[ContextItem, int]]] = {}

        self.logger = logger.bind(component="pipeline")

    async def start(self, adapter_ids: Optional[List[str]] = None) -> None:
        """Start the ingestion pipeline.

        Args:
            adapter_ids: Specific adapters to start, or None for all registered
        """
        self.logger.info("Starting ingestion pipeline")

        if self._running:
            self.logger.warning("Pipeline already running")
            return

        try:
            # Initialize database connection
            await self._initialize_database()

            self._running = True
            self._start_time = datetime.utcnow()
            self._shutdown_event.clear()

            # Clear retry queues
            self._retry_queues.clear()

            # Start background tasks first
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            self._metrics_task = asyncio.create_task(self._metrics_collection_loop())

            if self.config.enable_memory_monitoring:
                self._gc_task = asyncio.create_task(self._garbage_collection_loop())

            if self.config.enable_relationship_detection:
                self._relationship_detection_task = asyncio.create_task(
                    self._relationship_detection_loop()
                )

            # Start specified adapters or all registered adapters
            target_adapters = adapter_ids or list(self.registry.list_adapters())

            startup_tasks = []
            for adapter_id in target_adapters:
                startup_tasks.append(self._start_adapter(adapter_id))

            # Start adapters concurrently
            if startup_tasks:
                startup_results = await asyncio.gather(
                    *startup_tasks, return_exceptions=True
                )

                success_count = 0
                for i, result in enumerate(startup_results):
                    if isinstance(result, Exception):
                        self.logger.error(
                            "Failed to start adapter",
                            adapter_id=target_adapters[i],
                            error=str(result),
                        )
                    elif result:
                        success_count += 1

                self.logger.info(
                    "Pipeline startup completed",
                    successful_adapters=success_count,
                    target_adapters=len(target_adapters),
                    active_adapters=len(self._active_adapters),
                )
            else:
                self.logger.warning("No adapters to start")

        except Exception as e:
            self.logger.error("Failed to start pipeline", error=str(e))
            # Cleanup on failure
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop the ingestion pipeline."""
        self.logger.info("Stopping ingestion pipeline")

        if not self._running:
            self.logger.warning("Pipeline not running")
            return

        self._running = False
        self._shutdown_event.set()

        # Stop all adapters
        stop_tasks = []
        for adapter_id in list(self._active_adapters.keys()):
            stop_tasks.append(self._stop_adapter(adapter_id))

        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)

        # Stop background tasks
        background_tasks = [
            self._health_check_task,
            self._metrics_task,
            self._gc_task,
            self._relationship_detection_task,
        ]

        for task in background_tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=5.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass

        # Close database connection
        if self.db_pool:
            await self.db_pool.close()
            self.db_pool = None
            self.database = None

        self.logger.info("Pipeline stopped")

    async def pause_adapter(self, adapter_id: str) -> bool:
        """Pause a specific adapter.

        Args:
            adapter_id: ID of adapter to pause

        Returns:
            True if paused successfully, False otherwise
        """
        adapter = self._active_adapters.get(adapter_id)
        if not adapter:
            return False

        try:
            await adapter.pause()
            self.logger.info("Adapter paused", adapter_id=adapter_id)
            return True
        except Exception as e:
            self.logger.error(
                "Failed to pause adapter", adapter_id=adapter_id, error=str(e)
            )
            return False

    async def resume_adapter(self, adapter_id: str) -> bool:
        """Resume a paused adapter.

        Args:
            adapter_id: ID of adapter to resume

        Returns:
            True if resumed successfully, False otherwise
        """
        adapter = self._active_adapters.get(adapter_id)
        if not adapter:
            return False

        try:
            await adapter.resume()
            self.logger.info("Adapter resumed", adapter_id=adapter_id)
            return True
        except Exception as e:
            self.logger.error(
                "Failed to resume adapter", adapter_id=adapter_id, error=str(e)
            )
            return False

    async def get_status(self) -> Dict[str, Any]:
        """Get pipeline status and metrics.

        Returns:
            Comprehensive status information
        """
        adapter_status = {}
        for adapter_id, adapter in self._active_adapters.items():
            adapter_status[adapter_id] = await adapter.health_check()

        return {
            "pipeline": {
                "running": self._running,
                "uptime_seconds": self.metrics.pipeline_uptime_seconds,
                "total_items_ingested": self.metrics.total_items_ingested,
                "total_items_failed": self.metrics.total_items_failed,
                "adapters_running": len(self._active_adapters),
                "adapters_failed": len(self._failed_adapters),
                "average_throughput": self.metrics.average_pipeline_throughput,
                "peak_throughput": self.metrics.peak_pipeline_throughput,
            },
            "adapters": adapter_status,
            "failed_adapters": {
                adapter_id: failed_at.isoformat()
                for adapter_id, failed_at in self._failed_adapters.items()
            },
        }

    async def process_batch(
        self,
        adapter_id: str,
        items: List[ContextItem],
        commit_immediately: bool = False,
    ) -> Dict[str, Any]:
        """Process a batch of items.

        Args:
            adapter_id: ID of source adapter
            items: Items to process
            commit_immediately: Whether to commit immediately or batch

        Returns:
            Processing results and metrics
        """
        batch_start = datetime.utcnow()
        results = {"processed": 0, "failed": 0, "skipped": 0, "errors": []}

        processed_items = []

        for item in items:
            try:
                # Apply transformations
                transformed_item = await self.transformer.transform_item(item)

                # Validate
                if not await self._validate_item(transformed_item):
                    results["skipped"] += 1
                    continue

                processed_items.append(transformed_item)
                results["processed"] += 1

            except Exception as e:
                results["failed"] += 1
                results["errors"].append(
                    {"item_id": getattr(item, "source_id", "unknown"), "error": str(e)}
                )

                self.logger.error(
                    "Failed to process item",
                    adapter_id=adapter_id,
                    item_id=getattr(item, "source_id", "unknown"),
                    error=str(e),
                )

        # Store processed items
        storage_result = None
        if processed_items:
            try:
                storage_result = await self._store_items(
                    processed_items, commit_immediately, adapter_id
                )

                # Update results based on storage outcome
                if storage_result.failed_items > 0:
                    results["failed"] += storage_result.failed_items
                    results["errors"].extend(storage_result.errors)

            except Exception as e:
                results["failed"] += len(processed_items)
                results["errors"].append({"error": f"Batch storage failed: {str(e)}"})

        # Update metrics (note: metrics are also updated in _store_items_with_retry)
        batch_duration = (datetime.utcnow() - batch_start).total_seconds()
        if not storage_result:  # Only update if not already updated in storage
            self.metrics.total_items_ingested += results["processed"]
            self.metrics.total_items_failed += results["failed"]
            self.metrics.total_batches_processed += 1
        self.metrics.total_processing_time_seconds += batch_duration

        return results

    # Private methods

    async def _start_adapter(self, adapter_id: str) -> bool:
        """Start a specific adapter.

        Args:
            adapter_id: ID of adapter to start

        Returns:
            True if started successfully, False otherwise
        """
        try:
            # Check if adapter is in failure backoff period
            if adapter_id in self._failed_adapters:
                failure_time = self._failed_adapters[adapter_id]
                backoff_until = failure_time + timedelta(
                    seconds=self.config.adapter_failure_backoff_seconds
                )

                if datetime.utcnow() < backoff_until:
                    self.logger.info(
                        "Adapter still in backoff period",
                        adapter_id=adapter_id,
                        backoff_until=backoff_until,
                    )
                    return False

                # Remove from failed list
                del self._failed_adapters[adapter_id]

            # Get adapter from registry
            adapter = self.registry.get_adapter(adapter_id)
            if not adapter:
                self.logger.error(
                    "Adapter not found in registry", adapter_id=adapter_id
                )
                return False

            # Start adapter
            await adapter.start()

            # Create processing task
            task = asyncio.create_task(
                self._adapter_processing_loop(adapter_id, adapter)
            )

            # Track adapter
            self._active_adapters[adapter_id] = adapter
            self._adapter_tasks[adapter_id] = task

            self.logger.info("Adapter started", adapter_id=adapter_id)
            return True

        except Exception as e:
            self.logger.error(
                "Failed to start adapter", adapter_id=adapter_id, error=str(e)
            )
            self._failed_adapters[adapter_id] = datetime.utcnow()
            return False

    async def _stop_adapter(self, adapter_id: str) -> None:
        """Stop a specific adapter."""
        try:
            # Cancel processing task
            task = self._adapter_tasks.get(adapter_id)
            if task:
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=30)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                del self._adapter_tasks[adapter_id]

            # Stop adapter
            adapter = self._active_adapters.get(adapter_id)
            if adapter:
                await adapter.stop()
                del self._active_adapters[adapter_id]

            self.logger.info("Adapter stopped", adapter_id=adapter_id)

        except Exception as e:
            self.logger.error(
                "Error stopping adapter", adapter_id=adapter_id, error=str(e)
            )

    async def _adapter_processing_loop(
        self, adapter_id: str, adapter: BaseAdapter
    ) -> None:
        """Main processing loop for an adapter."""
        try:
            while self._running and not self._shutdown_event.is_set():
                if adapter.status != AdapterStatus.RUNNING:
                    await asyncio.sleep(1)
                    continue

                try:
                    # Fetch and process items based on batch mode
                    if adapter.config.batch_mode == BatchMode.STREAMING:
                        await self._process_streaming(adapter_id, adapter)
                    else:
                        await self._process_batch_mode(adapter_id, adapter)

                except Exception as e:
                    adapter._record_error(e)
                    self.logger.error(
                        "Adapter processing error", adapter_id=adapter_id, error=str(e)
                    )

                    # Brief pause before retrying
                    await asyncio.sleep(5)

        except asyncio.CancelledError:
            self.logger.info("Adapter processing cancelled", adapter_id=adapter_id)
        except Exception as e:
            self.logger.error(
                "Fatal adapter error", adapter_id=adapter_id, error=str(e)
            )
            self._failed_adapters[adapter_id] = datetime.utcnow()
        finally:
            # Clean up
            if adapter_id in self._active_adapters:
                del self._active_adapters[adapter_id]

    async def _process_streaming(self, adapter_id: str, adapter: BaseAdapter) -> None:
        """Process items in streaming mode."""
        async for raw_item in adapter.fetch_items(limit=1):
            try:
                # Transform item
                context_item = await adapter.transform_item(raw_item)

                # Process single item
                await self.process_batch(
                    adapter_id, [context_item], commit_immediately=True
                )

                adapter._record_success()

            except Exception as e:
                adapter._record_error(e, {"raw_item": raw_item})

    async def _process_batch_mode(self, adapter_id: str, adapter: BaseAdapter) -> None:
        """Process items in batch mode."""
        batch_items = []

        async for raw_item in adapter.fetch_items(limit=adapter.config.batch_size):
            try:
                context_item = await adapter.transform_item(raw_item)
                batch_items.append(context_item)

                # Process batch when full or timeout reached
                if len(batch_items) >= adapter.config.batch_size:
                    await self.process_batch(adapter_id, batch_items)
                    batch_items.clear()

            except Exception as e:
                adapter._record_error(e, {"raw_item": raw_item})

        # Process remaining items
        if batch_items:
            await self.process_batch(adapter_id, batch_items)

    async def _validate_item(self, item: ContextItem) -> bool:
        """Validate a context item."""
        try:
            return await self.transformer.validate_item(item)
        except Exception as e:
            self.logger.error("Validation error", error=str(e))
            return False

    async def _store_items(
        self,
        items: List[ContextItem],
        commit_immediately: bool = False,
        adapter_id: str = "unknown",
    ) -> BatchProcessingResult:
        """Store items in database with retry logic."""
        if not items:
            return BatchProcessingResult()

        try:
            return await self._store_items_with_retry(items, adapter_id)
        except Exception as e:
            self.logger.error(
                "Failed to store items",
                count=len(items),
                adapter_id=adapter_id,
                error=str(e),
            )
            return BatchProcessingResult(
                total_items=len(items),
                failed_items=len(items),
                errors=[{"error": str(e)}],
            )

    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        while self._running and not self._shutdown_event.is_set():
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Health check error", error=str(e))
                await asyncio.sleep(self.config.health_check_interval)

    async def _perform_health_checks(self) -> None:
        """Perform health checks on all adapters."""
        for adapter_id, adapter in list(self._active_adapters.items()):
            try:
                health = await adapter.health_check()

                if not health.get("is_healthy", False):
                    self.logger.warning(
                        "Unhealthy adapter detected",
                        adapter_id=adapter_id,
                        health=health,
                    )

                    # Optionally restart failed adapters
                    if (
                        adapter.status == AdapterStatus.ERROR
                        and self.config.auto_restart_failed_adapters
                    ):
                        await self._restart_adapter(adapter_id)

            except Exception as e:
                self.logger.error(
                    "Health check failed", adapter_id=adapter_id, error=str(e)
                )

    async def _restart_adapter(self, adapter_id: str) -> None:
        """Restart a failed adapter."""
        self.logger.info("Restarting failed adapter", adapter_id=adapter_id)

        try:
            await self._stop_adapter(adapter_id)
            await asyncio.sleep(5)  # Brief pause
            await self._start_adapter(adapter_id)
        except Exception as e:
            self.logger.error(
                "Failed to restart adapter", adapter_id=adapter_id, error=str(e)
            )
            self._failed_adapters[adapter_id] = datetime.utcnow()

    async def _metrics_collection_loop(self) -> None:
        """Background metrics collection loop."""
        start_time = datetime.utcnow()

        while self._running and not self._shutdown_event.is_set():
            try:
                await self._collect_metrics(start_time)
                await asyncio.sleep(self.config.metrics_collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Metrics collection error", error=str(e))
                await asyncio.sleep(self.config.metrics_collection_interval)

    async def _collect_metrics(self, start_time: datetime) -> None:
        """Collect and update pipeline metrics."""
        now = datetime.utcnow()
        uptime = (now - start_time).total_seconds()

        self.metrics.pipeline_uptime_seconds = uptime
        self.metrics.adapters_running = len(self._active_adapters)
        self.metrics.adapters_failed = len(self._failed_adapters)

        # Calculate throughput
        if uptime > 0:
            self.metrics.average_pipeline_throughput = (
                self.metrics.total_items_ingested / uptime
            )

        self.metrics.last_activity = now

    @asynccontextmanager
    async def managed_pipeline(self, adapter_ids: Optional[List[str]] = None):
        """Context manager for pipeline lifecycle.

        Args:
            adapter_ids: Specific adapters to start

        Usage:
            async with pipeline.managed_pipeline(['chat', 'git']):
                # Pipeline is running
                await asyncio.sleep(60)
            # Pipeline is automatically stopped
        """
        try:
            await self.start(adapter_ids)
            yield self
        finally:
            await self.stop()

    # Enhanced pipeline methods

    async def _initialize_database(self) -> None:
        """Initialize database connection pool and interface."""
        try:
            self.db_pool = DatabaseConnectionPool(
                database_url=self.config.database_url,
                min_connections=self.config.database_pool_min,
                max_connections=self.config.database_pool_max,
                command_timeout=self.config.database_command_timeout,
            )

            await self.db_pool.initialize()
            self.database = IngestionDatabase(self.db_pool)

            # Test database connectivity
            health = await self.database.health_check()
            if health["status"] != "healthy":
                raise Exception(f"Database health check failed: {health}")

            self.logger.info(
                "Database initialized successfully",
                pool_size=self.config.database_pool_max,
                response_time_ms=health.get("response_time_ms", 0),
            )

        except Exception as e:
            self.logger.error("Database initialization failed", error=str(e))
            if self.db_pool:
                await self.db_pool.close()
                self.db_pool = None
            raise

    async def _store_items_with_retry(
        self,
        items: List[ContextItem],
        adapter_id: str,
        max_attempts: Optional[int] = None,
    ) -> BatchProcessingResult:
        """Store items with retry logic and circuit breaker support.

        Args:
            items: Items to store
            adapter_id: Source adapter ID
            max_attempts: Override default retry attempts

        Returns:
            BatchProcessingResult with operation details
        """
        if not self.database:
            raise Exception("Database not initialized")

        max_attempts = max_attempts or self.config.max_retry_attempts
        last_exception = None

        for attempt in range(max_attempts):
            try:
                # Add items to context window for relationship detection
                if self.config.enable_relationship_detection:
                    await self._add_to_context_window(items)

                # Store items in database
                result = await self.database.store_context_items(
                    items, batch_size=self.config.batch_commit_size
                )

                # Update metrics
                self.metrics.total_items_ingested += result.processed_items
                self.metrics.total_items_failed += result.failed_items
                self.metrics.total_batches_processed += 1

                self.logger.debug(
                    "Batch stored successfully",
                    adapter_id=adapter_id,
                    items=len(items),
                    attempt=attempt + 1,
                    processed=result.processed_items,
                    failed=result.failed_items,
                )

                return result

            except CircuitBreakerOpenError:
                # Don't retry if circuit breaker is open
                self.logger.warning(
                    "Circuit breaker open, skipping retry",
                    adapter_id=adapter_id,
                    attempt=attempt + 1,
                )
                raise

            except Exception as e:
                last_exception = e

                if attempt < max_attempts - 1:
                    # Calculate delay with exponential backoff
                    delay = min(
                        self.config.retry_base_delay
                        * (self.config.retry_exponential_base**attempt),
                        self.config.retry_max_delay,
                    )

                    self.logger.warning(
                        "Storage attempt failed, retrying",
                        adapter_id=adapter_id,
                        attempt=attempt + 1,
                        max_attempts=max_attempts,
                        delay=delay,
                        error=str(e),
                    )

                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        "All storage attempts failed",
                        adapter_id=adapter_id,
                        attempts=max_attempts,
                        error=str(e),
                    )

        # All attempts failed
        result = BatchProcessingResult(
            total_items=len(items),
            failed_items=len(items),
            errors=[{"error": str(last_exception)}],
        )

        return result

    async def _add_to_context_window(self, items: List[ContextItem]) -> None:
        """Add items to context window for relationship detection."""
        async with self._recent_items_lock:
            # Add new items
            self._recent_items.extend(items)

            # Trim to max size, keeping most recent
            max_size = self.config.relationship_context_window_size
            if len(self._recent_items) > max_size:
                self._recent_items = self._recent_items[-max_size:]

    async def _relationship_detection_loop(self) -> None:
        """Background loop for relationship detection."""
        while self._running and not self._shutdown_event.is_set():
            try:
                # Process relationship detection in batches
                if len(self._recent_items) >= self.config.relationship_batch_size:
                    async with self._recent_items_lock:
                        # Get batch for processing
                        batch_size = self.config.relationship_batch_size
                        batch = self._recent_items[-batch_size:]

                    await self._detect_and_store_relationships(batch)

                # Wait before next check
                await asyncio.sleep(10)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Relationship detection error", error=str(e))
                await asyncio.sleep(30)

    async def _detect_and_store_relationships(self, items: List[ContextItem]) -> None:
        """Detect and store relationships for a batch of items."""
        if not items or not self.database:
            return

        try:
            relationships = []

            # Get context window from recent items
            async with self._recent_items_lock:
                context_window = list(self._recent_items)

            # Detect relationships for each item
            for item in items:
                # Get adapter for relationship detection
                adapter = self._get_adapter_for_item(item)
                if not adapter:
                    continue

                try:
                    item_relationships = await adapter.detect_relationships(
                        item, context_window
                    )

                    # Convert to ContextRelationship objects
                    for rel_type, target_id, confidence in item_relationships:
                        relationship = ContextRelationship(
                            source_id=item.id,
                            target_id=target_id,
                            relationship_type=rel_type,
                            confidence=confidence,
                            created_by="system",
                            metadata={"detected_by_adapter": adapter.config.adapter_id},
                        )
                        relationships.append(relationship)

                except Exception as e:
                    self.logger.warning(
                        "Relationship detection failed for item",
                        item_id=str(item.id),
                        error=str(e),
                    )

            # Store relationships if any were detected
            if relationships:
                result = await self.database.store_relationships(relationships)

                self.logger.debug(
                    "Relationships processed",
                    detected=len(relationships),
                    stored=result.processed_items,
                    failed=result.failed_items,
                )

        except Exception as e:
            self.logger.error("Relationship detection and storage failed", error=str(e))

    def _get_adapter_for_item(self, item: ContextItem) -> Optional[BaseAdapter]:
        """Get the adapter that can handle relationship detection for an item."""
        # Find adapter by source type
        for adapter_id, adapter in self._active_adapters.items():
            if adapter.config.source_type == item.source_type:
                return adapter
        return None

    async def _garbage_collection_loop(self) -> None:
        """Background garbage collection loop."""
        while self._running and not self._shutdown_event.is_set():
            try:
                import gc

                # Force garbage collection
                collected = gc.collect()

                if collected > 0:
                    self.logger.debug(
                        "Garbage collection completed", objects_collected=collected
                    )

                # Check memory usage
                try:
                    import psutil

                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / (1024 * 1024)

                    if memory_mb > self.config.max_pipeline_memory_mb:
                        self.logger.warning(
                            "High pipeline memory usage",
                            current_memory_mb=memory_mb,
                            max_memory_mb=self.config.max_pipeline_memory_mb,
                        )

                        # Trim context window if too large
                        async with self._recent_items_lock:
                            if len(self._recent_items) > 50:
                                self._recent_items = self._recent_items[-50:]
                                self.logger.info(
                                    "Context window trimmed due to memory pressure"
                                )

                except ImportError:
                    pass  # psutil not available

                await asyncio.sleep(self.config.gc_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Garbage collection error", error=str(e))
                await asyncio.sleep(self.config.gc_interval_seconds)
