"""Gateway router base for opsvi-gateway.

Provides a simple Router with dispatch table support and parameter extraction
from route patterns. Patterns support static segments and parameter segments of
form :name. Example:
  router.register("/users/:id", handler)
  handler will be called with {'id': '123'} for path '/users/123'.

Handlers may be sync or async callables; route() is async and returns the
handler result. If no route matches, raises LookupError.
"""
from __future__ import annotations

import asyncio
import inspect
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

Handler = Callable[[Dict[str, str]], Awaitable[Any]]
SyncHandler = Callable[[Dict[str, str]], Any]


class RoutePattern:
    """Compiled representation of a route pattern."""

    def __init__(self, pattern: str) -> None:
        self.pattern = pattern.rstrip("/") or "/"
        self.segments = self._compile(self.pattern)

    @staticmethod
    def _compile(pattern: str) -> List[Tuple[str, Optional[str]]]:
        # Each segment: (type, name) where type is 'static' or 'param'
        raw = pattern.lstrip("/").split("/") if pattern != "/" else [""]
        segments: List[Tuple[str, Optional[str]]] = []
        for seg in raw:
            if seg.startswith(":") and len(seg) > 1:
                segments.append(("param", seg[1:]))
            else:
                segments.append(("static", seg))
        return segments

    def match(self, path: str) -> Optional[Dict[str, str]]:
        """Match a path against this pattern and return extracted params or None."""
        input_path = path.rstrip("/") or "/"
        parts = input_path.lstrip("/").split("/") if input_path != "/" else [""]
        if len(parts) != len(self.segments):
            return None
        params: Dict[str, str] = {}
        for seg_def, actual in zip(self.segments, parts):
            kind, name = seg_def
            if kind == "static":
                if name != actual:
                    return None
            else:  # param
                assert name is not None
                params[name] = actual
        return params


class Router:
    """Router supporting registration of handlers and async dispatch.

    Handlers may be regular functions or coroutines. Registered patterns may
    include parameters like ":id".
    """

    def __init__(self) -> None:
        self._routes: List[Tuple[RoutePattern, Callable[..., Any]]] = []

    def register(self, pattern: str, handler: Callable[..., Any]) -> None:
        """Register a handler for a route pattern.

        Raises ValueError on duplicate identical pattern registration.
        """
        rp = RoutePattern(pattern)
        for existing, _ in self._routes:
            if existing.pattern == rp.pattern:
                raise ValueError(f"route already registered: {pattern}")
        self._routes.append((rp, handler))

    async def route(self, path: str) -> Any:
        """Find a matching handler for path, call it with extracted params.

        If handler is a coroutine function it will be awaited. If it's a sync
        function it will be executed in the default loop executor.
        Raises LookupError if no route matches.
        """
        for pattern, handler in self._routes:
            params = pattern.match(path)
            if params is None:
                continue
            if inspect.iscoroutinefunction(handler):
                return await handler(params)
            # allow regular callable returning awaitable as well
            result = handler(params)
            if inspect.isawaitable(result):
                return await result
            # run sync in threadpool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: result)
        raise LookupError(f"no route matches path: {path}")

    def list_routes(self) -> List[str]:
        """Return registered route patterns in order of registration."""
        return [rp.pattern for rp, _ in self._routes]
