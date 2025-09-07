# Multi-Agent Log Tailer - CLI Interface

## Overview

The Multi-Agent Log Tailer CLI provides a comprehensive command-line interface for monitoring Claude Code session logs with intelligent swarm detection and beautiful visual output.

## Quick Start

```bash
# Basic usage - monitor default directory
python cli_interface.py

# Monitor specific directory with pattern
python cli_interface.py --projects-dir /path/to/logs --pattern "**/*.jsonl"

# Include historical entries
python cli_interface.py --include-historical

# High-performance mode
python cli_interface.py --workers 100 --buffer-size 5000
```

## Command-Line Options

### Core Options

| Option | Description | Default |
|--------|-------------|---------|
| `--projects-dir PATH` | Projects directory to monitor | `~/.claude/projects` |
| `--pattern GLOB` | File pattern to match | `*.jsonl` |
| `--include-historical` | Include historical log entries | `false` |

### Swarm Detection

| Option | Description | Default |
|--------|-------------|---------|
| `--no-swarm-detection` | Disable swarm detection | `false` |
| `--swarm-time-window SECONDS` | Time window for detection | `300` |
| `--swarm-min-agents N` | Minimum agents for swarm | `3` |

### Visual Options

| Option | Description | Default |
|--------|-------------|---------|
| `--color-scheme SCHEME` | Color scheme (default/high-contrast/colorblind) | `default` |
| `--no-color` | Disable color output | `false` |
| `--ascii-only` | Use ASCII characters only | `false` |
| `--no-emoji` | Disable emoji in output | `false` |

### Performance Tuning

| Option | Description | Default |
|--------|-------------|---------|
| `--workers N` | Number of worker threads | `50` |
| `--buffer-size N` | Output buffer size | `1000` |
| `--poll-interval MS` | File polling interval (ms) | `100` |
| `--max-files N` | Maximum files to monitor | `1000` |
| `--max-memory MB` | Maximum memory usage | `500` |

### Monitoring

| Option | Description |
|--------|-------------|
| `--metrics-port PORT` | Prometheus metrics export port |
| `--health-port PORT` | Health check endpoint port |

### Output Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output-format FORMAT` | Output format (text/json/csv) | `text` |
| `--output-file FILE` | Write output to file | `stdout` |
| `--quiet` | Suppress non-essential output | `false` |

### Debugging

| Option | Description |
|--------|-------------|
| `--verbose`, `-v` | Verbose output (use multiple times) |
| `--debug` | Enable debug mode |
| `--log-file FILE` | Log file path |
| `--profile` | Enable performance profiling |

### Commands

| Command | Description |
|---------|-------------|
| `--version` | Show version and exit |
| `--help` | Show help and exit |
| `--health-check` | Run health check and exit |
| `--list-files` | List matching files and exit |
| `--test-config` | Test configuration and exit |
| `--export-config FILE` | Export configuration to file |

## Configuration

### Configuration File

Create a `config.yaml` file:

```yaml
system:
  projects_dir: ~/.claude/projects
  pattern: "**/*.jsonl"

monitoring:
  poll_interval_ms: 100
  buffer_size: 1000

swarm_detection:
  enabled: true
  time_window_seconds: 300
  min_agents: 3

visual:
  color_scheme: default
  use_emoji: true

performance:
  worker_threads: 50
  max_memory_mb: 500
```

Use with: `python cli_interface.py --config config.yaml`

### Environment Variables

```bash
export SWARM_TAILER_CONFIG=/path/to/config.yaml
export SWARM_TAILER_PROJECTS_DIR=~/.claude/projects
export SWARM_TAILER_LOG_LEVEL=INFO
export SWARM_TAILER_WORKERS=50
export SWARM_TAILER_NO_COLOR=0
```

## Signal Handling

The CLI responds to standard Unix signals for runtime control:

| Signal | Action |
|--------|--------|
| `SIGINT` (Ctrl+C) | Graceful shutdown |
| `SIGTERM` | Graceful shutdown |
| `SIGUSR1` | Toggle debug mode |
| `SIGUSR2` | Print statistics |
| `SIGHUP` | Reload configuration |

### Examples

```bash
# Send SIGUSR1 to toggle debug mode
kill -USR1 <pid>

# Send SIGUSR2 to print statistics
kill -USR2 <pid>

# Send SIGHUP to reload config
kill -HUP <pid>
```

## Usage Examples

### Basic Monitoring

```bash
# Monitor default directory
python cli_interface.py

# Monitor with specific pattern
python cli_interface.py --pattern "*agent*.jsonl"
```

### Performance Optimized

```bash
# High-performance monitoring
python cli_interface.py \
  --workers 100 \
  --buffer-size 5000 \
  --poll-interval 50
```

### Production Deployment

```bash
# Production configuration with metrics
python cli_interface.py \
  --config production.yaml \
  --metrics-port 9090 \
  --health-port 8080 \
  --log-file /var/log/swarm-tailer.log
```

### Debugging Issues

```bash
# Debug mode with verbose output
python cli_interface.py \
  --debug \
  --verbose \
  --log-file debug.log
```

### Accessibility Mode

```bash
# Colorblind-safe with ASCII only
python cli_interface.py \
  --color-scheme colorblind \
  --ascii-only
```

### Batch Processing

```bash
# Process historical logs to JSON
python cli_interface.py \
  --include-historical \
  --output-format json \
  --output-file results.json \
  --quiet
```

## Health Checks

Run health check:

```bash
python cli_interface.py --health-check
```

Output:
```
Health Check: HEALTHY
  ✓ config
  ✓ projects_dir
  ✓ permissions
```

## Testing Configuration

Test configuration without starting:

```bash
python cli_interface.py --test-config --config my-config.yaml
```

## List Files

List files that would be monitored:

```bash
python cli_interface.py --list-files --pattern "**/*.jsonl"
```

Output:
```
Found 42 matching file(s):
  project1/session.jsonl (1,234 bytes)
  project2/session.jsonl (5,678 bytes)
  ...
```

## Export Configuration

Export current configuration:

```bash
# Export to YAML
python cli_interface.py --export-config current-config.yaml

# Export to JSON
python cli_interface.py --export-config current-config.json
```

## Error Handling

The CLI provides comprehensive error handling:

- **Exit Code 0**: Success
- **Exit Code 1**: General error
- **Exit Code 130**: Interrupted (SIGINT)
- **Exit Code 2**: Configuration error
- **Exit Code 3**: Permission error

## Performance Tips

1. **Adjust Worker Count**: More workers handle more files efficiently
2. **Tune Poll Interval**: Lower intervals for real-time, higher for CPU savings
3. **Buffer Size**: Larger buffers reduce I/O but increase memory
4. **Disable Features**: Turn off swarm detection or colors for better performance

## Troubleshooting

### High CPU Usage
```bash
python cli_interface.py --workers 20 --poll-interval 200
```

### Memory Issues
```bash
python cli_interface.py --buffer-size 500 --max-memory 200
```

### No Output
```bash
python cli_interface.py --debug --verbose
```

## Integration

### Systemd Service

```ini
[Unit]
Description=Multi-Agent Log Tailer
After=network.target

[Service]
Type=simple
User=monitor
ExecStart=/usr/bin/python3 /opt/swarm-tailer/cli_interface.py --config /etc/swarm-tailer/config.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Docker

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "cli_interface.py"]
```

## License

MIT License - See LICENSE file for details