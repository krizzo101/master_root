"""Error handling middleware for opsvi-foundation."""

import logging
import traceback
from typing import Any, Callable, Dict, Optional, Type, Awaitable
import json

from .base import Middleware, Request, Response

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(Middleware):
    """Middleware for handling errors and exceptions."""
    
    def __init__(
        self,
        name: str = "ErrorHandlingMiddleware",
        catch_all: bool = True,
        log_errors: bool = True,
        include_traceback: bool = False,
        error_handlers: Optional[Dict[Type[Exception], Callable]] = None,
        default_status: int = 500
    ):
        """Initialize error handling middleware.
        
        Args:
            name: Name of the middleware
            catch_all: Whether to catch all exceptions
            log_errors: Whether to log errors
            include_traceback: Whether to include traceback in response
            error_handlers: Custom error handlers by exception type
            default_status: Default error status code
        """
        super().__init__(name)
        self.catch_all = catch_all
        self.log_errors = log_errors
        self.include_traceback = include_traceback
        self.error_handlers = error_handlers or {}
        self.default_status = default_status
    
    async def process(
        self,
        request: Request,
        next_handler: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request with error handling."""
        try:
            return await next_handler(request)
            
        except Exception as e:
            # Update metrics
            self._metrics["errors"] += 1
            
            # Log error if enabled
            if self.log_errors:
                request_id = request.metadata.get("request_id", "unknown")
                logger.error(
                    f"Error processing request {request_id}: {str(e)}",
                    exc_info=True
                )
            
            # Check for custom handler
            for exc_type, handler in self.error_handlers.items():
                if isinstance(e, exc_type):
                    return await self._handle_custom_error(e, handler, request)
            
            # Handle based on settings
            if self.catch_all:
                return self._create_error_response(e, request)
            else:
                raise
    
    async def _handle_custom_error(
        self,
        error: Exception,
        handler: Callable,
        request: Request
    ) -> Response:
        """Handle error with custom handler."""
        try:
            # Handler can be sync or async
            if asyncio.iscoroutinefunction(handler):
                return await handler(error, request)
            else:
                return handler(error, request)
        except Exception as handler_error:
            logger.error(f"Error in custom error handler: {handler_error}")
            return self._create_error_response(error, request)
    
    def _create_error_response(self, error: Exception, request: Request) -> Response:
        """Create error response."""
        error_data = {
            "error": error.__class__.__name__,
            "message": str(error),
            "path": request.path,
            "method": request.method,
        }
        
        if self.include_traceback:
            error_data["traceback"] = traceback.format_exc()
        
        # Determine status code
        status = getattr(error, "status_code", self.default_status)
        
        return Response(
            status=status,
            headers={"Content-Type": "application/json"},
            body=error_data,
            metadata={"error": True}
        )
    
    def register_handler(
        self,
        exception_type: Type[Exception],
        handler: Callable
    ) -> None:
        """Register a custom error handler.
        
        Args:
            exception_type: Type of exception to handle
            handler: Handler function
        """
        self.error_handlers[exception_type] = handler
        logger.info(f"Registered error handler for {exception_type.__name__}")


class RetryMiddleware(Middleware):
    """Middleware for retrying failed requests."""
    
    def __init__(
        self,
        name: str = "RetryMiddleware",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
        retry_on: Optional[list] = None
    ):
        """Initialize retry middleware.
        
        Args:
            name: Name of the middleware
            max_retries: Maximum number of retries
            retry_delay: Initial delay between retries (seconds)
            exponential_backoff: Whether to use exponential backoff
            retry_on: List of exception types to retry on
        """
        super().__init__(name)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.exponential_backoff = exponential_backoff
        self.retry_on = retry_on or [Exception]
    
    async def process(
        self,
        request: Request,
        next_handler: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request with retry logic."""
        import asyncio
        
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await next_handler(request)
                
                # Check if response indicates we should retry
                if self._should_retry_response(response) and attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Retrying request (attempt {attempt + 1}/{self.max_retries}) "
                        f"after {delay}s due to status {response.status}"
                    )
                    await asyncio.sleep(delay)
                    continue
                
                return response
                
            except Exception as e:
                last_error = e
                
                # Check if we should retry this exception
                should_retry = any(
                    isinstance(e, exc_type) for exc_type in self.retry_on
                )
                
                if should_retry and attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Retrying request (attempt {attempt + 1}/{self.max_retries}) "
                        f"after {delay}s due to {e.__class__.__name__}"
                    )
                    await asyncio.sleep(delay)
                else:
                    # Update metrics
                    self._metrics["errors"] += 1
                    raise
        
        # If we get here, all retries failed
        if last_error:
            raise last_error
    
    def _should_retry_response(self, response: Response) -> bool:
        """Check if response indicates we should retry."""
        # Retry on 5xx errors and specific 4xx errors
        return response.status >= 500 or response.status in [429, 408]
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        if self.exponential_backoff:
            return self.retry_delay * (2 ** attempt)
        return self.retry_delay


class CircuitBreakerMiddleware(Middleware):
    """Middleware implementing circuit breaker pattern."""
    
    def __init__(
        self,
        name: str = "CircuitBreakerMiddleware",
        failure_threshold: int = 5,
        timeout: float = 60.0,
        half_open_requests: int = 1
    ):
        """Initialize circuit breaker middleware.
        
        Args:
            name: Name of the middleware
            failure_threshold: Number of failures before opening circuit
            timeout: Time before attempting to close circuit (seconds)
            half_open_requests: Number of requests to allow in half-open state
        """
        super().__init__(name)
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_requests = half_open_requests
        
        self.state = "closed"  # closed, open, half_open
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_count = 0
    
    async def process(
        self,
        request: Request,
        next_handler: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request with circuit breaker."""
        import time
        
        # Check circuit state
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half_open"
                self.half_open_count = 0
                logger.info("Circuit breaker entering half-open state")
            else:
                raise CircuitOpenError("Circuit breaker is open")
        
        if self.state == "half_open":
            if self.half_open_count >= self.half_open_requests:
                raise CircuitOpenError("Circuit breaker is in half-open state")
            self.half_open_count += 1
        
        try:
            response = await next_handler(request)
            
            # Success - update state
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("Circuit breaker closed")
            
            return response
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
            
            raise


class CircuitOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


__all__ = [
    "ErrorHandlingMiddleware",
    "RetryMiddleware",
    "CircuitBreakerMiddleware",
    "CircuitOpenError",
]