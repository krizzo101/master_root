"""Tracing base for opsvi-monitoring.

Provides an asynchronous-friendly Tracer abstraction and a simple in-memory
Span implementation suitable for testing and local use. The API is kept
minimal to allow later integration with OpenTelemetry or other tracing
libraries.
"""
from __future__ import annotations

import asyncio
import contextlib
import contextvars
import time
from typing import Any, Dict, Optional

_current_span_var: contextvars.ContextVar[Optional["Span"]] = contextvars.ContextVar(
    "_current_span_var", default=None
)


class Span:
    """A lightweight span object representing a unit of work.

    This span records a name, start/finish timestamps, attributes and an
    optional parent span. It can be used as an async context manager.
    """

    def __init__(self, name: str, parent: Optional["Span"] = None) -> None:
        self.name = name
        self.parent = parent
        self.attributes: Dict[str, Any] = {}
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.children: list["Span"] = []

    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the span."""
        self.attributes[key] = value

    def start(self) -> "Span":
        """Mark the span as started and return self."""
        self.start_time = time.time()
        return self

    def finish(self) -> None:
        """Mark the span as finished."""
        self.end_time = time.time()

    def duration(self) -> Optional[float]:
        """Return the span duration in seconds, or None if not finished."""
        if self.start_time is None:
            return None
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    async def __aenter__(self) -> "Span":
        self.start()
        token = _current_span_var.set(self)
        # store the token so __aexit__ can restore
        setattr(self, "_cv_token", token)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            if exc is not None:
                # Record minimal error info as attributes
                self.set_attribute("error.type", str(exc_type))
                self.set_attribute("error.message", str(exc))
            self.finish()
        finally:
            # restore previous current span
            token = getattr(self, "_cv_token", None)
            if token is not None:
                _current_span_var.reset(token)


class Tracer:
    """Minimal tracer abstraction.

    Use start_span to create and enter spans. Spans are context-aware so
    nested async tasks will preserve the current span via contextvars.
    """

    def start_span(self, name: str) -> Span:
        """Create a new Span with the current span as parent.

        Returned Span can be used as an async context manager:

            async with tracer.start_span("op") as span:
                ...
        """
        parent = _current_span_var.get()
        span = Span(name=name, parent=parent)
        if parent is not None:
            parent.children.append(span)
        return span


# Convenience helpers
@contextlib.asynccontextmanager
async def start_span(tracer: Tracer, name: str):
    """Async context manager wrapper for tracer.start_span.

    Example:
        async with start_span(tracer, "work") as span:
            ...
    """
    span = tracer.start_span(name)
    await span.__aenter__()
    try:
        yield span
    finally:
        await span.__aexit__(None, None, None)


def current_span() -> Optional[Span]:
    """Return the current active span, if any."""
    return _current_span_var.get()
