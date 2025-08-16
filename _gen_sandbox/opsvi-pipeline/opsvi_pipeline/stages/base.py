"""Pipeline stage base for opsvi-pipeline.

Defines an asynchronous Stage base class with lifecycle hooks,
input/output contracts via typing, and error handling utilities.
"""
from __future__ import annotations

import asyncio
from typing import Callable, Dict, Generic, Iterable, List, Optional, TypeVar, Union

T = TypeVar("T")
U = TypeVar("U")


class StageError(Exception):
    """Base exception for stage-related failures."""


class ValidationError(StageError):
    """Raised when input validation fails."""


class Stage(Generic[T, U]):
    """Asynchronous pipeline stage base.

    Subclasses should override `process` to implement the stage-specific
    transformation from input type T to output type U. The `run` method
    provides a stable entrypoint that performs validation and error handling.
    """

    def __init__(self, name: Optional[str] = None) -> None:
        self.name = name or self.__class__.__name__

    async def run(self, data: T, *, timeout: Optional[float] = None) -> U:
        """Run the stage asynchronously.

        Args:
            data: Input data for the stage.
            timeout: Optional timeout in seconds for the processing step.

        Returns:
            The processed output.

        Raises:
            ValidationError: If input validation fails.
            StageError: If processing fails or is cancelled.
        """
        self._validate_input(data)
        await self.on_start(data)

        try:
            coro = self.process(data)
            result: U
            if timeout is None:
                result = await coro
            else:
                result = await asyncio.wait_for(coro, timeout)
        except asyncio.TimeoutError as exc:
            await self.on_error(data, exc)
            raise StageError(f"Stage '{self.name}' timed out") from exc
        except asyncio.CancelledError as exc:
            await self.on_error(data, exc)
            raise StageError(f"Stage '{self.name}' cancelled") from exc
        except Exception as exc:  # pragma: no cover - defensive
            await self.on_error(data, exc)
            raise StageError(f"Stage '{self.name}' failed: {exc}") from exc

        self._validate_output(result)
        await self.on_success(data, result)
        return result

    async def process(self, data: T) -> U:
        """Override this method with stage-specific logic.

        The default implementation is an identity transformation and may be
        suitable for simple passthrough stages.
        """
        return data  # type: ignore[return-value]

    def _validate_input(self, data: T) -> None:
        """Simple input validation hook. Override as needed.

        By default, accepts any non-None value. Raise ValidationError to
        signal invalid input.
        """
        if data is None:  # type: ignore[unreachable]
            raise ValidationError(f"Stage '{self.name}' received None input")

    def _validate_output(self, data: U) -> None:
        """Simple output validation hook. Override as needed.

        By default, accepts any value (including None).
        """
        return

    async def on_start(self, data: T) -> None:
        """Hook invoked right before processing begins."""
        return

    async def on_success(self, data: T, result: U) -> None:
        """Hook invoked after successful processing."""
        return

    async def on_error(self, data: T, exc: BaseException) -> None:
        """Hook invoked when processing raises an exception."""
        return

    async def run_many(
        self,
        items: Iterable[T],
        *,
        concurrency: int = 1,
        timeout: Optional[float] = None,
    ) -> List[U]:
        """Run the stage over multiple items with bounded concurrency.

        Args:
            items: Inputs to process.
            concurrency: Max number of in-flight tasks.
            timeout: Optional timeout per item.
        """
        if concurrency <= 0:
            raise ValueError("concurrency must be >= 1")

        sem = asyncio.Semaphore(concurrency)
        results: List[Optional[U]] = [None] * len(list(items))  # pre-size if possible

        # Convert to list to preserve ordering; supports single-pass iterables
        seq = list(items)
        results = [None] * len(seq)

        async def worker(idx: int, item: T) -> None:
            async with sem:
                results[idx] = await self.run(item, timeout=timeout)

        tasks = [asyncio.create_task(worker(i, it)) for i, it in enumerate(seq)]
        try:
            await asyncio.gather(*tasks)
        except Exception:
            for t in tasks:
                t.cancel()
            raise

        # Cast results now that all entries are filled
        return [r for r in results if r is not None]

    async def __aenter__(self) -> "Stage[T, U]":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    def info(self) -> Dict[str, Union[str, bool]]:
        """Return lightweight metadata about the stage."""
        return {"name": self.name, "callable": True}

    def __repr__(self) -> str:  # pragma: no cover - representation utility
        return f"{self.__class__.__name__}(name={self.name!r})"


# Simple convenience stage implementations
class IdentityStage(Stage[T, T]):
    """A stage that returns the input unchanged."""

    async def process(self, data: T) -> T:
        return data


class MapStage(Stage[T, U]):
    """Stage that applies a synchronous mapping function to the input.

    The mapper receives the input and must return the output.
    """

    def __init__(self, mapper: Callable[[T], U], name: Optional[str] = None) -> None:
        super().__init__(name=name)
        if not callable(mapper):
            raise TypeError("mapper must be callable")
        self._mapper: Callable[[T], U] = mapper

    async def process(self, data: T) -> U:
        # Run mapping in a thread to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._mapper, data)
