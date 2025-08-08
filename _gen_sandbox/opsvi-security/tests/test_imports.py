"""Smoke import tests for opsvi-security.

Ensures public modules can be imported without side effects.
"""

import importlib
import pytest

def test_import_root():
    importlib.import_module("opsvi_security")

@pytest.mark.parametrize(
    "mod",
    [
        "opsvi_security.config.settings",
        "opsvi_security.core.base",
        "opsvi_security.exceptions.base",
    ],
)
def test_import_submodules(mod: str):
    importlib.import_module(mod)

"""Base tests for opsvi-security.

Tests for opsvi-security components
"""

import pytest
import asyncio
from typing import Any, Dict, Optional
from unittest.mock import Mock, AsyncMock, patch

from opsvi_security.core.base import OpsviSecurityManager
from opsvi_security.config.settings import OpsviSecurityConfig
from opsvi_security.exceptions.base import OpsviSecurityError

class TestOpsviSecurityManager:
    """Test cases for OpsviSecurityManager."""

    @pytest.fixture
    def config(self) -> OpsviSecurityConfig:
        """Create test configuration."""
        return OpsviSecurityConfig(
            enabled=True,
            debug=True,
            log_level="DEBUG"
        )

    @pytest.fixture
    def component(self, config: OpsviSecurityConfig) -> OpsviSecurityManager:
        """Create test component."""
        return OpsviSecurityManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviSecurityManager) -> None:
        """Test component initialization."""
        await component.initialize()
        assert component._initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self, component: OpsviSecurityManager) -> None:
        """Test component shutdown."""
        await component.initialize()
        await component.shutdown()
        assert component._initialized is False

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, component: OpsviSecurityManager) -> None:
        """Test health check when initialized."""
        await component.initialize()
        assert await component.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, component: OpsviSecurityManager) -> None:
        """Test health check when not initialized."""
        assert await component.health_check() is False

    @pytest.mark.asyncio
    async def test_initialization_error(self, config: OpsviSecurityConfig) -> None:
        """Test initialization error handling."""
        # Mock component to raise error during initialization
        with patch.object(OpsviSecurityManager, '_initialize_component', side_effect=Exception("Init failed")):
            component = OpsviSecurityManager(config=config)
            with pytest.raises(OpsviSecurityErrorInitializationError):
                await component.initialize()

    @pytest.mark.asyncio
    async def test_shutdown_error(self, component: OpsviSecurityManager) -> None:
        """Test shutdown error handling."""
        await component.initialize()

        # Mock component to raise error during shutdown
        with patch.object(OpsviSecurityManager, '_shutdown_component', side_effect=Exception("Shutdown failed")):
            with pytest.raises(OpsviSecurityErrorError):
                await component.shutdown()

    # Component-specific tests
    
