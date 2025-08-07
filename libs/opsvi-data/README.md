# opsvi-data

Data management and database access

## Features

Core opsvi-data functionality, configuration management, error handling

## Installation

```bash
pip install opsvi-data
```

## Quick Start

```python
from opsvi_data import OpsviDataManager
from opsvi_data.config.settings import OpsviDataConfig

# Create configuration
config = OpsviDataConfig(
    enabled=True,
    debug=True
)

# Create and initialize component
component = OpsviDataManager(config=config)
await component.initialize()

# Use the component
from opsvi_data import OpsviDataManager

# Cleanup
await component.shutdown()
```

## Configuration

opsvi-data can be configured using environment variables or programmatically:

### Environment Variables

```bash
export OPSVI_OPSVI_DATA__ENABLED=true
export OPSVI_OPSVI_DATA__DEBUG=false
export OPSVI_OPSVI_DATA__LOG_LEVEL=INFO
OPSVI_OPSVI_DATA_ENABLED=true
```

### Programmatic Configuration

```python
from opsvi_data.config.settings import OpsviDataConfig

config = OpsviDataConfig(
    enabled=True,
    debug=False,
    log_level="INFO",
    OpsviDataConfig(enabled=True)
)
```

## API Reference

### OpsviDataManager

The main component class for opsvi-data.

#### Methods

- `initialize()` - Initialize the component
- `shutdown()` - Shutdown the component
- `health_check()` - Perform health check


### OpsviDataConfig

Configuration class for opsvi-data.

#### Fields

- `enabled` (bool) - Enable the component
- `debug` (bool) - Enable debug mode
- `log_level` (str) - Logging level


## Development

### Setup

```bash
git clone https://github.com/opsvi/opsvi-data
cd opsvi-data
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
