# opsvi-foundation

Foundation library providing base components and utilities

## Features

Core opsvi-foundation functionality, configuration management, error handling

## Installation

```bash
pip install opsvi-foundation
```

## Quick Start

```python
from opsvi_foundation import OpsviFoundationManager
from opsvi_foundation.config.settings import OpsviFoundationConfig

# Create configuration
config = OpsviFoundationConfig(
    enabled=True,
    debug=True
)

# Create and initialize component
component = OpsviFoundationManager(config=config)
await component.initialize()

# Use the component
from opsvi_foundation import OpsviFoundationManager

# Cleanup
await component.shutdown()
```

## Configuration

opsvi-foundation can be configured using environment variables or programmatically:

### Environment Variables

```bash
export OPSVI_OPSVI_FOUNDATION__ENABLED=true
export OPSVI_OPSVI_FOUNDATION__DEBUG=false
export OPSVI_OPSVI_FOUNDATION__LOG_LEVEL=INFO
OPSVI_OPSVI_FOUNDATION_ENABLED=true
```

### Programmatic Configuration

```python
from opsvi_foundation.config.settings import OpsviFoundationConfig

config = OpsviFoundationConfig(
    enabled=True,
    debug=False,
    log_level="INFO",
    OpsviFoundationConfig(enabled=True)
)
```

## API Reference

### OpsviFoundationManager

The main component class for opsvi-foundation.

#### Methods

- `initialize()` - Initialize the component
- `shutdown()` - Shutdown the component
- `health_check()` - Perform health check


### OpsviFoundationConfig

Configuration class for opsvi-foundation.

#### Fields

- `enabled` (bool) - Enable the component
- `debug` (bool) - Enable debug mode
- `log_level` (str) - Logging level


## Development

### Setup

```bash
git clone https://github.com/opsvi/opsvi-foundation
cd opsvi-foundation
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
