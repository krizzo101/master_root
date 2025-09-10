# Unified Context Ingestion Pipeline Examples

This directory contains examples demonstrating the usage of the unified context ingestion pipeline.

## Quick Start

```bash
cd /home/opsvi/master_root/apps/project-context
python examples/pipeline_example.py
```

## Examples Overview

### 1. Basic Pipeline Example
Demonstrates the simplest way to start the ingestion pipeline:
- Uses default configuration
- Initializes with built-in adapters
- Runs for a short duration

### 2. Configuration-Based Example
Shows how to use configuration files:
- Creates a template configuration
- Loads pipeline with custom settings
- Demonstrates configuration management

### 3. Manual Setup Example
Illustrates manual component setup:
- Creates registry and adapters manually
- Shows adapter registration process
- Demonstrates validation

### 4. Monitoring Example
Demonstrates monitoring capabilities:
- Creates monitoring system
- Records sample metrics
- Shows status reporting

### 5. Context Manager Example
Shows proper lifecycle management:
- Uses async context manager
- Automatic cleanup
- Exception handling

## Production Usage

For production deployments, use the orchestrator:

```python
from src.project_context.ingestion import PipelineOrchestrator

# Create with configuration file
orchestrator = PipelineOrchestrator(config_path="config.yaml")

# Run pipeline
async with orchestrator.managed_lifecycle():
    # Pipeline runs automatically
    await orchestrator.start(wait=True)
```

## Command Line Usage

Run the pipeline from command line:

```bash
python -m src.project_context.ingestion.orchestrator --config config.yaml
```

Create template configuration:

```bash
python -m src.project_context.ingestion.orchestrator --template
```

## Configuration

Example configuration file structure:

```yaml
pipeline:
  max_concurrent_adapters: 10
  batch_commit_size: 1000
  database_url: "postgresql://user:pass@localhost/db"
  enable_relationship_detection: true

adapters:
  chat:
    source_type: "chat"
    batch_mode: "streaming"
    source_config:
      input_format: "jsonl"
      watch_directories: ["./data"]

  code:
    source_type: "code"
    batch_mode: "batch"
    source_config:
      scan_directories: ["."]
      include_patterns: ["*.py", "*.js"]

monitoring:
  metrics_retention_hours: 24
  enable_system_metrics: true
```

## Key Features

### Async Processing
- Full asynchronous pipeline
- Non-blocking operations
- Concurrent adapter processing

### Error Handling
- Circuit breaker pattern
- Exponential backoff retry
- Comprehensive error logging

### Monitoring
- Real-time metrics collection
- Health checks
- Alert system

### Pluggable Architecture
- Custom adapter development
- Runtime adapter registration
- Configuration-driven setup

### Database Integration
- PostgreSQL + TimescaleDB support
- Connection pooling
- Batch processing

### Relationship Detection
- Automatic relationship discovery
- Temporal correlation analysis
- Cross-source relationships

## Adapter Development

Create custom adapters by extending BaseAdapter:

```python
from src.project_context.ingestion import BaseAdapter, AdapterConfig

class CustomAdapter(BaseAdapter):
    @classmethod
    def default_config(cls):
        return AdapterConfig(
            adapter_id="custom",
            source_type="custom",
            # ... other config
        )

    async def initialize(self):
        # Setup resources
        pass

    async def fetch_items(self, since=None, until=None, limit=None):
        # Yield raw data items
        pass

    async def transform_item(self, raw_item):
        # Transform to ContextItem
        pass

    async def cleanup(self):
        # Cleanup resources
        pass
```

## Performance

Expected throughput targets:
- **Chat Adapter**: 100-500 messages/second
- **Code Adapter**: 50-200 files/second
- **Git Adapter**: 200-1000 commits/second
- **Error Adapter**: 500-2000 log entries/second

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check `database_url` in configuration
   - Ensure PostgreSQL is running
   - Verify permissions

2. **Adapter Not Starting**
   - Check adapter configuration
   - Verify source directories exist
   - Check logs for specific errors

3. **High Memory Usage**
   - Reduce batch sizes
   - Enable garbage collection
   - Check `max_pipeline_memory_mb` setting

4. **Performance Issues**
   - Adjust `max_concurrent_adapters`
   - Tune batch processing parameters
   - Monitor system resources

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Checks

Monitor pipeline health:

```python
status = await orchestrator.get_status()
print(f"Pipeline healthy: {status['pipeline']['running']}")
print(f"Failed adapters: {len(status['failed_adapters'])}")
```
