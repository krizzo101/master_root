# opsvi-deploy

Deployment and infrastructure management

## Features

Core opsvi-deploy functionality, configuration management, error handling

## Installation

```bash
pip install opsvi-deploy
```

## Quick Start

```python
from opsvi_deploy import OpsviDeployManager
from opsvi_deploy.config.settings import OpsviDeployConfig

# Create configuration
config = OpsviDeployConfig(
    enabled=True,
    debug=True
)

# Create and initialize component
component = OpsviDeployManager(config=config)
await component.initialize()

# Use the component
from opsvi_deploy import OpsviDeployManager

# Cleanup
await component.shutdown()
```

## Configuration

opsvi-deploy can be configured using environment variables or programmatically:

### Environment Variables

```bash
export OPSVI_OPSVI_DEPLOY__ENABLED=true
export OPSVI_OPSVI_DEPLOY__DEBUG=false
export OPSVI_OPSVI_DEPLOY__LOG_LEVEL=INFO
OPSVI_OPSVI_DEPLOY_ENABLED=true
```

### Programmatic Configuration

```python
from opsvi_deploy.config.settings import OpsviDeployConfig

config = OpsviDeployConfig(
    enabled=True,
    debug=False,
    log_level="INFO",
    OpsviDeployConfig(enabled=True)
)
```

## API Reference

### OpsviDeployManager

The main component class for opsvi-deploy.

#### Methods

- `initialize()` - Initialize the component
- `shutdown()` - Shutdown the component
- `health_check()` - Perform health check


### OpsviDeployConfig

Configuration class for opsvi-deploy.

#### Fields

- `enabled` (bool) - Enable the component
- `debug` (bool) - Enable debug mode
- `log_level` (str) - Logging level


## Development

### Setup

```bash
git clone https://github.com/opsvi/opsvi-deploy
cd opsvi-deploy
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
