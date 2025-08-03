# OPSVI Core Library

Core utilities and base classes for OPSVI applications.

## Features

- Configuration management with environment variable support
- Structured logging with structlog
- Base exception classes
- Common utilities

## Usage

```python
from opsvi_core import Config, ConfigManager, get_logger, setup_logging

# Setup logging
setup_logging(level="INFO")

# Get logger
logger = get_logger(__name__)

# Load configuration
config_manager = ConfigManager()
config = config_manager.load_from_env()

logger.info("Application started", app_name=config.app_name)
```

## Installation

```bash
uv add opsvi-core
```