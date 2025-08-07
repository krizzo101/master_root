# opsvi-pipeline

Data processing pipeline orchestration

## Features

Core opsvi-pipeline functionality, configuration management, error handling

## Installation

```bash
pip install opsvi-pipeline
```

## Quick Start

```python
from opsvi_pipeline import OpsviPipelineManager
from opsvi_pipeline.config.settings import OpsviPipelineConfig

# Create configuration
config = OpsviPipelineConfig(
    enabled=True,
    debug=True
)

# Create and initialize component
component = OpsviPipelineManager(config=config)
await component.initialize()

# Use the component
from opsvi_pipeline import OpsviPipelineManager

# Cleanup
await component.shutdown()
```

## Configuration

opsvi-pipeline can be configured using environment variables or programmatically:

### Environment Variables

```bash
export OPSVI_OPSVI_PIPELINE__ENABLED=true
export OPSVI_OPSVI_PIPELINE__DEBUG=false
export OPSVI_OPSVI_PIPELINE__LOG_LEVEL=INFO
OPSVI_OPSVI_PIPELINE_ENABLED=true
```

### Programmatic Configuration

```python
from opsvi_pipeline.config.settings import OpsviPipelineConfig

config = OpsviPipelineConfig(
    enabled=True,
    debug=False,
    log_level="INFO",
    OpsviPipelineConfig(enabled=True)
)
```

## API Reference

### OpsviPipelineManager

The main component class for opsvi-pipeline.

#### Methods

- `initialize()` - Initialize the component
- `shutdown()` - Shutdown the component
- `health_check()` - Perform health check


### OpsviPipelineConfig

Configuration class for opsvi-pipeline.

#### Fields

- `enabled` (bool) - Enable the component
- `debug` (bool) - Enable debug mode
- `log_level` (str) - Logging level


## Development

### Setup

```bash
git clone https://github.com/opsvi/opsvi-pipeline
cd opsvi-pipeline
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
