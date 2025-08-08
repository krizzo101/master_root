# opsvi-gateway

Multi-interface gateway and API management

## Features

Core opsvi-gateway functionality, configuration management, error handling

## Installation

```bash
pip install opsvi-gateway
```

## Quick Start

```python
from opsvi_gateway import OpsviGatewayManager
from opsvi_gateway.config.settings import OpsviGatewayConfig

# Create configuration
config = OpsviGatewayConfig(
    enabled=True,
    debug=True
)

# Create and initialize component
component = OpsviGatewayManager(config=config)
await component.initialize()

# Use the component
from opsvi_gateway import OpsviGatewayManager

# Cleanup
await component.shutdown()
```

## Configuration

opsvi-gateway can be configured using environment variables or programmatically:

### Environment Variables

```bash
export OPSVI_OPSVI_GATEWAY__ENABLED=true
export OPSVI_OPSVI_GATEWAY__DEBUG=false
export OPSVI_OPSVI_GATEWAY__LOG_LEVEL=INFO
OPSVI_OPSVI_GATEWAY_ENABLED=true
```

### Programmatic Configuration

```python
from opsvi_gateway.config.settings import OpsviGatewayConfig

config = OpsviGatewayConfig(
    enabled=True,
    debug=False,
    log_level="INFO",
    OpsviGatewayConfig(enabled=True)
)
```

## API Reference

### OpsviGatewayManager

The main component class for opsvi-gateway.

#### Methods

- `initialize()` - Initialize the component
- `shutdown()` - Shutdown the component
- `health_check()` - Perform health check


### OpsviGatewayConfig

Configuration class for opsvi-gateway.

#### Fields

- `enabled` (bool) - Enable the component
- `debug` (bool) - Enable debug mode
- `log_level` (str) - Logging level


## Development

### Setup

```bash
git clone https://github.com/opsvi/opsvi-gateway
cd opsvi-gateway
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
