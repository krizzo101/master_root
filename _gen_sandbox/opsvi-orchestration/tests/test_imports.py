"""Smoke import tests for opsvi-orchestration.

Ensures public modules can be imported without side effects.
"""

import importlib
import pytest

def test_import_root():
    importlib.import_module("opsvi_orchestration")

@pytest.mark.parametrize(
    "mod",
    [
        "opsvi_orchestration.config.settings",
        "opsvi_orchestration.core.base",
        "opsvi_orchestration.exceptions.base",
    ],
)
def test_import_submodules(mod: str):
    importlib.import_module(mod)

"""Base tests for opsvi-orchestration.

Tests for opsvi-orchestration components
"""

import pytest
import asyncio
from typing import Any, Dict, Optional
from unittest.mock import Mock, AsyncMock, patch

from opsvi_orchestration.core.base import OpsviOrchestrationManager
from opsvi_orchestration.config.settings import OpsviOrchestrationConfig
from opsvi_orchestration.exceptions.base import OpsviOrchestrationError

class TestOpsviOrchestrationManager:
    """Test cases for OpsviOrchestrationManager."""

    @pytest.fixture
    def config(self) -> OpsviOrchestrationConfig:
        """Create test configuration."""
        return OpsviOrchestrationConfig(
            enabled=True,
            debug=True,
            log_level="DEBUG"
        )

    @pytest.fixture
    def component(self, config: OpsviOrchestrationConfig) -> OpsviOrchestrationManager:
        """Create test component."""
        return OpsviOrchestrationManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviOrchestrationManager) -> None:
        """Test component initialization."""
        await component.initialize()
        assert component._initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self, component: OpsviOrchestrationManager) -> None:
        """Test component shutdown."""
        await component.initialize()
        await component.shutdown()
        assert component._initialized is False

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, component: OpsviOrchestrationManager) -> None:
        """Test health check when initialized."""
        await component.initialize()
        assert await component.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, component: OpsviOrchestrationManager) -> None:
        """Test health check when not initialized."""
        assert await component.health_check() is False

    @pytest.mark.asyncio
    async def test_initialization_error(self, config: OpsviOrchestrationConfig) -> None:
        """Test initialization error handling."""
        # Mock component to raise error during initialization
        with patch.object(OpsviOrchestrationManager, '_initialize_component', side_effect=Exception("Init failed")):
            component = OpsviOrchestrationManager(config=config)
            with pytest.raises(OpsviOrchestrationErrorInitializationError):
                await component.initialize()

    @pytest.mark.asyncio
    async def test_shutdown_error(self, component: OpsviOrchestrationManager) -> None:
        """Test shutdown error handling."""
        await component.initialize()

        # Mock component to raise error during shutdown
        with patch.object(OpsviOrchestrationManager, '_shutdown_component', side_effect=Exception("Shutdown failed")):
            with pytest.raises(OpsviOrchestrationErrorError):
                await component.shutdown()

    # Component-specific tests
    
