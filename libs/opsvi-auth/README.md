# opsvi-auth

Authentication and authorization system

## Features

Core opsvi-auth functionality, configuration management, error handling

## Installation

```bash
pip install opsvi-auth
```

## Quick Start

```python
from opsvi_auth import OpsviAuthManager
from opsvi_auth.config.settings import OpsviAuthConfig

# Create configuration
config = OpsviAuthConfig(
    enabled=True,
    debug=True
)

# Create and initialize component
component = OpsviAuthManager(config=config)
await component.initialize()

# Use the component
from opsvi_auth import OpsviAuthManager

# Cleanup
await component.shutdown()
```

## Configuration

opsvi-auth can be configured using environment variables or programmatically:

### Environment Variables

```bash
export OPSVI_OPSVI_AUTH__ENABLED=true
export OPSVI_OPSVI_AUTH__DEBUG=false
export OPSVI_OPSVI_AUTH__LOG_LEVEL=INFO
OPSVI_OPSVI_AUTH_ENABLED=true
```

### Programmatic Configuration

```python
from opsvi_auth.config.settings import OpsviAuthConfig

config = OpsviAuthConfig(
    enabled=True,
    debug=False,
    log_level="INFO",
    OpsviAuthConfig(enabled=True)
)
```

## API Reference

### OpsviAuthManager

The main component class for opsvi-auth.

#### Methods

- `initialize()` - Initialize the component
- `shutdown()` - Shutdown the component
- `health_check()` - Perform health check


### OpsviAuthConfig

Configuration class for opsvi-auth.

#### Fields

- `enabled` (bool) - Enable the component
- `debug` (bool) - Enable debug mode
- `log_level` (str) - Logging level


## Development

### Setup

```bash
git clone https://github.com/opsvi/opsvi-auth
cd opsvi-auth
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
