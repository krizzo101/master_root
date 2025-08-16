# opsvi-agents

Multi-agent system management

## Features

Core opsvi-agents functionality, configuration management, error handling

## Installation

```bash
pip install opsvi-agents
```

## Quick Start

```python
from opsvi_agents import OpsviAgentsManager
from opsvi_agents.config.settings import OpsviAgentsConfig

# Create configuration
config = OpsviAgentsConfig(
    enabled=True,
    debug=True
)

# Create and initialize component
component = OpsviAgentsManager(config=config)
await component.initialize()

# Use the component
from opsvi_agents import OpsviAgentsManager

# Cleanup
await component.shutdown()
```

## Configuration

opsvi-agents can be configured using environment variables or programmatically:

### Environment Variables

```bash
export OPSVI_OPSVI_AGENTS__ENABLED=true
export OPSVI_OPSVI_AGENTS__DEBUG=false
export OPSVI_OPSVI_AGENTS__LOG_LEVEL=INFO
OPSVI_OPSVI_AGENTS_ENABLED=true
```

### Programmatic Configuration

```python
from opsvi_agents.config.settings import OpsviAgentsConfig

config = OpsviAgentsConfig(
    enabled=True,
    debug=False,
    log_level="INFO",
    OpsviAgentsConfig(enabled=True)
)
```

## API Reference

### OpsviAgentsManager

The main component class for opsvi-agents.

#### Methods

- `initialize()` - Initialize the component
- `shutdown()` - Shutdown the component
- `health_check()` - Perform health check


### OpsviAgentsConfig

Configuration class for opsvi-agents.

#### Fields

- `enabled` (bool) - Enable the component
- `debug` (bool) - Enable debug mode
- `log_level` (str) - Logging level


## Development

### Setup

```bash
git clone https://github.com/opsvi/opsvi-agents
cd opsvi-agents
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
