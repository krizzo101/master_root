"""Smoke import tests for opsvi-http.

Ensures public modules can be imported without side effects.
"""

import importlib
import pytest

def test_import_root():
    importlib.import_module("opsvi_http")

@pytest.mark.parametrize(
    "mod",
    [
        "opsvi_http.config.settings",
        "opsvi_http.core.base",
        "opsvi_http.exceptions.base",
    ],
)
def test_import_submodules(mod: str):
    importlib.import_module(mod)

"""Base tests for opsvi-http.

Tests for opsvi-http components
"""

import pytest
import asyncio
from typing import Any, Dict, Optional
from unittest.mock import Mock, AsyncMock, patch

from opsvi_http.core.base import OpsviHttpManager
from opsvi_http.config.settings import OpsviHttpConfig
from opsvi_http.exceptions.base import OpsviHttpError

class TestOpsviHttpManager:
    """Test cases for OpsviHttpManager."""

    @pytest.fixture
    def config(self) -> OpsviHttpConfig:
        """Create test configuration."""
        return OpsviHttpConfig(
            enabled=True,
            debug=True,
            log_level="DEBUG"
        )

    @pytest.fixture
    def component(self, config: OpsviHttpConfig) -> OpsviHttpManager:
        """Create test component."""
        return OpsviHttpManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviHttpManager) -> None:
        """Test component initialization."""
        await component.initialize()
        assert component._initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self, component: OpsviHttpManager) -> None:
        """Test component shutdown."""
        await component.initialize()
        await component.shutdown()
        assert component._initialized is False

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, component: OpsviHttpManager) -> None:
        """Test health check when initialized."""
        await component.initialize()
        assert await component.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, component: OpsviHttpManager) -> None:
        """Test health check when not initialized."""
        assert await component.health_check() is False

    @pytest.mark.asyncio
    async def test_initialization_error(self, config: OpsviHttpConfig) -> None:
        """Test initialization error handling."""
        # Mock component to raise error during initialization
        with patch.object(OpsviHttpManager, '_initialize_component', side_effect=Exception("Init failed")):
            component = OpsviHttpManager(config=config)
            with pytest.raises(OpsviHttpErrorInitializationError):
                await component.initialize()

    @pytest.mark.asyncio
    async def test_shutdown_error(self, component: OpsviHttpManager) -> None:
        """Test shutdown error handling."""
        await component.initialize()

        # Mock component to raise error during shutdown
        with patch.object(OpsviHttpManager, '_shutdown_component', side_effect=Exception("Shutdown failed")):
            with pytest.raises(OpsviHttpErrorError):
                await component.shutdown()

    # Component-specific tests
    
