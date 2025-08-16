import pytest


def test_ecosystem_imports():
    """Test that all major ecosystem components can be imported."""
    try:
        from opsvi_auth import BaseAuthProvider
        from opsvi_core import EventBus, ServiceRegistry
        from opsvi_data import BaseDatabaseProvider
        from opsvi_foundation import BaseComponent, ComponentError
        from opsvi_http import BaseHTTPClient
        from opsvi_llm import BaseLLMProvider

        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_basic_functionality():
    """Test basic ecosystem functionality."""
    from opsvi_foundation import BaseComponent

    class TestComponent(BaseComponent):
        async def _initialize_impl(self):
            pass

        async def _shutdown_impl(self):
            pass

        async def _health_check_impl(self):
            return True

    component = TestComponent()
    assert component is not None


if __name__ == "__main__":
    pytest.main([__file__])
