"""Smoke import tests for opsvi-rag.

Ensures public modules can be imported without side effects.
"""

import importlib
import pytest

def test_import_root():
    importlib.import_module("opsvi_rag")

@pytest.mark.parametrize(
    "mod",
    [
        "opsvi_rag.config.settings",
        "opsvi_rag.core.base",
        "opsvi_rag.exceptions.base",
    ],
)
def test_import_submodules(mod: str):
    importlib.import_module(mod)

"""Base tests for opsvi-rag.

Tests for opsvi-rag components
"""

import pytest
import asyncio
from typing import Any, Dict, Optional
from unittest.mock import Mock, AsyncMock, patch

from opsvi_rag.core.base import OpsviRagManager
from opsvi_rag.config.settings import OpsviRagConfig
from opsvi_rag.exceptions.base import OpsviRagError

class TestOpsviRagManager:
    """Test cases for OpsviRagManager."""

    @pytest.fixture
    def config(self) -> OpsviRagConfig:
        """Create test configuration."""
        return OpsviRagConfig(
            enabled=True,
            debug=True,
            log_level="DEBUG"
        )

    @pytest.fixture
    def component(self, config: OpsviRagConfig) -> OpsviRagManager:
        """Create test component."""
        return OpsviRagManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviRagManager) -> None:
        """Test component initialization."""
        await component.initialize()
        assert component._initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self, component: OpsviRagManager) -> None:
        """Test component shutdown."""
        await component.initialize()
        await component.shutdown()
        assert component._initialized is False

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, component: OpsviRagManager) -> None:
        """Test health check when initialized."""
        await component.initialize()
        assert await component.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, component: OpsviRagManager) -> None:
        """Test health check when not initialized."""
        assert await component.health_check() is False

    @pytest.mark.asyncio
    async def test_initialization_error(self, config: OpsviRagConfig) -> None:
        """Test initialization error handling."""
        # Mock component to raise error during initialization
        with patch.object(OpsviRagManager, '_initialize_component', side_effect=Exception("Init failed")):
            component = OpsviRagManager(config=config)
            with pytest.raises(OpsviRagErrorInitializationError):
                await component.initialize()

    @pytest.mark.asyncio
    async def test_shutdown_error(self, component: OpsviRagManager) -> None:
        """Test shutdown error handling."""
        await component.initialize()

        # Mock component to raise error during shutdown
        with patch.object(OpsviRagManager, '_shutdown_component', side_effect=Exception("Shutdown failed")):
            with pytest.raises(OpsviRagErrorError):
                await component.shutdown()

    # Component-specific tests
    
