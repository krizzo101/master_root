"""Document processors for opsvi-rag.

Defines a base DocumentProcessor with pipeline hooks and simple error
recovery utilities. Concrete processors should subclass DocumentProcessor
and override the async _process method. The base class provides:

- before_process: called before processing a document
- after_process: called after successful processing
- on_error: called when processing raises an exception
- process: orchestrates the pipeline, runs hooks, and can retry on error

This is kept lightweight and asyncio-friendly.
"""
from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine, Optional


class ProcessingError(Exception):
    """Generic processing error wrapper."""


class DocumentProcessor:
    """Base class for document processors.

    Subclasses should implement _process to perform actual work. The
    public method process orchestrates lifecycle hooks and simple retry
    error recovery.
    """

    def __init__(self) -> None:
        # Maximum number of attempts (initial try + retries - 1)
        self.max_retries: int = 0
        # Backoff in seconds between retries; can be a callable for jitter
        self.backoff: Callable[[int], float] = lambda attempt: 0.0

    async def before_process(self, doc: Any) -> Any:
        """Hook called before processing. Can modify and must return the doc.

        Default implementation returns document unchanged.
        """
        return doc

    async def after_process(self, original: Any, result: Any) -> Any:
        """Hook called after successful processing. Returns final result.

        Default implementation returns result unchanged.
        """
        return result

    async def on_error(self, original: Any, exc: Exception, attempt: int) -> Optional[Any]:
        """Hook called when processing raises an exception.

        Can return a replacement result to recover, or None to indicate
        the error should be retried/propagated.

        Default implementation returns None.
        """
        return None

    async def _process(self, doc: Any) -> Any:
        """Actual processing logic to be implemented by subclasses.

        Must be overridden.
        """
        raise NotImplementedError

    async def process(self, doc: Any) -> Any:
        """Orchestrate processing with hooks and simple retry/error recovery.

        Workflow:
        - Call before_process
        - Attempt _process up to max_retries + 1 times
        - On success call after_process and return result
        - On exception call on_error; if it returns a value, return it
        - Otherwise, sleep backoff and retry or raise ProcessingError
        """
        original = doc
        doc = await self.before_process(doc)

        attempt = 0
        last_exc: Optional[BaseException] = None
        total_attempts = max(1, self.max_retries + 1)

        while attempt < total_attempts:
            try:
                result = await self._process(doc)
                result = await self.after_process(original, result)
                return result
            except Exception as exc:  # pragma: no cover - behavior tested in subclasses
                attempt += 1
                last_exc = exc
                # Allow on_error to provide a recovery result
                recovery = await self.on_error(original, exc, attempt)
                if recovery is not None:
                    return recovery
                if attempt >= total_attempts:
                    # No more retries; raise a wrapped error
                    raise ProcessingError(
                        f"Processing failed after {attempt} attempts: {exc!r}"
                    ) from exc
                # Wait before retrying
                wait = self.backoff(attempt)
                if wait:
                    try:
                        await asyncio.sleep(wait)
                    except asyncio.CancelledError:
                        # Preserve cancellation
                        raise
        # Should not reach here
        raise ProcessingError("Unreachable processing state")
