"""opsvi-llm - Core opsvi-llm functionality.

Comprehensive opsvi-llm library for the OPSVI ecosystem
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, Iterable
import asyncio
import logging

from opsvi_foundation import BaseComponent, ComponentError
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class OpsviLlmManagerError(ComponentError):
    """Base exception for opsvi-llm errors."""


class OpsviLlmManagerConfigurationError(OpsviLlmManagerError):
    """Configuration-related errors in opsvi-llm."""


class OpsviLlmManagerInitializationError(OpsviLlmManagerError):
    """Initialization-related errors in opsvi-llm."""


class OpsviLlmManagerConfig(BaseSettings):
    """Configuration for opsvi-llm."""

    # Core configuration
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    # Component-specific configuration
    default_model: Optional[str] = None
    max_concurrency: int = 5
    request_timeout_seconds: float = 60.0

    class Config:
        env_prefix = "OPSVI_OPSVI_LLM__"


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a completion for a prompt."""

    async def aclose(self) -> None:
        """Optional async cleanup for provider."""
        return None


class OpsviLlmManager(BaseComponent):
    """Base class for opsvi-llm components.

    Provides base functionality for managing LLM providers and generating text.
    """

    def __init__(
        self,
        config: Optional[OpsviLlmManagerConfig] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize OpsviLlmManager."""
        cfg = config or OpsviLlmManagerConfig(**kwargs)
        super().__init__("opsvi-llm", cfg.dict())
        self.config = cfg
        self._initialized = False
        self._logger = logging.getLogger(f"{__name__}.opsvi-llm")
        self._providers: Dict[str, BaseProvider] = {}
        self._semaphore = asyncio.Semaphore(max(1, self.config.max_concurrency))

    # Lifecycle
    async def initialize(self) -> None:
        """Initialize the component."""
        try:
            self._setup_logging()
            if not self.config.enabled:
                self._logger.info("opsvi-llm disabled by configuration")
                self._initialized = True
                return

            self._logger.info("Initializing opsvi-llm")
            # No built-in providers here; rely on register_provider by users/extensions.
            self._initialized = True
            self._logger.info("opsvi-llm initialized successfully")
        except Exception as e:  # pragma: no cover - defensive
            self._logger.error(f"Failed to initialize opsvi-llm: {e}")
            raise OpsviLlmManagerInitializationError(f"Initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown the component."""
        try:
            self._logger.info("Shutting down opsvi-llm")
            await self._close_providers()
            self._initialized = False
            self._logger.info("opsvi-llm shut down successfully")
        except Exception as e:  # pragma: no cover - defensive
            self._logger.error(f"Failed to shutdown opsvi-llm: {e}")
            raise OpsviLlmManagerError(f"Shutdown failed: {e}") from e

    async def health_check(self) -> bool:
        """Return True when initialized and configuration is coherent."""
        try:
            if not self._initialized:
                return False
            if self.config.enabled and not self._providers:
                # Manager is enabled but has no providers registered.
                return False
            return True
        except Exception as e:  # pragma: no cover - defensive
            self._logger.error(f"Health check failed: {e}")
            return False

    # Provider management
    def register_provider(self, provider: BaseProvider, *, alias: Optional[str] = None) -> None:
        """Register a provider by name or alias."""
        key = alias or provider.name
        if not key:
            raise OpsviLlmManagerConfigurationError("Provider must have a name or explicit alias")
        if key in self._providers:
            raise OpsviLlmManagerConfigurationError(f"Provider '{key}' already registered")
        self._providers[key] = provider
        self._logger.debug("Registered provider: %s", key)

    def unregister_provider(self, name: str) -> None:
        """Unregister a provider by name and close if possible."""
        prov = self._providers.pop(name, None)
        if prov is None:
            return
        # Fire-and-forget cleanup
        try:
            coro = prov.aclose()
            if asyncio.iscoroutine(coro):
                asyncio.create_task(coro)
        except Exception:  # pragma: no cover
            self._logger.debug("Provider cleanup failed for %s", name)

    def get_provider(self, name: Optional[str] = None) -> BaseProvider:
        """Get a provider by name or default_model."""
        key = name or self.config.default_model
        if not key:
            if len(self._providers) == 1:
                # single provider can be default implicitly
                return next(iter(self._providers.values()))
            raise OpsviLlmManagerConfigurationError("No provider name given and no default_model configured")
        try:
            return self._providers[key]
        except KeyError as e:
            raise OpsviLlmManagerConfigurationError(f"Provider '{key}' not found") from e

    # Generation APIs
    async def generate(self, prompt: str, *, provider: Optional[str] = None, **kwargs: Any) -> str:
        """Generate text from a single prompt using the selected provider."""
        self._ensure_ready()
        prov = self.get_provider(provider)
        async with self._acquire():
            return await asyncio.wait_for(
                prov.generate(prompt, **kwargs),
                timeout=self.config.request_timeout_seconds if self.config.request_timeout_seconds > 0 else None,
            )

    async def batch_generate(
        self,
        prompts: Iterable[str],
        *,
        provider: Optional[str] = None,
        return_exceptions: bool = False,
        **kwargs: Any,
    ) -> list[Union[str, Exception]]:
        """Generate for multiple prompts concurrently, respecting concurrency limits."""
        self._ensure_ready()
        prov = self.get_provider(provider)

        async def _task(p: str) -> Union[str, Exception]:
            try:
                async with self._acquire():
                    return await asyncio.wait_for(
                        prov.generate(p, **kwargs),
                        timeout=self.config.request_timeout_seconds if self.config.request_timeout_seconds > 0 else None,
                    )
            except Exception as exc:
                if return_exceptions:
                    return exc
                raise

        tasks = [asyncio.create_task(_task(p)) for p in prompts]
        results: list[Union[str, Exception]] = []
        for t in tasks:
            try:
                results.append(await t)
            except Exception as exc:
                # Cancel remaining tasks if not collecting exceptions
                for other in tasks:
                    if not other.done():
                        other.cancel()
                raise exc
        return results

    # Internal helpers
    def _ensure_ready(self) -> None:
        if not self._initialized:
            raise OpsviLlmManagerInitializationError("Manager not initialized")
        if not self.config.enabled:
            raise OpsviLlmManagerConfigurationError("Manager is disabled")

    def _setup_logging(self) -> None:
        level = getattr(logging, (self.config.log_level or "INFO").upper(), logging.INFO)
        logging.getLogger(__name__).setLevel(level)
        if self.config.debug:
            logging.getLogger().setLevel(logging.DEBUG)

    async def _close_providers(self) -> None:
        if not self._providers:
            return
        tasks = []
        for name, prov in list(self._providers.items()):
            try:
                coro = prov.aclose()
                if asyncio.iscoroutine(coro):
                    tasks.append(asyncio.create_task(coro))
            except Exception:  # pragma: no cover
                self._logger.debug("Error scheduling provider close for %s", name)
        if tasks:
            with contextlib.suppress(Exception):
                await asyncio.gather(*tasks)
        self._providers.clear()

    from contextlib import asynccontextmanager as _acm  # local import alias

    @_acm
    async def _acquire(self):  # type: ignore[override]
        async with self._semaphore:
            yield


# If desired by library consumers, they can implement concrete providers inheriting BaseProvider.
import contextlib  # placed at end to support _close_providers
