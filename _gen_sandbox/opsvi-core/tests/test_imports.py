"""Smoke import tests for opsvi-core.

Ensures public modules can be imported without side effects.
"""

import importlib
import pytest

def test_import_root():
    importlib.import_module("opsvi_core")

@pytest.mark.parametrize(
    "mod",
    [
        "opsvi_core.config.settings",
        "opsvi_core.core.base",
        "opsvi_core.exceptions.base",
    ],
)
def test_import_submodules(mod: str):
    importlib.import_module(mod)

"""Base tests for opsvi-core.

Tests for opsvi-core components
"""

import pytest
import asyncio
from typing import Any, Dict, Optional
from unittest.mock import Mock, AsyncMock, patch

from opsvi_core.core.base import OpsviCoreManager
from opsvi_core.config.settings import OpsviCoreConfig
from opsvi_core.exceptions.base import OpsviCoreError

class TestOpsviCoreManager:
    """Test cases for OpsviCoreManager."""

    @pytest.fixture
    def config(self) -> OpsviCoreConfig:
        """Create test configuration."""
        return OpsviCoreConfig(
            enabled=True,
            debug=True,
            log_level="DEBUG"
        )

    @pytest.fixture
    def component(self, config: OpsviCoreConfig) -> OpsviCoreManager:
        """Create test component."""
        return OpsviCoreManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviCoreManager) -> None:
        """Test component initialization."""
        await component.initialize()
        assert component._initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self, component: OpsviCoreManager) -> None:
        """Test component shutdown."""
        await component.initialize()
        await component.shutdown()
        assert component._initialized is False

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, component: OpsviCoreManager) -> None:
        """Test health check when initialized."""
        await component.initialize()
        assert await component.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, component: OpsviCoreManager) -> None:
        """Test health check when not initialized."""
        assert await component.health_check() is False

    @pytest.mark.asyncio
    async def test_initialization_error(self, config: OpsviCoreConfig) -> None:
        """Test initialization error handling."""
        # Mock component to raise error during initialization
        with patch.object(OpsviCoreManager, '_initialize_component', side_effect=Exception("Init failed")):
            component = OpsviCoreManager(config=config)
            with pytest.raises(OpsviCoreErrorInitializationError):
                await component.initialize()

    @pytest.mark.asyncio
    async def test_shutdown_error(self, component: OpsviCoreManager) -> None:
        """Test shutdown error handling."""
        await component.initialize()

        # Mock component to raise error during shutdown
        with patch.object(OpsviCoreManager, '_shutdown_component', side_effect=Exception("Shutdown failed")):
            with pytest.raises(OpsviCoreErrorError):
                await component.shutdown()

    # Component-specific tests
    
