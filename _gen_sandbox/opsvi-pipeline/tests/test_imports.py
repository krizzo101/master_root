"""Smoke import tests for opsvi-pipeline.

Ensures public modules can be imported without side effects.
"""

import importlib
import pytest

def test_import_root():
    importlib.import_module("opsvi_pipeline")

@pytest.mark.parametrize(
    "mod",
    [
        "opsvi_pipeline.config.settings",
        "opsvi_pipeline.core.base",
        "opsvi_pipeline.exceptions.base",
    ],
)
def test_import_submodules(mod: str):
    importlib.import_module(mod)

"""Base tests for opsvi-pipeline.

Tests for opsvi-pipeline components
"""

import pytest
import asyncio
from typing import Any, Dict, Optional
from unittest.mock import Mock, AsyncMock, patch

from opsvi_pipeline.core.base import OpsviPipelineManager
from opsvi_pipeline.config.settings import OpsviPipelineConfig
from opsvi_pipeline.exceptions.base import OpsviPipelineError

class TestOpsviPipelineManager:
    """Test cases for OpsviPipelineManager."""

    @pytest.fixture
    def config(self) -> OpsviPipelineConfig:
        """Create test configuration."""
        return OpsviPipelineConfig(
            enabled=True,
            debug=True,
            log_level="DEBUG"
        )

    @pytest.fixture
    def component(self, config: OpsviPipelineConfig) -> OpsviPipelineManager:
        """Create test component."""
        return OpsviPipelineManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviPipelineManager) -> None:
        """Test component initialization."""
        await component.initialize()
        assert component._initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self, component: OpsviPipelineManager) -> None:
        """Test component shutdown."""
        await component.initialize()
        await component.shutdown()
        assert component._initialized is False

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, component: OpsviPipelineManager) -> None:
        """Test health check when initialized."""
        await component.initialize()
        assert await component.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, component: OpsviPipelineManager) -> None:
        """Test health check when not initialized."""
        assert await component.health_check() is False

    @pytest.mark.asyncio
    async def test_initialization_error(self, config: OpsviPipelineConfig) -> None:
        """Test initialization error handling."""
        # Mock component to raise error during initialization
        with patch.object(OpsviPipelineManager, '_initialize_component', side_effect=Exception("Init failed")):
            component = OpsviPipelineManager(config=config)
            with pytest.raises(OpsviPipelineErrorInitializationError):
                await component.initialize()

    @pytest.mark.asyncio
    async def test_shutdown_error(self, component: OpsviPipelineManager) -> None:
        """Test shutdown error handling."""
        await component.initialize()

        # Mock component to raise error during shutdown
        with patch.object(OpsviPipelineManager, '_shutdown_component', side_effect=Exception("Shutdown failed")):
            with pytest.raises(OpsviPipelineErrorError):
                await component.shutdown()

    # Component-specific tests
    
