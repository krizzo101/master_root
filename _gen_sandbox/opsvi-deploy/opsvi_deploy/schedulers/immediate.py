"""Immediate scheduler for opsvi-deploy (executes tasks ASAP)."""
from typing import Awaitable, Callable, Any
import asyncio

class ImmediateScheduler:
    def __init__(self) -> None:
        self._tasks: list[asyncio.Task[Any]] = []

    async def schedule(self, coro_factory: Callable[[], Awaitable[Any]]) -> None:
        self._tasks.append(asyncio.create_task(coro_factory()))

    async def drain(self) -> None:
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
