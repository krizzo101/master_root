"""Tests for opsvi-security.

Tests for opsvi-security components
"""

import pytest

from opsvi_security import OpsviSecurityManager
from opsvi_security.config.settings import OpsviSecurityConfig
from opsvi_security.exceptions.base import OpsviSecurityError


class TestOpsviSecurity:
    """Test cases for opsvi-security."""

    @pytest.fixture
    def config(self) -> OpsviSecurityConfig:
        """Create test configuration."""
        return OpsviSecurityConfig(enabled=True, debug=True)

    @pytest.fixture
    def component(self, config: OpsviSecurityConfig) -> OpsviSecurityManager:
        """Create test component."""
        return OpsviSecurityManager(config=config)

    @pytest.mark.asyncio
    async def test_initialization(self, component: OpsviSecurityManager):
        """Test component initialization."""
        assert component is not None
        assert component.config is not None

    @pytest.mark.asyncio
    async def test_start_stop(self, component: OpsviSecurityManager):
        """Test component start and stop."""
        await component.start()
        assert component.is_active()

        await component.stop()
        assert not component.is_active()

    @pytest.mark.asyncio
    async def test_health_check(self, component: OpsviSecurityManager):
        """Test component health check."""
        await component.start()
        assert await component.health_check()

    @pytest.mark.asyncio
    async def test_error_handling(self, component: OpsviSecurityManager):
        """Test error handling."""
        with pytest.raises(OpsviSecurityError):
            # Test error condition
            pass

    # Component-specific tests
