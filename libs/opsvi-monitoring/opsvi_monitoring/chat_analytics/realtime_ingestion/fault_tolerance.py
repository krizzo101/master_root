#!/usr/bin/env python3
"""
Fault tolerance and recovery mechanisms for real-time chat log ingestion.
Handles failures, retries, circuit breakers, and persistence.
"""

import asyncio
import json
import logging
import sqlite3
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import aiofiles

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryConfig:
    """Configuration for retry mechanisms."""

    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    recovery_timeout_seconds: int = 60
    half_open_max_calls: int = 3
    success_threshold: int = 2


@dataclass
class FailedOperation:
    """Represents a failed operation that needs retry."""

    operation_id: str
    operation_type: str
    payload: Dict[str, Any]
    error_message: str
    attempt_count: int
    last_attempt: str
    next_retry: str
    created_at: str


class ExponentialBackoff:
    """Implements exponential backoff with jitter."""

    def __init__(self, config: RetryConfig):
        self.config = config

    def get_delay(self, attempt: int) -> float:
        """Get delay for specific attempt number."""
        delay = min(
            self.config.base_delay_seconds * (self.config.exponential_base**attempt),
            self.config.max_delay_seconds,
        )

        if self.config.jitter:
            import random

            delay *= 0.5 + random.random() * 0.5  # Add 0-50% jitter

        return delay

    async def sleep_for_attempt(self, attempt: int):
        """Sleep for the appropriate delay."""
        delay = self.get_delay(attempt)
        await asyncio.sleep(delay)


class CircuitBreaker:
    """Circuit breaker for protecting against cascading failures."""

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                logger.info(f"Circuit breaker {self.name} moved to HALF_OPEN")
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN")

        try:
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls += 1
                if self.half_open_calls > self.config.half_open_max_calls:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker {self.name} exceeded half-open calls"
                    )

            result = await func(*args, **kwargs)
            self._record_success()
            return result

        except Exception as e:
            self._record_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset."""
        if self.last_failure_time is None:
            return True

        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.recovery_timeout_seconds

    def _record_success(self):
        """Record successful operation."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(f"Circuit breaker {self.name} moved to CLOSED")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)

    def _record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker {self.name} moved to OPEN after {self.failure_count} failures"
                )
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.half_open_calls = 0
            logger.warning(f"Circuit breaker {self.name} moved back to OPEN")

    def get_status(self) -> Dict:
        """Get circuit breaker status."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "half_open_calls": self.half_open_calls,
            "last_failure_time": self.last_failure_time,
        }


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""

    pass


class FailureStore:
    """Persists failed operations for retry."""

    def __init__(self, db_path: str = "/tmp/chat_ingestion_failures.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize failure store database."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS failed_operations (
                operation_id TEXT PRIMARY KEY,
                operation_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                error_message TEXT NOT NULL,
                attempt_count INTEGER NOT NULL DEFAULT 1,
                last_attempt TEXT NOT NULL,
                next_retry TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """
        )
        conn.commit()
        conn.close()

    def store_failure(self, failure: FailedOperation):
        """Store a failed operation."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT OR REPLACE INTO failed_operations
            (operation_id, operation_type, payload, error_message,
             attempt_count, last_attempt, next_retry, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                failure.operation_id,
                failure.operation_type,
                json.dumps(failure.payload),
                failure.error_message,
                failure.attempt_count,
                failure.last_attempt,
                failure.next_retry,
                failure.created_at,
            ),
        )
        conn.commit()
        conn.close()

    def get_ready_for_retry(self, limit: int = 100) -> List[FailedOperation]:
        """Get operations ready for retry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """
            SELECT operation_id, operation_type, payload, error_message,
                   attempt_count, last_attempt, next_retry, created_at
            FROM failed_operations
            WHERE next_retry <= ?
            ORDER BY created_at ASC
            LIMIT ?
        """,
            (datetime.now().isoformat(), limit),
        )

        failures = []
        for row in cursor.fetchall():
            failures.append(
                FailedOperation(
                    operation_id=row[0],
                    operation_type=row[1],
                    payload=json.loads(row[2]),
                    error_message=row[3],
                    attempt_count=row[4],
                    last_attempt=row[5],
                    next_retry=row[6],
                    created_at=row[7],
                )
            )

        conn.close()
        return failures

    def remove_success(self, operation_id: str):
        """Remove successfully retried operation."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "DELETE FROM failed_operations WHERE operation_id = ?", (operation_id,)
        )
        conn.commit()
        conn.close()

    def update_failure(
        self, operation_id: str, attempt_count: int, next_retry: str, error_message: str
    ):
        """Update failure with new retry information."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            UPDATE failed_operations
            SET attempt_count = ?, next_retry = ?, error_message = ?, last_attempt = ?
            WHERE operation_id = ?
        """,
            (
                attempt_count,
                next_retry,
                error_message,
                datetime.now().isoformat(),
                operation_id,
            ),
        )
        conn.commit()
        conn.close()

    def get_statistics(self) -> Dict:
        """Get failure store statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """
            SELECT
                COUNT(*) as total_failures,
                COUNT(CASE WHEN next_retry <= ? THEN 1 END) as ready_for_retry,
                AVG(attempt_count) as avg_attempts,
                operation_type,
                COUNT(*) as type_count
            FROM failed_operations
            GROUP BY operation_type
        """,
            (datetime.now().isoformat(),),
        )

        stats = {"total_failures": 0, "ready_for_retry": 0, "by_type": {}}
        for row in cursor.fetchall():
            if row[3]:  # operation_type is not None
                stats["by_type"][row[3]] = row[4]
            else:
                stats["total_failures"] = row[0]
                stats["ready_for_retry"] = row[1]

        conn.close()
        return stats


class RetryManager:
    """Manages retry logic for failed operations."""

    def __init__(
        self,
        failure_store: FailureStore,
        retry_config: RetryConfig = None,
        circuit_breakers: Dict[str, CircuitBreaker] = None,
    ):
        self.failure_store = failure_store
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breakers = circuit_breakers or {}
        self.backoff = ExponentialBackoff(self.retry_config)
        self.running = False

    async def execute_with_retry(
        self,
        operation_id: str,
        operation_type: str,
        func: Callable,
        payload: Dict[str, Any],
        circuit_breaker_name: Optional[str] = None,
    ) -> Any:
        """Execute operation with retry logic."""
        circuit_breaker = (
            self.circuit_breakers.get(circuit_breaker_name)
            if circuit_breaker_name
            else None
        )

        for attempt in range(self.retry_config.max_attempts):
            try:
                if circuit_breaker:
                    result = await circuit_breaker.call(func, **payload)
                else:
                    result = await func(**payload)

                # Success - remove any stored failure
                self.failure_store.remove_success(operation_id)
                return result

            except CircuitBreakerOpenError:
                # Don't retry immediately if circuit breaker is open
                raise
            except Exception as e:
                is_last_attempt = attempt == self.retry_config.max_attempts - 1

                if is_last_attempt:
                    # Store for later retry
                    await self._store_failure(
                        operation_id, operation_type, payload, str(e), attempt + 1
                    )
                    raise
                else:
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {operation_type} {operation_id}: {e}"
                    )
                    await self.backoff.sleep_for_attempt(attempt)

    async def _store_failure(
        self,
        operation_id: str,
        operation_type: str,
        payload: Dict[str, Any],
        error: str,
        attempts: int,
    ):
        """Store failed operation for later retry."""
        next_retry_delay = self.backoff.get_delay(attempts)
        next_retry = (datetime.now() + timedelta(seconds=next_retry_delay)).isoformat()

        failure = FailedOperation(
            operation_id=operation_id,
            operation_type=operation_type,
            payload=payload,
            error_message=error,
            attempt_count=attempts,
            last_attempt=datetime.now().isoformat(),
            next_retry=next_retry,
            created_at=datetime.now().isoformat(),
        )

        self.failure_store.store_failure(failure)
        logger.error(
            f"Stored failed operation {operation_id} for retry at {next_retry}"
        )

    async def start_retry_worker(self):
        """Start background worker to process failed operations."""
        logger.info("Starting retry worker")
        self.running = True

        while self.running:
            try:
                failures = self.failure_store.get_ready_for_retry()

                for failure in failures:
                    try:
                        await self._retry_failed_operation(failure)
                    except Exception as e:
                        logger.error(
                            f"Error retrying operation {failure.operation_id}: {e}"
                        )

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in retry worker: {e}")
                await asyncio.sleep(60)  # Back off on worker errors

    async def _retry_failed_operation(self, failure: FailedOperation):
        """Retry a single failed operation."""
        operation_type = failure.operation_type

        # Map operation types to retry functions
        retry_functions = {
            "file_processing": self._retry_file_processing,
            "database_write": self._retry_database_write,
            "correlation": self._retry_correlation,
        }

        retry_func = retry_functions.get(operation_type)
        if not retry_func:
            logger.error(f"No retry function for operation type {operation_type}")
            return

        try:
            await retry_func(failure.payload)

            # Success - remove from failure store
            self.failure_store.remove_success(failure.operation_id)
            logger.info(f"Successfully retried operation {failure.operation_id}")

        except Exception as e:
            # Update failure for next retry
            next_attempt = failure.attempt_count + 1
            if (
                next_attempt <= self.retry_config.max_attempts * 2
            ):  # Allow more retries for background processing
                next_retry_delay = self.backoff.get_delay(next_attempt)
                next_retry = (
                    datetime.now() + timedelta(seconds=next_retry_delay)
                ).isoformat()

                self.failure_store.update_failure(
                    failure.operation_id, next_attempt, next_retry, str(e)
                )
                logger.warning(
                    f"Retry failed for {failure.operation_id}, will retry at {next_retry}"
                )
            else:
                logger.error(
                    f"Giving up on operation {failure.operation_id} after {next_attempt} attempts"
                )

    async def _retry_file_processing(self, payload: Dict[str, Any]):
        """Retry file processing operation."""
        # Import here to avoid circular dependencies
        from opsvi_monitoring.chat_analytics.realtime_ingestion.ingestion_pipeline import (
            RealTimeIngestionPipeline,
        )

        pipeline = RealTimeIngestionPipeline()
        await pipeline.process_file(payload)

    async def _retry_database_write(self, payload: Dict[str, Any]):
        """Retry database write operation."""
        # Implement database retry logic
        pass

    async def _retry_correlation(self, payload: Dict[str, Any]):
        """Retry correlation operation."""
        # Implement correlation retry logic
        pass

    def stop(self):
        """Stop retry worker."""
        self.running = False


class FaultToleranceManager:
    """Main fault tolerance coordinator."""

    def __init__(self):
        self.failure_store = FailureStore()
        self.retry_config = RetryConfig()
        self.circuit_breakers = {
            "database": CircuitBreaker("database", CircuitBreakerConfig()),
            "correlation": CircuitBreaker("correlation", CircuitBreakerConfig()),
            "file_processing": CircuitBreaker(
                "file_processing", CircuitBreakerConfig()
            ),
        }
        self.retry_manager = RetryManager(
            self.failure_store, self.retry_config, self.circuit_breakers
        )

    async def start(self):
        """Start fault tolerance services."""
        logger.info("Starting fault tolerance manager")
        await self.retry_manager.start_retry_worker()

    def stop(self):
        """Stop fault tolerance services."""
        logger.info("Stopping fault tolerance manager")
        self.retry_manager.stop()

    async def execute_with_protection(
        self,
        operation_id: str,
        operation_type: str,
        func: Callable,
        payload: Dict[str, Any],
        circuit_breaker_name: str = None,
    ) -> Any:
        """Execute operation with full fault tolerance protection."""
        return await self.retry_manager.execute_with_retry(
            operation_id, operation_type, func, payload, circuit_breaker_name
        )

    def get_status(self) -> Dict:
        """Get comprehensive fault tolerance status."""
        return {
            "circuit_breakers": {
                name: cb.get_status() for name, cb in self.circuit_breakers.items()
            },
            "failure_store": self.failure_store.get_statistics(),
            "retry_config": asdict(self.retry_config),
        }


# Health check utilities
async def check_database_health(db_adapter) -> bool:
    """Check if database is healthy."""
    try:
        # Simple health check query
        with db_adapter.pg_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def check_correlator_health(correlator) -> bool:
    """Check if correlator is healthy."""
    try:
        # Try to process a simple message
        test_message = {
            "id": "health_check",
            "content": "test",
            "timestamp": datetime.now().isoformat(),
            "tool_calls": [],
        }
        correlator.process_message(test_message, "health_check_session")
        return True
    except Exception as e:
        logger.error(f"Correlator health check failed: {e}")
        return False
