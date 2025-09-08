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

### Development Philosophy

The Agent Orchestrator follows these core development principles:

- **Production-First Design**: All features are built with production reliability in mind
- **Async-First Architecture**: Leveraging Python's asyncio for high concurrency
- **Comprehensive Testing**: Unit, integration, and load testing for all components
- **Documentation-Driven Development**: Code changes must include documentation updates
- **Security by Design**: Security considerations are integrated from the start

## Getting Started

### Development Environment Setup

#### Prerequisites
- Python 3.11+ (recommended)
- Git 2.0+
- PostgreSQL 13+ (for development database)
- Redis 6.0+ (for caching and message bus)
- Docker 20.10+ (optional, for containerized development)

#### Quick Setup Script
```bash
#!/bin/bash
# setup-dev-environment.sh

set -e

echo "Setting up Agent Orchestrator development environment..."

# Create project directory
mkdir -p ~/projects/agent-orchestrator
cd ~/projects/agent-orchestrator

# Clone repository
git clone <repository-url> .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Create development directories
mkdir -p {logs,outputs,checkpoints,test-data}

# Setup development database
createdb orchestrator_dev || echo "Database already exists"

# Copy configuration templates
cp .env.example .env.development
cp production_config.json dev_config.json

echo "Development environment setup complete!"
echo "Next steps:"
echo "1. Edit .env.development with your API keys"
echo "2. Run: python -m pytest tests/ to verify setup"
echo "3. Run: python main.py --example to test basic functionality"
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
# requirements-dev.txt
# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0

# Code Quality
black>=23.0.0
isort>=5.12.0
flake8>=5.0.0
mypy>=1.0.0
pre-commit>=3.0.0

# Development Tools
ipython>=8.0.0
ipdb>=0.13.0
watchdog>=3.0.0

# Documentation
sphinx>=5.0.0
sphinx-rtd-theme>=1.2.0
myst-parser>=1.0.0

# Performance Testing
locust>=2.14.0
memory-profiler>=0.60.0
```

## Development Workflow

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

### Pre-commit Hooks

Our pre-commit configuration (`.pre-commit-config.yaml`):

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 5.0.4
    hooks:
      - id: flake8
        args: ["--max-line-length=88", "--extend-ignore=E203,W503"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.1
    hooks:
      - id: mypy
        args: [--strict]
        additional_dependencies: [types-requests, types-PyYAML]
```

## Code Architecture

### Project Structure

```
agent-orchestrator/
├── src/                              # Core source code
│   ├── __init__.py
│   ├── generic_orchestrator.py       # Main orchestrator
│   ├── enhanced_orchestrator.py      # Advanced orchestrator
│   ├── enhanced_token_pool.py        # Token management
│   ├── session_analytics_engine.py   # Analytics system
│   ├── gpt5_payload_generator.py     # Payload generation
│   ├── providers/                    # AI provider integrations
│   │   ├── __init__.py
│   │   ├── base_provider.py         # Abstract base provider
│   │   └── openai_provider.py       # OpenAI integration
│   ├── workflows/                    # Workflow management
│   │   ├── __init__.py
│   │   └── resumable_orchestrator.py
│   ├── persistence/                  # Database layer
│   │   ├── __init__.py
│   │   ├── database.py              # Database management
│   │   └── models.py                # Data models
│   ├── monitoring/                   # Monitoring components
│   │   ├── __init__.py
│   │   └── dashboard_server.py      # Dashboard backend
│   └── utils/                       # Utility functions
│       ├── __init__.py
│       ├── logging.py              # Logging configuration
│       └── config.py               # Configuration management
├── tests/                           # Test suite
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   ├── performance/                # Performance tests
│   └── fixtures/                   # Test fixtures
├── docs/                           # Documentation
│   ├── README.md                   # Project overview
│   ├── ARCHITECTURE.md             # System architecture
│   ├── USER_GUIDE.md               # User documentation
│   ├── API_REFERENCE.md            # API documentation
│   ├── DEPLOYMENT.md               # Deployment guide
│   └── DEVELOPER_GUIDE.md          # This file
├── web/                            # Dashboard frontend
│   ├── index.html                  # Main dashboard
│   ├── css/                        # Styles
│   └── js/                         # JavaScript
├── scripts/                        # Utility scripts
├── config/                         # Configuration files
└── docker/                         # Docker configurations
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
tests/
├── unit/                    # Unit tests (isolated, fast)
│   ├── test_orchestrator.py
│   ├── test_token_pool.py
│   └── test_providers.py
├── integration/             # Integration tests (components together)
│   ├── test_workflow_execution.py
│   ├── test_database_integration.py
│   └── test_dashboard_api.py
├── performance/             # Performance and load tests
│   ├── test_load_balancing.py
│   ├── test_memory_usage.py
│   └── test_concurrent_execution.py
├── fixtures/               # Test data and fixtures
│   ├── sample_tasks.json
│   └── test_responses.py
└── conftest.py            # Pytest configuration
```

### Testing Guidelines

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
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run specific test categories
python -m pytest tests/unit/          # Unit tests only
python -m pytest tests/integration/   # Integration tests only
python -m pytest tests/performance/   # Performance tests only

# Run tests matching pattern
python -m pytest -k "test_orchestrator"

# Run with verbose output
python -m pytest -v

# Run with performance profiling
python -m pytest --profile --profile-svg

# Parallel test execution
python -m pytest -n auto  # Requires pytest-xdist
```

### Test Configuration

```python
# tests/conftest.py
import pytest
import asyncio
from unittest.mock import AsyncMock

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
from src.providers.base_provider import BaseProvider
from typing import Dict, Any

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
from src.factory import ProviderFactory
ProviderFactory._providers['custom'] = CustomAIProvider
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
# Update version in setup.py and __init__.py
# Commit version bump
git add .
git commit -m "chore: bump version to v1.2.3"

# Create and push tag
git tag v1.2.3
git push origin v1.2.3

# Trigger release workflow
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
# Problem: ModuleNotFoundError
# Solution: Ensure PYTHONPATH includes src/
export PYTHONPATH="${PYTHONPATH}:/path/to/agent-orchestrator/src"

# Or use development installation
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
psql -h localhost -U orchestrator -d collaboration -c "SELECT 1;"
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
```

---

This developer guide provides comprehensive information for contributing to the Agent Orchestrator project. For additional help or questions, please:

1. Check the other documentation files
2. Review existing issues and pull requests
3. Create a new issue with detailed information
4. Join the development discussions

Happy coding! 🚀
