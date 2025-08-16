"""Smoke import tests for opsvi-fs.

Ensures public modules can be imported without side effects.
"""

import importlib
import pytest

def test_import_root():
    importlib.import_module("opsvi_fs")

@pytest.mark.parametrize(
    "mod",
    [
        "opsvi_fs.config.settings",
        "opsvi_fs.core.base",
        "opsvi_fs.exceptions.base",
    ],
)
def test_import_submodules(mod: str):
    importlib.import_module(mod)

"""Base tests for opsvi-fs.

Tests for opsvi-fs components
"""

import pytest
import asyncio
from typing import Any, Dict, Optional
from unittest.mock import Mock, AsyncMock, patch

from opsvi_fs.core.base import OpsviFsManager
from opsvi_fs.config.settings import OpsviFsConfig
from opsvi_fs.exceptions.base import OpsviFsError

class TestOpsviFsManager:
    """Test cases for OpsviFsManager."""

    @pytest.fixture
    def config(self) -> OpsviFsConfig:
        """Create test configuration."""
        return OpsviFsConfig(
            enabled=True,
            debug=True,
            log_level="DEBUG"
        )

    @pytest.fixture
    def component(self, config: OpsviFsConfig) -> OpsviFsManager:
        """Create test component."""
        return OpsviFsManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviFsManager) -> None:
        """Test component initialization."""
        await component.initialize()
        assert component._initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self, component: OpsviFsManager) -> None:
        """Test component shutdown."""
        await component.initialize()
        await component.shutdown()
        assert component._initialized is False

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, component: OpsviFsManager) -> None:
        """Test health check when initialized."""
        await component.initialize()
        assert await component.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, component: OpsviFsManager) -> None:
        """Test health check when not initialized."""
        assert await component.health_check() is False

    @pytest.mark.asyncio
    async def test_initialization_error(self, config: OpsviFsConfig) -> None:
        """Test initialization error handling."""
        # Mock component to raise error during initialization
        with patch.object(OpsviFsManager, '_initialize_component', side_effect=Exception("Init failed")):
            component = OpsviFsManager(config=config)
            with pytest.raises(OpsviFsErrorInitializationError):
                await component.initialize()

    @pytest.mark.asyncio
    async def test_shutdown_error(self, component: OpsviFsManager) -> None:
        """Test shutdown error handling."""
        await component.initialize()

        # Mock component to raise error during shutdown
        with patch.object(OpsviFsManager, '_shutdown_component', side_effect=Exception("Shutdown failed")):
            with pytest.raises(OpsviFsErrorError):
                await component.shutdown()

    # Component-specific tests
    
