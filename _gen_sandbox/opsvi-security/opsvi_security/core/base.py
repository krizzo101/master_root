"""opsvi-security - Core opsvi-security functionality.

Comprehensive opsvi-security library for the OPSVI ecosystem
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Awaitable, Callable
import asyncio
import logging
from datetime import datetime, timedelta

from opsvi_foundation import BaseComponent, ComponentError
from pydantic_settings import BaseSettings
from pydantic import Field, validator

logger = logging.getLogger(__name__)


class OpsviSecurityManagerError(ComponentError):
    """Base exception for opsvi-security errors."""
    pass


class OpsviSecurityManagerConfigurationError(OpsviSecurityManagerError):
    """Configuration-related errors in opsvi-security."""
    pass


class OpsviSecurityManagerInitializationError(OpsviSecurityManagerError):
    """Initialization-related errors in opsvi-security."""
    pass


class OpsviSecurityManagerConfig(BaseSettings):
    """Configuration for opsvi-security."""

    # Core configuration
    enabled: bool = True
    debug: bool = False
    log_level: str = Field("INFO", description="Python logging level name")

    # Component-specific configuration
    health_interval_seconds: int = Field(30, ge=5, description="Periodic health check interval")
    default_policy: str = Field(
        "deny", description="Default policy when no rule matches (allow/deny)"
    )
    allow_rules: List[str] = Field(default_factory=list, description="Simple allow rules")
    deny_rules: List[str] = Field(default_factory=list, description="Simple deny rules")

    class Config:
        env_prefix = "OPSVI_OPSVI_SECURITY__"

    @validator("log_level")
    def _validate_log_level(cls, v: str) -> str:
        if v.upper() not in {
            "CRITICAL",
            "ERROR",
            "WARNING",
            "INFO",
            "DEBUG",
            "NOTSET",
        }:
            raise OpsviSecurityManagerConfigurationError(
                f"Invalid log level: {v}"
            )
        return v.upper()

    @validator("default_policy")
    def _validate_policy(cls, v: str) -> str:
        if v.lower() not in {"allow", "deny"}:
            raise OpsviSecurityManagerConfigurationError(
                "default_policy must be 'allow' or 'deny'"
            )
        return v.lower()


class PolicyDecision:
    """Represents the outcome of an authorization decision."""

    def __init__(self, allowed: bool, reason: str = "", matched_rule: Optional[str] = None) -> None:
        self.allowed = allowed
        self.reason = reason
        self.matched_rule = matched_rule

    def __repr__(self) -> str:
        return f"PolicyDecision(allowed={self.allowed}, rule={self.matched_rule!r}, reason={self.reason!r})"


class OpsviSecurityManager(BaseComponent):
    """Base class for opsvi-security components.

    Provides base functionality for all opsvi-security components
    """

    def __init__(
        self,
        config: Optional[OpsviSecurityManagerConfig] = None,
        **kwargs: Any
    ) -> None:
        """Initialize OpsviSecurityManager.

        Args:
            config: Configuration for the component
            **kwargs: Additional configuration parameters
        """
        # Build config first to pass base settings dict to BaseComponent
        cfg = config or OpsviSecurityManagerConfig(**kwargs)
        super().__init__("opsvi-security", cfg.dict())
        self.config = cfg
        self._initialized = False
        self._logger = logging.getLogger(f"{__name__}.opsvi-security")

        # In-memory rule sets for quick checks
        self._allow: List[str] = []
        self._deny: List[str] = []

        # Health tracking
        self._last_health_ok: Optional[datetime] = None
        self._bg_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        """Initialize the component.

        Raises:
            OpsviSecurityManagerInitializationError: If initialization fails
        """
        try:
            # Configure logging level
            self._logger.setLevel(getattr(logging, self.config.log_level))
            self._logger.debug("Starting initialization of opsvi-security")

            if not self.config.enabled:
                self._logger.info("opsvi-security is disabled by configuration")
                self._initialized = True
                return

            # Load rules from config
            self._allow = list(dict.fromkeys(self.config.allow_rules))
            self._deny = list(dict.fromkeys(self.config.deny_rules))

            # Basic validation
            for r in self._allow + self._deny:
                if not r or not isinstance(r, str):
                    raise OpsviSecurityManagerInitializationError("Invalid rule encountered")

            self._last_health_ok = datetime.utcnow()

            # Start background health ticker
            self._bg_task = asyncio.create_task(self._health_ticker())

            self._initialized = True
            self._logger.info("opsvi-security initialized successfully")

        except Exception as e:
            self._logger.error(f"Failed to initialize opsvi-security: {e}")
            raise OpsviSecurityManagerInitializationError(f"Initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown the component.

        Raises:
            OpsviSecurityManagerError: If shutdown fails
        """
        try:
            self._logger.info("Shutting down opsvi-security")

            # Cancel background task if running
            if self._bg_task and not self._bg_task.done():
                self._bg_task.cancel()
                try:
                    await self._bg_task
                except asyncio.CancelledError:
                    pass
                finally:
                    self._bg_task = None

            self._initialized = False
            self._logger.info("opsvi-security shut down successfully")

        except Exception as e:
            self._logger.error(f"Failed to shutdown opsvi-security: {e}")
            raise OpsviSecurityManagerError(f"Shutdown failed: {e}") from e

    async def health_check(self) -> bool:
        """Perform health check.

        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self._initialized:
                return False

            # Simple liveness based on last successful tick
            if self._last_health_ok is None:
                return False
            delta = datetime.utcnow() - self._last_health_ok
            return delta <= timedelta(seconds=self.config.health_interval_seconds * 2)

        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False

    # Component-specific methods
    async def authorize(self, subject: str, action: str, resource: str, context: Optional[Dict[str, Any]] = None) -> PolicyDecision:
        """Authorize a subject performing an action on a resource.

        Implements a simple rule engine with allow/deny lists of patterns.
        Rule format examples: "user:read:resource", "*:write:projects/*", "user:*:*".
        Deny rules take precedence over allow rules. If no rule matches, default_policy applies.
        """
        if not self._initialized or not self.config.enabled:
            return PolicyDecision(False, reason="service_unavailable")

        key = f"{subject}:{action}:{resource}"
        # Deny takes precedence
        for rule in self._deny:
            if _match_rule(rule, key):
                return PolicyDecision(False, reason="matched_deny_rule", matched_rule=rule)
        for rule in self._allow:
            if _match_rule(rule, key):
                return PolicyDecision(True, reason="matched_allow_rule", matched_rule=rule)

        return PolicyDecision(self.config.default_policy == "allow", reason="default_policy")

    async def update_rules(self, allow: Optional[List[str]] = None, deny: Optional[List[str]] = None) -> None:
        """Replace allow/deny rule sets atomically."""
        if not self._initialized:
            raise OpsviSecurityManagerError("Component not initialized")
        if allow is not None:
            self._allow = list(dict.fromkeys([r for r in allow if isinstance(r, str) and r]))
        if deny is not None:
            self._deny = list(dict.fromkeys([r for r in deny if isinstance(r, str) and r]))
        self._logger.debug("Rules updated: allow=%d deny=%d", len(self._allow), len(self._deny))

    async def add_rule(self, rule: str, allow: bool = True) -> None:
        """Add a single rule to allow or deny sets."""
        if not rule or not isinstance(rule, str):
            raise OpsviSecurityManagerError("Invalid rule")
        target = self._allow if allow else self._deny
        if rule not in target:
            target.append(rule)

    async def remove_rule(self, rule: str) -> None:
        """Remove a rule from both allow and deny sets if present."""
        try:
            if rule in self._allow:
                self._allow.remove(rule)
            if rule in self._deny:
                self._deny.remove(rule)
        except ValueError:
            pass

    async def _health_ticker(self) -> None:
        """Background coroutine to advance health heartbeat."""
        try:
            interval = max(5, self.config.health_interval_seconds)
            while True:
                await asyncio.sleep(interval)
                # lightweight self-check
                self._last_health_ok = datetime.utcnow()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self._logger.error("Health ticker error: %s", e)


def _match_rule(rule: str, key: str) -> bool:
    """Match a rule with '*' wildcards against a key of form 'a:b:c'."""
    r_parts = rule.split(":")
    k_parts = key.split(":")
    if len(r_parts) != len(k_parts):
        return False
    for rp, kp in zip(r_parts, k_parts):
        if rp == "*":
            continue
        # support segment wildcard like 'projects/*'
        if rp.endswith("/*") and kp.startswith(rp[:-1]):
            continue
        if rp != kp:
            return False
    return True
