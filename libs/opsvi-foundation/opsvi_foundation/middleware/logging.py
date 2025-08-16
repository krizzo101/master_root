"""Logging middleware for opsvi-foundation."""

import logging
import time
from typing import Any, Callable, Dict, Optional, Awaitable
import json

from .base import Middleware, Request, Response

logger = logging.getLogger(__name__)


class LoggingMiddleware(Middleware):
    """Middleware for logging requests and responses."""
    
    def __init__(
        self,
        name: str = "LoggingMiddleware",
        log_level: int = logging.INFO,
        log_body: bool = False,
        log_headers: bool = True,
        max_body_length: int = 1000,
        exclude_paths: Optional[list] = None
    ):
        """Initialize logging middleware.
        
        Args:
            name: Name of the middleware
            log_level: Logging level to use
            log_body: Whether to log request/response bodies
            log_headers: Whether to log headers
            max_body_length: Maximum body length to log
            exclude_paths: List of paths to exclude from logging
        """
        super().__init__(name)
        self.log_level = log_level
        self.log_body = log_body
        self.log_headers = log_headers
        self.max_body_length = max_body_length
        self.exclude_paths = exclude_paths or []
    
    async def process(
        self,
        request: Request,
        next_handler: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request with logging."""
        # Check if path should be excluded
        if request.path in self.exclude_paths:
            return await next_handler(request)
        
        start_time = time.time()
        request_id = request.metadata.get("request_id", "unknown")
        
        # Log request
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.path,
        }
        
        if self.log_headers:
            log_data["headers"] = self._sanitize_headers(request.headers)
        
        if self.log_body and request.body:
            log_data["body"] = self._truncate_body(request.body)
        
        logger.log(self.log_level, f"Request: {json.dumps(log_data)}")
        
        try:
            # Process request
            response = await next_handler(request)
            
            # Log response
            duration = time.time() - start_time
            response_data = {
                "request_id": request_id,
                "status": response.status,
                "duration_ms": round(duration * 1000, 2),
            }
            
            if self.log_headers:
                response_data["headers"] = self._sanitize_headers(response.headers)
            
            if self.log_body and response.body:
                response_data["body"] = self._truncate_body(response.body)
            
            logger.log(self.log_level, f"Response: {json.dumps(response_data)}")
            
            # Update metrics
            self._metrics["requests_processed"] += 1
            self._metrics["total_time"] += duration
            
            return response
            
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            error_data = {
                "request_id": request_id,
                "error": str(e),
                "duration_ms": round(duration * 1000, 2),
            }
            
            logger.error(f"Request failed: {json.dumps(error_data)}")
            
            # Update metrics
            self._metrics["errors"] += 1
            self._metrics["total_time"] += duration
            
            raise
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize headers to remove sensitive information."""
        sanitized = {}
        sensitive_keys = ["authorization", "api-key", "token", "password", "secret"]
        
        for key, value in headers.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _truncate_body(self, body: Any) -> Any:
        """Truncate body if it's too long."""
        if isinstance(body, str):
            if len(body) > self.max_body_length:
                return body[:self.max_body_length] + "... (truncated)"
            return body
        elif isinstance(body, (dict, list)):
            body_str = json.dumps(body, default=str)
            if len(body_str) > self.max_body_length:
                return body_str[:self.max_body_length] + "... (truncated)"
            return body
        else:
            return str(body)[:self.max_body_length]


class RequestTracingMiddleware(Middleware):
    """Middleware for tracing requests with correlation IDs."""
    
    def __init__(
        self,
        name: str = "RequestTracingMiddleware",
        header_name: str = "X-Request-ID",
        generate_if_missing: bool = True
    ):
        """Initialize request tracing middleware.
        
        Args:
            name: Name of the middleware
            header_name: Header name for request ID
            generate_if_missing: Whether to generate ID if missing
        """
        super().__init__(name)
        self.header_name = header_name
        self.generate_if_missing = generate_if_missing
    
    async def process(
        self,
        request: Request,
        next_handler: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request with tracing."""
        # Get or generate request ID
        request_id = request.headers.get(self.header_name)
        
        if not request_id and self.generate_if_missing:
            import uuid
            request_id = str(uuid.uuid4())
            request.headers[self.header_name] = request_id
        
        # Store in metadata
        if request_id:
            request.metadata["request_id"] = request_id
        
        # Process request
        response = await next_handler(request)
        
        # Add request ID to response
        if request_id:
            response.headers[self.header_name] = request_id
            response.metadata["request_id"] = request_id
        
        return response


__all__ = [
    "LoggingMiddleware",
    "RequestTracingMiddleware",
]