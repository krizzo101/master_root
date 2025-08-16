# opsvi-security

Security and encryption utilities

## Features

Core opsvi-security functionality, configuration management, error handling

## Installation

```bash
pip install opsvi-security
```

## Quick Start

```python
from opsvi_security import OpsviSecurityManager
from opsvi_security.config.settings import OpsviSecurityConfig

# Create configuration
config = OpsviSecurityConfig(
    enabled=True,
    debug=True
)

# Create and initialize component
component = OpsviSecurityManager(config=config)
await component.initialize()

# Use the component
from opsvi_security import OpsviSecurityManager

# Cleanup
await component.shutdown()
```

## Configuration

opsvi-security can be configured using environment variables or programmatically:

### Environment Variables

```bash
export OPSVI_OPSVI_SECURITY__ENABLED=true
export OPSVI_OPSVI_SECURITY__DEBUG=false
export OPSVI_OPSVI_SECURITY__LOG_LEVEL=INFO
OPSVI_OPSVI_SECURITY_ENABLED=true
```

### Programmatic Configuration

```python
from opsvi_security.config.settings import OpsviSecurityConfig

config = OpsviSecurityConfig(
    enabled=True,
    debug=False,
    log_level="INFO",
    OpsviSecurityConfig(enabled=True)
)
```

## API Reference

### OpsviSecurityManager

The main component class for opsvi-security.

#### Methods

- `initialize()` - Initialize the component
- `shutdown()` - Shutdown the component
- `health_check()` - Perform health check


### OpsviSecurityConfig

Configuration class for opsvi-security.

#### Fields

- `enabled` (bool) - Enable the component
- `debug` (bool) - Enable debug mode
- `log_level` (str) - Logging level


## Development

### Setup

```bash
git clone https://github.com/opsvi/opsvi-security
cd opsvi-security
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
