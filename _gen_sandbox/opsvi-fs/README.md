# opsvi-fs

File system and storage management

## Features

Core opsvi-fs functionality, configuration management, error handling

## Installation

```bash
pip install opsvi-fs
```

## Quick Start

```python
from opsvi_fs import OpsviFsManager
from opsvi_fs.config.settings import OpsviFsConfig

# Create configuration
config = OpsviFsConfig(
    enabled=True,
    debug=True
)

# Create and initialize component
component = OpsviFsManager(config=config)
await component.initialize()

# Use the component
from opsvi_fs import OpsviFsManager

# Cleanup
await component.shutdown()
```

## Configuration

opsvi-fs can be configured using environment variables or programmatically:

### Environment Variables

```bash
export OPSVI_OPSVI_FS__ENABLED=true
export OPSVI_OPSVI_FS__DEBUG=false
export OPSVI_OPSVI_FS__LOG_LEVEL=INFO
OPSVI_OPSVI_FS_ENABLED=true
```

### Programmatic Configuration

```python
from opsvi_fs.config.settings import OpsviFsConfig

config = OpsviFsConfig(
    enabled=True,
    debug=False,
    log_level="INFO",
    OpsviFsConfig(enabled=True)
)
```

## API Reference

### OpsviFsManager

The main component class for opsvi-fs.

#### Methods

- `initialize()` - Initialize the component
- `shutdown()` - Shutdown the component
- `health_check()` - Perform health check


### OpsviFsConfig

Configuration class for opsvi-fs.

#### Fields

- `enabled` (bool) - Enable the component
- `debug` (bool) - Enable debug mode
- `log_level` (str) - Logging level


## Development

### Setup

```bash
git clone https://github.com/opsvi/opsvi-fs
cd opsvi-fs
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
