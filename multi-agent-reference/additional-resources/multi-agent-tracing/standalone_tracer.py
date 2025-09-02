"""
Standalone Tracer Utility for Agent Operations

This module provides a tracing system built on OpenTelemetry for agent operations,
allowing detailed monitoring of agent performance, request flow, and system behavior.
"""

import functools
import inspect
import logging
import os
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# Optional Jaeger exporter if installed
try:
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter

    JAEGER_AVAILABLE = True
except ImportError:
    JAEGER_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variable for generic function decorators
F = TypeVar("F", bound=Callable[..., Any])


class AgentTracer:
    """
    Tracer utility for monitoring and analyzing agent operations.

    This class provides a wrapper around OpenTelemetry tracing with convenience
    methods for agent-specific tracing needs.
    """

    def __init__(
        self,
        service_name: str = "agent-system",
        enable_console_export: bool = False,
        enable_otlp_export: bool = False,
        otlp_endpoint: str = "localhost:4317",
        enable_jaeger_export: bool = False,
        jaeger_endpoint: str = "localhost:6831",
        sampling_ratio: float = 1.0,
        attributes: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the agent tracer.

        Args:
            service_name: Name of the service for trace identification
            enable_console_export: Whether to export traces to console
            enable_otlp_export: Whether to export traces to an OTLP endpoint
            otlp_endpoint: OTLP endpoint for trace export
            enable_jaeger_export: Whether to export traces to Jaeger
            jaeger_endpoint: Jaeger endpoint for trace export
            sampling_ratio: Ratio of requests to sample (0.0-1.0)
            attributes: Additional resource attributes to include in all spans
        """
        self._service_name = service_name

        # Create resource with service information and additional attributes
        resource_attributes = {
            "service.name": service_name,
            "service.version": os.environ.get("SERVICE_VERSION", "0.1.0"),
            "deployment.environment": os.environ.get("DEPLOYMENT_ENV", "development"),
        }

        if attributes:
            resource_attributes.update(attributes)

        resource = Resource.create(resource_attributes)

        # Configure trace provider with sampling
        sampler = TraceIdRatioBased(sampling_ratio)
        provider = TracerProvider(resource=resource, sampler=sampler)

        # Set up exporters
        if enable_console_export:
            console_exporter = ConsoleSpanExporter()
            console_processor = BatchSpanProcessor(console_exporter)
            provider.add_span_processor(console_processor)
            logger.info(f"Console trace export enabled for {service_name}")

        if enable_otlp_export:
            try:
                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                otlp_processor = BatchSpanProcessor(otlp_exporter)
                provider.add_span_processor(otlp_processor)
                logger.info(f"OTLP trace export enabled to {otlp_endpoint}")
            except Exception as e:
                logger.error(f"Failed to initialize OTLP exporter: {e}")

        if enable_jaeger_export and JAEGER_AVAILABLE:
            try:
                jaeger_exporter = JaegerExporter(
                    agent_host_name=jaeger_endpoint.split(":")[0],
                    agent_port=int(jaeger_endpoint.split(":")[1]),
                )
                jaeger_processor = BatchSpanProcessor(jaeger_exporter)
                provider.add_span_processor(jaeger_processor)
                logger.info(f"Jaeger trace export enabled to {jaeger_endpoint}")
            except Exception as e:
                logger.error(f"Failed to initialize Jaeger exporter: {e}")

        # Set the global trace provider
        trace.set_tracer_provider(provider)

        # Create a tracer for the service
        self._tracer = trace.get_tracer(service_name)

        # Propagator for distributed tracing context
        self._propagator = TraceContextTextMapPropagator()

        logger.info(f"Agent tracer initialized for service: {service_name}")

    def get_current_span(self) -> trace.Span:
        """
        Get the current active span.

        Returns:
            The current span or a no-op span if none is active
        """
        return trace.get_current_span()

    @contextmanager
    def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: Optional[trace.SpanKind] = None,
    ) -> trace.Span:
        """
        Start a new span as a context manager.

        Args:
            name: Name of the span
            attributes: Initial span attributes
            kind: Kind of span (client, server, internal, etc.)

        Yields:
            The created span
        """
        span = self._tracer.start_span(
            name=name, attributes=attributes, kind=kind or trace.SpanKind.INTERNAL
        )

        with trace.use_span(span, end_on_exit=True):
            yield span

    @contextmanager
    def start_as_current_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: Optional[trace.SpanKind] = None,
        links: Optional[List[trace.Link]] = None,
    ) -> trace.Span:
        """
        Start a new span as the current active span within a context manager.

        Args:
            name: Name of the span
            attributes: Initial span attributes
            kind: Kind of span (client, server, internal, etc.)
            links: Optional links to other spans

        Yields:
            The created span
        """
        with self._tracer.start_as_current_span(
            name=name,
            attributes=attributes,
            kind=kind or trace.SpanKind.INTERNAL,
            links=links,
        ) as span:
            yield span


def configure_tracing(
    service_name: str,
    exporter_type: str = "console",
    endpoint: Optional[str] = None,
    sampling_ratio: float = 1.0,
) -> AgentTracer:
    """
    Configure tracing for the application.

    Args:
        service_name: Name of the service
        exporter_type: Type of exporter (console, otlp, jaeger)
        endpoint: Exporter endpoint
        sampling_ratio: Sampling ratio (0.0-1.0)

    Returns:
        Configured AgentTracer instance
    """
    # Default configuration
    config = {
        "service_name": service_name,
        "enable_console_export": False,
        "enable_otlp_export": False,
        "enable_jaeger_export": False,
        "sampling_ratio": sampling_ratio,
    }

    # Configure based on exporter type
    if exporter_type == "console":
        config["enable_console_export"] = True
    elif exporter_type == "otlp":
        config["enable_otlp_export"] = True
        if endpoint:
            config["otlp_endpoint"] = endpoint
    elif exporter_type == "jaeger":
        config["enable_jaeger_export"] = True
        if endpoint:
            config["jaeger_endpoint"] = endpoint
    else:
        logger.warning(f"Unknown exporter type: {exporter_type}, defaulting to console")
        config["enable_console_export"] = True

    # Create the tracer
    return AgentTracer(**config)


# Main test if run directly
if __name__ == "__main__":
    # Test the tracer
    print("Testing standalone tracer...")

    # Configure a tracer
    tracer = configure_tracing(
        service_name="standalone-test", exporter_type="console", sampling_ratio=1.0
    )

    # Create a span
    with tracer.start_as_current_span("test-operation") as span:
        span.set_attribute("test.key", "test-value")

        # Create a nested span
        with tracer.start_as_current_span("test-sub-operation") as sub_span:
            sub_span.set_attribute("sub.key", "sub-value")

            # Add an event
            sub_span.add_event("test-event", {"event.key": "event-value"})

            # Simulate some work
            time.sleep(0.1)

    print("Tracing test completed successfully!")
