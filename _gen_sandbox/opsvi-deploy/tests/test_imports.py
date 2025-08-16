"""Smoke import tests for opsvi-deploy.

Ensures public modules can be imported without side effects.
"""

import importlib
import pytest

def test_import_root():
    importlib.import_module("opsvi_deploy")

@pytest.mark.parametrize(
    "mod",
    [
        "opsvi_deploy.config.settings",
        "opsvi_deploy.core.base",
        "opsvi_deploy.exceptions.base",
    ],
)
def test_import_submodules(mod: str):
    importlib.import_module(mod)

"""Base tests for opsvi-deploy.

Tests for opsvi-deploy components
"""

import pytest
import asyncio
from typing import Any, Dict, Optional
from unittest.mock import Mock, AsyncMock, patch

from opsvi_deploy.core.base import OpsviDeployManager
from opsvi_deploy.config.settings import OpsviDeployConfig
from opsvi_deploy.exceptions.base import OpsviDeployError

class TestOpsviDeployManager:
    """Test cases for OpsviDeployManager."""

    @pytest.fixture
    def config(self) -> OpsviDeployConfig:
        """Create test configuration."""
        return OpsviDeployConfig(
            enabled=True,
            debug=True,
            log_level="DEBUG"
        )

    @pytest.fixture
    def component(self, config: OpsviDeployConfig) -> OpsviDeployManager:
        """Create test component."""
        return OpsviDeployManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviDeployManager) -> None:
        """Test component initialization."""
        await component.initialize()
        assert component._initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self, component: OpsviDeployManager) -> None:
        """Test component shutdown."""
        await component.initialize()
        await component.shutdown()
        assert component._initialized is False

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, component: OpsviDeployManager) -> None:
        """Test health check when initialized."""
        await component.initialize()
        assert await component.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, component: OpsviDeployManager) -> None:
        """Test health check when not initialized."""
        assert await component.health_check() is False

    @pytest.mark.asyncio
    async def test_initialization_error(self, config: OpsviDeployConfig) -> None:
        """Test initialization error handling."""
        # Mock component to raise error during initialization
        with patch.object(OpsviDeployManager, '_initialize_component', side_effect=Exception("Init failed")):
            component = OpsviDeployManager(config=config)
            with pytest.raises(OpsviDeployErrorInitializationError):
                await component.initialize()

    @pytest.mark.asyncio
    async def test_shutdown_error(self, component: OpsviDeployManager) -> None:
        """Test shutdown error handling."""
        await component.initialize()

        # Mock component to raise error during shutdown
        with patch.object(OpsviDeployManager, '_shutdown_component', side_effect=Exception("Shutdown failed")):
            with pytest.raises(OpsviDeployErrorError):
                await component.shutdown()

    # Component-specific tests
    
