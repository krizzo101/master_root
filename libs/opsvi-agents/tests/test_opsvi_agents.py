"""Tests for opsvi-agents.

Tests for opsvi-agents components
"""

import pytest

from opsvi_agents import OpsviAgentsManager
from opsvi_agents.config.settings import OpsviAgentsConfig
from opsvi_agents.exceptions.base import OpsviAgentsError


class TestOpsviAgents:
    """Test cases for opsvi-agents."""

    @pytest.fixture
    def config(self) -> OpsviAgentsConfig:
        """Create test configuration."""
        return OpsviAgentsConfig(enabled=True, debug=True)

    @pytest.fixture
    def component(self, config: OpsviAgentsConfig) -> OpsviAgentsManager:
        """Create test component."""
        return OpsviAgentsManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviAgentsManager):
        """Test component initialization."""
        assert component is not None
        assert component.config is not None

    @pytest.mark.asyncio
    async def test_start_stop(self, component: OpsviAgentsManager):
        """Test component start and stop."""
        await component.start()
        assert component.is_active()

        await component.stop()
        assert not component.is_active()

    @pytest.mark.asyncio
    async def test_health_check(self, component: OpsviAgentsManager):
        """Test component health check."""
        await component.start()
        assert await component.health_check()

    @pytest.mark.asyncio
    async def test_error_handling(self, component: OpsviAgentsManager):
        """Test error handling."""
        with pytest.raises(OpsviAgentsError):
            # Test error condition
            pass

    # Component-specific tests
