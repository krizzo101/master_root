"""Smoke import tests for opsvi-monitoring.

Ensures public modules can be imported without side effects.
"""

import importlib
import pytest

def test_import_root():
    importlib.import_module("opsvi_monitoring")

@pytest.mark.parametrize(
    "mod",
    [
        "opsvi_monitoring.config.settings",
        "opsvi_monitoring.core.base",
        "opsvi_monitoring.exceptions.base",
    ],
)
def test_import_submodules(mod: str):
    importlib.import_module(mod)

"""Base tests for opsvi-monitoring.

Tests for opsvi-monitoring components
"""

import pytest
import asyncio
from typing import Any, Dict, Optional
from unittest.mock import Mock, AsyncMock, patch

from opsvi_monitoring.core.base import OpsviMonitoringManager
from opsvi_monitoring.config.settings import OpsviMonitoringConfig
from opsvi_monitoring.exceptions.base import OpsviMonitoringError

class TestOpsviMonitoringManager:
    """Test cases for OpsviMonitoringManager."""

    @pytest.fixture
    def config(self) -> OpsviMonitoringConfig:
        """Create test configuration."""
        return OpsviMonitoringConfig(
            enabled=True,
            debug=True,
            log_level="DEBUG"
        )

    @pytest.fixture
    def component(self, config: OpsviMonitoringConfig) -> OpsviMonitoringManager:
        """Create test component."""
        return OpsviMonitoringManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviMonitoringManager) -> None:
        """Test component initialization."""
        await component.initialize()
        assert component._initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self, component: OpsviMonitoringManager) -> None:
        """Test component shutdown."""
        await component.initialize()
        await component.shutdown()
        assert component._initialized is False

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, component: OpsviMonitoringManager) -> None:
        """Test health check when initialized."""
        await component.initialize()
        assert await component.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, component: OpsviMonitoringManager) -> None:
        """Test health check when not initialized."""
        assert await component.health_check() is False

    @pytest.mark.asyncio
    async def test_initialization_error(self, config: OpsviMonitoringConfig) -> None:
        """Test initialization error handling."""
        # Mock component to raise error during initialization
        with patch.object(OpsviMonitoringManager, '_initialize_component', side_effect=Exception("Init failed")):
            component = OpsviMonitoringManager(config=config)
            with pytest.raises(OpsviMonitoringErrorInitializationError):
                await component.initialize()

    @pytest.mark.asyncio
    async def test_shutdown_error(self, component: OpsviMonitoringManager) -> None:
        """Test shutdown error handling."""
        await component.initialize()

        # Mock component to raise error during shutdown
        with patch.object(OpsviMonitoringManager, '_shutdown_component', side_effect=Exception("Shutdown failed")):
            with pytest.raises(OpsviMonitoringErrorError):
                await component.shutdown()

    # Component-specific tests
    
