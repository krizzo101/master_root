"""Smoke import tests for opsvi-foundation.

Ensures public modules can be imported without side effects.
"""

import importlib
import pytest

def test_import_root():
    importlib.import_module("opsvi_foundation")

@pytest.mark.parametrize(
    "mod",
    [
        "opsvi_foundation.config.settings",
        "opsvi_foundation.core.base",
        "opsvi_foundation.exceptions.base",
    ],
)
def test_import_submodules(mod: str):
    importlib.import_module(mod)

"""Base tests for opsvi-foundation.

Tests for opsvi-foundation components
"""

import pytest
import asyncio
from typing import Any, Dict, Optional
from unittest.mock import Mock, AsyncMock, patch

from opsvi_foundation.core.base import OpsviFoundationManager
from opsvi_foundation.config.settings import OpsviFoundationConfig
from opsvi_foundation.exceptions.base import OpsviFoundationError

class TestOpsviFoundationManager:
    """Test cases for OpsviFoundationManager."""

    @pytest.fixture
    def config(self) -> OpsviFoundationConfig:
        """Create test configuration."""
        return OpsviFoundationConfig(
            enabled=True,
            debug=True,
            log_level="DEBUG"
        )

    @pytest.fixture
    def component(self, config: OpsviFoundationConfig) -> OpsviFoundationManager:
        """Create test component."""
        return OpsviFoundationManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviFoundationManager) -> None:
        """Test component initialization."""
        await component.initialize()
        assert component._initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self, component: OpsviFoundationManager) -> None:
        """Test component shutdown."""
        await component.initialize()
        await component.shutdown()
        assert component._initialized is False

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, component: OpsviFoundationManager) -> None:
        """Test health check when initialized."""
        await component.initialize()
        assert await component.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, component: OpsviFoundationManager) -> None:
        """Test health check when not initialized."""
        assert await component.health_check() is False

    @pytest.mark.asyncio
    async def test_initialization_error(self, config: OpsviFoundationConfig) -> None:
        """Test initialization error handling."""
        # Mock component to raise error during initialization
        with patch.object(OpsviFoundationManager, '_initialize_component', side_effect=Exception("Init failed")):
            component = OpsviFoundationManager(config=config)
            with pytest.raises(OpsviFoundationErrorInitializationError):
                await component.initialize()

    @pytest.mark.asyncio
    async def test_shutdown_error(self, component: OpsviFoundationManager) -> None:
        """Test shutdown error handling."""
        await component.initialize()

        # Mock component to raise error during shutdown
        with patch.object(OpsviFoundationManager, '_shutdown_component', side_effect=Exception("Shutdown failed")):
            with pytest.raises(OpsviFoundationErrorError):
                await component.shutdown()

    # Component-specific tests
    
