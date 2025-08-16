"""Smoke import tests for opsvi-data.

Ensures public modules can be imported without side effects.
"""

import importlib
import pytest

def test_import_root():
    importlib.import_module("opsvi_data")

@pytest.mark.parametrize(
    "mod",
    [
        "opsvi_data.config.settings",
        "opsvi_data.core.base",
        "opsvi_data.exceptions.base",
    ],
)
def test_import_submodules(mod: str):
    importlib.import_module(mod)

"""Base tests for opsvi-data.

Tests for opsvi-data components
"""

import pytest
import asyncio
from typing import Any, Dict, Optional
from unittest.mock import Mock, AsyncMock, patch

from opsvi_data.core.base import OpsviDataManager
from opsvi_data.config.settings import OpsviDataConfig
from opsvi_data.exceptions.base import OpsviDataError

class TestOpsviDataManager:
    """Test cases for OpsviDataManager."""

    @pytest.fixture
    def config(self) -> OpsviDataConfig:
        """Create test configuration."""
        return OpsviDataConfig(
            enabled=True,
            debug=True,
            log_level="DEBUG"
        )

    @pytest.fixture
    def component(self, config: OpsviDataConfig) -> OpsviDataManager:
        """Create test component."""
        return OpsviDataManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviDataManager) -> None:
        """Test component initialization."""
        await component.initialize()
        assert component._initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self, component: OpsviDataManager) -> None:
        """Test component shutdown."""
        await component.initialize()
        await component.shutdown()
        assert component._initialized is False

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, component: OpsviDataManager) -> None:
        """Test health check when initialized."""
        await component.initialize()
        assert await component.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, component: OpsviDataManager) -> None:
        """Test health check when not initialized."""
        assert await component.health_check() is False

    @pytest.mark.asyncio
    async def test_initialization_error(self, config: OpsviDataConfig) -> None:
        """Test initialization error handling."""
        # Mock component to raise error during initialization
        with patch.object(OpsviDataManager, '_initialize_component', side_effect=Exception("Init failed")):
            component = OpsviDataManager(config=config)
            with pytest.raises(OpsviDataErrorInitializationError):
                await component.initialize()

    @pytest.mark.asyncio
    async def test_shutdown_error(self, component: OpsviDataManager) -> None:
        """Test shutdown error handling."""
        await component.initialize()

        # Mock component to raise error during shutdown
        with patch.object(OpsviDataManager, '_shutdown_component', side_effect=Exception("Shutdown failed")):
            with pytest.raises(OpsviDataErrorError):
                await component.shutdown()

    # Component-specific tests
    
