# opsvi-http

HTTP client and server functionality

## Features

Core opsvi-http functionality, configuration management, error handling

## Installation

```bash
pip install opsvi-http
```

## Quick Start

```python
from opsvi_http import OpsviHttpManager
from opsvi_http.config.settings import OpsviHttpConfig

# Create configuration
config = OpsviHttpConfig(
    enabled=True,
    debug=True
)

# Create and initialize component
component = OpsviHttpManager(config=config)
await component.initialize()

# Use the component
from opsvi_http import OpsviHttpManager

# Cleanup
await component.shutdown()
```

## Configuration

opsvi-http can be configured using environment variables or programmatically:

### Environment Variables

```bash
export OPSVI_OPSVI_HTTP__ENABLED=true
export OPSVI_OPSVI_HTTP__DEBUG=false
export OPSVI_OPSVI_HTTP__LOG_LEVEL=INFO
OPSVI_OPSVI_HTTP_ENABLED=true
```

### Programmatic Configuration

```python
from opsvi_http.config.settings import OpsviHttpConfig

config = OpsviHttpConfig(
    enabled=True,
    debug=False,
    log_level="INFO",
    OpsviHttpConfig(enabled=True)
)
```

## API Reference

### OpsviHttpManager

The main component class for opsvi-http.

#### Methods

- `initialize()` - Initialize the component
- `shutdown()` - Shutdown the component
- `health_check()` - Perform health check


### OpsviHttpConfig

Configuration class for opsvi-http.

#### Fields

- `enabled` (bool) - Enable the component
- `debug` (bool) - Enable debug mode
- `log_level` (str) - Logging level


## Development

### Setup

```bash
git clone https://github.com/opsvi/opsvi-http
cd opsvi-http
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
