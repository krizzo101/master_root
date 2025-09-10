"""Real-time Error Processing Pipeline with High-Volume Ingestion.

This module provides real-time error log processing capabilities with:
- Stream processing for high-volume log ingestion
- Real-time correlation detection and alerting
- Adaptive batch processing based on load
- Circuit breaker patterns for resilience
- Comprehensive monitoring and metrics
"""

import asyncio
import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Set, Tuple
from uuid import uuid4

import structlog

from ..base_adapter import AdapterStatus, BatchMode
from ..database import IngestionDatabase
from .enhanced_error_adapter import EnhancedErrorAdapter, ErrorPattern, ParsedError

logger = structlog.get_logger(__name__)


class ProcessingMode(Enum):
    """Pipeline processing modes."""

    BATCH = "batch"
    STREAMING = "streaming"
    ADAPTIVE = "adaptive"


class AlertSeverity(Enum):
    """Alert severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorAlert:
    """Represents an error-based alert."""

    alert_id: str
    timestamp: datetime
    severity: AlertSeverity
    alert_type: str
    message: str
    error_pattern_id: Optional[str] = None
    affected_files: Set[str] = field(default_factory=set)
    error_count: int = 1
    correlation_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineMetrics:
    """Real-time pipeline metrics."""

    # Processing metrics
    total_processed: int = 0
    errors_per_second: float = 0.0
    current_batch_size: int = 0
    processing_latency_ms: float = 0.0

    # Queue metrics
    input_queue_size: int = 0
    processing_queue_size: int = 0
    correlation_queue_size: int = 0

    # Error metrics
    critical_errors_count: int = 0
    high_severity_errors_count: int = 0
    error_rate: float = 0.0

    # Pattern metrics
    active_patterns_count: int = 0
    new_patterns_detected: int = 0
    pattern_matches_per_hour: float = 0.0

    # Alert metrics
    active_alerts_count: int = 0
    alerts_generated_today: int = 0
    alert_resolution_time_minutes: float = 0.0

    # Performance metrics
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    database_connection_pool_usage: float = 0.0


@dataclass
class StreamProcessor:
    """Configuration for stream processing."""

    # Processing configuration
    max_concurrent_workers: int = 10
    batch_size_range: Tuple[int, int] = (10, 1000)
    processing_timeout_seconds: int = 30
    adaptive_batch_sizing: bool = True

    # Queue configuration
    input_queue_maxsize: int = 10000
    processing_queue_maxsize: int = 5000
    correlation_queue_maxsize: int = 2000

    # Circuit breaker
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout_seconds: int = 60
    circuit_breaker_recovery_threshold: int = 3

    # Alerting
    enable_realtime_alerts: bool = True
    alert_aggregation_window_minutes: int = 5
    alert_cooldown_minutes: int = 15

    # Performance tuning
    enable_adaptive_processing: bool = True
    target_latency_ms: int = 100
    max_memory_usage_mb: int = 1024


class CircuitBreaker:
    """Circuit breaker for fault tolerance."""

    def __init__(
        self, failure_threshold: int, timeout_seconds: int, recovery_threshold: int
    ):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.recovery_threshold = recovery_threshold

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if (
                datetime.now() - self.last_failure_time
            ).total_seconds() > self.timeout_seconds:
                self.state = "half_open"
                self.success_count = 0
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)

            if self.state == "half_open":
                self.success_count += 1
                if self.success_count >= self.recovery_threshold:
                    self.state = "closed"
                    self.failure_count = 0

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"

            raise e


class AlertManager:
    """Manages error-based alerting and notifications."""

    def __init__(self, config: StreamProcessor):
        self.config = config
        self.active_alerts: Dict[str, ErrorAlert] = {}
        self.alert_history: deque = deque(maxsize=1000)
        self.alert_cooldowns: Dict[str, datetime] = {}

    async def process_error_for_alerts(
        self, parsed_error: ParsedError, patterns: List[ErrorPattern]
    ) -> List[ErrorAlert]:
        """Process error and generate alerts if needed."""
        alerts = []

        # Check for critical error alerts
        if parsed_error.severity == "critical":
            alert = await self._create_critical_error_alert(parsed_error)
            alerts.append(alert)

        # Check for pattern-based alerts
        for pattern in patterns:
            if pattern.frequency >= 10:  # Alert on frequent patterns
                alert = await self._create_pattern_alert(parsed_error, pattern)
                if alert:
                    alerts.append(alert)

        # Check for security-related alerts
        if "security" in getattr(parsed_error, "tags", []):
            alert = await self._create_security_alert(parsed_error)
            alerts.append(alert)

        # Process and store alerts
        for alert in alerts:
            await self._process_alert(alert)

        return alerts

    async def _create_critical_error_alert(
        self, parsed_error: ParsedError
    ) -> ErrorAlert:
        """Create alert for critical errors."""
        return ErrorAlert(
            alert_id=f"critical_{parsed_error.error_id}_{int(time.time())}",
            timestamp=parsed_error.timestamp,
            severity=AlertSeverity.CRITICAL,
            alert_type="critical_error",
            message=f"Critical error detected: {parsed_error.error_type} in {parsed_error.file_path or 'unknown location'}",
            affected_files={parsed_error.file_path}
            if parsed_error.file_path
            else set(),
            metadata={
                "error_type": parsed_error.error_type,
                "error_message": parsed_error.message,
                "file_path": parsed_error.file_path,
                "line_number": parsed_error.line_number,
                "stack_trace": parsed_error.stack_trace,
            },
        )

    async def _create_pattern_alert(
        self, parsed_error: ParsedError, pattern: ErrorPattern
    ) -> Optional[ErrorAlert]:
        """Create alert for frequent error patterns."""
        cooldown_key = f"pattern_{pattern.pattern_id}"

        # Check cooldown
        if cooldown_key in self.alert_cooldowns:
            cooldown_end = self.alert_cooldowns[cooldown_key] + timedelta(
                minutes=self.config.alert_cooldown_minutes
            )
            if datetime.now() < cooldown_end:
                return None

        # Create pattern alert
        alert = ErrorAlert(
            alert_id=f"pattern_{pattern.pattern_id}_{int(time.time())}",
            timestamp=datetime.now(),
            severity=AlertSeverity.HIGH,
            alert_type="error_pattern",
            message=f"Frequent error pattern detected: {pattern.error_signature} ({pattern.frequency} occurrences)",
            error_pattern_id=pattern.pattern_id,
            affected_files=pattern.file_paths,
            error_count=pattern.frequency,
            metadata={
                "pattern_signature": pattern.error_signature,
                "frequency": pattern.frequency,
                "first_seen": pattern.first_seen.isoformat()
                if pattern.first_seen
                else None,
                "last_seen": pattern.last_seen.isoformat()
                if pattern.last_seen
                else None,
                "severity_distribution": pattern.severity_distribution,
            },
        )

        self.alert_cooldowns[cooldown_key] = datetime.now()
        return alert

    async def _create_security_alert(self, parsed_error: ParsedError) -> ErrorAlert:
        """Create alert for security-related errors."""
        return ErrorAlert(
            alert_id=f"security_{parsed_error.error_id}_{int(time.time())}",
            timestamp=parsed_error.timestamp,
            severity=AlertSeverity.HIGH,
            alert_type="security_error",
            message=f"Security-related error detected: {parsed_error.message[:200]}",
            affected_files={parsed_error.file_path}
            if parsed_error.file_path
            else set(),
            metadata={
                "error_type": parsed_error.error_type,
                "error_message": parsed_error.message,
                "file_path": parsed_error.file_path,
                "user_id": parsed_error.user_id,
                "request_id": parsed_error.request_id,
            },
        )

    async def _process_alert(self, alert: ErrorAlert) -> None:
        """Process and store alert."""
        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)

        logger.warning(
            f"Alert generated: {alert.alert_type}",
            alert_id=alert.alert_id,
            severity=alert.severity.value,
            message=alert.message,
        )


class RealtimeErrorPipeline:
    """High-performance real-time error processing pipeline."""

    def __init__(
        self,
        adapter: EnhancedErrorAdapter,
        database: IngestionDatabase,
        config: Optional[StreamProcessor] = None,
    ):
        self.adapter = adapter
        self.database = database
        self.config = config or StreamProcessor()

        # Processing components
        self.alert_manager = AlertManager(self.config)
        self.circuit_breaker = CircuitBreaker(
            self.config.circuit_breaker_failure_threshold,
            self.config.circuit_breaker_timeout_seconds,
            self.config.circuit_breaker_recovery_threshold,
        )

        # Queues for stream processing
        self.input_queue: asyncio.Queue = asyncio.Queue(
            maxsize=self.config.input_queue_maxsize
        )
        self.processing_queue: asyncio.Queue = asyncio.Queue(
            maxsize=self.config.processing_queue_maxsize
        )
        self.correlation_queue: asyncio.Queue = asyncio.Queue(
            maxsize=self.config.correlation_queue_maxsize
        )

        # Processing state
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
        self.metrics = PipelineMetrics()

        # Adaptive processing
        self.current_batch_size = self.config.batch_size_range[0]
        self.processing_latencies = deque(maxsize=100)
        self.throughput_samples = deque(maxsize=50)

        # Pattern tracking
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.pattern_update_lock = asyncio.Lock()

    async def start(self) -> None:
        """Start the real-time processing pipeline."""
        if self.is_running:
            logger.warning("Pipeline already running")
            return

        self.is_running = True
        logger.info("Starting real-time error processing pipeline")

        # Start worker tasks
        self.worker_tasks = [
            asyncio.create_task(self._input_processor()),
            asyncio.create_task(self._batch_processor()),
            asyncio.create_task(self._correlation_processor()),
            asyncio.create_task(self._metrics_collector()),
            asyncio.create_task(self._adaptive_tuner()),
        ]

        # Start multiple processing workers
        for i in range(self.config.max_concurrent_workers):
            task = asyncio.create_task(self._processing_worker(f"worker_{i}"))
            self.worker_tasks.append(task)

        logger.info(f"Started pipeline with {len(self.worker_tasks)} workers")

    async def stop(self) -> None:
        """Stop the pipeline gracefully."""
        if not self.is_running:
            return

        logger.info("Stopping real-time error processing pipeline")
        self.is_running = False

        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)

        logger.info("Pipeline stopped")

    async def ingest_error_stream(
        self, error_stream: AsyncIterator[Dict[str, Any]]
    ) -> None:
        """Ingest errors from a stream source."""
        try:
            async for error_data in error_stream:
                if not self.is_running:
                    break

                # Add to input queue with backpressure handling
                try:
                    self.input_queue.put_nowait(error_data)
                except asyncio.QueueFull:
                    logger.warning("Input queue full, dropping error")
                    continue

        except Exception as e:
            logger.error(f"Error in stream ingestion: {e}")

    async def ingest_error_batch(self, error_batch: List[Dict[str, Any]]) -> None:
        """Ingest a batch of errors."""
        for error_data in error_batch:
            if not self.is_running:
                break

            try:
                self.input_queue.put_nowait(error_data)
            except asyncio.QueueFull:
                logger.warning("Input queue full, dropping error")

    async def _input_processor(self) -> None:
        """Process incoming errors and route to appropriate queues."""
        logger.info("Started input processor")

        while self.is_running:
            try:
                # Get errors from input queue
                errors_batch = []
                deadline = time.time() + 1.0  # 1-second batch window

                while (
                    len(errors_batch) < self.current_batch_size
                    and time.time() < deadline
                ):
                    try:
                        error_data = await asyncio.wait_for(
                            self.input_queue.get(), timeout=0.1
                        )
                        errors_batch.append(error_data)
                    except asyncio.TimeoutError:
                        break

                if errors_batch:
                    # Route to processing queue
                    try:
                        await self.processing_queue.put(errors_batch)
                        self.metrics.current_batch_size = len(errors_batch)
                    except asyncio.QueueFull:
                        logger.warning("Processing queue full, dropping batch")

                # Update metrics
                self.metrics.input_queue_size = self.input_queue.qsize()
                self.metrics.processing_queue_size = self.processing_queue.qsize()

            except Exception as e:
                logger.error(f"Error in input processor: {e}")
                await asyncio.sleep(1)

    async def _processing_worker(self, worker_id: str) -> None:
        """Worker for processing error batches."""
        logger.info(f"Started processing worker: {worker_id}")

        while self.is_running:
            try:
                # Get batch from processing queue
                error_batch = await asyncio.wait_for(
                    self.processing_queue.get(), timeout=1.0
                )

                # Process batch with circuit breaker
                start_time = time.time()
                await self.circuit_breaker.call(self._process_error_batch, error_batch)
                processing_time = (time.time() - start_time) * 1000

                # Update latency metrics
                self.processing_latencies.append(processing_time)
                self.metrics.processing_latency_ms = sum(
                    self.processing_latencies
                ) / len(self.processing_latencies)

                # Update throughput
                self.throughput_samples.append((len(error_batch), time.time()))

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in processing worker {worker_id}: {e}")
                await asyncio.sleep(1)

    async def _process_error_batch(self, error_batch: List[Dict[str, Any]]) -> None:
        """Process a batch of errors."""
        processed_errors = []
        context_items = []

        # Transform errors to context items
        for error_data in error_batch:
            try:
                context_item = await self.adapter.transform_item(error_data)
                context_items.append(context_item)
                processed_errors.append(error_data)

                # Update severity metrics
                severity = context_item.severity
                if severity == "critical":
                    self.metrics.critical_errors_count += 1
                elif severity == "high":
                    self.metrics.high_severity_errors_count += 1

            except Exception as e:
                logger.error(f"Error transforming error item: {e}")
                continue

        if not context_items:
            return

        # Store in database
        await self.database.store_context_items(context_items)

        # Detect relationships and correlations
        if self.config.enable_realtime_alerts:
            await self.correlation_queue.put((processed_errors, context_items))

        # Update processing metrics
        self.metrics.total_processed += len(context_items)

    async def _correlation_processor(self) -> None:
        """Process correlations and generate alerts."""
        logger.info("Started correlation processor")

        while self.is_running:
            try:
                # Get items for correlation processing
                processed_errors, context_items = await asyncio.wait_for(
                    self.correlation_queue.get(), timeout=1.0
                )

                # Update error patterns
                async with self.pattern_update_lock:
                    await self._update_error_patterns(processed_errors)

                # Generate alerts
                if self.config.enable_realtime_alerts:
                    await self._generate_alerts(processed_errors)

                # Detect relationships
                await self._detect_relationships(context_items)

                self.metrics.correlation_queue_size = self.correlation_queue.qsize()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in correlation processor: {e}")
                await asyncio.sleep(1)

    async def _update_error_patterns(
        self, processed_errors: List[Dict[str, Any]]
    ) -> None:
        """Update error patterns from processed errors."""
        for error_data in processed_errors:
            try:
                # Create pattern signature
                pattern_key = self._create_pattern_key(error_data)

                if pattern_key not in self.error_patterns:
                    self.error_patterns[pattern_key] = ErrorPattern(
                        pattern_id=pattern_key,
                        error_signature=self._create_error_signature(error_data),
                        first_seen=error_data.get("timestamp", datetime.now()),
                    )
                    self.metrics.new_patterns_detected += 1

                # Update pattern
                pattern = self.error_patterns[pattern_key]
                pattern.frequency += 1
                pattern.last_seen = error_data.get("timestamp", datetime.now())

                if error_data.get("file_path"):
                    pattern.file_paths.add(error_data["file_path"])

                severity = error_data.get("severity", "medium")
                pattern.severity_distribution[severity] = (
                    pattern.severity_distribution.get(severity, 0) + 1
                )

            except Exception as e:
                logger.error(f"Error updating pattern: {e}")

        self.metrics.active_patterns_count = len(self.error_patterns)

    async def _generate_alerts(self, processed_errors: List[Dict[str, Any]]) -> None:
        """Generate alerts from processed errors."""
        for error_data in processed_errors:
            try:
                # Convert to ParsedError for alert processing
                parsed_error = self._dict_to_parsed_error(error_data)

                # Get relevant patterns
                relevant_patterns = [
                    pattern
                    for pattern in self.error_patterns.values()
                    if pattern.pattern_id == self._create_pattern_key(error_data)
                ]

                # Generate alerts
                alerts = await self.alert_manager.process_error_for_alerts(
                    parsed_error, relevant_patterns
                )

                self.metrics.active_alerts_count = len(self.alert_manager.active_alerts)

            except Exception as e:
                logger.error(f"Error generating alerts: {e}")

    async def _detect_relationships(self, context_items) -> None:
        """Detect relationships between context items."""
        # This would implement relationship detection logic
        # For now, we'll just update metrics
        pass

    async def _metrics_collector(self) -> None:
        """Collect and update pipeline metrics."""
        logger.info("Started metrics collector")

        last_processed = 0
        last_time = time.time()

        while self.is_running:
            try:
                current_time = time.time()
                time_diff = current_time - last_time

                if time_diff >= 1.0:  # Update every second
                    # Calculate errors per second
                    processed_diff = self.metrics.total_processed - last_processed
                    self.metrics.errors_per_second = processed_diff / time_diff

                    # Calculate error rate
                    if self.metrics.total_processed > 0:
                        total_errors = (
                            self.metrics.critical_errors_count
                            + self.metrics.high_severity_errors_count
                        )
                        self.metrics.error_rate = (
                            total_errors / self.metrics.total_processed
                        )

                    # Calculate pattern matches per hour
                    if self.error_patterns:
                        total_frequency = sum(
                            pattern.frequency
                            for pattern in self.error_patterns.values()
                        )
                        self.metrics.pattern_matches_per_hour = (
                            total_frequency * 3600 / time_diff
                        )

                    last_processed = self.metrics.total_processed
                    last_time = current_time

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in metrics collector: {e}")
                await asyncio.sleep(1)

    async def _adaptive_tuner(self) -> None:
        """Adaptive tuning of pipeline parameters."""
        logger.info("Started adaptive tuner")

        while self.is_running:
            try:
                if (
                    self.config.enable_adaptive_processing
                    and len(self.processing_latencies) > 10
                ):
                    avg_latency = sum(self.processing_latencies) / len(
                        self.processing_latencies
                    )

                    # Adjust batch size based on latency
                    if avg_latency > self.config.target_latency_ms * 1.5:
                        # Latency too high, reduce batch size
                        self.current_batch_size = max(
                            self.config.batch_size_range[0],
                            int(self.current_batch_size * 0.9),
                        )
                    elif avg_latency < self.config.target_latency_ms * 0.5:
                        # Latency acceptable, increase batch size
                        self.current_batch_size = min(
                            self.config.batch_size_range[1],
                            int(self.current_batch_size * 1.1),
                        )

                await asyncio.sleep(10)  # Tune every 10 seconds

            except Exception as e:
                logger.error(f"Error in adaptive tuner: {e}")
                await asyncio.sleep(10)

    def _create_pattern_key(self, error_data: Dict[str, Any]) -> str:
        """Create a unique key for error pattern."""
        key_parts = [
            error_data.get("error_type", "unknown"),
            error_data.get("file_path", "")[:50],  # Limit path length
            str(error_data.get("severity", "medium")),
        ]
        return "|".join(key_parts)

    def _create_error_signature(self, error_data: Dict[str, Any]) -> str:
        """Create a human-readable error signature."""
        return f"{error_data.get('error_type', 'Unknown')} in {error_data.get('file_path', 'unknown location')}"

    def _dict_to_parsed_error(self, error_data: Dict[str, Any]) -> ParsedError:
        """Convert dictionary to ParsedError."""
        return ParsedError(
            error_id=error_data.get("error_id", str(uuid4())),
            timestamp=error_data.get("timestamp", datetime.now()),
            severity=error_data.get("severity", "medium"),
            error_type=error_data.get("error_type", "unknown"),
            message=error_data.get("message", ""),
            source=error_data.get("source", "unknown"),
            file_path=error_data.get("file_path"),
            line_number=error_data.get("line_number"),
            function_name=error_data.get("function_name"),
            class_name=error_data.get("class_name"),
            stack_trace=error_data.get("stack_trace"),
            environment=error_data.get("environment"),
            process_id=error_data.get("process_id"),
            thread_id=error_data.get("thread_id"),
            user_id=error_data.get("user_id"),
            request_id=error_data.get("request_id"),
            raw_data=error_data,
        )

    # Public API methods

    async def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get current pipeline metrics."""
        return {
            "total_processed": self.metrics.total_processed,
            "errors_per_second": self.metrics.errors_per_second,
            "current_batch_size": self.metrics.current_batch_size,
            "processing_latency_ms": self.metrics.processing_latency_ms,
            "queue_sizes": {
                "input": self.metrics.input_queue_size,
                "processing": self.metrics.processing_queue_size,
                "correlation": self.metrics.correlation_queue_size,
            },
            "error_metrics": {
                "critical_errors": self.metrics.critical_errors_count,
                "high_severity_errors": self.metrics.high_severity_errors_count,
                "error_rate": self.metrics.error_rate,
            },
            "pattern_metrics": {
                "active_patterns": self.metrics.active_patterns_count,
                "new_patterns_detected": self.metrics.new_patterns_detected,
                "pattern_matches_per_hour": self.metrics.pattern_matches_per_hour,
            },
            "alert_metrics": {
                "active_alerts": self.metrics.active_alerts_count,
                "alerts_today": self.metrics.alerts_generated_today,
            },
            "pipeline_status": "running" if self.is_running else "stopped",
            "worker_count": len(self.worker_tasks),
            "circuit_breaker_state": self.circuit_breaker.state,
        }

    async def get_error_patterns(self) -> List[Dict[str, Any]]:
        """Get current error patterns."""
        async with self.pattern_update_lock:
            return [
                {
                    "pattern_id": pattern.pattern_id,
                    "error_signature": pattern.error_signature,
                    "frequency": pattern.frequency,
                    "first_seen": pattern.first_seen.isoformat()
                    if pattern.first_seen
                    else None,
                    "last_seen": pattern.last_seen.isoformat()
                    if pattern.last_seen
                    else None,
                    "affected_files": list(pattern.file_paths),
                    "severity_distribution": dict(pattern.severity_distribution),
                }
                for pattern in self.error_patterns.values()
            ]

    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts."""
        return [
            {
                "alert_id": alert.alert_id,
                "timestamp": alert.timestamp.isoformat(),
                "severity": alert.severity.value,
                "alert_type": alert.alert_type,
                "message": alert.message,
                "error_pattern_id": alert.error_pattern_id,
                "affected_files": list(alert.affected_files),
                "error_count": alert.error_count,
                "metadata": alert.metadata,
            }
            for alert in self.alert_manager.active_alerts.values()
        ]

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an active alert."""
        if alert_id in self.alert_manager.active_alerts:
            del self.alert_manager.active_alerts[alert_id]
            logger.info(f"Alert acknowledged: {alert_id}")
            return True
        return False


# Factory functions


async def create_realtime_pipeline(
    adapter: EnhancedErrorAdapter, database: IngestionDatabase, **config_kwargs
) -> RealtimeErrorPipeline:
    """Create and configure a real-time error processing pipeline."""
    config = StreamProcessor(**config_kwargs)
    pipeline = RealtimeErrorPipeline(adapter, database, config)

    logger.info("Created real-time error processing pipeline")
    return pipeline


async def create_high_volume_pipeline(
    adapter: EnhancedErrorAdapter, database: IngestionDatabase
) -> RealtimeErrorPipeline:
    """Create a pipeline optimized for high-volume processing."""
    config = StreamProcessor(
        max_concurrent_workers=20,
        batch_size_range=(100, 2000),
        input_queue_maxsize=50000,
        processing_queue_maxsize=20000,
        adaptive_batch_sizing=True,
        enable_adaptive_processing=True,
        target_latency_ms=50,
        max_memory_usage_mb=2048,
    )

    pipeline = RealtimeErrorPipeline(adapter, database, config)
    logger.info("Created high-volume error processing pipeline")
    return pipeline
