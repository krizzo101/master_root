"""Request tracing middleware for opsvi-core."""

import logging
import time
import uuid
from typing import Any, Callable, Dict, Optional, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
import json

from opsvi_foundation.middleware import Middleware, Request, Response

logger = logging.getLogger(__name__)


@dataclass
class TraceSpan:
    """Represents a trace span."""
    
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: list = field(default_factory=list)
    status: str = "in_progress"
    
    def finish(self) -> None:
        """Finish the span."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status = "completed"
    
    def add_tag(self, key: str, value: Any) -> None:
        """Add a tag to the span."""
        self.tags[key] = value
    
    def add_log(self, message: str, level: str = "info") -> None:
        """Add a log entry to the span."""
        self.logs.append({
            "timestamp": time.time(),
            "level": level,
            "message": message
        })


class TracingMiddleware(Middleware):
    """Middleware for request tracing."""
    
    def __init__(
        self,
        name: str = "TracingMiddleware",
        trace_header: str = "X-Trace-ID",
        span_header: str = "X-Span-ID",
        parent_span_header: str = "X-Parent-Span-ID",
        sample_rate: float = 1.0,
        max_spans: int = 1000
    ):
        """Initialize tracing middleware.
        
        Args:
            name: Name of the middleware
            trace_header: Header name for trace ID
            span_header: Header name for span ID
            parent_span_header: Header name for parent span ID
            sample_rate: Sampling rate (0.0 - 1.0)
            max_spans: Maximum number of spans to keep in memory
        """
        super().__init__(name)
        self.trace_header = trace_header
        self.span_header = span_header
        self.parent_span_header = parent_span_header
        self.sample_rate = sample_rate
        self.max_spans = max_spans
        
        self._spans: Dict[str, TraceSpan] = {}
        self._traces: Dict[str, list] = {}
    
    async def process(
        self,
        request: Request,
        next_handler: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request with tracing."""
        # Check sampling
        import random
        if random.random() > self.sample_rate:
            return await next_handler(request)
        
        # Get or create trace ID
        trace_id = request.headers.get(self.trace_header)
        if not trace_id:
            trace_id = str(uuid.uuid4())
            request.headers[self.trace_header] = trace_id
        
        # Get parent span ID
        parent_span_id = request.headers.get(self.parent_span_header)
        
        # Create new span
        span_id = str(uuid.uuid4())
        span = TraceSpan(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            operation_name=f"{request.method} {request.path}",
            start_time=time.time()
        )
        
        # Add initial tags
        span.add_tag("http.method", request.method)
        span.add_tag("http.path", request.path)
        span.add_tag("component", "http")
        
        # Store span
        self._store_span(span)
        
        # Add span ID to request
        request.headers[self.span_header] = span_id
        request.metadata["trace_id"] = trace_id
        request.metadata["span_id"] = span_id
        
        try:
            # Process request
            response = await next_handler(request)
            
            # Add response tags
            span.add_tag("http.status_code", response.status)
            span.add_tag("error", response.status >= 400)
            
            # Finish span
            span.finish()
            
            # Add trace headers to response
            response.headers[self.trace_header] = trace_id
            response.headers[self.span_header] = span_id
            
            return response
            
        except Exception as e:
            # Log error
            span.add_tag("error", True)
            span.add_tag("error.message", str(e))
            span.add_log(f"Error: {str(e)}", "error")
            
            # Finish span
            span.status = "error"
            span.finish()
            
            raise
    
    def _store_span(self, span: TraceSpan) -> None:
        """Store a span."""
        # Store in spans dict
        self._spans[span.span_id] = span
        
        # Store in traces dict
        if span.trace_id not in self._traces:
            self._traces[span.trace_id] = []
        self._traces[span.trace_id].append(span)
        
        # Cleanup if too many spans
        if len(self._spans) > self.max_spans:
            # Remove oldest spans
            sorted_spans = sorted(
                self._spans.values(),
                key=lambda s: s.start_time
            )
            to_remove = len(self._spans) - self.max_spans
            
            for span in sorted_spans[:to_remove]:
                del self._spans[span.span_id]
                if span.trace_id in self._traces:
                    self._traces[span.trace_id].remove(span)
                    if not self._traces[span.trace_id]:
                        del self._traces[span.trace_id]
    
    def get_span(self, span_id: str) -> Optional[TraceSpan]:
        """Get a span by ID."""
        return self._spans.get(span_id)
    
    def get_trace(self, trace_id: str) -> list:
        """Get all spans for a trace."""
        return self._traces.get(trace_id, [])
    
    def export_traces(self) -> Dict[str, Any]:
        """Export all traces."""
        return {
            "traces": {
                trace_id: [
                    {
                        "span_id": span.span_id,
                        "parent_span_id": span.parent_span_id,
                        "operation_name": span.operation_name,
                        "start_time": span.start_time,
                        "duration": span.duration,
                        "tags": span.tags,
                        "logs": span.logs,
                        "status": span.status
                    }
                    for span in spans
                ]
                for trace_id, spans in self._traces.items()
            }
        }


class OpenTelemetryMiddleware(TracingMiddleware):
    """OpenTelemetry-compatible tracing middleware."""
    
    def __init__(
        self,
        name: str = "OpenTelemetryMiddleware",
        service_name: str = "opsvi-service",
        **kwargs
    ):
        """Initialize OpenTelemetry middleware.
        
        Args:
            name: Name of the middleware
            service_name: Service name for traces
            **kwargs: Additional arguments for TracingMiddleware
        """
        super().__init__(name, **kwargs)
        self.service_name = service_name
        
        # Try to import OpenTelemetry
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
            
            # Set up tracer
            trace.set_tracer_provider(TracerProvider())
            self.tracer = trace.get_tracer(service_name)
            
            # Add console exporter (for demo)
            span_processor = BatchSpanProcessor(ConsoleSpanExporter())
            trace.get_tracer_provider().add_span_processor(span_processor)
            
            self.otel_available = True
            logger.info("OpenTelemetry tracing initialized")
        except ImportError:
            self.otel_available = False
            logger.warning("OpenTelemetry not available, using basic tracing")
    
    async def process(
        self,
        request: Request,
        next_handler: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request with OpenTelemetry tracing."""
        if not self.otel_available:
            # Fall back to basic tracing
            return await super().process(request, next_handler)
        
        # Use OpenTelemetry tracing
        from opentelemetry import trace
        
        with self.tracer.start_as_current_span(
            f"{request.method} {request.path}",
            attributes={
                "http.method": request.method,
                "http.path": request.path,
                "http.scheme": "http",
                "service.name": self.service_name,
            }
        ) as span:
            try:
                response = await next_handler(request)
                
                # Add response attributes
                span.set_attribute("http.status_code", response.status)
                if response.status >= 400:
                    span.set_status(trace.Status(trace.StatusCode.ERROR))
                
                return response
                
            except Exception as e:
                # Record exception
                span.record_exception(e)
                span.set_status(
                    trace.Status(trace.StatusCode.ERROR, str(e))
                )
                raise


class DistributedTracingMiddleware(TracingMiddleware):
    """Middleware for distributed tracing across services."""
    
    def __init__(
        self,
        name: str = "DistributedTracingMiddleware",
        propagate_headers: bool = True,
        **kwargs
    ):
        """Initialize distributed tracing middleware.
        
        Args:
            name: Name of the middleware
            propagate_headers: Whether to propagate trace headers
            **kwargs: Additional arguments for TracingMiddleware
        """
        super().__init__(name, **kwargs)
        self.propagate_headers = propagate_headers
    
    async def process(
        self,
        request: Request,
        next_handler: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request with distributed tracing."""
        # Extract trace context from headers
        trace_context = self._extract_trace_context(request)
        
        if trace_context:
            # Continue existing trace
            request.headers[self.trace_header] = trace_context["trace_id"]
            request.headers[self.parent_span_header] = trace_context["span_id"]
        
        # Process with regular tracing
        response = await super().process(request, next_handler)
        
        # Propagate trace context if enabled
        if self.propagate_headers and trace_context:
            response.headers["X-Trace-Context"] = json.dumps({
                "trace_id": request.metadata.get("trace_id"),
                "span_id": request.metadata.get("span_id"),
                "service": self.name
            })
        
        return response
    
    def _extract_trace_context(self, request: Request) -> Optional[Dict[str, str]]:
        """Extract trace context from request headers."""
        # Check for W3C Trace Context
        traceparent = request.headers.get("traceparent")
        if traceparent:
            # Parse W3C format (simplified)
            parts = traceparent.split("-")
            if len(parts) >= 3:
                return {
                    "trace_id": parts[1],
                    "span_id": parts[2]
                }
        
        # Check for custom trace context header
        trace_context = request.headers.get("X-Trace-Context")
        if trace_context:
            try:
                return json.loads(trace_context)
            except json.JSONDecodeError:
                pass
        
        return None


__all__ = [
    "TraceSpan",
    "TracingMiddleware",
    "OpenTelemetryMiddleware",
    "DistributedTracingMiddleware",
]