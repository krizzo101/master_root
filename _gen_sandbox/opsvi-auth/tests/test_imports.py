"""Smoke import tests for opsvi-auth.

Ensures public modules can be imported without side effects.
"""

import importlib
import pytest

def test_import_root():
    importlib.import_module("opsvi_auth")

@pytest.mark.parametrize(
    "mod",
    [
        "opsvi_auth.config.settings",
        "opsvi_auth.core.base",
        "opsvi_auth.exceptions.base",
    ],
)
def test_import_submodules(mod: str):
    importlib.import_module(mod)

"""Base tests for opsvi-auth.

Tests for opsvi-auth components
"""

import pytest
import asyncio
from typing import Any, Dict, Optional
from unittest.mock import Mock, AsyncMock, patch

from opsvi_auth.core.base import OpsviAuthManager
from opsvi_auth.config.settings import OpsviAuthConfig
from opsvi_auth.exceptions.base import OpsviAuthError

class TestOpsviAuthManager:
    """Test cases for OpsviAuthManager."""

    @pytest.fixture
    def config(self) -> OpsviAuthConfig:
        """Create test configuration."""
        return OpsviAuthConfig(
            enabled=True,
            debug=True,
            log_level="DEBUG"
        )

    @pytest.fixture
    def component(self, config: OpsviAuthConfig) -> OpsviAuthManager:
        """Create test component."""
        return OpsviAuthManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviAuthManager) -> None:
        """Test component initialization."""
        await component.initialize()
        assert component._initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self, component: OpsviAuthManager) -> None:
        """Test component shutdown."""
        await component.initialize()
        await component.shutdown()
        assert component._initialized is False

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, component: OpsviAuthManager) -> None:
        """Test health check when initialized."""
        await component.initialize()
        assert await component.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, component: OpsviAuthManager) -> None:
        """Test health check when not initialized."""
        assert await component.health_check() is False

    @pytest.mark.asyncio
    async def test_initialization_error(self, config: OpsviAuthConfig) -> None:
        """Test initialization error handling."""
        # Mock component to raise error during initialization
        with patch.object(OpsviAuthManager, '_initialize_component', side_effect=Exception("Init failed")):
            component = OpsviAuthManager(config=config)
            with pytest.raises(OpsviAuthErrorInitializationError):
                await component.initialize()

    @pytest.mark.asyncio
    async def test_shutdown_error(self, component: OpsviAuthManager) -> None:
        """Test shutdown error handling."""
        await component.initialize()

        # Mock component to raise error during shutdown
        with patch.object(OpsviAuthManager, '_shutdown_component', side_effect=Exception("Shutdown failed")):
            with pytest.raises(OpsviAuthErrorError):
                await component.shutdown()

    # Component-specific tests
    
