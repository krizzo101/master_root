"""Smoke import tests for opsvi-communication.

Ensures public modules can be imported without side effects.
"""

import importlib
import pytest

def test_import_root():
    importlib.import_module("opsvi_communication")

@pytest.mark.parametrize(
    "mod",
    [
        "opsvi_communication.config.settings",
        "opsvi_communication.core.base",
        "opsvi_communication.exceptions.base",
    ],
)
def test_import_submodules(mod: str):
    importlib.import_module(mod)

"""Base tests for opsvi-communication.

Tests for opsvi-communication components
"""

import pytest
import asyncio
from typing import Any, Dict, Optional
from unittest.mock import Mock, AsyncMock, patch

from opsvi_communication.core.base import OpsviCommunicationManager
from opsvi_communication.config.settings import OpsviCommunicationConfig
from opsvi_communication.exceptions.base import OpsviCommunicationError

class TestOpsviCommunicationManager:
    """Test cases for OpsviCommunicationManager."""

    @pytest.fixture
    def config(self) -> OpsviCommunicationConfig:
        """Create test configuration."""
        return OpsviCommunicationConfig(
            enabled=True,
            debug=True,
            log_level="DEBUG"
        )

    @pytest.fixture
    def component(self, config: OpsviCommunicationConfig) -> OpsviCommunicationManager:
        """Create test component."""
        return OpsviCommunicationManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviCommunicationManager) -> None:
        """Test component initialization."""
        await component.initialize()
        assert component._initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self, component: OpsviCommunicationManager) -> None:
        """Test component shutdown."""
        await component.initialize()
        await component.shutdown()
        assert component._initialized is False

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, component: OpsviCommunicationManager) -> None:
        """Test health check when initialized."""
        await component.initialize()
        assert await component.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, component: OpsviCommunicationManager) -> None:
        """Test health check when not initialized."""
        assert await component.health_check() is False

    @pytest.mark.asyncio
    async def test_initialization_error(self, config: OpsviCommunicationConfig) -> None:
        """Test initialization error handling."""
        # Mock component to raise error during initialization
        with patch.object(OpsviCommunicationManager, '_initialize_component', side_effect=Exception("Init failed")):
            component = OpsviCommunicationManager(config=config)
            with pytest.raises(OpsviCommunicationErrorInitializationError):
                await component.initialize()

    @pytest.mark.asyncio
    async def test_shutdown_error(self, component: OpsviCommunicationManager) -> None:
        """Test shutdown error handling."""
        await component.initialize()

        # Mock component to raise error during shutdown
        with patch.object(OpsviCommunicationManager, '_shutdown_component', side_effect=Exception("Shutdown failed")):
            with pytest.raises(OpsviCommunicationErrorError):
                await component.shutdown()

    # Component-specific tests
    
