# Claude Monitoring Service

Comprehensive monitoring backend service for Claude processes with FastAPI and WebSocket support.

## Features

- **Real-time System Monitoring**: CPU, memory, disk usage with psutil
- **Token Usage Tracking**: Query SQLite database for token consumption statistics
- **Docker Container Monitoring**: Track containers with Claude processes
- **WebSocket Support**: Real-time updates for dashboards
- **REST API**: Complete set of endpoints for monitoring data

## API Endpoints

- `GET /api/dashboard` - Complete dashboard data
- `GET /api/tokens` - Token usage statistics
- `GET /api/docker` - Docker container status
- `GET /api/system` - System resource metrics
- `GET /health` - Health check
- `WS /ws` - WebSocket for real-time updates
- `GET /docs` - Interactive API documentation

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the service:
```bash
python monitoring_service.py
```

3. Or use the startup script:
```bash
bash start_service.sh
```

The service will be available at:
- HTTP API: http://localhost:8000
- WebSocket: ws://localhost:8000/ws
- API Docs: http://localhost:8000/docs

## Database Requirements

The service expects a SQLite database at `/home/opsvi/master_root/chat_logs.db` with tables:
- `nodes` - Contains `raw_json` field with token usage data
- `sessions` - Session information
- `tool_calls` - Tool usage tracking

## Configuration

- **Host/Port**: Modify the `uvicorn.run()` call in `monitoring_service.py`
- **Database Path**: Update `DB_PATH` constant
- **Update Intervals**: Adjust sleep intervals in WebSocket and broadcast functions

## Error Handling

- Comprehensive logging with timestamps
- Graceful degradation when database unavailable
- WebSocket connection management with cleanup
- Docker API error handling
