# Real-time Chat Log Ingestion System

A production-ready, high-performance real-time chat log ingestion system for Claude chat logs. This system provides immediate ingestion, correlation, and analytics of chat logs with comprehensive fault tolerance and monitoring.

## 🚀 Features

### Core Functionality
- **Real-time File Watching**: Monitors multiple directories for new/modified JSONL files
- **High-performance Ingestion**: Buffered batch processing with configurable thresholds
- **Intelligent Correlation**: Integrates with existing correlator for immediate code analysis
- **Dual Database Support**: Writes to both PostgreSQL and SQLite simultaneously
- **Production Ready**: Comprehensive logging, monitoring, and service management

### Fault Tolerance
- **Circuit Breaker Pattern**: Prevents cascade failures with automatic recovery
- **Exponential Backoff Retry**: Configurable retry logic with jitter
- **Persistent Failure Storage**: Failed operations stored for later retry
- **Health Monitoring**: Continuous health checks with alerting

### Monitoring & Observability
- **Real-time Metrics**: System and application metrics collection
- **Health Dashboard**: Comprehensive health status and trends
- **Alert Management**: Configurable alerts with multiple severity levels
- **Prometheus Integration**: Optional metrics export for external monitoring

### Performance & Scalability
- **Async Architecture**: High-performance async processing with uvloop
- **Configurable Buffering**: Optimized batch sizes and timeouts
- **Resource Management**: Memory and CPU limits with monitoring
- **Horizontal Scaling**: Design supports multiple service instances

## 📋 Requirements

### System Requirements
- Python 3.8+
- PostgreSQL 12+ (for unified_context database)
- Linux/Unix environment (recommended)
- Minimum 512MB RAM
- 1GB available disk space

### Python Dependencies
```bash
pip install asyncio asyncpg psycopg2-binary watchdog psutil pyyaml uvloop aiofiles
```

### Optional Dependencies
```bash
pip install prometheus_client  # For Prometheus metrics export
```

## 🛠 Installation

### Quick Start
```bash
# Clone or navigate to the project
cd /home/opsvi/master_root

# Run the deployment script
./libs/opsvi-monitoring/opsvi_monitoring/chat_analytics/realtime_ingestion/deploy.sh

# Edit configuration as needed
vim ~/.config/realtime-chat-ingestion/config.yml

# Start the service
~/.config/realtime-chat-ingestion/start_service.sh
```

### Manual Installation
```bash
# Create directories
mkdir -p ~/.config/realtime-chat-ingestion
mkdir -p ~/.local/var/log/realtime-chat-ingestion
mkdir -p ~/.local/var/run/realtime-chat-ingestion

# Copy configuration
cp config/default_config.yml ~/.config/realtime-chat-ingestion/config.yml

# Install Python dependencies
pip install -r requirements.txt

# Set Python path
export PYTHONPATH="/home/opsvi/master_root:$PYTHONPATH"

# Start service
python -m opsvi_monitoring.chat_analytics.realtime_ingestion.service_runner start
```

### System-wide Installation (requires root)
```bash
sudo ./deploy.sh --service-user opsvi
sudo systemctl enable realtime-chat-ingestion
sudo systemctl start realtime-chat-ingestion
```

## ⚙️ Configuration

### Configuration File Structure
```yaml
service:
  name: "realtime-chat-ingestion"
  log_level: "INFO"
  enable_monitoring: true
  enable_fault_tolerance: true

watcher:
  enabled: true
  batch_size: 10
  queue_size: 1000
  file_extensions: [".jsonl"]

database:
  postgres_url: "postgresql://user:pass@localhost:5432/unified_context"
  sqlite_path: "/path/to/chat_logs.db"

fault_tolerance:
  retry_max_attempts: 3
  circuit_breaker_failure_threshold: 5

monitoring:
  dashboard_enabled: true
  alert_enabled: true
```

### Environment Variables
```bash
# Override key settings
export CHAT_INGESTION_LOG_LEVEL=DEBUG
export CHAT_WATCHER_ENABLED=true
export CHAT_WATCHER_QUEUE_SIZE=2000
export POSTGRES_URL="postgresql://..."
```

### Watch Directory Configuration
The service automatically discovers chat log sources:

1. **Claude Projects**: `~/.claude/projects/`
2. **Additional Directories**: Configurable in `discovery.additional_watch_dirs`
3. **Exclusion Patterns**: Skip directories like `.git`, `__pycache__`

## 🚦 Usage

### Service Management
```bash
# Start service
python -m opsvi_monitoring.chat_analytics.realtime_ingestion.service_runner start

# Start with custom config
python -m opsvi_monitoring.chat_analytics.realtime_ingestion.service_runner start --config /path/to/config.yml

# Start as daemon
python -m opsvi_monitoring.chat_analytics.realtime_ingestion.service_runner start --daemon

# Stop service
python -m opsvi_monitoring.chat_analytics.realtime_ingestion.service_runner stop

# Restart service
python -m opsvi_monitoring.chat_analytics.realtime_ingestion.service_runner restart

# Check status
python -m opsvi_monitoring.chat_analytics.realtime_ingestion.service_runner status

# View configuration
python -m opsvi_monitoring.chat_analytics.realtime_ingestion.service_runner config
```

### Programmatic Usage
```python
from opsvi_monitoring.chat_analytics.realtime_ingestion import RealTimeChatLogService

# Create and start service
service = RealTimeChatLogService()
await service.start()

# Process specific file immediately
await service.process_file_immediately("/path/to/chat.jsonl")

# Get health status
status = service.get_health_status()
print(f"Service health: {status['is_healthy']}")

# Graceful shutdown
await service.shutdown()
```

### Monitoring Commands
```bash
# Monitor service health
~/.config/realtime-chat-ingestion/monitor_service.sh health

# View recent logs
~/.config/realtime-chat-ingestion/monitor_service.sh logs

# Get current metrics
~/.config/realtime-chat-ingestion/monitor_service.sh metrics

# Check service status
~/.config/realtime-chat-ingestion/monitor_service.sh status
```

## 📊 Monitoring & Metrics

### Health Checks
The service provides comprehensive health monitoring:

- **System Resources**: CPU, memory, disk usage
- **Queue Status**: Processing queue size and capacity
- **Processing Activity**: Files and entries processed per minute
- **Circuit Breaker States**: Status of fault tolerance mechanisms
- **Database Connectivity**: PostgreSQL and SQLite connection health

### Key Metrics
- `files_processed_per_minute`: Rate of file processing
- `entries_processed_per_minute`: Rate of chat entry processing
- `queue_size`: Current ingestion queue size
- `buffer_size`: Current buffer size
- `circuit_breaker_status`: Status of circuit breakers
- `cpu_percent`: System CPU usage
- `memory_percent`: System memory usage

### Alerts
Configurable alerts for:
- Queue nearly full (> 90% capacity)
- High CPU usage (> 85%)
- High memory usage (> 85%)
- No processing activity (> 10 minutes)
- Circuit breaker open state

### Dashboard Data Export
```python
# Export dashboard data
dashboard = MonitoringDashboard(service)
dashboard.export_dashboard_data("/tmp/dashboard_data.json")

# Get Prometheus metrics
metrics = create_prometheus_metrics(dashboard)
print(metrics)
```

## 🔧 Architecture

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  File Watcher   │───▶│ Ingestion Queue  │───▶│ Processing      │
│                 │    │                  │    │ Pipeline        │
│ • Monitors dirs │    │ • Async queue    │    │ • Parse JSONL   │
│ • Detects new   │    │ • Configurable   │    │ • Correlate     │
│   and modified  │    │   capacity       │    │ • Store context │
│   JSONL files   │    │ • Backpressure   │    │ • Fault tolerant│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Health Monitor  │    │ Metrics          │    │ Fault Tolerance │
│                 │    │ Collector        │    │                 │
│ • System health │    │ • Performance    │    │ • Circuit       │
│ • Service status│    │ • Resource usage │    │   breakers      │
│ • Alert manager │    │ • Dashboard data │    │ • Retry logic   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Data Flow

1. **File Detection**: Watchdog monitors directories for JSONL changes
2. **Queuing**: Files queued for processing with metadata
3. **Parsing**: JSONL files parsed incrementally (only new lines)
4. **Buffering**: Entries buffered for efficient batch processing
5. **Correlation**: Integration with existing correlator for code analysis
6. **Storage**: Dual-write to PostgreSQL and SQLite databases
7. **Monitoring**: Continuous metrics collection and health monitoring

### Fault Tolerance

- **Circuit Breakers**: Protect against external service failures
- **Retry Logic**: Exponential backoff with configurable limits
- **Failure Persistence**: Failed operations stored for later retry
- **Health Recovery**: Automatic recovery monitoring and alerting

## 🧪 Testing

### Run Test Suites
```bash
# All tests
python tests/test_realtime_ingestion.py

# Unit tests only
python tests/test_realtime_ingestion.py --suite unit

# Integration tests
python tests/test_realtime_ingestion.py --suite integration

# Performance tests
python tests/test_realtime_ingestion.py --suite performance
```

### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end system validation
- **Performance Tests**: Load and throughput testing
- **Fault Tolerance Tests**: Failure scenario validation

### Manual Testing
```bash
# Create test JSONL file
echo '{"content": "Test message", "id": "test1", "timestamp": "2024-01-01T00:00:00"}' > /tmp/test.jsonl

# Process specific file
python -m opsvi_monitoring.chat_analytics.realtime_ingestion.service_runner start --test-file /tmp/test.jsonl
```

## 🔍 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check configuration
python -m opsvi_monitoring.chat_analytics.realtime_ingestion.service_runner config

# Check dependencies
python -c "import asyncpg, psycopg2, watchdog; print('Dependencies OK')"

# Check database connectivity
psql -h localhost -U opsvi -d unified_context -c "SELECT 1;"
```

#### High Memory Usage
```bash
# Check buffer sizes in config
vim ~/.config/realtime-chat-ingestion/config.yml

# Reduce buffer_max_size and queue_size
# Monitor with system tools
top -p $(cat /var/run/realtime-chat-ingestion/service.pid)
```

#### No Files Being Processed
```bash
# Check watch directories exist
ls -la ~/.claude/projects/

# Verify file permissions
ls -la /path/to/chat/logs/

# Check service logs
tail -f ~/.local/var/log/realtime-chat-ingestion/service.log

# Test manual file processing
python -c "
from opsvi_monitoring.chat_analytics.realtime_ingestion.chat_log_watcher import ChatLogDiscovery
discovery = ChatLogDiscovery()
dirs = discovery.discover_watch_directories()
print('Watch directories:', dirs)
"
```

### Log Analysis
```bash
# Service logs
tail -f ~/.local/var/log/realtime-chat-ingestion/service.log

# System logs (systemd)
journalctl --user -u realtime-chat-ingestion -f

# Error patterns
grep -i error ~/.local/var/log/realtime-chat-ingestion/service.log | tail -20
```

### Performance Tuning
```yaml
# In config.yml - increase for high throughput
watcher:
  batch_size: 20
  queue_size: 2000
  max_files_per_minute: 200

ingestion:
  buffer_max_size: 200
  buffer_max_age_seconds: 15

performance:
  max_concurrent_files: 100
  worker_threads: 4
```

## 🔐 Security Considerations

### File Permissions
```bash
# Recommended permissions
chmod 750 ~/.config/realtime-chat-ingestion/
chmod 640 ~/.config/realtime-chat-ingestion/config.yml
chmod 700 ~/.local/var/log/realtime-chat-ingestion/
chmod 755 ~/.local/var/run/realtime-chat-ingestion/
```

### Database Security
- Use strong passwords for database connections
- Enable SSL/TLS for PostgreSQL connections
- Regularly rotate database credentials
- Monitor database access logs

### Network Security
- Restrict PostgreSQL access to necessary hosts
- Use VPN or private networks when possible
- Monitor network connections

## 🚀 Production Deployment

### System Service Setup
```bash
# Install as system service
sudo ./deploy.sh

# Enable automatic startup
sudo systemctl enable realtime-chat-ingestion

# Start service
sudo systemctl start realtime-chat-ingestion

# Monitor service
sudo systemctl status realtime-chat-ingestion
```

### Resource Requirements
- **Minimum**: 1 CPU core, 512MB RAM, 1GB disk
- **Recommended**: 2 CPU cores, 1GB RAM, 5GB disk
- **High Volume**: 4 CPU cores, 2GB RAM, 10GB disk

### Scaling Considerations
- **Horizontal**: Run multiple service instances with different watch directories
- **Vertical**: Increase buffer sizes and worker threads
- **Database**: Use connection pooling and read replicas

### Backup & Recovery
```bash
# Backup configuration
cp -r ~/.config/realtime-chat-ingestion/ /backup/location/

# Backup failure store
cp ~/.local/var/run/realtime-chat-ingestion/chat_ingestion_failures.db /backup/location/

# Backup logs
tar czf logs_backup.tar.gz ~/.local/var/log/realtime-chat-ingestion/
```

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone https://github.com/opsvi/master_root.git
cd master_root

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -e .[dev]

# Run tests
python -m pytest libs/opsvi-monitoring/opsvi_monitoring/chat_analytics/realtime_ingestion/tests/
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints for all functions
- Add comprehensive docstrings
- Include unit tests for new features

### Submitting Changes
1. Create feature branch
2. Add tests for new functionality
3. Ensure all tests pass
4. Update documentation
5. Submit pull request

## 📚 API Reference

### Main Classes

#### `RealTimeChatLogService`
Main service coordinator.

```python
class RealTimeChatLogService:
    def __init__(self, config: WatcherConfig = None)
    async def start(self) -> None
    async def shutdown(self) -> None
    async def process_file_immediately(self, file_path: str) -> None
    def get_health_status(self) -> Dict
```

#### `ChatLogWatcher`
File system monitoring.

```python
class ChatLogWatcher:
    def __init__(self, watch_directories: List[str], ingestion_queue: asyncio.Queue)
    def start(self) -> None
    def stop(self) -> None
```

#### `RealTimeIngestionPipeline`
Processing pipeline.

```python
class RealTimeIngestionPipeline:
    async def start(self) -> None
    async def stop(self) -> None
    async def process_file(self, file_info: Dict) -> None
    def get_stats(self) -> Dict
```

#### `MonitoringDashboard`
Monitoring and metrics.

```python
class MonitoringDashboard:
    def __init__(self, service: RealTimeChatLogService)
    async def start_monitoring(self) -> None
    def get_dashboard_data(self) -> Dict
    def export_dashboard_data(self, file_path: str) -> None
```

## 📄 License

This project is part of the OPSVI master_root system. See the main project license for details.

## 📞 Support

For support and questions:
- Check the troubleshooting guide above
- Review service logs for error messages
- Create an issue in the project repository
- Contact the OPSVI development team

---

*Built with ❤️ for real-time chat log analytics*
