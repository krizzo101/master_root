# opsvi-memory

Memory and caching systems

## Features

Core opsvi-memory functionality, configuration management, error handling

## Installation

```bash
pip install opsvi-memory
```

## Quick Start

```python
from opsvi_memory import OpsviMemoryManager
from opsvi_memory.config.settings import OpsviMemoryConfig

# Create configuration
config = OpsviMemoryConfig(
    enabled=True,
    debug=True
)

# Create and initialize component
component = OpsviMemoryManager(config=config)
await component.initialize()

# Use the component
from opsvi_memory import OpsviMemoryManager

# Cleanup
await component.shutdown()
```

## Configuration

opsvi-memory can be configured using environment variables or programmatically:

### Environment Variables

```bash
export OPSVI_OPSVI_MEMORY__ENABLED=true
export OPSVI_OPSVI_MEMORY__DEBUG=false
export OPSVI_OPSVI_MEMORY__LOG_LEVEL=INFO
OPSVI_OPSVI_MEMORY_ENABLED=true
```

### Programmatic Configuration

```python
from opsvi_memory.config.settings import OpsviMemoryConfig

config = OpsviMemoryConfig(
    enabled=True,
    debug=False,
    log_level="INFO",
    OpsviMemoryConfig(enabled=True)
)
```

## API Reference

### OpsviMemoryManager

The main component class for opsvi-memory.

#### Methods

- `initialize()` - Initialize the component
- `shutdown()` - Shutdown the component
- `health_check()` - Perform health check


### OpsviMemoryConfig

Configuration class for opsvi-memory.

#### Fields

- `enabled` (bool) - Enable the component
- `debug` (bool) - Enable debug mode
- `log_level` (str) - Logging level


## Development

### Setup

```bash
git clone https://github.com/opsvi/opsvi-memory
cd opsvi-memory
pip install -e ".[dev]"
```

### Testing

```bash
pytest
```

### Code Quality

```bash
ruff check .
black .
mypy .
```

## Contributing

Please read CONTRIBUTING.md for development guidelines

## License

MIT License - see LICENSE file for details

## Changelog

See CHANGELOG.md for version history
