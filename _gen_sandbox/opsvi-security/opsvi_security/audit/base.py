"""Audit base for opsvi-security.

Provides a simple, extensible Auditor interface and a default in-memory
implementation suitable for testing or low-volume auditing. Designed to be
extended with other sinks (files, databases, remote collectors) as needed.
"""
from __future__ import annotations

import asyncio
import datetime
from typing import List, Protocol, runtime_checkable


@runtime_checkable
class AuditSink(Protocol):
    """Protocol for audit sinks.

    Implementations should handle storing or forwarding audit entries.
    """

    async def write(self, timestamp: datetime.datetime, event: str) -> None:
        """Write an audit entry.

        Args:
            timestamp: UTC timestamp of the event.
            event: Human-readable event description.
        """


class Auditor:
    """Asynchronous auditor that fans out events to configured sinks.

    By default it uses an in-memory sink that retains recent events. This
    class is safe to call from multiple coroutines.
    """

    def __init__(self, sinks: List[AuditSink] | None = None) -> None:
        self._sinks: List[AuditSink] = sinks[:] if sinks else [InMemorySink()]
        self._lock = asyncio.Lock()

    async def log(self, event: str) -> None:
        """Log an event to all configured sinks.

        The method timestamps the event with UTC now and writes to each sink
        concurrently. Exceptions from individual sinks are collected and
        raised as an aggregated RuntimeError to avoid silent failures.
        """
        timestamp = datetime.datetime.utcnow()
        async with self._lock:
            # write to all sinks concurrently
            coros = [sink.write(timestamp, event) for sink in self._sinks]
            results = await asyncio.gather(*coros, return_exceptions=True)
        errors: List[Exception] = []
        for r in results:
            if isinstance(r, Exception):
                errors.append(r)
        if errors:
            # aggregate into a single error
            msg = f"{len(errors)} audit sink(s) failed: " + ", ".join(
                type(e).__name__ for e in errors
            )
            raise RuntimeError(msg)

    async def add_sink(self, sink: AuditSink) -> None:
        """Add a new audit sink at runtime."""
        async with self._lock:
            self._sinks.append(sink)

    async def clear_sinks(self) -> None:
        """Remove all configured sinks."""
        async with self._lock:
            self._sinks.clear()


class InMemorySink:
    """Simple in-memory audit sink with optional retention.

    Retains a bounded list of (timestamp, event) tuples. Thread/async safe.
    """

    def __init__(self, max_entries: int = 1000) -> None:
        if max_entries <= 0:
            raise ValueError("max_entries must be positive")
        self._max = max_entries
        self._entries: List[tuple[datetime.datetime, str]] = []
        self._lock = asyncio.Lock()

    async def write(self, timestamp: datetime.datetime, event: str) -> None:
        async with self._lock:
            self._entries.append((timestamp, event))
            # enforce retention
            if len(self._entries) > self._max:
                # drop oldest
                excess = len(self._entries) - self._max
                if excess >= len(self._entries):
                    self._entries = []
                else:
                    self._entries = self._entries[excess:]

    async def recent(self, limit: int = 100) -> List[tuple[datetime.datetime, str]]:
        """Return up to `limit` most recent entries (most recent last)."""
        if limit <= 0:
            return []
        async with self._lock:
            return self._entries[-limit:]

    async def clear(self) -> None:
        """Clear stored entries."""
        async with self._lock:
            self._entries.clear()
