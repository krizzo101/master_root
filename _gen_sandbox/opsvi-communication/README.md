# opsvi-communication

Communication and messaging systems

## Features

Core opsvi-communication functionality, configuration management, error handling

## Installation

```bash
pip install opsvi-communication
```

## Quick Start

```python
from opsvi_communication import OpsviCommunicationManager
from opsvi_communication.config.settings import OpsviCommunicationConfig

# Create configuration
config = OpsviCommunicationConfig(
    enabled=True,
    debug=True
)

# Create and initialize component
component = OpsviCommunicationManager(config=config)
await component.initialize()

# Use the component
from opsvi_communication import OpsviCommunicationManager

# Cleanup
await component.shutdown()
```

## Configuration

opsvi-communication can be configured using environment variables or programmatically:

### Environment Variables

```bash
export OPSVI_OPSVI_COMMUNICATION__ENABLED=true
export OPSVI_OPSVI_COMMUNICATION__DEBUG=false
export OPSVI_OPSVI_COMMUNICATION__LOG_LEVEL=INFO
OPSVI_OPSVI_COMMUNICATION_ENABLED=true
```

### Programmatic Configuration

```python
from opsvi_communication.config.settings import OpsviCommunicationConfig

config = OpsviCommunicationConfig(
    enabled=True,
    debug=False,
    log_level="INFO",
    OpsviCommunicationConfig(enabled=True)
)
```

## API Reference

### OpsviCommunicationManager

The main component class for opsvi-communication.

#### Methods

- `initialize()` - Initialize the component
- `shutdown()` - Shutdown the component
- `health_check()` - Perform health check


### OpsviCommunicationConfig

Configuration class for opsvi-communication.

#### Fields

- `enabled` (bool) - Enable the component
- `debug` (bool) - Enable debug mode
- `log_level` (str) - Logging level


## Development

### Setup

```bash
git clone https://github.com/opsvi/opsvi-communication
cd opsvi-communication
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
