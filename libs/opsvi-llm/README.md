# opsvi-llm

LLM integration and management

## Features

Core opsvi-llm functionality, configuration management, error handling

## Installation

```bash
pip install opsvi-llm
```

## Quick Start

```python
from opsvi_llm import OpsviLlmManager
from opsvi_llm.config.settings import OpsviLlmConfig

# Create configuration
config = OpsviLlmConfig(
    enabled=True,
    debug=True
)

# Create and initialize component
component = OpsviLlmManager(config=config)
await component.initialize()

# Use the component
from opsvi_llm import OpsviLlmManager

# Cleanup
await component.shutdown()
```

## Configuration

opsvi-llm can be configured using environment variables or programmatically:

### Environment Variables

```bash
export OPSVI_OPSVI_LLM__ENABLED=true
export OPSVI_OPSVI_LLM__DEBUG=false
export OPSVI_OPSVI_LLM__LOG_LEVEL=INFO
OPSVI_OPSVI_LLM_ENABLED=true
```

### Programmatic Configuration

```python
from opsvi_llm.config.settings import OpsviLlmConfig

config = OpsviLlmConfig(
    enabled=True,
    debug=False,
    log_level="INFO",
    OpsviLlmConfig(enabled=True)
)
```

## API Reference

### OpsviLlmManager

The main component class for opsvi-llm.

#### Methods

- `initialize()` - Initialize the component
- `shutdown()` - Shutdown the component
- `health_check()` - Perform health check


### OpsviLlmConfig

Configuration class for opsvi-llm.

#### Fields

- `enabled` (bool) - Enable the component
- `debug` (bool) - Enable debug mode
- `log_level` (str) - Logging level


## Development

### Setup

```bash
git clone https://github.com/opsvi/opsvi-llm
cd opsvi-llm
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
