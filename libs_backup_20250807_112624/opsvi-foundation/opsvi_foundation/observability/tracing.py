"""
OpenTelemetry tracing utilities.

Provides span management, trace propagation, sampling, and distributed
tracing capabilities for monitoring and debugging.
"""

from __future__ import annotations

import asyncio
import functools
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

from opsvi_foundation.patterns import ComponentError


class TracingError(ComponentError):
    """Raised when tracing operation fails."""


class SamplingStrategy(Enum):
    """Tracing sampling strategies."""

    ALWAYS = "always"
    NEVER = "never"
    PROBABILISTIC = "probabilistic"
    RATE_LIMITING = "rate_limiting"
    DYNAMIC = "dynamic"


@dataclass
class TracingConfig:
    """Configuration for tracing."""

    service_name: str = "opsvi-service"
    service_version: str = "1.0.0"
    environment: str = "development"
    sampling_rate: float = 1.0  # 100% sampling
    sampling_strategy: SamplingStrategy = SamplingStrategy.ALWAYS
    max_attributes: int = 32
    max_events: int = 128
    max_links: int = 32


T = TypeVar("T")


class TraceContext:
    """Trace context for propagating trace information."""

    def __init__(self, trace_id: str, span_id: str, sampled: bool = True):
        """
        Initialize trace context.

        Args:
            trace_id: Trace ID
            span_id: Span ID
            sampled: Whether trace is sampled
        """
        self.trace_id = trace_id
        self.span_id = span_id
        self.sampled = sampled

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for propagation."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "sampled": str(self.sampled).lower(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> TraceContext:
        """Create from dictionary."""
        return cls(
            trace_id=data.get("trace_id", ""),
            span_id=data.get("span_id", ""),
            sampled=data.get("sampled", "true").lower() == "true",
        )


class Span:
    """OpenTelemetry span implementation."""

    def __init__(self, name: str, context: TraceContext | None = None):
        """
        Initialize span.

        Args:
            name: Span name
            context: Trace context
        """
        self.name = name
        self.context = context or self._generate_context()
        self.start_time = None
        self.end_time = None
        self.attributes: dict[str, Any] = {}
        self.events: list[dict[str, Any]] = []
        self.links: list[dict[str, Any]] = []
        self.status = "UNSET"
        self.status_message = ""
        self._is_active = False

    def _generate_context(self) -> TraceContext:
        """Generate new trace context."""
        import uuid

        trace_id = str(uuid.uuid4()).replace("-", "")
        span_id = str(uuid.uuid4()).replace("-", "")[:16]
        return TraceContext(trace_id, span_id)

    def start(self) -> None:
        """Start the span."""
        import time

        self.start_time = time.time()
        self._is_active = True

    def end(self) -> None:
        """End the span."""
        import time

        self.end_time = time.time()
        self._is_active = False

    def set_attribute(self, key: str, value: Any) -> None:
        """
        Set span attribute.

        Args:
            key: Attribute key
            value: Attribute value
        """
        if len(self.attributes) < 32:  # Max attributes limit
            self.attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """
        Add event to span.

        Args:
            name: Event name
            attributes: Event attributes
        """
        import time

        if len(self.events) < 128:  # Max events limit
            event = {
                "name": name,
                "timestamp": time.time(),
                "attributes": attributes or {},
            }
            self.events.append(event)

    def set_status(self, status: str, message: str = "") -> None:
        """
        Set span status.

        Args:
            status: Status (OK, ERROR, UNSET)
            message: Status message
        """
        self.status = status
        self.status_message = message

    def add_link(
        self,
        trace_id: str,
        span_id: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """
        Add link to span.

        Args:
            trace_id: Linked trace ID
            span_id: Linked span ID
            attributes: Link attributes
        """
        if len(self.links) < 32:  # Max links limit
            link = {
                "trace_id": trace_id,
                "span_id": span_id,
                "attributes": attributes or {},
            }
            self.links.append(link)

    @property
    def duration(self) -> float | None:
        """Get span duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def is_active(self) -> bool:
        """Check if span is active."""
        return self._is_active


class Tracer:
    """Main tracer class for creating and managing spans."""

    def __init__(self, config: TracingConfig):
        """
        Initialize tracer.

        Args:
            config: Tracing configuration
        """
        self.config = config
        self.active_spans: dict[str, Span] = {}
        self._span_counter = 0

    def start_span(self, name: str, context: TraceContext | None = None) -> Span:
        """
        Start a new span.

        Args:
            name: Span name
            context: Trace context

        Returns:
            Started span
        """
        span = Span(name, context)
        span.start()

        # Store active span
        span_id = f"{span.context.trace_id}:{span.context.span_id}"
        self.active_spans[span_id] = span

        return span

    def end_span(self, span: Span) -> None:
        """
        End a span.

        Args:
            span: Span to end
        """
        span.end()

        # Remove from active spans
        span_id = f"{span.context.trace_id}:{span.context.span_id}"
        self.active_spans.pop(span_id, None)

    def get_current_span(self) -> Span | None:
        """Get current active span."""
        # In a real implementation, this would use contextvars
        # For now, return the most recently created span
        if self.active_spans:
            return list(self.active_spans.values())[-1]
        return None

    def inject_context(self, span: Span, carrier: dict[str, str]) -> None:
        """
        Inject trace context into carrier.

        Args:
            span: Span to inject
            carrier: Carrier dictionary
        """
        carrier.update(span.context.to_dict())

    def extract_context(self, carrier: dict[str, str]) -> TraceContext | None:
        """
        Extract trace context from carrier.

        Args:
            carrier: Carrier dictionary

        Returns:
            Extracted trace context
        """
        if "trace_id" in carrier and "span_id" in carrier:
            return TraceContext.from_dict(carrier)
        return None

    def should_sample(self, trace_id: str) -> bool:
        """
        Determine if trace should be sampled.

        Args:
            trace_id: Trace ID

        Returns:
            True if should sample, False otherwise
        """
        if self.config.sampling_strategy == SamplingStrategy.ALWAYS:
            return True
        if self.config.sampling_strategy == SamplingStrategy.NEVER:
            return False
        if self.config.sampling_strategy == SamplingStrategy.PROBABILISTIC:
            import random

            return random.random() < self.config.sampling_rate
        return True


class TraceManager:
    """Manager for multiple tracers."""

    def __init__(self):
        """Initialize trace manager."""
        self.tracers: dict[str, Tracer] = {}
        self.default_tracer: Tracer | None = None

    def add_tracer(self, name: str, config: TracingConfig) -> Tracer:
        """
        Add tracer.

        Args:
            name: Tracer name
            config: Tracer configuration

        Returns:
            Created tracer
        """
        tracer = Tracer(config)
        self.tracers[name] = tracer

        if self.default_tracer is None:
            self.default_tracer = tracer

        return tracer

    def get_tracer(self, name: str) -> Tracer | None:
        """Get tracer by name."""
        return self.tracers.get(name)

    def get_default_tracer(self) -> Tracer | None:
        """Get default tracer."""
        return self.default_tracer

    def set_default_tracer(self, name: str) -> None:
        """Set default tracer."""
        if name in self.tracers:
            self.default_tracer = self.tracers[name]


# Global trace manager
trace_manager = TraceManager()


@contextmanager
def trace_span(name: str, tracer_name: str | None = None):
    """
    Context manager for tracing spans.

    Args:
        name: Span name
        tracer_name: Tracer name (uses default if None)
    """
    tracer = (
        trace_manager.get_tracer(tracer_name)
        if tracer_name
        else trace_manager.get_default_tracer()
    )
    if not tracer:
        yield None
        return

    span = tracer.start_span(name)
    try:
        yield span
    finally:
        tracer.end_span(span)


@asynccontextmanager
async def async_trace_span(name: str, tracer_name: str | None = None):
    """
    Async context manager for tracing spans.

    Args:
        name: Span name
        tracer_name: Tracer name (uses default if None)
    """
    tracer = (
        trace_manager.get_tracer(tracer_name)
        if tracer_name
        else trace_manager.get_default_tracer()
    )
    if not tracer:
        yield None
        return

    span = tracer.start_span(name)
    try:
        yield span
    finally:
        tracer.end_span(span)


def trace_function(name: str | None = None, tracer_name: str | None = None):
    """
    Decorator for tracing functions.

    Args:
        name: Span name (uses function name if None)
        tracer_name: Tracer name (uses default if None)
    """

    def decorator(func):
        span_name = name or f"{func.__module__}.{func.__name__}"

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                async with async_trace_span(span_name, tracer_name) as span:
                    if span:
                        span.set_attribute("function.name", func.__name__)
                        span.set_attribute("function.module", func.__module__)
                    return await func(*args, **kwargs)

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with trace_span(span_name, tracer_name) as span:
                if span:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                return func(*args, **kwargs)

        return sync_wrapper

    return decorator


def inject_trace_context(
    carrier: dict[str, str],
    tracer_name: str | None = None,
) -> None:
    """
    Inject current trace context into carrier.

    Args:
        carrier: Carrier dictionary
        tracer_name: Tracer name (uses default if None)
    """
    tracer = (
        trace_manager.get_tracer(tracer_name)
        if tracer_name
        else trace_manager.get_default_tracer()
    )
    if not tracer:
        return

    current_span = tracer.get_current_span()
    if current_span:
        tracer.inject_context(current_span, carrier)


def extract_trace_context(
    carrier: dict[str, str],
    tracer_name: str | None = None,
) -> TraceContext | None:
    """
    Extract trace context from carrier.

    Args:
        carrier: Carrier dictionary
        tracer_name: Tracer name (uses default if None)

    Returns:
        Extracted trace context
    """
    tracer = (
        trace_manager.get_tracer(tracer_name)
        if tracer_name
        else trace_manager.get_default_tracer()
    )
    if not tracer:
        return None

    return tracer.extract_context(carrier)
