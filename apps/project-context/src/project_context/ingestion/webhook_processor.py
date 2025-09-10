"""Webhook processing infrastructure for CI/CD platforms."""

import asyncio
import json
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from ..models.common import ContextItem, ContextRelationship
from .adapters.cicd_adapter import CICDPlatform, GitHubActionsAdapter
from .database import IngestionDatabase

logger = structlog.get_logger(__name__)


class WebhookEvent:
    """Represents a webhook event."""

    def __init__(
        self,
        event_id: str,
        platform: CICDPlatform,
        event_type: str,
        payload: dict,
        signature: Optional[str] = None,
        received_at: Optional[datetime] = None,
    ):
        self.event_id = event_id
        self.platform = platform
        self.event_type = event_type
        self.payload = payload
        self.signature = signature
        self.received_at = received_at or datetime.utcnow()
        self.retry_count = 0
        self.processing_attempts = []


class ProcessingResult:
    """Result of webhook event processing."""

    def __init__(
        self,
        event_id: str,
        success: bool,
        context_item: Optional[ContextItem] = None,
        relationships: Optional[List[ContextRelationship]] = None,
        error: Optional[str] = None,
        processing_time_ms: Optional[float] = None,
    ):
        self.event_id = event_id
        self.success = success
        self.context_item = context_item
        self.relationships = relationships or []
        self.error = error
        self.processing_time_ms = processing_time_ms


class WebhookMetrics:
    """Webhook processing metrics."""

    def __init__(self):
        self.events_received = defaultdict(int)
        self.events_processed = defaultdict(int)
        self.events_failed = defaultdict(int)
        self.processing_times = defaultdict(lambda: deque(maxlen=1000))
        self.last_event_time = defaultdict(lambda: datetime.utcnow())

        # Rate limiting metrics
        self.rate_limit_hits = defaultdict(int)
        self.signature_failures = defaultdict(int)

        # Queue metrics
        self.queue_size = 0
        self.max_queue_size = 0
        self.worker_count = 0
        self.active_workers = 0

    def record_event_received(self, platform: str, event_type: str):
        """Record webhook event received."""
        self.events_received[f"{platform}.{event_type}"] += 1
        self.last_event_time[platform] = datetime.utcnow()

    def record_event_processed(
        self, platform: str, event_type: str, processing_time_ms: float
    ):
        """Record successful event processing."""
        key = f"{platform}.{event_type}"
        self.events_processed[key] += 1
        self.processing_times[key].append(processing_time_ms)

    def record_event_failed(self, platform: str, event_type: str, error: str):
        """Record failed event processing."""
        self.events_failed[f"{platform}.{event_type}"] += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        total_received = sum(self.events_received.values())
        total_processed = sum(self.events_processed.values())
        total_failed = sum(self.events_failed.values())

        # Calculate average processing times
        avg_processing_times = {}
        for key, times in self.processing_times.items():
            if times:
                avg_processing_times[key] = sum(times) / len(times)

        return {
            "total_events_received": total_received,
            "total_events_processed": total_processed,
            "total_events_failed": total_failed,
            "success_rate": total_processed / max(total_received, 1),
            "queue_size": self.queue_size,
            "max_queue_size": self.max_queue_size,
            "active_workers": self.active_workers,
            "worker_count": self.worker_count,
            "events_by_platform": dict(self.events_received),
            "average_processing_times_ms": avg_processing_times,
            "last_event_times": {
                k: v.isoformat() for k, v in self.last_event_time.items()
            },
        }


class WebhookProcessor:
    """Central webhook processing system."""

    def __init__(
        self,
        database: IngestionDatabase,
        num_workers: int = 10,
        queue_maxsize: int = 10000,
        processing_timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 5,
    ):
        self.database = database
        self.num_workers = num_workers
        self.processing_timeout = processing_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Event processing
        self.event_queue = asyncio.Queue(maxsize=queue_maxsize)
        self.failed_events_queue = asyncio.Queue(maxsize=queue_maxsize // 10)
        self.worker_tasks: List[asyncio.Task] = []
        self.retry_task: Optional[asyncio.Task] = None

        # Platform adapters
        self.adapters: Dict[CICDPlatform, Any] = {}

        # Metrics and monitoring
        self.metrics = WebhookMetrics()
        self.rate_limiters: Dict[str, deque] = defaultdict(lambda: deque())

        # Rate limiting settings (requests per minute per IP)
        self.rate_limit_per_minute = 1000
        self.rate_limit_window = 60

        # Processing state
        self.running = False
        self.shutdown_event = asyncio.Event()

        self.logger = logger.bind(component="webhook_processor")

    def register_adapter(self, platform: CICDPlatform, adapter: Any) -> None:
        """Register a CI/CD platform adapter."""
        self.adapters[platform] = adapter
        self.logger.info(f"Registered adapter for {platform.value}")

    async def start(self) -> None:
        """Start the webhook processing system."""
        if self.running:
            self.logger.warning("Webhook processor already running")
            return

        self.running = True
        self.shutdown_event.clear()

        # Start worker tasks
        for i in range(self.num_workers):
            task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.worker_tasks.append(task)

        # Start retry handler
        self.retry_task = asyncio.create_task(self._retry_failed_events())

        self.metrics.worker_count = self.num_workers

        self.logger.info(
            "Webhook processor started",
            workers=self.num_workers,
            queue_maxsize=self.event_queue.maxsize,
        )

    async def stop(self) -> None:
        """Stop the webhook processing system."""
        if not self.running:
            return

        self.logger.info("Stopping webhook processor")

        self.running = False
        self.shutdown_event.set()

        # Cancel all worker tasks
        for task in self.worker_tasks:
            if not task.done():
                task.cancel()

        if self.retry_task and not self.retry_task.done():
            self.retry_task.cancel()

        # Wait for tasks to complete
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)

        if self.retry_task:
            try:
                await asyncio.wait_for(self.retry_task, timeout=5)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        self.logger.info("Webhook processor stopped")

    async def process_webhook(
        self,
        platform: CICDPlatform,
        event_type: str,
        payload: dict,
        signature: Optional[str] = None,
        source_ip: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process an incoming webhook."""
        event_id = str(uuid4())
        start_time = time.time()

        try:
            # Rate limiting check
            if not self._check_rate_limit(source_ip or "unknown"):
                self.metrics.rate_limit_hits[platform.value] += 1
                raise HTTPException(status_code=429, detail="Rate limit exceeded")

            # Create webhook event
            event = WebhookEvent(
                event_id=event_id,
                platform=platform,
                event_type=event_type,
                payload=payload,
                signature=signature,
            )

            # Record metrics
            self.metrics.record_event_received(platform.value, event_type)

            # Validate signature if provided
            adapter = self.adapters.get(platform)
            if adapter and signature:
                payload_bytes = json.dumps(payload, separators=(",", ":")).encode()
                if not adapter.validate_webhook_signature(payload_bytes, signature):
                    self.metrics.signature_failures[platform.value] += 1
                    raise HTTPException(status_code=403, detail="Invalid signature")

            # Queue for processing
            try:
                await asyncio.wait_for(self.event_queue.put(event), timeout=5.0)
            except asyncio.TimeoutError:
                raise HTTPException(status_code=503, detail="Processing queue full")

            # Update queue metrics
            self.metrics.queue_size = self.event_queue.qsize()
            self.metrics.max_queue_size = max(
                self.metrics.max_queue_size, self.metrics.queue_size
            )

            processing_time = (time.time() - start_time) * 1000

            return {
                "event_id": event_id,
                "status": "queued",
                "platform": platform.value,
                "event_type": event_type,
                "processing_time_ms": processing_time,
                "queue_position": self.event_queue.qsize(),
            }

        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(
                "Webhook processing error",
                event_id=event_id,
                platform=platform.value,
                event_type=event_type,
                error=str(e),
            )
            raise HTTPException(status_code=500, detail="Internal processing error")

    def _check_rate_limit(self, source_ip: str) -> bool:
        """Check if request is within rate limits."""
        now = time.time()
        cutoff = now - self.rate_limit_window

        # Clean old requests
        requests = self.rate_limiters[source_ip]
        while requests and requests[0] < cutoff:
            requests.popleft()

        # Check limit
        if len(requests) >= self.rate_limit_per_minute:
            return False

        # Record request
        requests.append(now)
        return True

    async def _worker_loop(self, worker_id: str) -> None:
        """Main worker loop for processing events."""
        self.logger.debug(f"Worker {worker_id} started")

        while self.running:
            try:
                self.metrics.active_workers += 1

                # Get next event with timeout
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)

                # Update metrics
                self.metrics.queue_size = self.event_queue.qsize()

                # Process event
                result = await self._process_event(event, worker_id)

                # Handle result
                if result.success:
                    self.metrics.record_event_processed(
                        event.platform.value,
                        event.event_type,
                        result.processing_time_ms or 0,
                    )
                else:
                    self.metrics.record_event_failed(
                        event.platform.value,
                        event.event_type,
                        result.error or "Unknown error",
                    )

                    # Queue for retry if not max attempts
                    if event.retry_count < self.max_retries:
                        event.retry_count += 1
                        await self.failed_events_queue.put(event)

                # Mark task done
                self.event_queue.task_done()

            except asyncio.TimeoutError:
                continue  # No event available, continue waiting
            except asyncio.CancelledError:
                self.logger.debug(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                self.logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)  # Brief pause on error
            finally:
                self.metrics.active_workers = max(0, self.metrics.active_workers - 1)

        self.logger.debug(f"Worker {worker_id} stopped")

    async def _process_event(
        self, event: WebhookEvent, worker_id: str
    ) -> ProcessingResult:
        """Process a single webhook event."""
        start_time = time.time()

        try:
            self.logger.debug(
                "Processing webhook event",
                event_id=event.event_id,
                platform=event.platform.value,
                event_type=event.event_type,
                worker=worker_id,
                attempt=event.retry_count + 1,
            )

            # Get adapter for platform
            adapter = self.adapters.get(event.platform)
            if not adapter:
                raise ValueError(f"No adapter registered for {event.platform.value}")

            # Transform webhook payload to context item
            context_item = await adapter.process_webhook(
                event.event_type, event.payload
            )

            if not context_item:
                # Event type not handled by adapter
                return ProcessingResult(
                    event_id=event.event_id,
                    success=True,  # Not an error, just not processed
                    processing_time_ms=(time.time() - start_time) * 1000,
                )

            # Detect relationships
            relationships = []
            if hasattr(adapter, "detect_relationships"):
                # Get recent context for correlation
                recent_items = await self._get_recent_context_items(
                    event.platform, limit=100
                )

                relationship_tuples = await adapter.detect_relationships(
                    context_item, recent_items
                )

                # Convert to ContextRelationship objects
                for rel_type, target_id, confidence in relationship_tuples:
                    relationships.append(
                        ContextRelationship(
                            source_id=str(context_item.id),
                            target_id=target_id,
                            relationship_type=rel_type,
                            confidence=confidence,
                            created_by="webhook_processor",
                            metadata={
                                "event_id": event.event_id,
                                "platform": event.platform.value,
                                "event_type": event.event_type,
                            },
                        )
                    )

            # Store context item and relationships
            await self.database.store_context_items([context_item])

            if relationships:
                await self.database.store_relationships(relationships)

            processing_time = (time.time() - start_time) * 1000

            self.logger.debug(
                "Event processed successfully",
                event_id=event.event_id,
                context_item_id=str(context_item.id),
                relationships_detected=len(relationships),
                processing_time_ms=processing_time,
            )

            return ProcessingResult(
                event_id=event.event_id,
                success=True,
                context_item=context_item,
                relationships=relationships,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000

            self.logger.error(
                "Event processing failed",
                event_id=event.event_id,
                platform=event.platform.value,
                event_type=event.event_type,
                worker=worker_id,
                attempt=event.retry_count + 1,
                error=str(e),
                processing_time_ms=processing_time,
            )

            return ProcessingResult(
                event_id=event.event_id,
                success=False,
                error=str(e),
                processing_time_ms=processing_time,
            )

    async def _retry_failed_events(self) -> None:
        """Handle retrying failed events."""
        while self.running:
            try:
                # Wait for failed event
                failed_event = await asyncio.wait_for(
                    self.failed_events_queue.get(), timeout=5.0
                )

                # Wait before retry
                await asyncio.sleep(self.retry_delay * failed_event.retry_count)

                # Re-queue for processing
                await self.event_queue.put(failed_event)

            except asyncio.TimeoutError:
                continue  # No failed events, continue waiting
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Retry handler error: {e}")
                await asyncio.sleep(5)

    async def _get_recent_context_items(
        self, platform: CICDPlatform, limit: int = 100
    ) -> List[ContextItem]:
        """Get recent context items for relationship detection."""
        try:
            # Get recent items from last hour for correlation
            since = datetime.utcnow() - timedelta(hours=1)

            return await self.database.query_context_items(
                timestamp_range=(since, None), limit=limit, order_by="timestamp DESC"
            )
        except Exception as e:
            self.logger.error(f"Failed to get recent context items: {e}")
            return []

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of webhook processor."""
        return {
            "running": self.running,
            "workers_active": self.metrics.active_workers,
            "workers_total": self.metrics.worker_count,
            "queue_size": self.metrics.queue_size,
            "queue_max_size": self.event_queue.maxsize,
            "failed_queue_size": self.failed_events_queue.qsize(),
            "registered_platforms": list(self.adapters.keys()),
            "metrics": self.metrics.get_summary(),
        }

    async def get_processing_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get detailed processing statistics."""
        # This could query the database for processed events
        # and provide detailed analytics
        return {
            "time_period_hours": hours,
            "current_metrics": self.metrics.get_summary(),
            # Additional stats would come from database queries
        }
