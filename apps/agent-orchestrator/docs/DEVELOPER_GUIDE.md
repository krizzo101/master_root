# Agent Orchestrator Developer Guide

## Table of Contents
1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Code Architecture](#code-architecture)
5. [Testing Strategy](#testing-strategy)
6. [Contributing Guidelines](#contributing-guidelines)
7. [Advanced Development](#advanced-development)
8. [Documentation Navigation](#documentation-navigation)
9. [Release Process](#release-process)
10. [Troubleshooting Development Issues](#troubleshooting-development-issues)

## Overview

This developer guide provides comprehensive information for contributors, maintainers, and developers working on the Agent Orchestrator system. It covers development setup, coding standards, testing practices, and contribution workflows.

### Current Project State

The Agent Orchestrator is a production-ready multi-agent orchestration framework with:
- **Active Development**: Located at `/home/opsvi/master_root/apps/agent-orchestrator`
- **Python 3.8+**: Compatible with Python 3.8 through 3.12
- **Modular Architecture**: Plugin-based provider system, workflow management, and dashboard
- **Production Dashboard**: Web-based monitoring and control interface on port 8765
- **Task Resumption**: Checkpoint-based recovery for interrupted workflows

### Development Philosophy

The Agent Orchestrator follows these core development principles:

- **Production-First Design**: All features are built with production reliability in mind
- **Async-First Architecture**: Leveraging Python's asyncio for high concurrency
- **Incremental Testing**: Tests are added as features are developed
- **Practical Documentation**: Focus on working examples and real usage patterns
- **Resilient Design**: Built-in error handling and workflow resumption

## Getting Started

### Development Environment Setup

#### Prerequisites
- Python 3.8+ (3.11+ recommended)
- Git 2.0+
- PostgreSQL 13+ (for development database)
- Redis 6.0+ (for caching and message bus)
- Docker 20.10+ (optional, for containerized development)
- Miniconda or Python virtual environment

#### Quick Setup Script
```bash
#!/bin/bash
# setup-dev-environment.sh

set -e

echo "Setting up Agent Orchestrator development environment..."

# Navigate to project directory
cd /home/opsvi/master_root/apps/agent-orchestrator

# Create virtual environment (if using system Python)
# python3 -m venv venv
# source venv/bin/activate

# Or use existing Miniconda environment
source /home/opsvi/miniconda/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# Install development dependencies
pip install pytest pytest-asyncio

# Create required directories
mkdir -p output logs temp_docs_cleanup web/static web/templates

# Setup development database (if not exists)
createdb orchestrator_dev || echo "Database already exists"

# Create basic configuration if needed
if [ ! -f production_config.json ]; then
    echo '{"max_parallel": 10, "output_dir": "./output"}' > production_config.json
fi

echo "Development environment setup complete!"
echo "Next steps:"
echo "1. Configure .env.production with your API keys"
echo "2. Run: python main.py --example to test basic functionality"
echo "3. Run: python production_dashboard.py to start the dashboard"
```

#### IDE Configuration

##### VS Code Settings (.vscode/settings.json)
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=88"],
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/venv": true,
        "**/outputs": true,
        "**/logs": true
    }
}
```

##### PyCharm Configuration
1. Set interpreter to `./venv/bin/python`
2. Enable code style: Black (88 character line length)
3. Configure import optimizer: isort with black profile
4. Enable inspections: PEP 8, Type hints, Async code

### Development Dependencies

```txt
# requirements-dev.txt (additional development dependencies)
# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0

# Code Quality (optional but recommended)
black>=23.0.0
isort>=5.12.0
flake8>=5.0.0
mypy>=1.0.0

# Development Tools
ipython>=8.0.0
ipdb>=0.13.0

# Performance Testing
locust>=2.14.0
memory-profiler>=0.60.0
psutil>=5.9.0

# Note: Core dependencies are in requirements.txt:
# - watchdog>=3.0.0
# - aiofiles>=23.0.0
# - pydantic>=2.0.0
# - websockets>=12.0
# - aiohttp>=3.9.0
# - psycopg2-binary>=2.9.0
# - redis>=4.5.0
# - anthropic>=0.3.0 (in setup.py)
```

## Development Workflow

### Running the System

#### Starting the Orchestrator
```bash
# Basic execution with example tasks
python main.py --example

# Run with specific task file
python main.py --tasks-file system_analysis_tasks.json --output-dir ./output

# Run with enhanced features
python main.py --use-enhanced --enable-dashboard --max-parallel 10

# Run specific workflows
python run_orchestrator_task.py --app-name "your-app" \
  --app-root "/path/to/app" \
  --task-type "system-documentation"

# Resume interrupted workflow
python resume_orchestrator.py output/workflow_*/checkpoints/checkpoint_*.json
```

#### Starting the Dashboard
```bash
# Start production dashboard (Port 8765)
python production_dashboard.py

# Or use the integrated orchestrator with dashboard
python orchestrator_with_dashboard.py

# Access dashboard at: http://localhost:8765
```

#### Running Parallel Documentation Updates
```bash
# Update multiple documentation files in parallel
python run_parallel_doc_update.py

# This runs tasks defined in parallel_doc_update_tasks.json
```

### Branch Strategy

We follow a GitFlow-inspired branching model:

- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/***: Individual feature development
- **hotfix/***: Critical production fixes
- **release/***: Release preparation

#### Feature Development Workflow
```bash
# Start new feature
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Develop feature
# ... make changes ...

# Run tests before committing
python -m pytest tests/
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/

# Commit changes
git add .
git commit -m "feat: add new feature description

- Detail 1
- Detail 2

Closes #123"

# Push and create PR
git push origin feature/your-feature-name
# Create pull request via GitHub/GitLab
```

### Commit Message Convention

We use Conventional Commits for clear, structured commit messages:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Types:
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Build process or auxiliary tool changes
- **perf**: Performance improvements
- **ci**: CI/CD changes

#### Examples:
```bash
feat(orchestrator): add parallel execution limits

- Implement configurable max_parallel setting
- Add resource usage monitoring
- Update documentation

Closes #142

fix(dashboard): resolve WebSocket connection timeout

The WebSocket connection was timing out after 30 seconds
due to lack of ping/pong heartbeat mechanism.

- Add WebSocket keepalive with 30s interval
- Implement connection retry logic
- Update client-side error handling

Fixes #156
```

### Code Quality Tools (Optional)

While pre-commit hooks are not currently configured, you can manually run code quality tools:

```bash
# Format code with black (if installed)
black src/ --line-length=88

# Sort imports with isort (if installed)
isort src/ --profile black

# Check code style with flake8 (if installed)
flake8 src/ --max-line-length=88 --extend-ignore=E203,W503

# Type checking with mypy (if installed)
mypy src/ --ignore-missing-imports
```

To set up pre-commit hooks (optional):
```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml with desired hooks
# Then install the git hooks
pre-commit install
```

## Code Architecture

### Project Structure

```
agent-orchestrator/
├── src/                              # Core source code
│   ├── __init__.py
│   ├── generic_orchestrator.py       # Main orchestrator (101KB)
│   ├── enhanced_orchestrator.py      # Advanced orchestrator
│   ├── enhanced_token_pool.py        # Token management
│   ├── session_analytics_engine.py   # Analytics system
│   ├── gpt5_payload_generator.py     # Payload generation
│   ├── providers/                    # AI provider integrations
│   │   ├── __init__.py
│   │   └── openai_provider.py       # OpenAI integration
│   ├── workflows/                    # Workflow management
│   │   ├── __init__.py
│   │   └── resumable.py             # Resumable workflow support
│   ├── validators/                   # Input validation
│   │   └── task_validator.py        # Task validation logic
│   ├── persistence/                  # Database layer
│   ├── monitoring/                   # Monitoring components
│   ├── collaboration/               # Multi-agent collaboration
│   ├── load_balancing/              # Load distribution
│   ├── message_bus/                 # Inter-agent communication
│   ├── execution_plan/              # Execution planning
│   └── events/                      # Event system
├── output/                          # Task execution outputs
│   └── [task_outputs]/              # Timestamped output directories
├── docs/                            # Documentation
│   ├── README.md                    # Project overview
│   ├── ARCHITECTURE.md              # System architecture
│   ├── USER_GUIDE.md                # User documentation
│   ├── API_REFERENCE.md             # API documentation
│   ├── DEPLOYMENT.md                # Deployment guide
│   └── DEVELOPER_GUIDE.md           # This file
├── web/                             # Dashboard frontend
│   ├── static/                      # Static assets
│   └── templates/                   # HTML templates
├── archive/                         # Archived components
├── tools/                           # Development tools
├── *.py                             # Main entry points and utilities
│   ├── main.py                      # Primary CLI entry point
│   ├── production_dashboard.py      # Production dashboard server
│   ├── run_orchestrator_task.py     # Task runner utility
│   ├── resume_orchestrator.py       # Resume interrupted tasks
│   └── [various test files]         # Test and demo scripts
└── *.json                           # Task definitions and configs
    ├── production_config.json        # Production configuration
    ├── logging_config.json           # Logging settings
    └── [task definition files]      # Various task JSON files
```

### Coding Standards

#### Python Style Guide

We follow PEP 8 with Black formatting and these additional standards:

```python
"""Example module demonstrating coding standards."""

import asyncio
import logging
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TaskResult:
    """Represents the result of a task execution.

    Attributes:
        task_id: Unique identifier for the task
        status: Execution status (pending, running, completed, failed)
        result: Task execution result data
        error: Error message if task failed
        duration_seconds: Task execution time
    """

    task_id: str
    status: str
    result: Optional[Dict] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None


class AgentTaskProcessor:
    """Processes agent tasks with error handling and monitoring.

    This class handles the core task processing logic including
    validation, execution, and result collection.
    """

    def __init__(
        self,
        max_retries: int = 3,
        timeout_seconds: int = 3600,
        enable_monitoring: bool = True,
    ) -> None:
        """Initialize the task processor.

        Args:
            max_retries: Maximum number of retry attempts
            timeout_seconds: Task execution timeout
            enable_monitoring: Whether to enable performance monitoring
        """
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.enable_monitoring = enable_monitoring
        self._active_tasks: Dict[str, TaskResult] = {}

    async def process_task(
        self,
        task_id: str,
        task_data: Dict,
    ) -> TaskResult:
        """Process a single task with error handling.

        Args:
            task_id: Unique identifier for the task
            task_data: Task configuration and input data

        Returns:
            TaskResult with execution status and results

        Raises:
            ValueError: If task_data is invalid
            TimeoutError: If task exceeds timeout limit
        """
        if not task_id or not task_data:
            raise ValueError("Task ID and data are required")

        logger.info(f"Processing task {task_id}")

        # Task processing logic here
        try:
            result = await self._execute_task(task_id, task_data)
            return TaskResult(
                task_id=task_id,
                status="completed",
                result=result,
            )
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            return TaskResult(
                task_id=task_id,
                status="failed",
                error=str(e),
            )

    async def _execute_task(self, task_id: str, task_data: Dict) -> Dict:
        """Execute the actual task logic."""
        # Implementation here
        return {"status": "success"}
```

#### Key Standards:

1. **Type Hints**: Always use type hints for function parameters and return values
2. **Docstrings**: Use Google-style docstrings for all public methods
3. **Error Handling**: Explicit exception handling with appropriate error types
4. **Logging**: Use structured logging with appropriate levels
5. **Async/Await**: Use async/await for all I/O operations
6. **Constants**: Use UPPER_CASE for constants, define at module level
7. **Private Methods**: Use single underscore prefix for internal methods

### Design Patterns Implementation

#### 1. Plugin Architecture Pattern
```python
# src/providers/base_provider.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using this provider."""
        pass

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Validate provider credentials."""
        pass

# src/providers/openai_provider.py
class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation."""

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation specific to OpenAI
        pass
```

#### 2. Factory Pattern
```python
# src/factory.py
from typing import Dict, Type
from src.providers.base_provider import BaseProvider
from src.providers.openai_provider import OpenAIProvider

class ProviderFactory:
    """Factory for creating provider instances."""

    _providers: Dict[str, Type[BaseProvider]] = {
        'openai': OpenAIProvider,
        # Add more providers here
    }

    @classmethod
    def create_provider(cls, provider_type: str, **kwargs) -> BaseProvider:
        """Create a provider instance."""
        if provider_type not in cls._providers:
            raise ValueError(f"Unknown provider type: {provider_type}")

        provider_class = cls._providers[provider_type]
        return provider_class(**kwargs)
```

#### 3. Observer Pattern for Events
```python
# src/events.py
from typing import List, Callable, Any
from dataclasses import dataclass

@dataclass
class Event:
    """Base event class."""
    event_type: str
    data: Any
    timestamp: float

class EventBus:
    """Event bus for decoupled communication."""

    def __init__(self):
        self._observers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type."""
        if event_type not in self._observers:
            self._observers[event_type] = []
        self._observers[event_type].append(callback)

    async def publish(self, event: Event):
        """Publish an event to all subscribers."""
        if event.event_type in self._observers:
            for callback in self._observers[event.event_type]:
                await callback(event)
```

## Testing Strategy

### Test Structure

```
# Current test files (scattered in project root and src/):
├── test_multi_provider.py           # Provider testing
├── test_session_analytics.py        # Analytics testing
├── test_task_organization.py        # Task organization
├── test_claude_sessions.py          # Session handling
├── test_enhanced_task_validation.py # Task validation
├── src/
│   ├── test_debug_logging.py       # Debug logging tests
│   ├── test_enhanced_quality_gates.py # Quality gates
│   └── collaboration/
│       └── test_collaboration_system.py # Collaboration tests

# Recommended test organization (to be implemented):
tests/
├── unit/                    # Unit tests (isolated, fast)
├── integration/             # Integration tests
├── performance/             # Performance tests
├── fixtures/               # Test data and fixtures
└── conftest.py            # Pytest configuration
```

**Note:** Tests are currently scattered throughout the project. Consider reorganizing them into a dedicated `tests/` directory for better organization.

### Testing Guidelines

#### Current Testing Approach

The project currently has test files scattered throughout the codebase rather than in a dedicated tests directory. When writing new tests:

1. **Naming Convention**: Use `test_*.py` for test files
2. **Location**: Place tests near the code they test or in project root
3. **Async Tests**: Use `pytest-asyncio` for async test functions
4. **Mocking**: Mock external dependencies (API calls, database)

#### Running Existing Tests
```bash
# Set up environment
cd /home/opsvi/master_root/apps/agent-orchestrator
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Run specific test files that exist
python -m pytest test_session_analytics.py -v
python -m pytest test_multi_provider.py -v
python -m pytest test_task_organization.py -v

# Run performance tests
python continuous_metrics_test.py
python realistic_load_test.py
python websocket_load_test.py
```

#### Unit Tests
```python
# tests/unit/test_orchestrator.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.generic_orchestrator import GenericOrchestrator, AgentTask

class TestGenericOrchestrator:
    """Test cases for GenericOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing."""
        return GenericOrchestrator(
            max_parallel=5,
            output_dir="test_outputs",
            workflow_name="test_workflow"
        )

    @pytest.fixture
    def sample_task(self):
        """Create sample task for testing."""
        return AgentTask(
            task_id="test_task_001",
            task_type="test",
            prompt="Test task prompt",
            context={"test": True}
        )

    @pytest.mark.asyncio
    async def test_execute_single_task(self, orchestrator, sample_task):
        """Test execution of a single task."""
        # Mock the token pool
        orchestrator.token_pool = AsyncMock()
        orchestrator.token_pool.acquire.return_value = "test_token"

        # Mock the provider
        mock_provider = AsyncMock()
        mock_provider.execute_task.return_value = {
            "status": "completed",
            "result": "test result"
        }

        # Execute test
        result = await orchestrator._execute_single_task(
            sample_task,
            mock_provider,
            "test_token"
        )

        # Assertions
        assert result["status"] == "completed"
        assert result["result"] == "test result"
        mock_provider.execute_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_dependency_resolution(self, orchestrator):
        """Test task dependency resolution."""
        # Create tasks with dependencies
        task1 = AgentTask(task_id="task1", task_type="test", prompt="Task 1")
        task2 = AgentTask(task_id="task2", task_type="test", prompt="Task 2", dependencies=["task1"])
        task3 = AgentTask(task_id="task3", task_type="test", prompt="Task 3", dependencies=["task2"])

        tasks = [task3, task1, task2]  # Intentionally out of order

        resolved_order = orchestrator._resolve_dependencies(tasks)
        resolved_ids = [task.task_id for task in resolved_order]

        assert resolved_ids == ["task1", "task2", "task3"]

    def test_circular_dependency_detection(self, orchestrator):
        """Test detection of circular dependencies."""
        task1 = AgentTask(task_id="task1", task_type="test", prompt="Task 1", dependencies=["task2"])
        task2 = AgentTask(task_id="task2", task_type="test", prompt="Task 2", dependencies=["task1"])

        with pytest.raises(ValueError, match="Circular dependency detected"):
            orchestrator._resolve_dependencies([task1, task2])
```

#### Integration Tests
```python
# tests/integration/test_workflow_execution.py
import pytest
import tempfile
from pathlib import Path
from src.generic_orchestrator import GenericOrchestrator, AgentTask

class TestWorkflowExecution:
    """Integration tests for complete workflow execution."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.mark.asyncio
    async def test_complete_documentation_workflow(self, temp_output_dir):
        """Test complete documentation generation workflow."""
        orchestrator = GenericOrchestrator(
            output_dir=temp_output_dir,
            max_parallel=3,
            workflow_name="test_documentation"
        )

        # Define realistic task sequence
        tasks = [
            AgentTask(
                task_id="analyze_structure",
                task_type="analysis",
                prompt="Analyze project structure",
                context={"target_dir": str(temp_output_dir)}
            ),
            AgentTask(
                task_id="generate_readme",
                task_type="documentation",
                prompt="Generate README.md based on analysis",
                dependencies=["analyze_structure"]
            ),
            AgentTask(
                task_id="generate_api_docs",
                task_type="documentation",
                prompt="Generate API documentation",
                dependencies=["analyze_structure"]
            )
        ]

        # Execute workflow
        results = await orchestrator.execute_batch(tasks)

        # Verify results
        assert len(results) == 3
        for task_id, result in results.items():
            assert result["status"] in ["completed", "skipped"]

        # Verify output files were created
        assert (temp_output_dir / "workflow_summary.json").exists()
        assert (temp_output_dir / "execution_log.txt").exists()
```

#### Performance Tests
```python
# tests/performance/test_concurrent_execution.py
import pytest
import asyncio
import time
from src.generic_orchestrator import GenericOrchestrator, AgentTask

class TestPerformance:
    """Performance tests for orchestrator."""

    @pytest.mark.asyncio
    async def test_parallel_execution_performance(self):
        """Test performance with multiple parallel tasks."""
        orchestrator = GenericOrchestrator(max_parallel=10)

        # Create 50 lightweight tasks
        tasks = [
            AgentTask(
                task_id=f"task_{i:03d}",
                task_type="performance_test",
                prompt="Simple test task"
            )
            for i in range(50)
        ]

        start_time = time.time()
        results = await orchestrator.execute_batch(tasks)
        end_time = time.time()

        execution_time = end_time - start_time

        # Performance assertions
        assert len(results) == 50
        assert execution_time < 60  # Should complete within 60 seconds

        # Calculate throughput
        throughput = len(tasks) / execution_time
        assert throughput > 1.0  # At least 1 task per second

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage with large number of tasks."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        orchestrator = GenericOrchestrator(max_parallel=20)

        # Create 200 tasks
        tasks = [
            AgentTask(
                task_id=f"memory_test_{i:03d}",
                task_type="memory_test",
                prompt="Memory usage test task"
            )
            for i in range(200)
        ]

        results = await orchestrator.execute_batch(tasks)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory usage should not increase dramatically
        assert memory_increase < 500  # Less than 500MB increase
        assert len(results) == 200
```

### Running Tests

```bash
# Run tests from project root
cd /home/opsvi/master_root/apps/agent-orchestrator

# Set Python path to include src/
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Run all test files
python -m pytest test_*.py -v

# Run specific test file
python -m pytest test_multi_provider.py -v

# Run with coverage (if pytest-cov installed)
python -m pytest --cov=src --cov-report=html

# Run tests matching pattern
python -m pytest -k "test_orchestrator"

# Run with verbose output
python -m pytest -v

# Common test files to run:
python -m pytest test_session_analytics.py    # Session analytics
python -m pytest test_task_organization.py     # Task organization
python -m pytest test_enhanced_task_validation.py  # Validation

# Note: Some tests may require API keys or database setup
```

### Test Configuration

```python
# conftest.py (create in project root)
import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock

# Add src to path for test imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_token_pool():
    """Mock token pool for testing."""
    pool = AsyncMock()
    pool.acquire.return_value = "test_token"
    pool.release.return_value = None
    pool.available_tokens.return_value = 5
    return pool

@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "task_id": "test_task",
        "task_type": "test",
        "prompt": "Test prompt",
        "context": {"test": True}
    }
```

## Contributing Guidelines

### Pull Request Process

1. **Fork and Branch**: Fork the repository and create a feature branch
2. **Develop**: Implement your changes following coding standards
3. **Test**: Ensure all tests pass and add new tests for your changes
4. **Document**: Update documentation as needed
5. **Submit**: Create a pull request with clear description

#### PR Template
```markdown
## Description
Brief description of the changes and their purpose.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Performance tests pass (if applicable)
- [ ] Manual testing completed

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] Any dependent changes have been merged and published
```

### Code Review Guidelines

#### For Authors:
- Keep PRs focused and reasonably sized
- Write clear commit messages and PR descriptions
- Respond to feedback promptly and professionally
- Test your changes thoroughly before submitting

#### For Reviewers:
- Focus on correctness, maintainability, and performance
- Provide constructive feedback with specific suggestions
- Approve when code meets standards, even if you would have done it differently
- Review within 24-48 hours when possible

### Documentation Requirements

All code changes must include appropriate documentation updates:

1. **Code Comments**: Complex logic should be commented
2. **Docstrings**: All public functions and classes need docstrings
3. **API Documentation**: Update API_REFERENCE.md for API changes
4. **User Guide**: Update USER_GUIDE.md for user-facing changes
5. **Architecture Docs**: Update ARCHITECTURE.md for structural changes

## Advanced Development

### Custom Provider Development

```python
# Example custom provider implementation
# Note: base_provider.py is not currently in the project
# This is a template for creating new providers
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using this provider."""
        pass

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Validate provider credentials."""
        pass

class CustomAIProvider(BaseProvider):
    """Custom AI provider implementation."""

    def __init__(self, api_key: str, endpoint: str):
        self.api_key = api_key
        self.endpoint = endpoint

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task using custom AI service."""
        # Implementation for your AI service
        async with aiohttp.ClientSession() as session:
            payload = {
                "prompt": task["prompt"],
                "context": task.get("context", {}),
                "model": "custom-model-v1"
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with session.post(
                self.endpoint,
                json=payload,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "status": "completed",
                        "result": result["output"],
                        "usage": result.get("usage", {})
                    }
                else:
                    return {
                        "status": "failed",
                        "error": f"API error: {response.status}"
                    }

    async def validate_credentials(self) -> bool:
        """Validate API credentials."""
        # Implementation for credential validation
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with session.get(
                    f"{self.endpoint}/health",
                    headers=headers
                ) as response:
                    return response.status == 200
        except Exception:
            return False

# Register the custom provider
# Note: You'll need to integrate this with the orchestrator's provider system
# Currently, providers are managed in src/providers/openai_provider.py
```

### Custom Quality Gates

```python
# src/quality_gates/custom_gates.py
from src.quality_gates.base_gate import BaseQualityGate
from typing import Dict, Any, List

class SecurityQualityGate(BaseQualityGate):
    """Security-focused quality gate."""

    async def validate(self, task_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate security aspects of task result."""
        issues = []

        # Check for sensitive information
        result_text = str(task_result.get("result", ""))

        # Simple pattern matching for common sensitive data
        sensitive_patterns = [
            r'api[_-]?key[s]?\s*[:=]\s*["\']?([a-zA-Z0-9_-]+)["\']?',
            r'password[s]?\s*[:=]\s*["\']?([^"\'\\s]+)["\']?',
            r'secret[_-]?key[s]?\s*[:=]\s*["\']?([a-zA-Z0-9_-]+)["\']?',
        ]

        for pattern in sensitive_patterns:
            if re.search(pattern, result_text, re.IGNORECASE):
                issues.append(f"Potential sensitive data detected: {pattern}")

        # Check for insecure code patterns
        insecure_patterns = [
            r'eval\s*\(',
            r'exec\s*\(',
            r'subprocess\.shell\s*=\s*True',
            r'input\s*\(',  # In certain contexts
        ]

        for pattern in insecure_patterns:
            if re.search(pattern, result_text):
                issues.append(f"Potentially insecure code pattern: {pattern}")

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "score": 1.0 if len(issues) == 0 else 0.5
        }

class PerformanceQualityGate(BaseQualityGate):
    """Performance-focused quality gate."""

    def __init__(self, max_execution_time: float = 300.0):
        self.max_execution_time = max_execution_time

    async def validate(self, task_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate performance aspects of task result."""
        issues = []

        # Check execution time
        duration = task_result.get("duration_seconds", 0)
        if duration > self.max_execution_time:
            issues.append(
                f"Task exceeded maximum execution time: "
                f"{duration}s > {self.max_execution_time}s"
            )

        # Check memory usage if available
        memory_usage = task_result.get("memory_usage_mb", 0)
        if memory_usage > 1000:  # 1GB limit
            issues.append(
                f"Task used excessive memory: {memory_usage}MB"
            )

        # Calculate performance score
        time_score = min(1.0, self.max_execution_time / max(duration, 1.0))
        memory_score = min(1.0, 1000.0 / max(memory_usage, 1.0))
        overall_score = (time_score + memory_score) / 2.0

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "score": overall_score,
            "metrics": {
                "execution_time": duration,
                "memory_usage": memory_usage,
                "time_score": time_score,
                "memory_score": memory_score
            }
        }
```

### Performance Profiling

```python
# scripts/profile_orchestrator.py
import cProfile
import pstats
import asyncio
from src.generic_orchestrator import GenericOrchestrator, AgentTask

async def profile_orchestrator_execution():
    """Profile orchestrator execution for performance analysis."""

    # Create test tasks
    tasks = [
        AgentTask(
            task_id=f"profile_task_{i:03d}",
            task_type="analysis",
            prompt=f"Profile test task {i}"
        )
        for i in range(20)
    ]

    orchestrator = GenericOrchestrator(
        max_parallel=10,
        output_dir="profile_output"
    )

    # Profile execution
    profiler = cProfile.Profile()
    profiler.enable()

    results = await orchestrator.execute_batch(tasks)

    profiler.disable()

    # Generate profiling report
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')

    # Print top functions by cumulative time
    print("Top 20 functions by cumulative time:")
    stats.print_stats(20)

    # Save detailed report
    stats.dump_stats('orchestrator_profile.stats')

    return results

if __name__ == "__main__":
    asyncio.run(profile_orchestrator_execution())
```

## Documentation Navigation

This developer guide is part of a comprehensive documentation suite. Here's how the documents relate to each other:

### Documentation Hierarchy

1. **[README.md](README.md)** - Start here for overview and quick start
2. **[USER_GUIDE.md](USER_GUIDE.md)** - For end users and operators
3. **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - This document, for contributors
4. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Deep technical architecture
5. **[API_REFERENCE.md](API_REFERENCE.md)** - Complete API documentation
6. **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guidance

### When to Use Which Document

- **New to the project?** → Start with README.md
- **Want to use the system?** → Read USER_GUIDE.md
- **Contributing code?** → Read this DEVELOPER_GUIDE.md
- **Need technical details?** → Consult ARCHITECTURE.md
- **Integrating via API?** → Reference API_REFERENCE.md
- **Deploying to production?** → Follow DEPLOYMENT.md

### Cross-References

Key sections that reference other documents:

- Architecture patterns → See ARCHITECTURE.md sections
- API usage examples → See API_REFERENCE.md
- Deployment procedures → See DEPLOYMENT.md
- User workflows → See USER_GUIDE.md

## Release Process

### Version Management

We follow Semantic Versioning (SemVer):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality, backward compatible
- **PATCH**: Bug fixes, backward compatible

#### Version Update Process
```bash
# Update version in setup.py
vim setup.py  # Update version="1.2.3"

# Update version in src/__init__.py if present
vim src/__init__.py  # Update __version__ = "1.2.3"

# Commit version bump
git add setup.py src/__init__.py
git commit -m "chore: bump version to v1.2.3"

# Create and push tag
git tag v1.2.3
git push origin v1.2.3

# Build and distribute (if publishing to PyPI)
python setup.py sdist bdist_wheel
# twine upload dist/*  # If publishing to PyPI
```

### Release Checklist

#### Pre-Release
- [ ] All tests pass on CI/CD
- [ ] Documentation is up to date
- [ ] Performance benchmarks meet requirements
- [ ] Security review completed
- [ ] Breaking changes documented
- [ ] Migration guide created (if needed)

#### Release
- [ ] Version number updated
- [ ] Release notes written
- [ ] Tag created and pushed
- [ ] Docker images built and pushed
- [ ] PyPI package published
- [ ] GitHub release created

#### Post-Release
- [ ] Release announcement sent
- [ ] Documentation deployed
- [ ] Monitoring alerts configured
- [ ] Support team notified
- [ ] Next version planning started

### Release Notes Template

```markdown
# Release v1.2.3

## 🚀 New Features
- Feature 1 description
- Feature 2 description

## 🐛 Bug Fixes
- Fix 1 description (#123)
- Fix 2 description (#124)

## 📈 Performance Improvements
- Improvement 1 description
- Improvement 2 description

## 📚 Documentation
- Documentation update 1
- Documentation update 2

## ⚠️ Breaking Changes
- Breaking change 1 (Migration: ...)
- Breaking change 2 (Migration: ...)

## 🔒 Security
- Security fix 1
- Security improvement 2

## Full Changelog
https://github.com/org/agent-orchestrator/compare/v1.2.2...v1.2.3
```

## Troubleshooting Development Issues

### Common Development Problems

#### Import Errors
```python
# Problem: ModuleNotFoundError or ImportError with relative imports
# Solution: The project uses sys.path manipulation in main entry points

# In your Python scripts, add at the top:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Or set PYTHONPATH environment variable:
export PYTHONPATH="${PYTHONPATH}:/home/opsvi/master_root/apps/agent-orchestrator/src"

# Or use development installation:
cd /home/opsvi/master_root/apps/agent-orchestrator
pip install -e .
```

#### Async Testing Issues
```python
# Problem: asyncio event loop issues in tests
# Solution: Use proper pytest-asyncio configuration

# In pytest.ini
[tool:pytest]
asyncio_mode = auto
```

#### Database Connection Issues
```bash
# Problem: Cannot connect to PostgreSQL
# Solution: Check service status and configuration
sudo systemctl status postgresql
# Or if using Docker:
docker ps | grep postgres

# Test connection
psql -h localhost -U orchestrator -d orchestrator_dev -c "SELECT 1;"

# Create database if needed
createdb orchestrator_dev

# Check Redis connection (for message bus)
redis-cli ping  # Should return PONG
```

#### Memory Leaks in Development
```python
# Problem: Memory usage grows during development
# Solution: Use memory profiling

from memory_profiler import profile

@profile
def memory_intensive_function():
    # Your code here
    pass
```

### Debugging Tools

#### Logging Configuration for Development
```python
# config/logging_dev.py
import logging

def setup_development_logging():
    """Configure logging for development environment."""

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/development.log')
        ]
    )

    # Set specific logger levels
    logging.getLogger('aiohttp').setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
```

#### Interactive Debugging
```python
# Use ipdb for debugging
import ipdb; ipdb.set_trace()

# Or use IDE breakpoints in VS Code/PyCharm
```

### Performance Debugging

#### Profiling Async Code
```python
# Use line_profiler for async code
@profile
async def async_function():
    # Your async code here
    pass
```

#### Memory Profiling
```bash
# Use memory_profiler
python -m memory_profiler script.py

# Use py-spy for live profiling
py-spy top --pid <pid>

# Monitor dashboard performance
python ui_performance_test.py  # UI performance testing
python websocket_load_test.py  # WebSocket load testing
python realistic_load_test.py  # Realistic load scenarios
```

---

This developer guide provides comprehensive information for contributing to the Agent Orchestrator project. For additional help or questions, please:

1. Check the other documentation files in `/docs`
2. Review task JSON files for workflow examples
3. Examine the `/output` directory for execution results
4. Check `/src` for implementation details

### Quick Reference

#### Key Files and Their Purpose
- `main.py` - Primary CLI entry point
- `production_dashboard.py` - Web dashboard server
- `src/generic_orchestrator.py` - Core orchestration engine
- `src/enhanced_orchestrator.py` - Advanced features
- `run_orchestrator_task.py` - Task execution utility
- `resume_orchestrator.py` - Resume interrupted workflows

#### Common Commands
```bash
# Check system status
python main.py --example

# Start dashboard
python production_dashboard.py

# Run documentation generation
python run_orchestrator_task.py --task-type system-documentation

# View logs
tail -f orchestrator_*.log

# Check output
ls -la output/
```

#### Environment Variables
- `PYTHONPATH` - Should include `src/` directory
- API keys configured in `.env.production`
- Database URLs in configuration files

Happy coding! 🚀
