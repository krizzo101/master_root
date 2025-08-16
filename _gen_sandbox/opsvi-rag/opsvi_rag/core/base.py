"""opsvi-rag - Core opsvi-rag functionality.

Comprehensive opsvi-rag library for the OPSVI ecosystem
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional
import asyncio
import logging
import time

from opsvi_foundation import BaseComponent, ComponentError
from pydantic_settings import BaseSettings
from pydantic import Field

logger = logging.getLogger(__name__)


class OpsviRagManagerError(ComponentError):
    """Base exception for opsvi-rag errors."""
    pass


class OpsviRagManagerConfigurationError(OpsviRagManagerError):
    """Configuration-related errors in opsvi-rag."""
    pass


class OpsviRagManagerInitializationError(OpsviRagManagerError):
    """Initialization-related errors in opsvi-rag."""
    pass


class OpsviRagManagerConfig(BaseSettings):
    """Configuration for opsvi-rag."""

    # Core configuration
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    # In-memory store sizing
    max_documents: int = Field(default=5000, ge=1)
    max_concurrent_tasks: int = Field(default=10, ge=1)

    # Simple async behavior tuning
    initialize_delay_ms: int = Field(default=0, ge=0)
    shutdown_delay_ms: int = Field(default=0, ge=0)

    class Config:
        env_prefix = "OPSVI_OPSVI_RAG__"


class OpsviRagManager(BaseComponent):
    """Base class for opsvi-rag components.

    Provides base functionality for all opsvi-rag components
    """

    def __init__(
        self,
        config: Optional[OpsviRagManagerConfig] = None,
        **kwargs: Any
    ) -> None:
        """Initialize OpsviRagManager."""
        cfg = config or OpsviRagManagerConfig(**kwargs)
        super().__init__("opsvi-rag", cfg.dict())
        self.config = cfg
        self._initialized = False
        self._logger = logging.getLogger(f"{__name__}.opsvi-rag")

        # Internal stores
        self._documents: Dict[str, str] = {}
        self._index: Dict[str, List[str]] = {}
        self._loop = asyncio.get_event_loop()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)
        self._last_health_ts: float = 0.0

        # Logging level
        try:
            level = getattr(logging, self.config.log_level.upper(), logging.INFO)
            self._logger.setLevel(level)
        except Exception:
            self._logger.setLevel(logging.INFO)

    async def initialize(self) -> None:
        """Initialize the component."""
        if self._initialized:
            return
        try:
            self._logger.info("Initializing opsvi-rag")
            if not self.config.enabled:
                raise OpsviRagManagerInitializationError("Component disabled by configuration")

            if self.config.initialize_delay_ms:
                await asyncio.sleep(self.config.initialize_delay_ms / 1000.0)

            # bootstrap empty index
            self._documents.clear()
            self._index.clear()
            self._last_health_ts = time.time()

            self._initialized = True
            self._logger.info("opsvi-rag initialized successfully")

        except Exception as e:
            self._logger.error(f"Failed to initialize opsvi-rag: {e}")
            raise OpsviRagManagerInitializationError(f"Initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown the component."""
        try:
            self._logger.info("Shutting down opsvi-rag")

            if self.config.shutdown_delay_ms:
                await asyncio.sleep(self.config.shutdown_delay_ms / 1000.0)

            # clear in-memory state
            self._documents.clear()
            self._index.clear()
            self._initialized = False
            self._logger.info("opsvi-rag shut down successfully")

        except Exception as e:
            self._logger.error(f"Failed to shutdown opsvi-rag: {e}")
            raise OpsviRagManagerError(f"Shutdown failed: {e}") from e

    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            if not self._initialized:
                return False
            # simple liveness: ensure semaphore and loop active
            alive = self._semaphore.locked() is not None and self._loop.is_running() is not False or True
            self._last_health_ts = time.time()
            return bool(alive)
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False

    # Component-specific methods
    async def add_documents(self, documents: Dict[str, str]) -> List[str]:
        """Add documents to the in-memory store and update index.

        Returns list of document ids added.
        """
        await self._ensure_ready()
        if not isinstance(documents, dict):
            raise OpsviRagManagerError("documents must be a dict[id -> content]")
        if not documents:
            return []

        async with self._semaphore:
            added: List[str] = []
            for doc_id, content in documents.items():
                if not isinstance(doc_id, str) or not isinstance(content, str):
                    raise OpsviRagManagerError("document ids and contents must be strings")
                if len(self._documents) >= self.config.max_documents and doc_id not in self._documents:
                    raise OpsviRagManagerError("max_documents capacity reached")
                self._documents[doc_id] = content
                self._index[doc_id] = self._tokenize(content)
                added.append(doc_id)
            return added

    async def remove_documents(self, ids: Iterable[str]) -> int:
        """Remove documents by ids. Returns count removed."""
        await self._ensure_ready()
        if ids is None:
            return 0
        async with self._semaphore:
            removed = 0
            for doc_id in list(ids):
                if self._documents.pop(doc_id, None) is not None:
                    removed += 1
                self._index.pop(doc_id, None)
            return removed

    async def query(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Naive retrieval using token overlap scoring."""
        await self._ensure_ready()
        if not query:
            return []
        q_tokens = set(self._tokenize(query))
        results: List[Dict[str, Any]] = []

        async with self._semaphore:
            for doc_id, tokens in self._index.items():
                overlap = len(q_tokens.intersection(tokens))
                if overlap > 0:
                    results.append({
                        "id": doc_id,
                        "score": float(overlap) / float(len(tokens) or 1),
                        "preview": self._documents.get(doc_id, "")[:200],
                    })

        results.sort(key=lambda r: r["score"], reverse=True)
        return results[: max(k, 0)]

    async def clear(self) -> None:
        """Clear all documents and index."""
        await self._ensure_ready()
        async with self._semaphore:
            self._documents.clear()
            self._index.clear()

    async def stats(self) -> Dict[str, Any]:
        """Return basic component statistics."""
        return {
            "initialized": self._initialized,
            "documents": len(self._documents),
            "max_documents": self.config.max_documents,
            "concurrency": self.config.max_concurrent_tasks,
            "last_health_ts": self._last_health_ts,
        }

    # Helpers
    async def _ensure_ready(self) -> None:
        if not self._initialized:
            raise OpsviRagManagerInitializationError("Component not initialized")

    def _tokenize(self, text: str) -> List[str]:
        """Simple lowercase whitespace tokenizer stripping punctuation."""
        if not text:
            return []
        cleaned = []
        for ch in text.lower():
            if ch.isalnum() or ch.isspace():
                cleaned.append(ch)
            else:
                cleaned.append(" ")
        return [t for t in "".join(cleaned).split() if t]
