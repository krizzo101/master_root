"""Smoke import tests for opsvi-memory.

Ensures public modules can be imported without side effects.
"""

import importlib
import pytest

def test_import_root():
    importlib.import_module("opsvi_memory")

@pytest.mark.parametrize(
    "mod",
    [
        "opsvi_memory.config.settings",
        "opsvi_memory.core.base",
        "opsvi_memory.exceptions.base",
    ],
)
def test_import_submodules(mod: str):
    importlib.import_module(mod)

"""Base tests for opsvi-memory.

Tests for opsvi-memory components
"""

import pytest
import asyncio
from typing import Any, Dict, Optional
from unittest.mock import Mock, AsyncMock, patch

from opsvi_memory.core.base import OpsviMemoryManager
from opsvi_memory.config.settings import OpsviMemoryConfig
from opsvi_memory.exceptions.base import OpsviMemoryError

class TestOpsviMemoryManager:
    """Test cases for OpsviMemoryManager."""

    @pytest.fixture
    def config(self) -> OpsviMemoryConfig:
        """Create test configuration."""
        return OpsviMemoryConfig(
            enabled=True,
            debug=True,
            log_level="DEBUG"
        )

    @pytest.fixture
    def component(self, config: OpsviMemoryConfig) -> OpsviMemoryManager:
        """Create test component."""
        return OpsviMemoryManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviMemoryManager) -> None:
        """Test component initialization."""
        await component.initialize()
        assert component._initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self, component: OpsviMemoryManager) -> None:
        """Test component shutdown."""
        await component.initialize()
        await component.shutdown()
        assert component._initialized is False

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, component: OpsviMemoryManager) -> None:
        """Test health check when initialized."""
        await component.initialize()
        assert await component.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, component: OpsviMemoryManager) -> None:
        """Test health check when not initialized."""
        assert await component.health_check() is False

    @pytest.mark.asyncio
    async def test_initialization_error(self, config: OpsviMemoryConfig) -> None:
        """Test initialization error handling."""
        # Mock component to raise error during initialization
        with patch.object(OpsviMemoryManager, '_initialize_component', side_effect=Exception("Init failed")):
            component = OpsviMemoryManager(config=config)
            with pytest.raises(OpsviMemoryErrorInitializationError):
                await component.initialize()

    @pytest.mark.asyncio
    async def test_shutdown_error(self, component: OpsviMemoryManager) -> None:
        """Test shutdown error handling."""
        await component.initialize()

        # Mock component to raise error during shutdown
        with patch.object(OpsviMemoryManager, '_shutdown_component', side_effect=Exception("Shutdown failed")):
            with pytest.raises(OpsviMemoryErrorError):
                await component.shutdown()

    # Component-specific tests
    
