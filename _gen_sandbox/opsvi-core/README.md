# opsvi-core

Core functionality for OPSVI applications

## Features

Core opsvi-core functionality, configuration management, error handling

## Installation

```bash
pip install opsvi-core
```

## Quick Start

```python
from opsvi_core import OpsviCoreManager
from opsvi_core.config.settings import OpsviCoreConfig

# Create configuration
config = OpsviCoreConfig(
    enabled=True,
    debug=True
)

# Create and initialize component
component = OpsviCoreManager(config=config)
await component.initialize()

# Use the component
from opsvi_core import OpsviCoreManager

# Cleanup
await component.shutdown()
```

## Configuration

opsvi-core can be configured using environment variables or programmatically:

### Environment Variables

```bash
export OPSVI_OPSVI_CORE__ENABLED=true
export OPSVI_OPSVI_CORE__DEBUG=false
export OPSVI_OPSVI_CORE__LOG_LEVEL=INFO
OPSVI_OPSVI_CORE_ENABLED=true
```

### Programmatic Configuration

```python
from opsvi_core.config.settings import OpsviCoreConfig

config = OpsviCoreConfig(
    enabled=True,
    debug=False,
    log_level="INFO",
    OpsviCoreConfig(enabled=True)
)
```

## API Reference

### OpsviCoreManager

The main component class for opsvi-core.

#### Methods

- `initialize()` - Initialize the component
- `shutdown()` - Shutdown the component
- `health_check()` - Perform health check


### OpsviCoreConfig

Configuration class for opsvi-core.

#### Fields

- `enabled` (bool) - Enable the component
- `debug` (bool) - Enable debug mode
- `log_level` (str) - Logging level


## Development

### Setup

```bash
git clone https://github.com/opsvi/opsvi-core
cd opsvi-core
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
