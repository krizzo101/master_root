# Comprehensive Monitoring Service Documentation

## Overview

The monitoring service provides comprehensive real-time monitoring and analytics for orchestrator processes that generate task output files. It automatically discovers and monitors all `*_output/tasks/*.json` files, providing detailed insights, performance metrics, and live updates via WebSocket.

## Key Features

### 🔍 **Automatic Discovery**
- **Auto-detects** all output directories ending in `_output`
- **Monitors** task JSON files in real-time with file change detection
- **Caches** data efficiently to minimize disk I/O

### 📊 **Comprehensive Analytics**
- **Task Status Tracking**: pending, running, completed, failed
- **Performance Metrics**: duration analysis, throughput, success rates
- **Resource Usage**: API costs, token consumption, utilization rates
- **Error Analysis**: pattern detection, failure categorization
- **Trend Analysis**: hourly completion rates, trending task types

### 🚀 **Real-Time Monitoring**
- **WebSocket Support**: Live updates pushed to dashboard
- **Smart Caching**: File-based change detection prevents unnecessary scans
- **Multi-Level Subscriptions**: Clients can subscribe to specific data types

### 🎯 **Quality Insights**
- **Success Rate Calculation**: Overall and by-category performance
- **Resource Efficiency**: Cost and token usage analysis
- **Activity Tracking**: Recent completions, trending types
- **Fastest/Slowest Task Identification**: Performance outlier detection

## Architecture

### Core Components

#### 1. **MonitoringService** (`monitoring_service.py`)
Main service class providing:
```python
# Key Methods
await get_system_status()          # Overall system health
await get_all_tasks()              # Task list with details
await get_task_analytics()         # Comprehensive analytics
await get_performance_metrics()    # Performance insights
await get_quality_report()         # Quality analysis
await get_live_monitoring_data()   # All data for dashboard
```

#### 2. **WebSocketManager** (`websocket_handler.py`)
Real-time communication handler:
```python
# Features
- Connection management
- Subscription-based updates
- Automatic broadcast loops
- Client command handling
- Error recovery
```

#### 3. **FastAPI Application** (`app.py`)
REST API and WebSocket endpoints:
```
GET  /api/status           - System overview
GET  /api/tasks            - All tasks
GET  /api/tasks/{id}       - Task details
GET  /api/analytics        - Comprehensive analytics
GET  /api/performance      - Performance metrics
GET  /api/live-data        - Complete monitoring data
GET  /api/directories      - Monitored directories
GET  /api/websocket-stats  - WebSocket statistics
WS   /ws                   - Real-time updates
```

## Data Sources

The service automatically monitors these patterns:
```
/home/opsvi/master_root/apps/project-context/
├── phase1_execution_output/tasks/*.json
├── phase1_completion_output/tasks/*.json
├── phase2_output/tasks/*.json
├── chat_import_output/tasks/*.json
├── production_output/tasks/*.json
└── [any_other_*_output]/tasks/*.json
```

## Task Data Structure

Each task JSON file contains:
```json
{
  "task_id": "unique_task_identifier",
  "task_type": "specialist_agent_type",
  "status": "pending|running|completed|failed",
  "start_time": 1234567890.123,
  "end_time": 1234567890.456,
  "result": {
    "duration_ms": 45000,
    "total_cost_usd": 0.15,
    "usage": {
      "input_tokens": 1000,
      "output_tokens": 500
    }
  },
  "error": "error_message_if_failed",
  "phase_id": "execution_phase",
  "session_id": "orchestrator_session"
}
```

## Analytics Capabilities

### 📈 **Performance Analytics**
- **Average Duration**: Task completion time analysis
- **Throughput**: Tasks completed per hour
- **Parallel Utilization**: Resource usage efficiency
- **Success Rate**: Completion vs failure ratios

### 💰 **Cost Analytics**
- **Total API Costs**: Cumulative spending across all tasks
- **Cost by Task Type**: Spending breakdown by specialist
- **Token Usage**: Input/output token consumption
- **Efficiency Metrics**: Cost per successful task

### ⚡ **Real-Time Metrics**
- **Recent Activity**: Last 1h, 6h, 24h completion counts
- **Live Status**: Currently running tasks
- **Hot Trends**: Most active task types
- **Quality Indicators**: Success rate trends

### 🔍 **Error Analysis**
- **Failure Patterns**: Common error categories
- **Error by Type**: Failure rates by task specialist
- **Error by Phase**: Which phases have issues
- **Recent Failures**: Latest error occurrences

## WebSocket Real-Time Updates

### Connection Protocol
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

// Subscribe to specific updates
ws.send(JSON.stringify({
    type: "subscribe",
    subscription: "tasks",
    action: "subscribe"
}));

// Receive real-time updates
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // data.type: "update"|"initial_data"|"pong"
    // data.data_type: "status"|"tasks"|"performance"
    // data.data: actual payload
};
```

### Update Frequency
- **System Status**: Every 2 seconds
- **Task Updates**: Every 5 seconds
- **Performance Metrics**: Every 10 seconds
- **Event-Driven**: Immediate for task completions/failures

## File System Monitoring

### Smart Caching Strategy
```python
# Efficient change detection
file_hash = f"{modification_time}_{file_size}"
if cached_hash != current_hash:
    # File changed, reload data
    reload_task_data()
```

### Directory Discovery
- **Automatic**: Scans base path for `*_output` directories
- **Dynamic**: Updates when new directories appear
- **Resilient**: Handles missing/inaccessible directories gracefully

## Usage Examples

### Basic Monitoring
```python
from monitoring_service import MonitoringService

service = MonitoringService()
await service.start_monitoring()

# Get current status
status = await service.get_system_status()
print(f"Progress: {status['overall_progress']}%")

# Get detailed analytics
analytics = await service.get_task_analytics()
print(f"Success rate: {analytics['quality']['success_rate']}%")
```

### WebSocket Integration
```python
from websocket_handler import WebSocketManager

manager = WebSocketManager()
await manager.start_broadcast_loop()

# Broadcast custom event
await manager.broadcast_system_event("phase_complete", {
    "phase": "phase1",
    "tasks_completed": 25
})
```

## API Response Examples

### System Status Response
```json
{
  "overall_progress": 75.5,
  "current_phase": "phase2_implementation",
  "elapsed_minutes": 120.5,
  "active_tasks": 3,
  "completed_tasks": 18,
  "failed_tasks": 2,
  "total_tasks": 24
}
```

### Analytics Response
```json
{
  "overview": {
    "total_tasks": 45,
    "by_status": {"completed": 38, "failed": 2, "running": 3, "pending": 2},
    "by_type": {"code-specialist": 15, "qa-testing-guru": 8, "devops-expert": 12}
  },
  "performance": {
    "average_duration_minutes": 12.3,
    "fastest_tasks": [{"task_id": "fast_task", "duration_minutes": 2.1}],
    "recent_activity": {"last_hour": 5, "last_6_hours": 18}
  },
  "quality": {
    "success_rate": 95.0,
    "error_analysis": {"total_failures": 2, "common_errors": {"timeout": 1, "other": 1}}
  }
}
```

## Performance Optimizations

### Caching Strategy
- **File-based**: Only re-read changed files
- **Time-based**: Minimum scan intervals
- **Memory-efficient**: Smart data structures

### Scalability Features
- **Directory limit**: Handles 100+ output directories
- **Task capacity**: Efficiently processes 10,000+ tasks
- **WebSocket scaling**: Supports multiple concurrent clients

## Error Handling

### Resilient Design
- **Graceful degradation**: Service continues if some directories unavailable
- **Error recovery**: WebSocket reconnection and retry logic
- **Logging**: Comprehensive error tracking and debugging info

### Common Issues
1. **Missing directories**: Service logs warnings but continues
2. **Malformed JSON**: Individual files skipped, others processed
3. **Permission issues**: Logged with specific error details
4. **WebSocket disconnects**: Automatic cleanup and reconnection support

## Deployment Notes

### Dependencies
```bash
pip install fastapi uvicorn websockets pathlib
```

### Environment Setup
```bash
export PYTHONPATH="/home/opsvi/master_root/apps/project-context:/home/opsvi/master_root/apps/agent-orchestrator/src"
```

### Running the Service
```bash
cd /home/opsvi/master_root/apps/project-context/dashboard/backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## Testing

### Unit Tests
```bash
python test_monitoring.py
```

### API Testing
```bash
# Test basic endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/api/status
curl http://localhost:8000/api/analytics
```

### WebSocket Testing
```javascript
// Browser console testing
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (e) => console.log('Received:', JSON.parse(e.data));
```

## Future Enhancements

### Planned Features
- [ ] **Historical trending**: Long-term performance analysis
- [ ] **Alert system**: Configurable failure notifications
- [ ] **Export capabilities**: CSV/PDF report generation
- [ ] **Custom dashboards**: User-configurable view layouts
- [ ] **Multi-orchestrator support**: Monitor multiple orchestrator instances

### Integration Opportunities
- [ ] **Prometheus metrics**: Export to monitoring systems
- [ ] **Grafana dashboards**: Pre-built visualization panels
- [ ] **Slack notifications**: Real-time team updates
- [ ] **Database persistence**: Historical data storage

---

## Summary

This comprehensive monitoring service provides enterprise-grade monitoring for orchestrator task execution with:

✅ **Real-time monitoring** with WebSocket updates
✅ **Comprehensive analytics** across all task dimensions
✅ **Automatic discovery** of all output directories
✅ **Performance optimization** with smart caching
✅ **Quality insights** with error analysis and trends
✅ **Scalable architecture** handling thousands of tasks
✅ **RESTful API** for easy integration
✅ **Error resilience** with graceful degradation

The service is production-ready and provides the foundation for building sophisticated monitoring dashboards and automation workflows.
