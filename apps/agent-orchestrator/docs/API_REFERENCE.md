# Agent Orchestrator API Reference

This document provides comprehensive API reference documentation for the Agent Orchestrator system, covering all public APIs, endpoints, functions, and classes.

## Table of Contents

1. [API Overview](#api-overview)
2. [HTTP/REST API](#httprest-api)
3. [WebSocket API](#websocket-api)
4. [Python API](#python-api)
5. [Command Line Interface](#command-line-interface)
6. [Configuration API](#configuration-api)
7. [Error Handling](#error-handling)
8. [Examples](#examples)

## API Overview

The Agent Orchestrator system provides multiple API layers:

- **HTTP/REST API**: Web-based endpoints for dashboard integration and remote management
- **WebSocket API**: Real-time communication for live monitoring and updates
- **Python API**: Core library classes and functions for direct integration
- **CLI API**: Command-line interface for task execution and management
- **Configuration API**: JSON-based configuration management

### Design Patterns

The system follows several key architectural patterns:

- **Plugin Architecture**: Extensible processor framework
- **Event-Driven Processing**: Async task execution with observers
- **Factory Pattern**: Dynamic orchestrator and provider creation
- **Strategy Pattern**: Multiple execution modes and optimization strategies
- **Circuit Breaker**: Fault tolerance and error recovery

## HTTP/REST API

### Base URLs

- **Development**: `http://localhost:8765`
- **Production**: `http://0.0.0.0:8765` (configurable)
- **Health Check**: Port 8766 (configurable)

### Authentication

Currently no authentication required. Future versions may implement API key authentication.

### Rate Limits

- **Default**: 300 requests per minute with burst size of 50
- **Configurable** via production config

---

### Dashboard API

#### GET /

**Description**: Serves the main dashboard interface

**Response**: HTML dashboard page

**Example**:
```bash
curl http://localhost:8765/
```

#### GET /api/summary

**Description**: Get orchestrator status summary

**Response**:
```json
{
  "status": "running",
  "active_workflows": 3,
  "total_tasks": 15,
  "completed_tasks": 8,
  "failed_tasks": 1,
  "uptime_seconds": 3600,
  "last_updated": "2025-09-08T15:00:00Z"
}
```

**Example**:
```bash
curl http://localhost:8765/api/summary
```

#### GET /api/metrics

**Description**: Get detailed performance metrics

**Response**:
```json
{
  "cpu_usage": 45.2,
  "memory_usage": 512.3,
  "active_connections": 12,
  "requests_per_second": 15.7,
  "average_response_time": 0.85,
  "error_rate": 0.02,
  "websocket_connections": 5
}
```

#### GET /api/active-tasks

**Description**: List all currently active tasks

**Response**:
```json
{
  "tasks": [
    {
      "task_id": "task_001",
      "task_type": "system-documentation",
      "status": "running",
      "start_time": "2025-09-08T14:30:00Z",
      "progress": 65,
      "workflow_name": "documentation_workflow"
    }
  ],
  "total_active": 3
}
```

#### GET /api/active-agents

**Description**: List all active agent instances

**Response**:
```json
{
  "agents": [
    {
      "agent_id": "agent_001",
      "agent_type": "documentation",
      "status": "executing",
      "current_task": "task_001",
      "provider": "openai",
      "start_time": "2025-09-08T14:30:00Z"
    }
  ],
  "total_active": 5
}
```

#### GET /health

**Description**: Health check endpoint

**Response**:
```json
{
  "status": "healthy",
  "timestamp": 1694188800,
  "uptime": 3600,
  "dashboard_running": true,
  "websocket_connections": 5,
  "collector_active": true,
  "dashboard_responsive": true
}
```

---

### Management API (Port 8888)

#### GET /status

**Description**: Get orchestrator execution status

**Response**:
```json
{
  "analysis_dir": "outputs/analysis/system_analysis_20250908_150000",
  "total_tasks": 25,
  "completed_tasks": 20,
  "timestamp": "2025-09-08T15:00:00Z",
  "task_files": ["task_001.json", "task_002.json"]
}
```

#### POST /inject_tasks

**Description**: Inject new tasks into running orchestrator

**Request Body**:
```json
{
  "tasks": [
    {
      "task_id": "new_task_001",
      "task_type": "analysis",
      "prompt": "Analyze system performance"
    }
  ]
}
```

**Response**:
```json
{
  "status": "injection_queued",
  "file": "outputs/analysis/task_injection_150030.json",
  "message": "Tasks queued for injection"
}
```

#### POST /update_dependencies

**Description**: Update task dependencies dynamically

**Request Body**:
```json
{
  "task_id": "task_001",
  "dependencies": ["task_002", "task_003"]
}
```

**Response**:
```json
{
  "status": "dependencies_updated",
  "file": "outputs/analysis/dependency_update_150030.json",
  "message": "Dependencies updated, orchestrator will reload"
}
```

#### POST /trigger_continue

**Description**: Force orchestrator to continue with available tasks

**Request Body**:
```json
{
  "override_dependencies": ["task_005"]
}
```

**Response**:
```json
{
  "status": "continue_triggered",
  "file": "outputs/analysis/continue_signal_150030.json",
  "message": "Orchestrator signaled to continue"
}
```

## WebSocket API

### Connection

**Endpoint**: `ws://localhost:8765/ws`

**Protocol**: Standard WebSocket with JSON message format

### Message Types

#### Real-time Metrics
```json
{
  "type": "metrics_update",
  "data": {
    "cpu_usage": 45.2,
    "memory_usage": 512.3,
    "active_tasks": 5,
    "timestamp": "2025-09-08T15:00:00Z"
  }
}
```

#### Task Updates
```json
{
  "type": "task_update",
  "data": {
    "task_id": "task_001",
    "status": "completed",
    "progress": 100,
    "result": "success",
    "timestamp": "2025-09-08T15:00:00Z"
  }
}
```

#### Log Stream
```json
{
  "type": "log_stream",
  "data": {
    "level": "INFO",
    "message": "Task completed successfully",
    "timestamp": "2025-09-08T15:00:00Z",
    "task_id": "task_001"
  }
}
```

### Example WebSocket Client

```javascript
const ws = new WebSocket('ws://localhost:8765/ws');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  switch(message.type) {
    case 'metrics_update':
      updateDashboard(message.data);
      break;
    case 'task_update':
      updateTaskStatus(message.data);
      break;
    case 'log_stream':
      appendLogMessage(message.data);
      break;
  }
};
```

## Python API

### Core Classes

#### AgentTask

**Description**: Represents a single agent task with dependencies and context

```python
from src.generic_orchestrator import AgentTask

# Create a task
task = AgentTask(
    task_id="analyze_code",
    task_type="analysis",
    prompt="Analyze the codebase for security issues",
    context={"target_dir": "/path/to/code"},
    dependencies=["setup_task"],
    quality_gates=["security_check", "performance_review"]
)

# Task properties
print(task.status)          # pending, running, completed, failed
print(task.start_time)      # Unix timestamp
print(task.to_dict())       # Serialize to dict
```

#### GenericOrchestrator

**Description**: Core orchestrator for managing parallel agent execution

```python
from src.generic_orchestrator import GenericOrchestrator
from pathlib import Path

# Initialize orchestrator
orchestrator = GenericOrchestrator(
    output_dir=Path("./outputs"),
    max_parallel=10,
    use_optimizations=True,
    workflow_name="my_workflow",
    enable_dashboard_reporting=True
)

# Execute tasks
results = await orchestrator.execute_batch(tasks)

# Properties
print(orchestrator.workflow_id)      # UUID
print(orchestrator.output_dir)       # Path object
print(orchestrator.metrics)          # Performance metrics
```

#### EnhancedOrchestrator

**Description**: Advanced orchestrator with quality gates and monitoring

```python
from src.enhanced_orchestrator import EnhancedOrchestrator

# Initialize with enhanced features
orchestrator = EnhancedOrchestrator(
    output_dir=Path("./outputs"),
    max_parallel=10,
    enable_quality_gates=True,
    enable_monitoring=True,
    use_optimizations=True,
    dashboard_state_callback=callback_function
)

# Execute with execution plan
result = await orchestrator.execute_plan(execution_plan)
print(result["quality_metrics"])
```

#### SessionAnalyticsEngine

**Description**: Comprehensive session log analytics system

```python
from src.session_analytics_engine import SessionAnalyticsEngine

# Initialize analytics engine
engine = SessionAnalyticsEngine()

# Analyze session file
metrics = await engine.analyze_session_file("/path/to/session.jsonl")

# Get conversation patterns
patterns = await engine.analyze_conversation_patterns(session_data)

# File operation analytics
file_ops = await engine.analyze_file_operations(session_data)
```

#### GPT5PayloadGenerator

**Description**: Generate optimized GPT-5 payloads from session data

```python
from src.gpt5_payload_generator import GPT5PayloadGenerator

# Initialize generator
generator = GPT5PayloadGenerator()

# Generate payload with chunking
payload = await generator.generate_payload(
    session_data,
    chunking_strategy="adaptive",
    max_tokens=32000,
    optimization_level="balanced"
)

print(payload.token_count)        # Estimated tokens
print(payload.compression_ratio)  # Compression achieved
print(payload.chunks)            # Generated chunks
```

#### TokenPool

**Description**: Manages API tokens for parallel execution

```python
from src.generic_orchestrator import TokenPool

# Initialize with explicit tokens
pool = TokenPool(tokens=["token1", "token2", "token3"])

# Or auto-load from token system
pool = TokenPool()  # Uses token_loader

# Get available tokens
print(pool.available_tokens())

# Thread-safe token acquisition
token = await pool.acquire()
# ... use token ...
pool.release(token)
```

### Data Classes

#### SessionMetrics
```python
@dataclass
class SessionMetrics:
    session_id: str
    start_time: datetime
    end_time: datetime
    duration_minutes: float
    total_messages: int
    user_messages: int
    assistant_messages: int
    total_tool_calls: int
    unique_tools_used: int
    total_file_operations: int
    conversation_turns: int
    working_directory: str
    git_branch: str
```

#### ConversationPattern
```python
@dataclass
class ConversationPattern:
    session_id: str
    pattern_type: str  # 'question_answer', 'iterative_refinement', etc.
    frequency: int
    average_response_time: float
    context_switches: int
    topic_coherence_score: float
```

### Provider Integration

#### OpenAI Provider
```python
from src.providers.openai_provider import OpenAIProvider

# Initialize provider
provider = OpenAIProvider(
    api_key="your_api_key",
    model="gpt-4",
    max_retries=3,
    timeout=60
)

# Execute task
response = await provider.execute_task(task)
```

### Exception Handling

```python
from src.generic_orchestrator import (
    OrchestratorError,
    TaskExecutionError,
    TokenPoolError,
    DependencyError
)

try:
    results = await orchestrator.execute_batch(tasks)
except TaskExecutionError as e:
    print(f"Task failed: {e.task_id} - {e.error}")
except TokenPoolError as e:
    print(f"Token pool exhausted: {e}")
except DependencyError as e:
    print(f"Dependency error: {e}")
```

## Command Line Interface

### Main CLI (main.py)

#### Basic Usage
```bash
# Run with example tasks
python main.py --example --max-parallel 5

# Run from task file
python main.py --tasks-file tasks.json --output-dir ./results

# Use enhanced orchestrator
python main.py --tasks-file tasks.json --use-enhanced --enable-dashboard

# Execute execution plan
python main.py --execution-plan plan.json --max-parallel 10
```

#### Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `--tasks-file` | string | JSON file with task definitions | None |
| `--output-dir` | string | Output directory for results | `./output` |
| `--max-parallel` | int | Max parallel agents | 5 |
| `--example` | flag | Run with example tasks | False |
| `--execution-plan` | string | ExecutionPlan JSON file | None |
| `--use-enhanced` | flag | Use EnhancedOrchestrator | False |
| `--workflow-name` | string | Custom workflow name | None |
| `--enable-dashboard` | flag | Enable dashboard reporting | False |

### Task Runner CLI (run_orchestrator_task.py)

#### Documentation Workflow
```bash
# Generate comprehensive system documentation
python run_orchestrator_task.py \
  --task-type system-documentation \
  --app-name my-app \
  --app-root /path/to/app \
  --detail-level comprehensive

# Custom output directory and template
python run_orchestrator_task.py \
  --task-type system-documentation \
  --app-name my-app \
  --app-root /path/to/app \
  --template enterprise \
  --output-dir /custom/docs/path
```

#### System Analysis Workflow
```bash
# Comprehensive system analysis
python run_system_analysis.py --target /path/to/analyze

# Analysis with specific focus
python run_system_analysis.py \
  --target /path/to/analyze \
  --focus security,performance
```

#### Checkpoint Management
```bash
# Resume from checkpoint
python run_orchestrator_task.py --resume-checkpoint checkpoint_12345

# List available checkpoints
python run_orchestrator_task.py --list-checkpoints --app-name my-app

# Clean old checkpoints
python run_orchestrator_task.py --clean-checkpoints --older-than 7
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `--task-type` | string | Type of workflow to run |
| `--app-name` | string | Application name |
| `--app-root` | string | Application root directory |
| `--template` | string | Documentation template |
| `--output-dir` | string | Output directory |
| `--detail-level` | string | Detail level (basic/standard/comprehensive) |
| `--resume-checkpoint` | string | Checkpoint to resume from |
| `--list-checkpoints` | flag | List available checkpoints |
| `--clean-checkpoints` | flag | Clean old checkpoints |
| `--older-than` | int | Days for checkpoint cleanup |

### Production Dashboard CLI (production_dashboard.py)

```bash
# Start with default config
python production_dashboard.py

# Custom configuration
python production_dashboard.py --config production_config.json

# Override specific settings
python production_dashboard.py \
  --host 0.0.0.0 \
  --port 8765 \
  --log-level DEBUG

# Environment variable overrides
DASHBOARD_HOST=0.0.0.0 DASHBOARD_PORT=8080 python production_dashboard.py
```

### GPT-5 Payload CLI (tools/payload_cli.py)

```bash
# Generate payload from session file
python tools/payload_cli.py generate \
  --input session.jsonl \
  --output payload.json \
  --strategy adaptive

# Analyze token counts
python tools/payload_cli.py analyze \
  --input session.jsonl \
  --format json

# Size optimization report
python tools/size_reporter.py \
  --input session.jsonl \
  --output report.html \
  --chunking-strategy adaptive
```

## Configuration API

### Production Configuration

**File**: `production_config.json`

```json
{
  "host": "0.0.0.0",
  "port": 8765,
  "health_port": 8766,
  "max_connections": 500,
  "keepalive_timeout": 30,
  "client_timeout": 60,
  "graceful_shutdown_timeout": 30,
  "static_dir": "web",
  "log_level": "INFO",
  "log_file": "logs/dashboard_production.log",
  "max_log_size": 52428800,
  "backup_count": 10,
  "metrics_retention_seconds": 7200,
  "websocket_ping_interval": 30,
  "websocket_timeout": 90,
  "performance": {
    "enable_compression": true,
    "compression_level": 6,
    "enable_keepalive": true,
    "tcp_nodelay": true,
    "backlog": 128
  },
  "monitoring": {
    "enable_prometheus_metrics": false,
    "metrics_port": 9090,
    "health_check_interval": 30,
    "auto_restart_threshold": 10
  },
  "security": {
    "allowed_origins": ["*"],
    "rate_limiting": {
      "requests_per_minute": 300,
      "burst_size": 50
    },
    "cors_enabled": true
  },
  "workflow_monitoring": {
    "auto_detect_workflows": true,
    "workflow_scan_interval": 10,
    "max_workflow_history": 100,
    "cleanup_old_workflows": true,
    "workflow_retention_days": 30
  }
}
```

### Task Definition Format

```json
{
  "tasks": [
    {
      "task_id": "unique_task_id",
      "task_type": "documentation|analysis|code|research",
      "prompt": "Detailed task prompt for the agent",
      "context": {
        "working_directory": "/path/to/work",
        "target_files": ["file1.py", "file2.py"],
        "custom_parameters": "value"
      },
      "dependencies": ["prerequisite_task_id"],
      "quality_gates": ["security_check", "performance_review"],
      "timeout_seconds": 3600,
      "retry_count": 3
    }
  ],
  "metadata": {
    "workflow_name": "my_workflow",
    "created_by": "user",
    "created_at": "2025-09-08T15:00:00Z"
  }
}
```

### Execution Plan Format

```json
{
  "name": "comprehensive_analysis",
  "execution_mode": "parallel",
  "enable_quality_gates": true,
  "enable_monitoring": true,
  "use_optimizations": true,
  "tasks": [
    {
      "task_id": "security_audit",
      "task_type": "security",
      "prompt": "Perform comprehensive security audit",
      "quality_gates": ["security_compliance", "vulnerability_scan"]
    }
  ],
  "quality_requirements": {
    "minimum_success_rate": 0.95,
    "maximum_error_rate": 0.05,
    "performance_thresholds": {
      "max_execution_time": 3600,
      "max_memory_usage": "2GB"
    }
  }
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DASHBOARD_HOST` | Dashboard server host | `localhost` |
| `DASHBOARD_PORT` | Dashboard server port | `8765` |
| `DASHBOARD_LOG_LEVEL` | Logging level | `INFO` |
| `DASHBOARD_MAX_CONNECTIONS` | Max connections | `100` |
| `ORCHESTRATOR_OUTPUT_DIR` | Default output directory | `./outputs` |
| `ORCHESTRATOR_MAX_PARALLEL` | Default max parallel | `5` |

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error |
| 503 | Service Unavailable - System overloaded |

### Error Response Format

```json
{
  "error": "Error description",
  "code": "ERROR_CODE",
  "details": {
    "field": "Invalid field value",
    "timestamp": "2025-09-08T15:00:00Z"
  },
  "request_id": "req_12345"
}
```

### Python Exceptions

```python
# Core exceptions
class OrchestratorError(Exception):
    """Base orchestrator exception"""

class TaskExecutionError(OrchestratorError):
    """Task execution failed"""
    def __init__(self, task_id: str, error: str):
        self.task_id = task_id
        self.error = error

class TokenPoolError(OrchestratorError):
    """Token pool issues"""

class DependencyError(OrchestratorError):
    """Task dependency issues"""

class ValidationError(OrchestratorError):
    """Configuration validation issues"""
```

## Examples

### Complete Workflow Example

```python
import asyncio
from pathlib import Path
from src.generic_orchestrator import GenericOrchestrator, AgentTask

async def run_documentation_workflow():
    # Define tasks
    tasks = [
        AgentTask(
            task_id="analyze_structure",
            task_type="analysis",
            prompt="Analyze the project structure and identify key components",
            context={"target_dir": "/path/to/project"}
        ),
        AgentTask(
            task_id="generate_api_docs",
            task_type="documentation",
            prompt="Generate API documentation from the analysis",
            dependencies=["analyze_structure"],
            quality_gates=["completeness_check"]
        ),
        AgentTask(
            task_id="create_user_guide",
            task_type="documentation",
            prompt="Create comprehensive user guide",
            dependencies=["analyze_structure"],
            quality_gates=["clarity_check", "example_validation"]
        )
    ]

    # Initialize orchestrator
    orchestrator = GenericOrchestrator(
        output_dir=Path("./outputs/documentation"),
        max_parallel=3,
        workflow_name="documentation_generation",
        enable_dashboard_reporting=True
    )

    # Execute tasks
    results = await orchestrator.execute_batch(tasks)

    # Process results
    for task_id, result in results.items():
        if result["status"] == "completed":
            print(f"✓ {task_id}: Success")
        else:
            print(f"✗ {task_id}: {result.get('error', 'Unknown error')}")

    return results

# Run the workflow
asyncio.run(run_documentation_workflow())
```

### Dashboard Integration Example

```python
import asyncio
from aiohttp import web
from src.monitoring.dashboard_server import DashboardServer

async def start_dashboard():
    # Create dashboard server
    dashboard = DashboardServer(
        host="0.0.0.0",
        port=8765,
        static_dir="web"
    )

    # Start server
    runner = web.AppRunner(dashboard.app)
    await runner.setup()

    site = web.TCPSite(runner, dashboard.host, dashboard.port)
    await site.start()

    print(f"Dashboard started at http://{dashboard.host}:{dashboard.port}")

    # Keep running
    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        await runner.cleanup()

# Start dashboard
asyncio.run(start_dashboard())
```

### CLI Integration Example

```bash
#!/bin/bash
# Production deployment script

# Start production dashboard
python production_dashboard.py --config production_config.json &
DASHBOARD_PID=$!

# Wait for dashboard to be ready
sleep 5

# Run comprehensive documentation workflow
python run_orchestrator_task.py \
  --task-type system-documentation \
  --app-name my-application \
  --app-root /opt/myapp \
  --detail-level comprehensive \
  --output-dir /opt/docs

# Monitor results
curl http://localhost:8765/api/summary

# Cleanup
kill $DASHBOARD_PID
```

### WebSocket Monitoring Example

```javascript
// Real-time workflow monitoring
class WorkflowMonitor {
    constructor(wsUrl = 'ws://localhost:8765/ws') {
        this.ws = new WebSocket(wsUrl);
        this.setupHandlers();
    }

    setupHandlers() {
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    handleMessage(message) {
        switch(message.type) {
            case 'task_update':
                this.updateTaskProgress(message.data);
                break;
            case 'metrics_update':
                this.updateSystemMetrics(message.data);
                break;
            case 'log_stream':
                this.appendLog(message.data);
                break;
        }
    }

    updateTaskProgress(taskData) {
        const progressBar = document.getElementById(`task_${taskData.task_id}`);
        if (progressBar) {
            progressBar.style.width = `${taskData.progress}%`;
        }
    }

    updateSystemMetrics(metrics) {
        document.getElementById('cpu-usage').textContent = `${metrics.cpu_usage}%`;
        document.getElementById('memory-usage').textContent = `${metrics.memory_usage}MB`;
        document.getElementById('active-tasks').textContent = metrics.active_tasks;
    }

    appendLog(logData) {
        const logContainer = document.getElementById('log-container');
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${logData.level.toLowerCase()}`;
        logEntry.textContent = `${logData.timestamp} [${logData.level}] ${logData.message}`;
        logContainer.appendChild(logEntry);
    }
}

// Initialize monitor
const monitor = new WorkflowMonitor();
```

This API reference provides comprehensive documentation for all public interfaces of the Agent Orchestrator system. For additional examples and advanced usage patterns, refer to the project's example files and test suite.
