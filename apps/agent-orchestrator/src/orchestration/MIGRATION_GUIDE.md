# GenericOrchestrator Refactoring Migration Guide

## Overview
The `GenericOrchestrator` god object (2530 lines) has been refactored into four focused components, each under 500 lines:

1. **TaskScheduler** (368 lines) - Task scheduling, dependencies, token management
2. **WorkflowEngine** (440 lines) - Agent execution, MCP config, checkpointing
3. **MetricsCollector** (486 lines) - Performance metrics, resource tracking, reporting
4. **StateManager** (459 lines) - State persistence, metadata, dashboard integration

## Public API Compatibility

The refactored `GenericOrchestrator` maintains **100% backward compatibility** with the original API.

### Unchanged Public Methods
```python
# Main execution
async def run(task_generator, result_processor, tasks)
async def execute_agent(task: AgentTask)
async def execute_batch(tasks: List[AgentTask])

# All backward compatibility wrappers maintained
def _log_audit_action(action, details)
def _track_deliverable(file_path, operation)
def _scan_for_deliverables()
def _report_workflow_started()
def _report_workflow_progress(completed, total, current, eta)
def _report_task_activity(task_id, activity_type, details)
def _report_workflow_completed(metrics)
def _calculate_eta(completed, total)
async def _create_checkpoint(task)
def _update_workflow_metadata(updates)
async def _generate_workflow_completion_report()
async def _save_completion_report(report)
```

### Unchanged Constructor Parameters
All original constructor parameters are preserved with identical behavior:
- `output_dir`
- `max_parallel`
- `tokens`
- `use_optimizations`
- `master_mcp_registry_path`
- `agent_execution_profile`
- `agent_debug_mode`
- `agent_base_work_dir`
- `enable_dynamic_configs`
- `log_to_work_dir`
- `workflow_name`
- `task_file_path`
- `enable_dashboard_reporting`
- `dashboard_state_callback`
- `workflow_source`

### Unchanged Data Classes
- `AgentTask` - Identical structure and fields

## Migration Steps

### Option 1: Drop-in Replacement (Recommended)
```python
# Old import
from src.generic_orchestrator import GenericOrchestrator, AgentTask

# New import - fully compatible
from src.orchestration import GenericOrchestrator, AgentTask
```

### Option 2: Use Individual Components
```python
from src.orchestration import (
    TaskScheduler,
    WorkflowEngine,
    MetricsCollector,
    StateManager
)

# Build custom orchestration logic using components
scheduler = TaskScheduler(max_parallel=10)
engine = WorkflowEngine(output_dir=Path("output"))
metrics = MetricsCollector(output_dir=Path("output"), workflow_id="test")
state = StateManager(output_dir=Path("output"), workflow_id="test", ...)
```

## Benefits of Refactoring

### Maintainability
- **Separation of Concerns**: Each component has a single responsibility
- **Smaller Files**: All components under 500 lines (vs 2530 lines)
- **Clearer Interfaces**: Well-defined boundaries between components
- **Easier Testing**: Components can be tested independently

### Extensibility
- **Pluggable Components**: Easy to swap implementations
- **Independent Evolution**: Components can be enhanced separately
- **Custom Orchestrators**: Build specialized orchestrators using components

### Performance
- **Reduced Memory Footprint**: Load only needed components
- **Better Concurrency**: Cleaner async/await patterns
- **Optimized Resource Usage**: Focused resource management

## Component Responsibilities

### TaskScheduler (368 lines)
- Task queue management
- Dependency resolution
- Token pool management
- Execution slot control
- Task state tracking

### WorkflowEngine (440 lines)
- Agent process execution
- MCP configuration management
- Workspace creation
- Command building
- Checkpoint operations
- Message bus for inter-agent communication

### MetricsCollector (486 lines)
- Performance metrics collection
- Resource usage tracking
- Task timing statistics
- Deliverable tracking
- Audit logging
- Report generation

### StateManager (459 lines)
- Workflow state persistence
- Metadata management
- Checkpoint save/restore
- Dashboard reporting
- Progress tracking
- State recovery

## Testing the Refactored Code

```python
# Example test maintaining original API
async def test_backward_compatibility():
    orchestrator = GenericOrchestrator(
        output_dir=Path("test_output"),
        max_parallel=5,
        workflow_name="compatibility_test"
    )

    tasks = [
        AgentTask(
            task_id="task1",
            task_type="test",
            prompt="Test task",
            dependencies=[]
        )
    ]

    results = await orchestrator.run(tasks=tasks)
    assert len(results) == 1
```

## Future Enhancements

With the refactored architecture, future enhancements are easier:

1. **Alternative Schedulers**: Implement priority-based or deadline-aware schedulers
2. **Different Execution Engines**: Support for different agent types or cloud execution
3. **Advanced Metrics**: Machine learning-based performance prediction
4. **Distributed State**: Redis or database-backed state management
5. **Plugin System**: Dynamic component loading

## Rollback Plan

If issues arise, the original monolithic `generic_orchestrator.py` remains available:
```python
# Rollback to original if needed
from src.generic_orchestrator import GenericOrchestrator
```

## Support

For questions or issues with the refactored components:
1. Check this migration guide
2. Review component docstrings
3. Run the compatibility test suite
4. File an issue with specific API compatibility concerns
