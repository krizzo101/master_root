# opsvi-rag

Retrieval Augmented Generation system

## Features

Core opsvi-rag functionality, configuration management, error handling

## Installation

```bash
pip install opsvi-rag
```

## Quick Start

```python
from opsvi_rag import OpsviRagManager
from opsvi_rag.config.settings import OpsviRagConfig

# Create configuration
config = OpsviRagConfig(
    enabled=True,
    debug=True
)

# Create and initialize component
component = OpsviRagManager(config=config)
await component.initialize()

# Use the component
from opsvi_rag import OpsviRagManager

# Cleanup
await component.shutdown()
```

## Configuration

opsvi-rag can be configured using environment variables or programmatically:

### Environment Variables

```bash
export OPSVI_OPSVI_RAG__ENABLED=true
export OPSVI_OPSVI_RAG__DEBUG=false
export OPSVI_OPSVI_RAG__LOG_LEVEL=INFO
OPSVI_OPSVI_RAG_ENABLED=true
```

### Programmatic Configuration

```python
from opsvi_rag.config.settings import OpsviRagConfig

config = OpsviRagConfig(
    enabled=True,
    debug=False,
    log_level="INFO",
    OpsviRagConfig(enabled=True)
)
```

## API Reference

### OpsviRagManager

The main component class for opsvi-rag.

#### Methods

- `initialize()` - Initialize the component
- `shutdown()` - Shutdown the component
- `health_check()` - Perform health check


### OpsviRagConfig

Configuration class for opsvi-rag.

#### Fields

- `enabled` (bool) - Enable the component
- `debug` (bool) - Enable debug mode
- `log_level` (str) - Logging level


## Development

### Setup

```bash
git clone https://github.com/opsvi/opsvi-rag
cd opsvi-rag
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
