"""Tests for opsvi-memory.

Tests for opsvi-memory components
"""

import pytest

from opsvi_memory import OpsviMemoryManager
from opsvi_memory.config.settings import OpsviMemoryConfig
from opsvi_memory.exceptions.base import OpsviMemoryError


class TestOpsviMemory:
    """Test cases for opsvi-memory."""

    @pytest.fixture
    def config(self) -> OpsviMemoryConfig:
        """Create test configuration."""
        return OpsviMemoryConfig(enabled=True, debug=True)

    @pytest.fixture
    def component(self, config: OpsviMemoryConfig) -> OpsviMemoryManager:
        """Create test component."""
        return OpsviMemoryManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviMemoryManager):
        """Test component initialization."""
        assert component is not None
        assert component.config is not None

    @pytest.mark.asyncio
    async def test_start_stop(self, component: OpsviMemoryManager):
        """Test component start and stop."""
        await component.start()
        assert component.is_active()

        await component.stop()
        assert not component.is_active()

    @pytest.mark.asyncio
    async def test_health_check(self, component: OpsviMemoryManager):
        """Test component health check."""
        await component.start()
        assert await component.health_check()

    @pytest.mark.asyncio
    async def test_error_handling(self, component: OpsviMemoryManager):
        """Test error handling."""
        with pytest.raises(OpsviMemoryError):
            # Test error condition
            pass

    # Component-specific tests
