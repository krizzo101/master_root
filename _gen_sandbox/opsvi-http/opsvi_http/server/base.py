"""HTTP server base for opsvi-http.

Provides a minimal asyncio-friendly HTTP server abstraction that manages
lifecycle, routing, and middleware pipeline. This is intentionally lightweight
and does not perform any real network I/O; concrete transports should subclass
and wire inbound request objects to handle_request.
"""
from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional, Tuple

from opsvi_http.core.base import OpsviHttpManager
from opsvi_http.config.settings import OpsviHttpConfig

logger = logging.getLogger(__name__)

# Types for clarity
Request = Any
Response = Any
Handler = Callable[[Request], Awaitable[Response]]
Middleware = Callable[[Handler], Handler]


class RouteNotFound(Exception):
    """Raised when no route matches a request."""


class HTTPServer(OpsviHttpManager):
    """Base HTTP server that manages routes and middleware.

    Subclasses should call handle_request(request) when an incoming request
    is received. Handlers and middleware are async-capable.
    """

    def __init__(self, config: Optional[OpsviHttpConfig] = None) -> None:
        self.config = config or OpsviHttpConfig()
        self._routes: Dict[str, Handler] = {}
        self._middleware: List[Middleware] = []
        self._lock = asyncio.Lock()
        self._running = False

    # ---- Lifecycle -----------------------------------------------------
    async def initialize(self) -> None:
        """Initialize server resources. Override and call super()."""
        logger.debug("Initializing HTTPServer")
        async with self._lock:
            self._running = True

    async def shutdown(self) -> None:
        """Shutdown server resources. Override and call super()."""
        logger.debug("Shutting down HTTPServer")
        async with self._lock:
            self._running = False

    async def start(self) -> None:
        """Start the server by initializing resources."""
        await self.initialize()

    async def stop(self) -> None:
        """Stop the server by shutting down resources."""
        await self.shutdown()

    async def __aenter__(self) -> "HTTPServer":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.stop()

    def is_running(self) -> bool:
        """Return True if the server has been started."""
        return self._running

    # ---- Routing -------------------------------------------------------
    def register(self, path: str, handler: Handler) -> None:
        """Register a handler for a path, overwriting if existing."""
        if path in self._routes:
            logger.warning("Overwriting route %s", path)
        self._routes[path] = handler
        logger.debug("Registered route %s -> %s", path, handler)

    def route(self, path: str) -> Callable[[Handler], Handler]:
        """Decorator to register a handler for a path.

        Handlers should be async callables accepting a single request object.
        """

        def decorator(func: Handler) -> Handler:
            self.register(path, func)
            return func

        return decorator

    def list_routes(self) -> Iterable[Tuple[str, Handler]]:
        """Return registered routes as (path, handler) pairs."""
        return list(self._routes.items())

    # ---- Middleware ----------------------------------------------------
    def add_middleware(self, mw: Middleware) -> None:
        """Append a middleware to the pipeline. Middleware wrap handlers."""
        self._middleware.append(mw)
        logger.debug("Added middleware %s", mw)

    # Alias commonly used in other ecosystems
    use = add_middleware

    # ---- Request handling ----------------------------------------------
    @staticmethod
    def _path_from_request(request: Request) -> Optional[str]:
        """Extract a path from mapping-like or object-like request."""
        path: Optional[str] = None
        if isinstance(request, dict):
            path = request.get("path") or request.get("url") or request.get("target")
        else:
            path = getattr(request, "path", None) or getattr(request, "url", None)
        if not path:
            return None
        # Normalize: strip scheme/host and query if present
        try:
            # lightweight parse without importing urllib; split on '?'
            if "?" in path:
                path = path.split("?", 1)[0]
            # remove scheme and host if present (e.g., http://host/path)
            if "://" in path:
                _, _, rest = path.partition("://")
                slash = rest.find("/")
                path = rest[slash:] if slash != -1 else "/"
        except Exception:  # pragma: no cover - be resilient to odd objects
            pass
        return path or "/"

    @staticmethod
    def _ensure_async(handler: Callable[[Request], Any]) -> Handler:
        """Wrap a possibly-sync handler to an async handler."""

        async def _async_handler(request: Request) -> Response:
            try:
                result = handler(request)
                if inspect.isawaitable(result):
                    return await result  # type: ignore[return-value]
                return result  # type: ignore[return-value]
            except Exception:
                logger.exception("Unhandled exception in handler")
                raise

        return _async_handler

    def _build_pipeline(self, final: Handler) -> Handler:
        """Wrap final handler with middleware in reverse registration order."""
        handler: Handler = self._ensure_async(final)
        for mw in reversed(self._middleware):
            # Ensure the handler provided to middleware is async-compatible
            handler = self._ensure_async(mw(handler))
        return handler

    async def handle_request(self, request: Request) -> Response:
        """Dispatch a request to a route, running middleware pipeline.

        Expects request to have a 'path' attribute or key. Returns whatever the
        handler returns. Raises RouteNotFound if no matching route.
        """
        if not self._running:
            raise RuntimeError("Server is not running")

        path = self._path_from_request(request)
        logger.debug("Handling request for path=%s", path)

        if path is None:
            raise ValueError("Request does not contain a path")

        handler = self._routes.get(path)
        if handler is None:
            logger.debug("No route for path=%s", path)
            raise RouteNotFound(f"No route for path: {path}")

        pipeline = self._build_pipeline(handler)
        return await pipeline(request)


# Small example middleware utilities (can be imported by users)

def simple_logging_middleware(logger_name: Optional[str] = None) -> Middleware:
    """Return middleware that logs requests and responses."""

    log = logging.getLogger(logger_name) if logger_name else logger

    def mw(next_handler: Handler) -> Handler:
        async def _handler(request: Request) -> Response:
            log.debug("Request received: %s", request)
            resp = await next_handler(request)
            log.debug("Response produced: %s", resp)
            return resp

        return _handler

    return mw
