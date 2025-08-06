# OPSVI Core Library

Core utilities and base classes for the OPSVI ecosystem. Provides configuration, logging, exceptions, and base patterns for AI/ML operations.

## Features

- **Type-Safe Configuration**: Pydantic V2-based configuration with environment variable support
- **Structured Logging**: Structlog integration with OpenTelemetry support
- **Comprehensive Error Handling**: Custom exception hierarchy for robust error management
- **Base Patterns**: Abstract base classes for actors, agents, and components
- **Async Support**: Full async/await support throughout the library
- **Production Ready**: Comprehensive testing, type safety, and documentation

## Installation

```bash
# Install from local development
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# Install with documentation dependencies
pip install -e ".[docs]"
```

## Quick Start

### Configuration

```python
from opsvi_core import config, AppConfig

# Access configuration
print(config.app_name)  # "opsvi"
print(config.environment)  # "development"

# Load custom configuration
custom_config = AppConfig(
    app_name="my_app",
    environment="production",
    debug=False
)
```

### Logging

```python
from opsvi_core import setup_logging, get_logger

# Setup logging (automatically done on import)
setup_logging("DEBUG")

# Get a structured logger
logger = get_logger(__name__)
logger.info("Application started", user_id="123", action="login")
```

### Base Actor

```python
from opsvi_core import BaseActor
import asyncio

class MyActor(BaseActor):
    async def on_start(self):
        # Custom initialization logic
        pass

    async def on_stop(self):
        # Custom cleanup logic
        pass

    async def process_message(self, message):
        # Process incoming messages
        return {"result": f"Processed: {message}"}

# Usage
async def main():
    actor = MyActor("my_actor")
    await actor.start()

    result = await actor.handle_message({"data": "test"})
    print(result)  # {"result": "Processed: {'data': 'test'}"}

    await actor.stop()

asyncio.run(main())
```

### Base Agent

```python
from opsvi_core import BaseAgent
import asyncio

class MyAgent(BaseAgent):
    async def process(self, message):
        # Process messages
        return {"response": f"Agent processed: {message}"}

# Usage
async def main():
    agent = MyAgent("my_agent")
    await agent.activate()

    response = await agent.handle({"query": "hello"})
    print(response)  # {"response": "Agent processed: {'query': 'hello'}"}

    await agent.deactivate()

asyncio.run(main())
```

### Error Handling

```python
from opsvi_core import (
    OpsviError,
    ConfigurationError,
    InitializationError,
    ValidationError,
    ExternalServiceError
)

try:
    # Your code here
    raise ConfigurationError("Invalid configuration")
except ConfigurationError as e:
    print(f"Configuration error: {e.message}")
    print(f"Details: {e.details}")
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd opsvi-core

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=opsvi_core

# Run specific test file
pytest tests/test_core.py

# Run async tests
pytest -m asyncio
```

### Code Quality

```bash
# Format code
black opsvi_core tests

# Lint code
ruff check opsvi_core tests

# Type checking
mypy opsvi_core

# Run all quality checks
pre-commit run --all-files
```

### Building Documentation

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build documentation
cd docs
make html
```

## Architecture

### Core Components

- **Configuration**: Type-safe configuration management with Pydantic V2
- **Logging**: Structured logging with Structlog and OpenTelemetry integration
- **Exceptions**: Comprehensive exception hierarchy for error handling
- **Patterns**: Base classes for actors, agents, and components

### Design Principles

- **Type Safety**: Full type hints and mypy compliance
- **Async First**: All I/O operations are async
- **Production Ready**: Comprehensive error handling and logging
- **Extensible**: Plugin architecture and base classes for extension
- **Testable**: Comprehensive test coverage and mocking support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For support and questions, please open an issue on GitHub or contact the OPSVI team.