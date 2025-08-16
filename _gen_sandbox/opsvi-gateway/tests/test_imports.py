"""Smoke import tests for opsvi-gateway.

Ensures public modules can be imported without side effects.
"""

import importlib
import pytest

def test_import_root():
    importlib.import_module("opsvi_gateway")

@pytest.mark.parametrize(
    "mod",
    [
        "opsvi_gateway.config.settings",
        "opsvi_gateway.core.base",
        "opsvi_gateway.exceptions.base",
    ],
)
def test_import_submodules(mod: str):
    importlib.import_module(mod)

"""Base tests for opsvi-gateway.

Tests for opsvi-gateway components
"""

import pytest
import asyncio
from typing import Any, Dict, Optional
from unittest.mock import Mock, AsyncMock, patch

from opsvi_gateway.core.base import OpsviGatewayManager
from opsvi_gateway.config.settings import OpsviGatewayConfig
from opsvi_gateway.exceptions.base import OpsviGatewayError

class TestOpsviGatewayManager:
    """Test cases for OpsviGatewayManager."""

    @pytest.fixture
    def config(self) -> OpsviGatewayConfig:
        """Create test configuration."""
        return OpsviGatewayConfig(
            enabled=True,
            debug=True,
            log_level="DEBUG"
        )

    @pytest.fixture
    def component(self, config: OpsviGatewayConfig) -> OpsviGatewayManager:
        """Create test component."""
        return OpsviGatewayManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviGatewayManager) -> None:
        """Test component initialization."""
        await component.initialize()
        assert component._initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self, component: OpsviGatewayManager) -> None:
        """Test component shutdown."""
        await component.initialize()
        await component.shutdown()
        assert component._initialized is False

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, component: OpsviGatewayManager) -> None:
        """Test health check when initialized."""
        await component.initialize()
        assert await component.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, component: OpsviGatewayManager) -> None:
        """Test health check when not initialized."""
        assert await component.health_check() is False

    @pytest.mark.asyncio
    async def test_initialization_error(self, config: OpsviGatewayConfig) -> None:
        """Test initialization error handling."""
        # Mock component to raise error during initialization
        with patch.object(OpsviGatewayManager, '_initialize_component', side_effect=Exception("Init failed")):
            component = OpsviGatewayManager(config=config)
            with pytest.raises(OpsviGatewayErrorInitializationError):
                await component.initialize()

    @pytest.mark.asyncio
    async def test_shutdown_error(self, component: OpsviGatewayManager) -> None:
        """Test shutdown error handling."""
        await component.initialize()

        # Mock component to raise error during shutdown
        with patch.object(OpsviGatewayManager, '_shutdown_component', side_effect=Exception("Shutdown failed")):
            with pytest.raises(OpsviGatewayErrorError):
                await component.shutdown()

    # Component-specific tests
    
