# Claude Monitor

A comprehensive monitoring system for Claude processes and system resources with real-time dashboards, multi-source data collection, and WebSocket support.

## 🌟 Features

### 📊 **Comprehensive Monitoring**
- **Real-time System Metrics**: CPU, memory, disk, and network monitoring via `psutil`
- **Token Usage Tracking**: Track Claude token consumption from SQLite database
- **Docker Container Monitoring**: Discover and monitor Claude-related containers
- **Process Monitoring**: Detect and track Claude processes across the system
- **Cost Analytics**: Calculate usage costs with current model pricing

### 🎛️ **Multiple Interfaces**
- **Terminal UI**: Rich-based interactive console with multiple view modes
- **REST API**: Complete FastAPI backend with comprehensive endpoints
- **WebSocket Support**: Real-time updates and streaming data
- **Web Dashboard**: Future web UI implementation (backend ready)

### 📈 **Advanced Analytics**
- Token usage by model type with cost breakdown
- Session-based metrics and trends
- Error pattern detection and analysis
- Resource consumption tracking
- Container discovery and lifecycle monitoring

## 🚀 Quick Start

### Installation

1. **Clone and navigate to the project:**
```bash
cd /home/opsvi/master_root/apps/claude-monitor
```

2. **Install dependencies:**
```bash
pip install -r backend/requirements.txt
```

Required dependencies:
- `fastapi==0.104.1` - Web framework
- `uvicorn[standard]==0.24.0` - ASGI server
- `websockets==12.0` - WebSocket support
- `psutil==5.9.6` - System monitoring
- `docker==6.1.3` - Container monitoring
- `pydantic==2.4.2` - Data validation

### Basic Usage

1. **Run with console UI (default):**
```bash
python main.py
# or
python main.py --console
```

2. **Run backend service only:**
```bash
python main.py --backend
```

3. **Run with custom host/port:**
```bash
python main.py --host 0.0.0.0 --port 8080
```

4. **Enable debug mode:**
```bash
python main.py --debug --log-level DEBUG
```

### Quick Commands
```bash
# Launch with console UI
python main.py

# Backend only on custom port
python main.py --backend --port 9000

# Debug mode with verbose logging
python main.py --debug --log-level DEBUG --access-log
```

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   Terminal UI       │    │   Web Dashboard      │    │   Direct API        │
│   (Rich-based)      │    │   (Future)           │    │   Clients           │
└──────────┬──────────┘    └───────────┬──────────┘    └──────────┬──────────┘
           │                           │                          │
           └───────────────────────────┼──────────────────────────┘
                                       │
                              ┌────────▼────────┐
                              │  FastAPI Backend │
                              │  (HTTP + WS)     │
                              └────────┬────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
┌───────▼───────┐            ┌─────────▼────────┐            ┌───────▼───────┐
│ Data Collector │            │ Monitoring       │            │ WebSocket     │
│ (Multi-source) │            │ Service Core     │            │ Manager       │
└───────┬───────┘            └─────────┬────────┘            └───────────────┘
        │                              │
        └──────────────┬───────────────┘
                       │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
┌───▼────┐  ┌────▼────┐  ┌──────▼──────┐
│ SQLite │  │ System  │  │   Docker    │
│   DB   │  │ psutil  │  │    API      │
└────────┘  └─────────┘  └─────────────┘
```

### Data Flow

1. **Collection Layer**: Multiple collectors gather data from:
   - SQLite database (token usage, sessions)
   - System resources (psutil)
   - Docker containers (Docker API)
   - Process monitoring
   - Log file analysis

2. **Processing Layer**: Data aggregation and analysis:
   - Token cost calculations
   - Resource utilization metrics
   - Error pattern detection
   - Performance analytics

3. **API Layer**: FastAPI backend provides:
   - REST endpoints for data access
   - WebSocket for real-time updates
   - Health checks and status endpoints

4. **Presentation Layer**: Multiple interface options:
   - Rich-based terminal UI with multiple view modes
   - Future web dashboard
   - Direct API access for custom clients

## 📡 API Documentation

### REST API Endpoints

#### Core Endpoints
- `GET /api/dashboard` - Complete dashboard data with all metrics
- `GET /health` - Service health check
- `GET /docs` - Interactive Swagger documentation
- `GET /redoc` - ReDoc API documentation

#### Specific Metrics
- `GET /api/tokens` - Token usage statistics and cost breakdown
- `GET /api/docker` - Docker container metrics and discovery
- `GET /api/system` - System resource utilization
- `GET /api/processes` - Claude process monitoring
- `GET /api/costs` - Cost analytics and projections

#### WebSocket
- `WS /ws` - Real-time monitoring data stream

### API Examples

#### Get Dashboard Data
```bash
curl http://localhost:8000/api/dashboard
```

Response:
```json
{
  "summary": {
    "total_cost": 1.2345,
    "total_tokens": 50000,
    "active_sessions": 3,
    "error_rate": 0.5,
    "system_cpu_percent": 45.2,
    "claude_processes": 2
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
    "disk_usage": 78.5
  }
}
```

#### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Real-time update:', data);
};
```

#### Token Usage Query
```bash
curl "http://localhost:8000/api/tokens?hours_back=24"
```

#### System Metrics
```bash
curl http://localhost:8000/api/system
```

### Error Responses

All endpoints return structured error responses:
```json
{
  "detail": "Database connection failed",
  "error_code": "DB_CONNECTION_ERROR",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

## ⚙️ Configuration Guide

### Command Line Arguments

#### Mode Selection
- `--console` - Run with terminal UI (default)
- `--web` - Run with web UI (future implementation)
- `--backend` - Run backend service only

#### Server Configuration
- `--host HOST` - Bind address (default: localhost)
- `--port PORT` - Service port (default: 8000)

#### Logging Configuration
- `--log-level LEVEL` - Set log level (DEBUG, INFO, WARNING, ERROR)
- `--access-log` - Enable HTTP access logging
- `--debug` - Enable debug mode

#### Development Options
- `--reload` - Enable auto-reload (development only)

### Environment Setup

#### Database Configuration
The service expects a SQLite database at `/home/opsvi/master_root/chat_logs.db` with these tables:
- `nodes` - Contains `raw_json` field with token usage data
- `sessions` - Session information
- `tool_calls` - Tool usage tracking

#### Docker Requirements
- Docker daemon must be running
- User must have Docker permissions (usually `docker` group membership)

#### System Requirements
- Python 3.8+
- Linux/macOS/Windows WSL2
- Minimum 100MB free memory
- Network access for WebSocket connections

### Advanced Configuration

#### Custom Database Path
```python
# In monitoring_service.py
DB_PATH = "/custom/path/to/database.db"
```

#### Update Intervals
```python
# WebSocket broadcast interval
BROADCAST_INTERVAL = 5  # seconds

# Cache TTL settings
CACHE_TTL = {
    'system': 5,      # System metrics
    'database': 60,   # Database queries
    'docker': 15,     # Docker metrics
    'logs': 300       # Log analysis
}
```

#### Log Directories
```python
# Custom log directories for analysis
LOG_DIRECTORIES = [
    "/var/log",
    "/home/user/logs",
    "/custom/log/path"
]
```

### Docker Configuration

#### Running in Container
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -r backend/requirements.txt

EXPOSE 8000
CMD ["python", "main.py", "--backend", "--host", "0.0.0.0"]
```

#### Docker Compose
```yaml
version: '3.8'
services:
  claude-monitor:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock"
      - "/home/opsvi/master_root/chat_logs.db:/app/chat_logs.db"
    environment:
      - LOG_LEVEL=INFO
```

## 🎮 Terminal UI Usage

### View Modes

#### Master View (Default)
- System overview with key metrics
- Recent activity summary
- Navigation shortcuts

#### Docker View (`d`)
- Container discovery and monitoring
- Resource usage per container
- Claude process detection

#### Agents View (`a`)
- Active Claude processes
- Process resource consumption
- Command line visibility

#### Tokens View (`t`)
- Token usage statistics
- Cost breakdown by model
- Usage trends and projections

#### System View (`s`)
- Detailed system resources
- CPU, memory, disk, network
- Load averages and performance

#### Costs View (`c`)
- Cost analytics dashboard
- Model pricing breakdown
- Usage projections

### Keyboard Shortcuts

| Key | Action |
|-----|---------|
| `q` | Quit application |
| `r` | Refresh/reload data |
| `m` | Master view |
| `d` | Docker view |
| `a` | Agents view |
| `t` | Tokens view |
| `s` | System view |
| `c` | Costs view |
| `h` | Help screen |
| `?` | Show keyboard shortcuts |

### View Features
- **Auto-refresh**: Updates every 5 seconds
- **Error handling**: Graceful degradation when services unavailable
- **Responsive design**: Adapts to terminal size
- **Color coding**: Status indicators and importance levels
- **Progress bars**: Visual representation of resource usage

## 🧪 Testing & Development

### Run Tests
```bash
# Test data collector
python test_collector.py

# Test Docker monitor
python monitors/test_docker_monitor.py

# Test terminal UI
python test_terminal_ui.py
```

### Example Scripts
```bash
# Run data collection demo
python example_data_collection.py

# Test monitoring service
python backend/monitoring_service.py
```

### Development Mode
```bash
# Run with auto-reload and debug logging
python main.py --debug --log-level DEBUG --reload
```

### Build Script
```bash
# Automated build with agents
python build_with_agents.py
```

## 📊 Model Pricing

Current pricing per 1K tokens:

| Model | Input | Output |
|-------|--------|---------|
| Claude 3 Opus | $0.015 | $0.075 |
| Claude 3 Sonnet | $0.003 | $0.015 |
| Claude 3 Haiku | $0.00025 | $0.00125 |
| GPT-4 | $0.030 | $0.060 |
| GPT-4 Turbo | $0.010 | $0.030 |
| GPT-3.5 Turbo | $0.001 | $0.002 |

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Error
```
FileNotFoundError: Database not found: /home/opsvi/master_root/chat_logs.db
```
**Solution**: Verify database path exists or create the database

#### Docker Connection Failed
```
Docker connection error: Cannot connect to Docker daemon
```
**Solution**:
- Ensure Docker is running: `systemctl start docker`
- Add user to docker group: `sudo usermod -aG docker $USER`
- Restart terminal session

#### Permission Denied
```
PermissionError: [Errno 13] Permission denied: '/var/log/system.log'
```
**Solution**: Run with appropriate permissions or adjust log directories

#### Port Already in Use
```
OSError: [Errno 98] Address already in use
```
**Solution**: Use a different port: `python main.py --port 8080`

### Debug Mode

Enable comprehensive logging:
```bash
python main.py --debug --log-level DEBUG --access-log
```

### Performance Issues

#### High Memory Usage
- Reduce cache size in `collectors/data_collector.py`
- Increase cache TTL to reduce data collection frequency

#### Slow Response Times
- Check database performance
- Verify Docker daemon responsiveness
- Monitor system resource availability

## 🔌 Integration Examples

### Custom API Client
```python
import requests
import asyncio
import websockets

class ClaudeMonitorClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def get_dashboard(self):
        response = requests.get(f"{self.base_url}/api/dashboard")
        return response.json()

    async def stream_updates(self):
        uri = f"ws://localhost:8000/ws"
        async with websockets.connect(uri) as websocket:
            async for message in websocket:
                data = json.loads(message)
                yield data

# Usage
client = ClaudeMonitorClient()
dashboard = client.get_dashboard()
print(f"Total cost: ${dashboard['summary']['total_cost']}")
```

### Prometheus Integration
```python
from prometheus_client import start_http_server, Gauge

# Create metrics
cpu_gauge = Gauge('claude_cpu_percent', 'CPU usage percentage')
memory_gauge = Gauge('claude_memory_percent', 'Memory usage percentage')
token_gauge = Gauge('claude_tokens_total', 'Total tokens consumed')

# Update from Claude Monitor API
def update_metrics():
    response = requests.get('http://localhost:8000/api/dashboard')
    data = response.json()

    cpu_gauge.set(data['system_resources']['cpu_percent'])
    memory_gauge.set(data['system_resources']['memory_percent'])
    token_gauge.set(data['summary']['total_tokens'])

# Start Prometheus metrics server
start_http_server(9090)
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Claude Monitor",
    "panels": [
      {
        "title": "Token Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "claude_tokens_total",
            "legendFormat": "Total Tokens"
          }
        ]
      }
    ]
  }
}
```

## 📝 Development Guidelines

### Adding New Collectors
```python
class CustomCollector:
    def __init__(self):
        self.cache = LRUCache()

    def get_custom_metrics(self):
        """Implement custom metrics collection"""
        pass
```

### Error Handling Pattern
```python
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Specific error occurred: {e}")
    return default_value
except Exception as e:
    logger.warning(f"Unexpected error: {e}")
    return default_value
```

### Caching Best Practices
- Use appropriate TTL for different data types
- Implement cache invalidation for critical updates
- Monitor cache hit rates and memory usage

## 📄 License

This project is part of the Claude Monitor system. See the main project license for terms and conditions.

## 🤝 Contributing

1. Follow existing code patterns and conventions
2. Include comprehensive error handling
3. Add tests for new functionality
4. Update documentation for changes
5. Consider performance implications

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the API documentation at `/docs`
3. Enable debug logging for detailed error information
4. Check system requirements and dependencies

---

**Claude Monitor** - Comprehensive monitoring for Claude processes and system resources
