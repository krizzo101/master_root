"""Smoke import tests for opsvi-agents.

Ensures public modules can be imported without side effects.
"""

import importlib
import pytest

def test_import_root():
    importlib.import_module("opsvi_agents")

@pytest.mark.parametrize(
    "mod",
    [
        "opsvi_agents.config.settings",
        "opsvi_agents.core.base",
        "opsvi_agents.exceptions.base",
    ],
)
def test_import_submodules(mod: str):
    importlib.import_module(mod)

"""Base tests for opsvi-agents.

Tests for opsvi-agents components
"""

import pytest
import asyncio
from typing import Any, Dict, Optional
from unittest.mock import Mock, AsyncMock, patch

from opsvi_agents.core.base import OpsviAgentsManager
from opsvi_agents.config.settings import OpsviAgentsConfig
from opsvi_agents.exceptions.base import OpsviAgentsError

class TestOpsviAgentsManager:
    """Test cases for OpsviAgentsManager."""

    @pytest.fixture
    def config(self) -> OpsviAgentsConfig:
        """Create test configuration."""
        return OpsviAgentsConfig(
            enabled=True,
            debug=True,
            log_level="DEBUG"
        )

    @pytest.fixture
    def component(self, config: OpsviAgentsConfig) -> OpsviAgentsManager:
        """Create test component."""
        return OpsviAgentsManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviAgentsManager) -> None:
        """Test component initialization."""
        await component.initialize()
        assert component._initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self, component: OpsviAgentsManager) -> None:
        """Test component shutdown."""
        await component.initialize()
        await component.shutdown()
        assert component._initialized is False

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, component: OpsviAgentsManager) -> None:
        """Test health check when initialized."""
        await component.initialize()
        assert await component.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, component: OpsviAgentsManager) -> None:
        """Test health check when not initialized."""
        assert await component.health_check() is False

    @pytest.mark.asyncio
    async def test_initialization_error(self, config: OpsviAgentsConfig) -> None:
        """Test initialization error handling."""
        # Mock component to raise error during initialization
        with patch.object(OpsviAgentsManager, '_initialize_component', side_effect=Exception("Init failed")):
            component = OpsviAgentsManager(config=config)
            with pytest.raises(OpsviAgentsErrorInitializationError):
                await component.initialize()

    @pytest.mark.asyncio
    async def test_shutdown_error(self, component: OpsviAgentsManager) -> None:
        """Test shutdown error handling."""
        await component.initialize()

        # Mock component to raise error during shutdown
        with patch.object(OpsviAgentsManager, '_shutdown_component', side_effect=Exception("Shutdown failed")):
            with pytest.raises(OpsviAgentsErrorError):
                await component.shutdown()

    # Component-specific tests
    
