"""Gateway middleware base for opsvi-gateway.

Defines a Middleware base class with async processing, composition helpers,
and simple error handling. Designed to be lightweight and easily extended.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Iterable, List, Optional, Protocol
import asyncio

Request = Any
Response = Any

class NextCallable(Protocol):
    def __call__(self, request: Request) -> Awaitable[Response]:
        ...

class Middleware:
    """Base middleware.

    Subclasses should override async def process(self, request, call_next) -> Response
    to implement behaviour. The default implementation simply calls the next
    handler unchanged.

    Middleware instances are callable and can be composed into a pipeline via
    `chain`.
    """

    async def process(self, request: Request, call_next: NextCallable) -> Response:
        """Process a request and optionally call the next middleware/handler.

        Default behaviour forwards to call_next unmodified.
        """
        return await call_next(request)

    def __call__(self, request: Request, call_next: NextCallable) -> Awaitable[Response]:
        return self.process(request, call_next)


def _wrap_handler(handler: NextCallable, middleware: Middleware) -> NextCallable:
    async def wrapped(request: Request) -> Response:
        return await middleware.process(request, handler)
    return wrapped


def chain(middlewares: Iterable[Middleware], terminal: NextCallable) -> NextCallable:
    """Compose a sequence of middleware into a single callable.

    Middlewares are executed in the order provided. The terminal callable is
    invoked last. Raises ValueError if middlewares contains non-Middleware.
    """
    handlers: List[Middleware] = list(middlewares)
    for m in handlers:
        if not isinstance(m, Middleware):
            raise ValueError("All items in middlewares must be Middleware instances")

    handler: NextCallable = terminal
    # Compose in reverse so first middleware in list runs first.
    for m in reversed(handlers):
        handler = _wrap_handler(handler, m)
    return handler


class ErrorHandlerMiddleware(Middleware):
    """Middleware that catches exceptions from downstream and returns or raises.

    The on_error callback is called with (request, exception) and its return
    value is used as the response. If on_error is None the exception is re-raised.
    """

    def __init__(self, on_error: Optional[Callable[[Request, Exception], Awaitable[Response]]] = None):
        self._on_error = on_error

    async def process(self, request: Request, call_next: NextCallable) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:  # pylint: disable=broad-except
            if self._on_error is None:
                raise
            result = self._on_error(request, exc)
            if asyncio.iscoroutine(result):
                return await result
            return result


# Simple example terminal handler for documentation/testing purposes.
async def terminal_handler(request: Request) -> Response:
    """A trivial terminal handler that echoes the request.

    Intended for use in unit tests or as a default.
    """
    return request
