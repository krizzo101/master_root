"""opsvi-auth - Core opsvi-auth functionality.

Comprehensive opsvi-auth library for the OPSVI ecosystem
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
import asyncio
import logging
import time

from opsvi_foundation import BaseComponent, ComponentError
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class OpsviAuthManagerError(ComponentError):
    """Base exception for opsvi-auth errors."""
    pass


class OpsviAuthManagerConfigurationError(OpsviAuthManagerError):
    """Configuration-related errors in opsvi-auth."""
    pass


class OpsviAuthManagerInitializationError(OpsviAuthManagerError):
    """Initialization-related errors in opsvi-auth."""
    pass


class OpsviAuthManagerConfig(BaseSettings):
    """Configuration for opsvi-auth."""

    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    default_provider: Optional[str] = None
    provider_timeout: float = 5.0
    use_token_cache: bool = True
    token_cache_ttl_sec: int = 300

    class Config:
        env_prefix = "OPSVI_OPSVI_AUTH__"


class AuthProvider(ABC):
    """Abstract authentication provider interface."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._initialized = False
        self._logger = logging.getLogger(f"{__name__}.provider.{name}")

    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the provider."""
        raise NotImplementedError

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the provider."""
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if provider is healthy."""
        raise NotImplementedError

    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate using credentials; returns claims and/or token."""
        raise NotImplementedError

    @abstractmethod
    async def verify(self, token: str) -> Dict[str, Any]:
        """Verify a token; returns claims if valid."""
        raise NotImplementedError

    async def revoke(self, token: str) -> None:
        """Revoke a token if supported (default: no-op)."""
        return None


class OpsviAuthManager(BaseComponent):
    """Base class for opsvi-auth components."""

    def __init__(
        self,
        config: Optional[OpsviAuthManagerConfig] = None,
        **kwargs: Any
    ) -> None:
        super().__init__("opsvi-auth", config.dict() if config else {})
        self.config = config or OpsviAuthManagerConfig(**kwargs)
        self._initialized = False
        self._logger = logging.getLogger(f"{__name__}.opsvi-auth")

        self._providers: Dict[str, AuthProvider] = {}
        self._provider_configs: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        # token -> (expires_at, claims)
        self._token_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}

    # ------------------------- lifecycle -------------------------
    async def __aenter__(self) -> "OpsviAuthManager":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - context helper
        await self.shutdown()

    async def initialize(self) -> None:
        """Initialize the component."""
        try:
            self._configure_logging()
            self._logger.info("Initializing opsvi-auth")

            if not self.config.enabled:
                self._logger.warning("opsvi-auth is disabled via configuration")

            await self._initialize_registered_providers()

            self._initialized = True
            self._logger.info("opsvi-auth initialized successfully")

        except Exception as e:  # pragma: no cover - defensive
            self._logger.error(f"Failed to initialize opsvi-auth: {e}")
            raise OpsviAuthManagerInitializationError(f"Initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown the component."""
        try:
            self._logger.info("Shutting down opsvi-auth")

            await self._shutdown_registered_providers()

            async with self._lock:
                self._token_cache.clear()

            self._initialized = False
            self._logger.info("opsvi-auth shut down successfully")

        except Exception as e:  # pragma: no cover - defensive
            self._logger.error(f"Failed to shutdown opsvi-auth: {e}")
            raise OpsviAuthManagerError(f"Shutdown failed: {e}") from e

    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            if not self._initialized:
                return False

            if not self._providers:
                self._logger.debug("No providers registered during health check")
                return True

            timeout = max(0.1, float(self.config.provider_timeout))
            tasks = [self._call_with_timeout(p.health_check(), timeout) for p in self._providers.values()]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception) or res is False:
                    return False
            return True

        except Exception as e:  # pragma: no cover - defensive
            self._logger.error(f"Health check failed: {e}")
            return False

    # ------------------------- provider management -------------------------
    async def register_provider(
        self,
        provider: AuthProvider,
        config: Optional[Dict[str, Any]] = None,
        initialize: bool = True,
    ) -> None:
        """Register an authentication provider."""
        async with self._lock:
            if provider.name in self._providers:
                raise OpsviAuthManagerConfigurationError(
                    f"Provider '{provider.name}' already registered"
                )
            self._providers[provider.name] = provider
            if config is not None:
                self._provider_configs[provider.name] = dict(config)

        if initialize:
            await self._call_with_timeout(
                provider.initialize(config or {}), self.config.provider_timeout
            )

    async def unregister_provider(self, name: str) -> None:
        """Unregister a provider and shut it down."""
        prov = self._providers.get(name)
        if prov is None:
            return
        await self._call_with_timeout(prov.shutdown(), self.config.provider_timeout)
        async with self._lock:
            self._providers.pop(name, None)
            self._provider_configs.pop(name, None)

    def list_providers(self) -> Dict[str, AuthProvider]:
        """Return a snapshot of registered providers."""
        return dict(self._providers)

    def get_provider(self, name: str) -> AuthProvider:
        """Get a registered provider by name."""
        prov = self._providers.get(name)
        if not prov:
            raise OpsviAuthManagerConfigurationError(f"Provider '{name}' is not registered")
        return prov

    def get_provider_config(self, name: str) -> Dict[str, Any]:
        """Get stored config for a provider (empty if none)."""
        return dict(self._provider_configs.get(name, {}))

    async def update_provider_config(self, name: str, config: Dict[str, Any], reinitialize: bool = False) -> None:
        """Update provider config and optionally reinitialize it."""
        async with self._lock:
            if name not in self._providers:
                raise OpsviAuthManagerConfigurationError(f"Provider '{name}' is not registered")
            self._provider_configs[name] = dict(config)
        if reinitialize:
            await self._call_with_timeout(self._providers[name].initialize(config), self.config.provider_timeout)

    # ------------------------- auth operations -------------------------
    async def authenticate(
        self,
        credentials: Dict[str, Any],
        provider_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Authenticate using a provider; caches token claims if available."""
        self._ensure_initialized()
        provider = self._choose_provider(provider_name)
        result = await self._call_with_timeout(
            provider.authenticate(credentials), self.config.provider_timeout
        )
        token = result.get("token") if isinstance(result, dict) else None
        claims = result.get("claims") if isinstance(result, dict) else None
        if token and claims and self.config.use_token_cache:
            await self._cache_set(token, claims)
        return result

    async def verify(
        self,
        token: str,
        provider_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Verify a token; uses cache when enabled."""
        self._ensure_initialized()
        cached = await self._cache_get(token)
        if cached is not None:
            return cached

        provider = self._choose_provider(provider_name)
        claims = await self._call_with_timeout(
            provider.verify(token), self.config.provider_timeout
        )
        if self.config.use_token_cache:
            await self._cache_set(token, claims)
        return claims

    async def revoke(self, token: str, provider_name: Optional[str] = None) -> None:
        """Revoke a token via the provider and evict cache."""
        self._ensure_initialized()
        provider = self._choose_provider(provider_name)
        try:
            await self._call_with_timeout(
                provider.revoke(token), self.config.provider_timeout
            )
        finally:
            await self._cache_delete(token)

    async def clear_cache(self) -> None:
        """Clear all cached token entries."""
        async with self._lock:
            self._token_cache.clear()

    # ------------------------- internals -------------------------
    def _configure_logging(self) -> None:
        level = getattr(logging, (self.config.log_level or "INFO").upper(), logging.INFO)
        logging.getLogger(__name__).setLevel(level)
        if self.config.debug:
            logging.getLogger().setLevel(logging.DEBUG)

    async def _initialize_registered_providers(self) -> None:
        if not self._providers:
            return
        tasks = []
        for name, provider in self._providers.items():
            cfg = self._provider_configs.get(name, {})
            tasks.append(self._call_with_timeout(provider.initialize(cfg), self.config.provider_timeout))
        await asyncio.gather(*tasks)

    async def _shutdown_registered_providers(self) -> None:
        if not self._providers:
            return
        tasks = [self._call_with_timeout(p.shutdown(), self.config.provider_timeout) for p in self._providers.values()]
        await asyncio.gather(*tasks, return_exceptions=True)

    def _choose_provider(self, provider_name: Optional[str]) -> AuthProvider:
        if provider_name:
            provider = self._providers.get(provider_name)
            if not provider:
                raise OpsviAuthManagerConfigurationError(
                    f"Provider '{provider_name}' is not registered"
                )
            return provider
        if self.config.default_provider:
            provider = self._providers.get(self.config.default_provider)
            if not provider:
                raise OpsviAuthManagerConfigurationError(
                    f"Default provider '{self.config.default_provider}' is not registered"
                )
            return provider
        if len(self._providers) == 1:
            return next(iter(self._providers.values()))
        raise OpsviAuthManagerConfigurationError(
            "No provider specified and unable to infer default; configure 'default_provider'"
        )

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            raise OpsviAuthManagerInitializationError("Component not initialized")

    async def _cache_get(self, token: str) -> Optional[Dict[str, Any]]:
        if not self.config.use_token_cache:
            return None
        now = time.time()
        async with self._lock:
            entry = self._token_cache.get(token)
            if not entry:
                return None
            expires_at, claims = entry
            if expires_at <= now:
                self._token_cache.pop(token, None)
                return None
            return claims

    async def _cache_set(self, token: str, claims: Dict[str, Any]) -> None:
        if not self.config.use_token_cache:
            return
        ttl_cfg = max(1, int(self.config.token_cache_ttl_sec))
        now = time.time()
        exp_claim = None
        try:
            exp_val = claims.get("exp") if isinstance(claims, dict) else None
            if isinstance(exp_val, (int, float)):
                exp_claim = float(exp_val)
        except Exception:  # pragma: no cover - defensive
            exp_claim = None
        ttl = ttl_cfg if exp_claim is None else max(1, int(exp_claim - now))
        expires_at = now + ttl
        async with self._lock:
            self._token_cache[token] = (expires_at, claims)
            # Opportunistic cleanup
            if len(self._token_cache) > 1024:
                for t, (exp, _) in list(self._token_cache.items()):
                    if exp <= now:
                        self._token_cache.pop(t, None)

    async def _cache_delete(self, token: str) -> None:
        async with self._lock:
            self._token_cache.pop(token, None)

    async def _call_with_timeout(self, coro, timeout: float):
        return await asyncio.wait_for(coro, timeout=max(0.1, float(timeout)))
