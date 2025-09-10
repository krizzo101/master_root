# Dashboard Integration Guide

## Overview

The GenericOrchestrator has been enhanced with workflow tracking and dashboard integration capabilities, enabling real-time monitoring of agent workflows while maintaining full backward compatibility.

## Key Features

### 1. Workflow-Specific Directory Structure
- **New Format**: `outputs/workflow_NAME/workflow_NAME_TIMESTAMP/`
- **Backward Compatible**: Uses original output directory when no workflow name is specified
- **Automatic Naming**: Derives workflow names from task file names (e.g., `system_analysis_tasks.json` → `system_analysis`)

### 2. Enhanced Logging
- **Workflow-Identified Logs**: `orchestrator_WORKFLOW_NAME_TIMESTAMP.log`
- **Structured Location**: All logs go into workflow-specific `logs/` directory
- **Backward Compatible**: Uses original naming when no workflow specified

### 3. Dashboard State Reporting
- **Real-time Events**: Workflow started, progress updates, task activity, completion
- **Progress Tracking**: Automatic progress percentage calculation
- **ETA Calculation**: Based on task completion rates and parallel execution
- **Activity Monitoring**: Individual task start, completion, and failure tracking

### 4. Agent Activity Monitoring
- **Task Lifecycle**: Tracks start time, duration, status changes
- **Error Reporting**: Detailed failure information with error types
- **Performance Metrics**: Duration tracking for ETA calculations

## Usage Examples

### Basic Usage (Backward Compatible)
```bash
# Original format - no changes required
python main.py --tasks-file my_tasks.json --output-dir ./output

# Uses: ./output/ directly (legacy mode)
```

### Workflow-Aware Usage
```bash
# Automatic workflow naming from task file
python main.py --tasks-file system_analysis_tasks.json --output-dir ./output

# Creates: outputs/system_analysis/system_analysis_YYYYMMDD_HHMMSS/
```

### Custom Workflow Name
```bash
# Custom workflow name
python main.py --tasks-file my_tasks.json --workflow-name "my_project" --output-dir ./output

# Creates: outputs/my_project/my_project_YYYYMMDD_HHMMSS/
```

### Dashboard Reporting Enabled
```bash
# Enable real-time dashboard reporting
python main.py --tasks-file my_tasks.json --enable-dashboard

# Provides: Real-time console output with progress, ETA, and status updates
```

## Dashboard Integration Points

### State Callback Interface
```python
def dashboard_callback(state_data: Dict[str, Any]):
    event = state_data.get('event')

    if event == 'workflow_started':
        # Handle workflow start
        workflow_id = state_data['workflow_id']
        workflow_name = state_data['workflow_name']

    elif event == 'workflow_progress':
        # Handle progress update
        progress_percent = state_data['progress_percent']
        eta_seconds = state_data['eta_seconds']

    elif event == 'task_activity':
        # Handle task activity
        task_id = state_data['task_id']
        activity = state_data['activity']  # started, completed, failed

    elif event == 'workflow_completed':
        # Handle workflow completion
        metrics = state_data['metrics']
```

### Programmatic Usage
```python
from pathlib import Path
from src.generic_orchestrator import GenericOrchestrator

def my_dashboard_callback(state_data):
    # Your dashboard integration logic here
    pass

orchestrator = GenericOrchestrator(
    output_dir=Path("./output"),
    max_parallel=5,
    workflow_name="my_workflow",
    task_file_path="my_tasks.json",
    enable_dashboard_reporting=True,
    dashboard_state_callback=my_dashboard_callback
)
```

## Directory Structure Examples

### With Workflow Tracking
```
outputs/
├── system_analysis/
│   ├── system_analysis_20250908_133656/
│   │   ├── logs/
│   │   │   └── orchestrator_system_analysis_20250908_133656.log
│   │   ├── tasks/
│   │   │   ├── task1.json
│   │   │   └── task2.json
│   │   └── messages/
│   └── system_analysis_20250908_140215/
│       └── ...
└── custom_workflow/
    └── custom_workflow_20250908_141030/
        └── ...
```

### Legacy Mode (Backward Compatible)
```
output/
├── logs/
│   └── orchestrator_generic_workflow_20250908_133922.log
├── tasks/
│   ├── task1.json
│   └── task2.json
└── messages/
```

## Backward Compatibility

All existing workflows continue to work without modification:

- **No workflow parameters**: Uses original output directory structure
- **Existing command-line arguments**: All work as before
- **Task file formats**: No changes required
- **Output formats**: Identical to previous versions

## Dashboard Events

### Workflow Events
- `workflow_started`: When orchestrator begins execution
- `workflow_progress`: Progress updates after each task batch
- `workflow_completed`: When all tasks finish

### Task Events
- `task_activity` with `activity='started'`: Task begins execution
- `task_activity` with `activity='running'`: Task is actively running
- `task_activity` with `activity='completed'`: Task completes successfully
- `task_activity` with `activity='failed'`: Task fails or encounters error

### State Data Fields

#### Workflow Started
```json
{
  "event": "workflow_started",
  "workflow_id": "uuid",
  "workflow_name": "system_analysis",
  "output_dir": "/path/to/output",
  "timestamp": "2025-09-08T13:36:56.123Z",
  "max_parallel": 5,
  "token_pool_size": 19
}
```

#### Workflow Progress
```json
{
  "event": "workflow_progress",
  "workflow_id": "uuid",
  "workflow_name": "system_analysis",
  "completed_tasks": 3,
  "total_tasks": 10,
  "progress_percent": 30,
  "current_task": "analysis_task_4",
  "eta_seconds": 180,
  "timestamp": "2025-09-08T13:37:15.456Z"
}
```

#### Task Activity
```json
{
  "event": "task_activity",
  "workflow_id": "uuid",
  "workflow_name": "system_analysis",
  "task_id": "task_1",
  "task_type": "research",
  "activity": "completed",
  "status": "completed",
  "timestamp": "2025-09-08T13:37:45.789Z",
  "duration": 45.2,
  "details": {
    "duration": 45.2,
    "result_type": "json"
  }
}
```

## Integration with Existing Dashboard

To integrate with the existing dashboard backend:

1. **Database Integration**: Connect the dashboard callback to the PostgreSQL schema defined in `TECHNICAL_SPECIFICATIONS.md`

2. **WebSocket Broadcasting**: Use the callback to emit events via the WebSocket hub

3. **State Persistence**: Store workflow state in the `workflows` and `workflow_tasks` tables

4. **Real-time Updates**: Broadcast progress and task activity to connected clients

Example integration:
```python
async def dashboard_integration_callback(state_data):
    # Store in database
    await store_workflow_state(state_data)

    # Broadcast via WebSocket
    await websocket_hub.broadcast_to_workflow(
        state_data['workflow_id'],
        state_data
    )

    # Update cache
    await cache_manager.invalidate_workflow(state_data['workflow_id'])
```

## Performance Considerations

- **ETA Calculation**: Based on rolling average of last 5 task completions
- **Callback Errors**: Non-blocking - dashboard callback failures don't affect workflow execution
- **Memory Usage**: Task completion times are capped at recent history
- **File I/O**: Workflow directories created lazily, only when needed

## Migration Guide

No migration required - all changes are additive and backward compatible. To opt into new features:

1. **Add workflow tracking**: Use `--workflow-name` or ensure task files follow naming conventions
2. **Enable dashboard**: Add `--enable-dashboard` flag
3. **Custom integration**: Provide `dashboard_state_callback` in programmatic usage

The integration maintains full compatibility while providing rich workflow tracking and dashboard integration capabilities.
