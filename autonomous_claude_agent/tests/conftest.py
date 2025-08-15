"""
Pytest configuration and shared fixtures
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime
import json

# Import modules to test
from src.core.agent import AutonomousAgent, AgentState
from src.core.claude_client import ClaudeClient
from src.core.state_manager import StateManager
from src.capabilities.discovery import CapabilityDiscovery
from src.learning.pattern_engine import PatternEngine
from src.governance.resource_monitor import ResourceMonitor

# Configure asyncio for testing
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)

@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        'max_iterations': 10,
        'mode': 'test',
        'claude': {
            'max_concurrent': 2,
            'timeout': 10,
            'retry_max': 2,
            'rate_limits': {
                'requests_per_minute': 60,
                'tokens_per_day': 10000
            }
        },
        'context': {
            'max_tokens': 1000,
            'summarization_threshold': 800,
            'compression_ratio': 0.5
        },
        'limits': {
            'memory_mb': 512,
            'cpu_percent': 50,
            'disk_mb': 100,
            'daily_tokens': 10000
        },
        'safety': {
            'allow_file_modifications': False,
            'allow_network_requests': False,
            'require_approval_for': ['delete', 'system_command'],
            'max_recursion_depth': 3
        },
        'research': {
            'cache_ttl_hours': 1,
            'max_search_results': 5,
            'enable_web_search': False
        },
        'logging': {
            'level': 'DEBUG',
            'file': 'test.log'
        }
    }

@pytest.fixture
def mock_claude_client():
    """Mock Claude client for testing"""
    client = AsyncMock(spec=ClaudeClient)
    
    # Setup default return values
    client.execute.return_value = {
        'progress': 50,
        'bottlenecks': [],
        'missing_capabilities': [],
        'metrics': {'success_rate': 0.8},
        'recommendations': []
    }
    
    client.execute_batch.return_value = [
        {'result': 'success', 'data': {}},
        {'result': 'success', 'data': {}}
    ]
    
    client.token_usage = 100
    client.request_count = 5
    
    return client

@pytest.fixture
async def agent(mock_config, mock_claude_client, temp_dir, monkeypatch):
    """Create test agent with mocked dependencies"""
    # Set temp directory for data
    monkeypatch.setattr('src.core.state_manager.Path', lambda x: temp_dir / x)
    
    # Create agent
    agent = AutonomousAgent(mock_config, mode='test')
    
    # Replace Claude client with mock
    agent.claude = mock_claude_client
    
    # Initialize components
    await agent.initialize("test goal")
    
    yield agent
    
    # Cleanup
    await agent.shutdown()

@pytest.fixture
def mock_capability():
    """Mock capability for testing"""
    from src.capabilities.discovery import Capability
    
    return Capability(
        name="test_capability",
        type="test",
        description="Test capability",
        parameters={'param1': 'value1'},
        requirements=[],
        examples=['example1'],
        cost=0.1,
        success_rate=0.95,
        available=True
    )

@pytest.fixture
def mock_pattern():
    """Mock pattern for testing"""
    return {
        'id': 'pattern_001',
        'type': 'optimization',
        'trigger': 'slow_performance',
        'solution': 'add_caching',
        'confidence': 0.85,
        'success_count': 10,
        'failure_count': 2
    }

@pytest.fixture
def mock_execution_context():
    """Mock execution context for testing"""
    from src.core.agent import ExecutionContext
    
    return ExecutionContext(
        iteration=1,
        goal="test goal",
        state=AgentState.EXECUTING,
        metrics={'duration': 1.5, 'success': True}
    )

@pytest.fixture
def mock_state_manager(temp_dir):
    """Mock state manager for testing"""
    manager = StateManager("test_agent")
    manager.db_path = temp_dir / "test_state.db"
    manager.checkpoint_dir = temp_dir / "checkpoints"
    manager.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    return manager

@pytest.fixture
def mock_resource_monitor(mock_config):
    """Mock resource monitor for testing"""
    monitor = ResourceMonitor(mock_config['limits'])
    
    # Mock resource checks to always pass
    monitor.check_all_limits = AsyncMock(return_value=True)
    monitor.get_current_usage = Mock(return_value={
        'cpu_percent': 25,
        'memory_mb': 256,
        'disk_mb': 50,
        'token_usage': 500
    })
    
    return monitor

@pytest.fixture
def sample_code():
    """Sample Python code for testing modifications"""
    return '''
def calculate(x, y):
    result = x + y
    return result

def process_data(data):
    for item in data:
        print(item)
'''

@pytest.fixture
def sample_test_result():
    """Sample test result for validation"""
    return {
        'context': {
            'iteration': 1,
            'goal': 'test goal',
            'state': 'executing'
        },
        'assessment': {
            'progress': 25,
            'bottlenecks': ['speed'],
            'missing_capabilities': ['caching'],
            'metrics': {'iteration_time': 2.5}
        },
        'opportunities': {
            'immediate': ['optimize_loops'],
            'research_needed': [],
            'capabilities_needed': ['caching']
        },
        'plan': {
            'type': 'sync',
            'prompt': 'Optimize performance',
            'opportunities': {}
        },
        'execution': {
            'success': True,
            'result': {'actions': ['added_caching']},
            'plan': {}
        },
        'validation': {
            'success': True,
            'improvements': 1,
            'issues': []
        },
        'timestamp': datetime.now()
    }

# Markers for test categorization
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "async: Async tests")
    config.addinivalue_line("markers", "requires_mcp: Tests requiring MCP")

# Test utilities
class TestUtils:
    """Utility functions for tests"""
    
    @staticmethod
    async def wait_for_condition(condition_func, timeout=5, interval=0.1):
        """Wait for a condition to become true"""
        elapsed = 0
        while elapsed < timeout:
            if await condition_func():
                return True
            await asyncio.sleep(interval)
            elapsed += interval
        return False
    
    @staticmethod
    def create_mock_response(success=True, data=None):
        """Create a mock Claude response"""
        return {
            'success': success,
            'content': [{'type': 'text', 'text': json.dumps(data or {})}],
            'token_usage': 50
        }
    
    @staticmethod
    async def run_agent_iterations(agent, count=3):
        """Run agent for specified iterations"""
        results = []
        for i in range(count):
            agent.iteration = i
            context = Mock(iteration=i, goal="test", state=AgentState.EXECUTING)
            result = await agent.execute_iteration(context)
            results.append(result)
        return results

@pytest.fixture
def test_utils():
    """Provide test utilities"""
    return TestUtils()

# Async test support
@pytest.fixture
def async_mock():
    """Create an async mock factory"""
    def _create_async_mock(**kwargs):
        mock = AsyncMock(**kwargs)
        return mock
    return _create_async_mock