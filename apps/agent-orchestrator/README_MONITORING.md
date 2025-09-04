# Real-Time Agent Status API

## Overview

The Real-Time Agent Status API provides comprehensive monitoring capabilities for launched Claude agents. This system solves the critical gap where "the orchestrator can launch agents but has NO way to monitor their progress in real-time."

## Key Features

- **Real-time agent status monitoring** - Track agent progress, errors, and deliverables as they execute
- **UUID-based log tracking** - Direct integration with `~/.claude/projects/{cwd}/{uuid}.jsonl` files
- **Chat_search integration** - Built on existing chat_search.py for reliable log parsing
- **Team-based monitoring** - Monitor agents by team or view all active agents
- **Stuck agent detection** - Automatically detect agents that haven't been active
- **Performance analytics** - Track efficiency, context usage, and error rates
- **Live log streaming** - Real-time monitoring of agent execution logs

## Architecture

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│  AgentStatusMonitor │────│   AgentLogParser     │────│   chat_search.py    │
│  (Main API)         │    │   (Analysis)         │    │   (Foundation)      │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
           │
           ▼
┌─────────────────────┐
│  UUIDMonitoringSystem│
│  (Real-time)        │
└─────────────────────┘
```

## Quick Start

### Basic Agent Monitoring

```python
from src import AgentStatusMonitor

# Initialize monitor
monitor = AgentStatusMonitor()

# Get agent status
status = await monitor.get_agent_status("agent-uuid-here")

print(f"Status: {status.status}")
print(f"Progress: {status.progress.progress_percentage}%")
print(f"Errors: {status.error_count}")
print(f"Context Usage: {status.context_usage}%")
```

### Real-time Monitoring

```python
from src import UUIDMonitoringSystem

# Start comprehensive monitoring
monitor = UUIDMonitoringSystem(update_interval=15)
await monitor.start_monitoring()

# Get all active agents
agents = await monitor.get_all_active_agents()

# Monitor specific team
team_agents = await monitor.get_team_agents("phase1")

# Detect stuck agents
stuck = await monitor.detect_stuck_agents(threshold_minutes=10)
```

### Live Log Streaming

```python
# Stream logs in real-time
async for log_entry in monitor.monitor_agent_logs(agent_uuid):
    print(f"[{log_entry.timestamp}] {log_entry.role}: {log_entry.content}")
```

## API Reference

### AgentStatusMonitor

Core monitoring class providing agent status queries.

#### Methods

- `async get_agent_status(agent_uuid: str) -> AgentStatus`
  - Get current status for a specific agent

- `async get_all_agent_statuses(team_id: str = None) -> Dict[str, AgentStatus]`
  - Get status for all agents, optionally filtered by team

- `async monitor_agent_logs(agent_uuid: str) -> AsyncGenerator[LogEntry, None]`
  - Stream agent logs in real-time

### AgentStatus Data Structure

```python
@dataclass
class AgentStatus:
    agent_uuid: str
    status: str  # running, completed, failed, stuck, unknown
    progress: ProgressStatus
    context_usage: float  # 0.0 to 100.0
    error_count: int
    recent_errors: List[ErrorInfo]
    last_activity_timestamp: Optional[str]
    deliverables_completed: List[str]
    deliverables_missing: List[str]
    start_time: Optional[str]
    runtime_duration: Optional[float]
```

### AgentLogParser

Advanced log analysis and parsing capabilities.

#### Methods

- `async parse_agent_progress(uuid: str) -> ProgressStatus`
  - Extract progress information from logs

- `async detect_agent_errors(uuid: str) -> List[ErrorInfo]`
  - Detect and categorize errors

- `async check_context_usage(uuid: str) -> float`
  - Estimate context window usage

- `async get_agent_deliverables(uuid: str) -> List[str]`
  - Extract list of files/outputs created

### UUIDMonitoringSystem

Comprehensive real-time monitoring with file system watching.

#### Methods

- `async start_monitoring()` / `async stop_monitoring()`
  - Control monitoring lifecycle

- `async get_real_time_status(uuid: str) -> AgentStatus`
  - Get fresh status with caching

- `async detect_stuck_agents(threshold_minutes: int = 10) -> List[str]`
  - Find agents without recent activity

- `async get_monitoring_summary() -> Dict[str, Any]`
  - Comprehensive monitoring dashboard data

## Integration Guide

### With Generic Orchestrator

```python
from src.generic_orchestrator import GenericOrchestrator
from src import AgentStatusMonitor

class MonitoredOrchestrator(GenericOrchestrator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.monitor = AgentStatusMonitor()

    async def execute_agent(self, task):
        # Get session UUID from execution
        session_id = str(uuid.uuid4())

        # Execute agent (existing logic)
        result = await super().execute_agent(task)

        # Monitor the agent
        status = await self.monitor.get_agent_status(session_id)
        print(f"Agent {task.task_id}: {status.status} ({status.progress.progress_percentage}%)")

        return result
```

### Management Dashboard

```python
async def create_dashboard():
    monitor = UUIDMonitoringSystem(update_interval=10)
    await monitor.start_monitoring()

    while True:
        summary = await monitor.get_monitoring_summary()

        print(f"Active: {summary['total_active_agents']}")
        print(f"Status: {dict(summary['agents_by_status'])}")
        print(f"Teams: {summary['agents_by_team']}")
        print(f"Errors: {summary['performance_metrics']['total_errors']}")

        stuck = await monitor.detect_stuck_agents()
        if stuck:
            print(f"⚠️ Stuck agents: {stuck}")

        await asyncio.sleep(30)
```

## Configuration

### Default Log Directory

The system automatically detects Claude project logs:
- Default: `~/.claude/projects/-home-opsvi-master-root-apps-agent-orchestrator`
- Custom: Pass `chat_logs_dir` parameter to any monitor class

### Update Intervals

- `AgentStatusMonitor`: 15-second cache duration
- `UUIDMonitoringSystem`: Configurable update interval (default: 15 seconds)
- File system monitoring: Real-time with watchdog

### Error Detection Patterns

The system recognizes these error patterns:
- Python exceptions and tracebacks
- Failed operations ("failed to", "unable to")
- Permission and file access errors
- Network and timeout errors
- Syntax and parsing errors

### Progress Indicators

Progress detection looks for:
- Percentage indicators ("50%", "Progress: 75%")
- Task completion markers ("completed", "finished", "done", "✓")
- Sequential task indicators ("task 3 of 10")
- Tool usage and deliverable creation

## Monitoring Patterns

### Stuck Agent Detection

Agents are considered "stuck" when:
- No log activity for >10 minutes (configurable)
- Status remains "running" with no progress updates
- No tool usage or deliverable creation

### Context Usage Estimation

Context usage is estimated based on:
- Total message content length
- Number of tool calls (weighted higher)
- Rough token estimation (4 chars per token)
- Percentage of ~200k context window

### Performance Scoring

Efficiency scores consider:
- Number of deliverables created (20 points each)
- Progress percentage achieved (0.5x multiplier)
- Error rate penalty (-2 points per error)
- Activity level bonus (up to 50 points)

## Error Handling

The monitoring system is designed to be resilient:
- Graceful handling of missing or corrupted log files
- Automatic retry on temporary file access issues
- Caching to reduce repeated log parsing
- Exception isolation (one agent's errors don't affect others)

## Performance Considerations

- **Caching**: Agent statuses cached for 15 seconds to avoid excessive parsing
- **Batching**: Multiple agent queries processed efficiently
- **File watching**: Uses `watchdog` for efficient file system monitoring
- **Memory usage**: LRU cache limits for large deployments

## Testing

Run the test suite:

```bash
python test_monitoring_integration.py
```

Run usage examples:

```bash
python monitoring_example.py
```

## Dependencies

- `watchdog` - File system monitoring
- `asyncio` - Asynchronous operations
- `pathlib` - Path handling
- `re` - Regular expressions for log parsing
- `json` - Log file parsing

## Success Criteria ✅

The Real-Time Agent Status API successfully delivers:

1. **✅ Management agents can query any running agent's current status**
   - `get_agent_status()` provides comprehensive status information

2. **✅ Real-time progress updates every 15 seconds**
   - Configurable update intervals with intelligent caching

3. **✅ Automatic detection of stuck/completed agents**
   - `detect_stuck_agents()` identifies inactive agents
   - Status detection recognizes completion and failure states

4. **✅ Integration with chat_search.py works reliably**
   - Built on ChatSearcher foundation for robust log parsing
   - Direct integration with existing log infrastructure

5. **✅ UUID-based monitoring by agent UUID**
   - Direct monitoring of `~/.claude/projects/{cwd}/{uuid}.jsonl` files
   - No manual log searching required

This foundational system enables everything else in the agent orchestration ecosystem by providing the critical missing piece: **real-time visibility into agent execution**.

## UUID Format

The monitoring system expects agent UUIDs in standard format:
- Pattern: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- Example: `team-phase1-001-monitor-1725408000`
- Log files: `{uuid}.jsonl` in the Claude projects directory

Team assignments are auto-detected from UUID content or early log entries containing team identifiers.
