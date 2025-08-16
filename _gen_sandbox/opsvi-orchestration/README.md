# opsvi-orchestration

Workflow and task orchestration

## Features

Core opsvi-orchestration functionality, configuration management, error handling

## Installation

```bash
pip install opsvi-orchestration
```

## Quick Start

```python
from opsvi_orchestration import OpsviOrchestrationManager
from opsvi_orchestration.config.settings import OpsviOrchestrationConfig

# Create configuration
config = OpsviOrchestrationConfig(
    enabled=True,
    debug=True
)

# Create and initialize component
component = OpsviOrchestrationManager(config=config)
await component.initialize()

# Use the component
from opsvi_orchestration import OpsviOrchestrationManager

# Cleanup
await component.shutdown()
```

## Configuration

opsvi-orchestration can be configured using environment variables or programmatically:

### Environment Variables

```bash
export OPSVI_OPSVI_ORCHESTRATION__ENABLED=true
export OPSVI_OPSVI_ORCHESTRATION__DEBUG=false
export OPSVI_OPSVI_ORCHESTRATION__LOG_LEVEL=INFO
OPSVI_OPSVI_ORCHESTRATION_ENABLED=true
```

### Programmatic Configuration

```python
from opsvi_orchestration.config.settings import OpsviOrchestrationConfig

config = OpsviOrchestrationConfig(
    enabled=True,
    debug=False,
    log_level="INFO",
    OpsviOrchestrationConfig(enabled=True)
)
```

## API Reference

### OpsviOrchestrationManager

The main component class for opsvi-orchestration.

#### Methods

- `initialize()` - Initialize the component
- `shutdown()` - Shutdown the component
- `health_check()` - Perform health check


### OpsviOrchestrationConfig

Configuration class for opsvi-orchestration.

#### Fields

- `enabled` (bool) - Enable the component
- `debug` (bool) - Enable debug mode
- `log_level` (str) - Logging level


## Development

### Setup

```bash
git clone https://github.com/opsvi/opsvi-orchestration
cd opsvi-orchestration
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
