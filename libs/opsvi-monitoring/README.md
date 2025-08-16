# opsvi-monitoring

Monitoring and observability

## Features

Core opsvi-monitoring functionality, configuration management, error handling

## Installation

```bash
pip install opsvi-monitoring
```

## Quick Start

```python
from opsvi_monitoring import OpsviMonitoringManager
from opsvi_monitoring.config.settings import OpsviMonitoringConfig

# Create configuration
config = OpsviMonitoringConfig(
    enabled=True,
    debug=True
)

# Create and initialize component
component = OpsviMonitoringManager(config=config)
await component.initialize()

# Use the component
from opsvi_monitoring import OpsviMonitoringManager

# Cleanup
await component.shutdown()
```

## Configuration

opsvi-monitoring can be configured using environment variables or programmatically:

### Environment Variables

```bash
export OPSVI_OPSVI_MONITORING__ENABLED=true
export OPSVI_OPSVI_MONITORING__DEBUG=false
export OPSVI_OPSVI_MONITORING__LOG_LEVEL=INFO
OPSVI_OPSVI_MONITORING_ENABLED=true
```

### Programmatic Configuration

```python
from opsvi_monitoring.config.settings import OpsviMonitoringConfig

config = OpsviMonitoringConfig(
    enabled=True,
    debug=False,
    log_level="INFO",
    OpsviMonitoringConfig(enabled=True)
)
```

## API Reference

### OpsviMonitoringManager

The main component class for opsvi-monitoring.

#### Methods

- `initialize()` - Initialize the component
- `shutdown()` - Shutdown the component
- `health_check()` - Perform health check


### OpsviMonitoringConfig

Configuration class for opsvi-monitoring.

#### Fields

- `enabled` (bool) - Enable the component
- `debug` (bool) - Enable debug mode
- `log_level` (str) - Logging level


## Development

### Setup

```bash
git clone https://github.com/opsvi/opsvi-monitoring
cd opsvi-monitoring
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
