"""Smoke import tests for opsvi-llm.

Ensures public modules can be imported without side effects.
"""

import importlib
import pytest

def test_import_root():
    importlib.import_module("opsvi_llm")

@pytest.mark.parametrize(
    "mod",
    [
        "opsvi_llm.config.settings",
        "opsvi_llm.core.base",
        "opsvi_llm.exceptions.base",
    ],
)
def test_import_submodules(mod: str):
    importlib.import_module(mod)

"""Base tests for opsvi-llm.

Tests for opsvi-llm components
"""

import pytest
import asyncio
from typing import Any, Dict, Optional
from unittest.mock import Mock, AsyncMock, patch

from opsvi_llm.core.base import OpsviLlmManager
from opsvi_llm.config.settings import OpsviLlmConfig
from opsvi_llm.exceptions.base import OpsviLlmError

class TestOpsviLlmManager:
    """Test cases for OpsviLlmManager."""

    @pytest.fixture
    def config(self) -> OpsviLlmConfig:
        """Create test configuration."""
        return OpsviLlmConfig(
            enabled=True,
            debug=True,
            log_level="DEBUG"
        )

    @pytest.fixture
    def component(self, config: OpsviLlmConfig) -> OpsviLlmManager:
        """Create test component."""
        return OpsviLlmManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviLlmManager) -> None:
        """Test component initialization."""
        await component.initialize()
        assert component._initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self, component: OpsviLlmManager) -> None:
        """Test component shutdown."""
        await component.initialize()
        await component.shutdown()
        assert component._initialized is False

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, component: OpsviLlmManager) -> None:
        """Test health check when initialized."""
        await component.initialize()
        assert await component.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, component: OpsviLlmManager) -> None:
        """Test health check when not initialized."""
        assert await component.health_check() is False

    @pytest.mark.asyncio
    async def test_initialization_error(self, config: OpsviLlmConfig) -> None:
        """Test initialization error handling."""
        # Mock component to raise error during initialization
        with patch.object(OpsviLlmManager, '_initialize_component', side_effect=Exception("Init failed")):
            component = OpsviLlmManager(config=config)
            with pytest.raises(OpsviLlmErrorInitializationError):
                await component.initialize()

    @pytest.mark.asyncio
    async def test_shutdown_error(self, component: OpsviLlmManager) -> None:
        """Test shutdown error handling."""
        await component.initialize()

        # Mock component to raise error during shutdown
        with patch.object(OpsviLlmManager, '_shutdown_component', side_effect=Exception("Shutdown failed")):
            with pytest.raises(OpsviLlmErrorError):
                await component.shutdown()

    # Component-specific tests
    
