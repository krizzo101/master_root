"""Environments base for opsvi-deploy.

This module provides a small asynchronous-friendly environment manager that
discovers the current environment from well-known environment variables, allows
registering available environments, and supports programmatic overrides (including
an async context manager for temporary overrides).
"""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import AsyncIterator, Dict, Iterable, List, Optional


logger = logging.getLogger(__name__)


class InvalidEnvironmentError(ValueError):
    """Raised when an environment is not recognized by the manager."""


@dataclass
class EnvironmentManager:
    """Manage environments for opsvi-deploy.

    The manager discovers the current environment using a set of well-known
    environment variables (by default OPSVI_ENV, ENV, NODE_ENV). A list of
    allowed environments can be supplied. Programmatic overrides are
    supported and take precedence over discovery.
    """

    available: List[str] = field(default_factory=lambda: ["dev", "staging", "prod"])
    default: str = "dev"
    env_vars: List[str] = field(default_factory=lambda: ["OPSVI_ENV", "ENV", "NODE_ENV"])
    _override: Optional[str] = field(default=None, init=False)
    _cache: Optional[str] = field(default=None, init=False)

    def __post_init__(self) -> None:
        # Normalize available to strings and ensure uniqueness while preserving order
        seen = set()
        normalized: List[str] = []
        for e in self.available:
            if e not in seen:
                normalized.append(e)
                seen.add(e)
        self.available = normalized

        if self.default not in self.available and self.available:
            # Ensure default is a known environment; if not provided, pick first available
            logger.debug("Provided default '%s' not in available, adjusting to '%s'", self.default, self.available[0])
            self.default = self.available[0]

    async def discover(self) -> str:
        """Discover the environment asynchronously.

        The resolution order is:
        - explicit override (set via set_override)
        - environment variables in self.env_vars (first one found)
        - cached discovery result
        - default value

        This method is async to allow integration with async workflows; it performs
        a micro-sleep to yield control.
        """
        # yield control to the event loop
        await asyncio.sleep(0)

        if self._override is not None:
            logger.debug("Using override environment: %s", self._override)
            return self._validate_and_cache(self._override)

        # Check env vars in order
        for key in self.env_vars:
            value = os.environ.get(key)
            if value:
                logger.debug("Found environment variable %s=%s", key, value)
                return self._validate_and_cache(value)

        # use cached
        if self._cache is not None:
            logger.debug("Using cached environment: %s", self._cache)
            return self._cache

        # fallback to default
        logger.debug("No environment variable or override found; using default '%s'", self.default)
        return self._validate_and_cache(self.default)

    def current(self) -> str:
        """Synchronous convenience wrapper around discover.

        If running in an async event loop, prefer calling discover() directly.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # no running loop; safe to run
            return asyncio.run(self.discover())
        else:
            # There's a running loop; schedule discover and block until done
            # Running a blocking wait in loop is not allowed, so return cached or override
            if self._override is not None:
                return self._validate_and_cache(self._override)
            if self._cache is not None:
                return self._cache
            # As a last resort, raise to encourage using async discover
            raise RuntimeError("current() cannot run discover() in a running event loop; use await discover()")

    def set_override(self, env: Optional[str]) -> None:
        """Set or clear a programmatic override for the environment.

        Passing None clears the override.
        """
        if env is None:
            self._override = None
            logger.debug("Environment override cleared")
            return

        if not isinstance(env, str):
            raise TypeError("env must be a string or None")

        self._override = self._validate(env)
        # update cache to reflect override immediately
        self._cache = self._override
        logger.debug("Environment override set to %s", self._override)

    def clear_override(self) -> None:
        """Clear any programmatic override."""
        self.set_override(None)

    @asynccontextmanager
    async def override_context(self, env: Optional[str]) -> AsyncIterator[None]:
        """Async context manager to temporarily set an override.

        Example:
            async with manager.override_context('staging'):
                # inside this block discover() will return 'staging'
                ...
        """
        old = self._override
        try:
            self.set_override(env)
            # yield control back to caller; discovery will now reflect override
            yield
        finally:
            # restore previous override/cache
            self._override = old
            # clear cache so next discover re-evaluates env vars if needed
            self._cache = None
            logger.debug("Environment override restored to %s", old)

    def register_environments(self, envs: Iterable[str]) -> None:
        """Register additional available environments.

        Environments are added in order; duplicates are ignored.
        """
        for e in envs:
            if not isinstance(e, str):
                raise TypeError("environment names must be strings")
            if e not in self.available:
                self.available.append(e)
                logger.debug("Registered environment '%s'", e)

        # ensure default is valid
        if self.default not in self.available and self.available:
            self.default = self.available[0]

    def is_valid(self, env: str) -> bool:
        """Return True if env is one of the available environments."""
        return env in self.available

    def _validate(self, env: str) -> str:
        if not isinstance(env, str):
            raise TypeError("env must be a string")
        if not env:
            raise InvalidEnvironmentError("environment name cannot be empty")
        if self.available and env not in self.available:
            raise InvalidEnvironmentError(f"Unknown environment: {env}")
        return env

    def _validate_and_cache(self, env: str) -> str:
        validated = self._validate(env)
        self._cache = validated
        return validated

    def available_environments(self) -> List[str]:
        """Return a copy of the available environments list."""
        return list(self.available)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"EnvironmentManager(available={self.available!r}, default={self.default!r}, "
            f"override={self._override!r}, cache={self._cache!r})"
        )


# module-level convenience manager
_default_manager: Optional[EnvironmentManager] = None


def get_manager() -> EnvironmentManager:
    """Return a module-level singleton EnvironmentManager.

    Using a singleton is convenient for small applications; callers may create
    their own EnvironmentManager if isolation is required.
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = EnvironmentManager()
    return _default_manager


__all__ = ["EnvironmentManager", "InvalidEnvironmentError", "get_manager"]
