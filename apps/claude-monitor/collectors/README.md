# Claude Monitor Data Collector

A comprehensive data collection service that aggregates metrics from multiple sources to provide complete visibility into Claude usage, system performance, and operational health.

## Features

### 🎯 Multi-Source Data Collection
- **SQLite Database**: Token usage, session data, tool calls
- **System Resources**: CPU, memory, disk, network via psutil
- **Docker Containers**: Claude-related container monitoring
- **Process Monitoring**: Claude process detection and resource usage
- **Log File Analysis**: Error patterns, performance issues

### 💰 Cost & Usage Analytics
- Token usage by model type
- Cost calculations using current pricing
- Session-based metrics
- Resource consumption tracking

### ⚡ Performance Optimized
- Thread-safe LRU caching system
- Concurrent data collection
- Configurable cache TTL
- Async/await support

### 📊 Comprehensive Metrics

#### Token Metrics
- Total input/output tokens
- Cost breakdown by model
- Average tokens per session
- Usage trends over time

#### System Metrics
- CPU usage percentage
- Memory utilization
- Disk space usage
- Network I/O statistics
- Load averages

#### Process Metrics
- Claude process detection
- CPU usage per process
- Memory consumption
- Process lifecycle tracking

#### Docker Metrics
- Container resource usage
- Claude-related container identification
- Network and storage metrics
- Container health monitoring

#### Log Analytics
- Error rate calculation
- Common error patterns
- Performance issue detection
- Log file processing stats

## Installation

```bash
cd /home/opsvi/master_root/apps/claude-monitor
pip install -r backend/requirements.txt
```

Required dependencies:
- `psutil >= 5.9.6` - System monitoring
- `docker >= 6.1.3` - Container monitoring
- `asyncio` - Concurrent processing
- `sqlite3` - Database access

## Usage

### Basic Usage

```python
import asyncio
from collectors.data_collector import DataCollector

async def main():
    collector = DataCollector()

    # Collect all metrics
    data = await collector.collect_all_metrics(hours_back=24)

    # Access specific metrics
    print(f"Total cost: ${data['summary']['total_cost']}")
    print(f"Total tokens: {data['summary']['total_tokens']:,}")
    print(f"Error rate: {data['summary']['error_rate']:.2f}%")

asyncio.run(main())
```

### Individual Collectors

```python
from collectors.data_collector import DataCollector

collector = DataCollector()

# System metrics
system_metrics = collector.system_collector.get_system_metrics()
print(f"CPU: {system_metrics.cpu_percent}%")

# Token usage
token_metrics = collector.db_collector.get_token_metrics(hours_back=24)
print(f"Tokens: {token_metrics.total_tokens:,}")

# Process monitoring
process_metrics = collector.process_collector.get_claude_processes()
print(f"Claude processes: {process_metrics.total_processes}")
```

### Cache Management

```python
# Clear all caches
collector.clear_cache()

# Get cache statistics
cache_stats = collector.get_cache_stats()
print(f"Total cached items: {sum(cache_stats.values())}")
```

## Configuration

### Database Path
```python
collector = DataCollector(db_path="/custom/path/to/database.db")
```

### Log Directories
```python
log_dirs = ["/var/log", "/custom/log/path"]
collector = DataCollector(log_directories=log_dirs)
```

### Cache Settings
```python
from collectors.data_collector import LRUCache

# Custom cache with different size and TTL
cache = LRUCache(max_size=500)
value = cache.get(key, ttl=300)  # 5-minute TTL
```

## Data Structure

### Aggregated Response
```json
{
  "summary": {
    "total_cost": 1.2345,
    "total_tokens": 50000,
    "active_sessions": 3,
    "error_rate": 0.5,
    "system_cpu_percent": 45.2,
    "system_memory_percent": 67.8,
    "claude_processes": 2,
    "claude_containers": 1
  },
  "token_usage": {
    "total_input_tokens": 30000,
    "total_output_tokens": 20000,
    "cost_by_model": {
      "claude-3-sonnet": 0.8945,
      "gpt-4": 0.3400
    }
  },
  "system_resources": {
    "cpu_percent": 45.2,
    "memory_percent": 67.8,
    "load_average": [1.2, 1.5, 1.8]
  }
}
```

## Examples

### Run Demo Script
```bash
python3 example_data_collection.py
```

### Run Tests
```bash
python3 test_collector.py
```

### Continuous Monitoring
```python
import asyncio

async def monitor_continuously():
    collector = DataCollector()

    while True:
        data = await collector.collect_all_metrics(hours_back=1)

        # Process data
        print(f"Current cost: ${data['summary']['total_cost']}")

        # Wait 60 seconds
        await asyncio.sleep(60)
```

## Model Pricing

The collector includes pricing for major models:

| Model | Input (per 1K tokens) | Output (per 1K tokens) |
|-------|----------------------|------------------------|
| Claude 3 Opus | $0.015 | $0.075 |
| Claude 3 Sonnet | $0.003 | $0.015 |
| Claude 3 Haiku | $0.00025 | $0.00125 |
| GPT-4 | $0.030 | $0.060 |
| GPT-4 Turbo | $0.010 | $0.030 |
| GPT-3.5 Turbo | $0.001 | $0.002 |

## Performance Considerations

### Caching Strategy
- System metrics: 5-second TTL
- Database queries: 60-second TTL
- Log analysis: 300-second TTL
- Docker metrics: 15-second TTL

### Concurrent Collection
The collector uses `ThreadPoolExecutor` with 4 workers to collect metrics concurrently, significantly reducing collection time.

### Memory Usage
- LRU cache with configurable max size (default: 1000 items)
- Automatic cleanup of stale cache entries
- Efficient data structures to minimize memory footprint

## Error Handling

The collector includes comprehensive error handling:

- Database connection failures return default metrics
- Docker connection issues are gracefully handled
- Permission errors for log files are logged but don't stop collection
- Individual collector failures don't affect other collectors

## Extending the Collector

### Adding New Collectors

```python
class CustomCollector:
    def __init__(self):
        self.cache = LRUCache()

    def get_custom_metrics(self):
        # Implementation here
        pass

# Add to DataCollector
class DataCollector:
    def __init__(self):
        # ... existing collectors ...
        self.custom_collector = CustomCollector()
```

### Custom Log Patterns

```python
CUSTOM_LOG_PATTERNS = {
    'custom_error': r'(my_custom_error_pattern)',
    'performance': r'(slow_operation|timeout)'
}
```

## Troubleshooting

### Common Issues

1. **Database not found**
   ```
   FileNotFoundError: Database not found: /path/to/database.db
   ```
   Solution: Verify database path or create database

2. **Docker connection failed**
   ```
   Docker connection error: Cannot connect to Docker daemon
   ```
   Solution: Ensure Docker is running and user has permissions

3. **Permission denied on log files**
   ```
   PermissionError: /var/log/system.log
   ```
   Solution: Run with appropriate permissions or adjust log directories

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Integration

### With FastAPI Backend
```python
from fastapi import FastAPI
from collectors.data_collector import collect_comprehensive_data

app = FastAPI()

@app.get("/api/metrics")
async def get_metrics():
    return await collect_comprehensive_data(hours_back=24)
```

### With Monitoring Dashboard
The collector is designed to integrate seamlessly with the existing monitoring service and dashboard components.

## Contributing

When adding new features:

1. Follow the existing patterns for collectors
2. Include comprehensive error handling
3. Add caching for expensive operations
4. Update tests and documentation
5. Consider performance implications

## License

This is part of the Claude Monitor project.
