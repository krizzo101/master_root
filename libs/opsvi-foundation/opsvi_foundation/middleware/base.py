"""Base middleware classes for opsvi-foundation."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, TypeVar, Awaitable
import asyncio
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class Request:
    """Generic request object for middleware processing."""
    
    method: str
    path: str
    headers: Dict[str, str]
    body: Optional[Any] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Response:
    """Generic response object for middleware processing."""
    
    status: int
    headers: Dict[str, str]
    body: Optional[Any] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Middleware(ABC):
    """Abstract base class for middleware components."""
    
    def __init__(self, name: str = None):
        """Initialize middleware.
        
        Args:
            name: Optional name for the middleware
        """
        self.name = name or self.__class__.__name__
        self.enabled = True
        self._metrics = {
            "requests_processed": 0,
            "errors": 0,
            "total_time": 0.0,
        }
    
    @abstractmethod
    async def process(
        self,
        request: Request,
        next_handler: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process a request through the middleware.
        
        Args:
            request: The request to process
            next_handler: The next handler in the chain
            
        Returns:
            The response from processing
        """
        pass
    
    async def initialize(self) -> None:
        """Initialize the middleware."""
        logger.info(f"Initialized middleware: {self.name}")
    
    async def shutdown(self) -> None:
        """Shutdown the middleware."""
        logger.info(f"Shutdown middleware: {self.name}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get middleware metrics."""
        return self._metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset middleware metrics."""
        self._metrics = {
            "requests_processed": 0,
            "errors": 0,
            "total_time": 0.0,
        }


class MiddlewareChain:
    """Chain of middleware components for processing requests."""
    
    def __init__(self):
        """Initialize middleware chain."""
        self._middlewares: List[Middleware] = []
        self._initialized = False
    
    def add(self, middleware: Middleware) -> "MiddlewareChain":
        """Add middleware to the chain.
        
        Args:
            middleware: The middleware to add
            
        Returns:
            Self for chaining
        """
        self._middlewares.append(middleware)
        logger.info(f"Added middleware to chain: {middleware.name}")
        return self
    
    def remove(self, middleware: Middleware) -> bool:
        """Remove middleware from the chain.
        
        Args:
            middleware: The middleware to remove
            
        Returns:
            True if removed, False if not found
        """
        try:
            self._middlewares.remove(middleware)
            logger.info(f"Removed middleware from chain: {middleware.name}")
            return True
        except ValueError:
            return False
    
    async def initialize(self) -> None:
        """Initialize all middleware in the chain."""
        for middleware in self._middlewares:
            await middleware.initialize()
        self._initialized = True
        logger.info(f"Initialized middleware chain with {len(self._middlewares)} components")
    
    async def shutdown(self) -> None:
        """Shutdown all middleware in the chain."""
        for middleware in reversed(self._middlewares):
            await middleware.shutdown()
        self._initialized = False
        logger.info("Shutdown middleware chain")
    
    async def process(
        self,
        request: Request,
        final_handler: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process a request through the middleware chain.
        
        Args:
            request: The request to process
            final_handler: The final handler after all middleware
            
        Returns:
            The response from processing
        """
        if not self._initialized:
            raise RuntimeError("Middleware chain not initialized")
        
        # Build the chain of handlers
        handler = final_handler
        for middleware in reversed(self._middlewares):
            if middleware.enabled:
                # Create a closure to capture the current handler
                async def make_handler(mw, next_h):
                    return await mw.process(request, next_h)
                
                # Bind the current middleware and handler
                current_middleware = middleware
                current_handler = handler
                handler = lambda req, m=current_middleware, h=current_handler: m.process(req, h)
        
        # Execute the chain
        return await handler(request)
    
    def get_middlewares(self) -> List[Middleware]:
        """Get list of all middleware in the chain."""
        return self._middlewares.copy()
    
    def clear(self) -> None:
        """Clear all middleware from the chain."""
        self._middlewares.clear()
        logger.info("Cleared middleware chain")
    
    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics from all middleware."""
        return {
            mw.name: mw.get_metrics()
            for mw in self._middlewares
        }


class SimpleMiddleware(Middleware):
    """Simple middleware implementation for basic processing."""
    
    def __init__(
        self,
        name: str,
        before: Optional[Callable[[Request], Awaitable[None]]] = None,
        after: Optional[Callable[[Request, Response], Awaitable[Response]]] = None
    ):
        """Initialize simple middleware.
        
        Args:
            name: Name of the middleware
            before: Optional function to call before processing
            after: Optional function to call after processing
        """
        super().__init__(name)
        self._before = before
        self._after = after
    
    async def process(
        self,
        request: Request,
        next_handler: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request through the middleware."""
        start_time = time.time()
        
        try:
            # Before processing
            if self._before:
                await self._before(request)
            
            # Process with next handler
            response = await next_handler(request)
            
            # After processing
            if self._after:
                response = await self._after(request, response)
            
            # Update metrics
            self._metrics["requests_processed"] += 1
            
            return response
        
        except Exception as e:
            self._metrics["errors"] += 1
            raise
        
        finally:
            self._metrics["total_time"] += time.time() - start_time


__all__ = [
    "Request",
    "Response",
    "Middleware",
    "MiddlewareChain",
    "SimpleMiddleware",
]