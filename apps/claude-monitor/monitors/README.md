# Docker Claude Monitor

A comprehensive Docker monitoring system designed to track Claude processes and activity across containers.

## Features

- **Container Discovery**: Automatically finds containers with Claude activity by checking:
  - Environment variables for CLAUDE/ANTHROPIC tokens
  - Running processes containing 'claude'
  - Container labels
  - Recent logs for Claude mentions

- **Resource Monitoring**: Tracks per-container:
  - CPU usage percentage
  - Memory usage and limits
  - Network I/O (RX/TX bytes)
  - Block I/O (read/write bytes)

- **Process Tracking**: Identifies and monitors running Claude processes within containers

- **Log Streaming**: Real-time log streaming with Claude mention detection

- **Token Estimation**: Estimates token consumption based on log analysis

- **Metrics Aggregation**: Provides aggregated metrics across all Claude containers

- **Error Handling**: Comprehensive error handling for Docker daemon connection issues

## Requirements

- Python 3.6+
- docker-py library (`pip install docker`)
- Access to Docker daemon (usually requires user to be in `docker` group)

## Usage

### Basic Usage

```python
from docker_monitor import DockerClaudeMonitor

# Initialize monitor
monitor = DockerClaudeMonitor()

# Discover containers with Claude activity
containers = monitor.discover_claude_containers()
print(f"Found {len(containers)} Claude containers")

# Get aggregated metrics
metrics = monitor.aggregate_metrics()
print(f"Total containers: {metrics['total_containers']}")
print(f"Running containers: {metrics['running_containers']}")
print(f"Total estimated tokens: {metrics['total_estimated_tokens']}")
```

### Continuous Monitoring

```python
# Start continuous monitoring (every 30 seconds)
monitor.start_monitoring(interval=30)

# ... do other work ...

# Stop monitoring
monitor.stop_monitoring()
```

### Log Streaming

```python
def log_callback(log_entry):
    if log_entry['claude_mention']:
        print(f"Claude mention in {log_entry['container_id']}: {log_entry['message']}")

# Stream logs from a specific container
monitor.stream_container_logs(container_id, callback=log_callback)
```

## API Reference

### DockerClaudeMonitor Class

#### Methods

- `discover_claude_containers()` - Discover all containers with Claude activity
- `get_container_resources(container_id)` - Get resource usage for specific container
- `stream_container_logs(container_id, callback=None)` - Stream container logs
- `get_claude_processes(container_id)` - Get running Claude processes
- `calculate_token_consumption(container_id)` - Estimate token usage
- `aggregate_metrics()` - Get aggregated metrics across all containers
- `start_monitoring(interval=30)` - Start continuous monitoring
- `stop_monitoring()` - Stop monitoring
- `get_status()` - Get current monitor status

## Container Detection Criteria

A container is considered to have Claude activity if ANY of the following are true:

1. **Environment Variables**: Contains environment variables with 'claude' or 'anthropic' in the name
2. **Running Processes**: Has processes with 'claude' in the command line
3. **Container Labels**: Has labels containing 'claude'
4. **Log Mentions**: Recent logs (last 5 minutes) contain 'claude' or 'anthropic'

## Error Handling

The monitor includes comprehensive error handling for:

- Docker daemon connection failures
- Container access permission issues
- Network timeouts
- Container state changes during monitoring
- Log streaming interruptions

## Example Output

```json
{
  "total_containers": 3,
  "running_containers": 2,
  "total_cpu_percent": 15.6,
  "total_memory_bytes": 1073741824,
  "total_network_rx_bytes": 2048576,
  "total_network_tx_bytes": 1024768,
  "total_estimated_tokens": 1500,
  "containers": {
    "abc123": {
      "name": "claude-app",
      "status": "running",
      "resources": {
        "cpu_percent": 8.2,
        "memory_usage_bytes": 536870912,
        "memory_percent": 25.0
      },
      "claude_processes": [
        {
          "pid": "1234",
          "command": "python claude_client.py",
          "cpu": "5.0",
          "memory": "12.3"
        }
      ],
      "token_consumption": {
        "estimated_tokens": 750,
        "claude_mentions": 15
      }
    }
  }
}
```

## Testing

Run the test script to verify functionality:

```bash
python test_docker_monitor.py
```

## Notes

- Token consumption estimation is approximate and based on log analysis
- Requires appropriate Docker permissions
- Performance impact is minimal due to efficient Docker API usage
- Log streaming runs in background threads for non-blocking operation
