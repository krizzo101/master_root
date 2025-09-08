# Orchestrator Output Structure Specification

## Overview

This document defines the standardized directory structure and workflow identification system for the agent-orchestrator. This new structure replaces the current chaotic system where multiple output directories (`output/`, `outputs/`, `orchestrator_output/`) contain mixed workflow logs and deliverables.

## Problem Statement

**Current Issues:**
- 3 different output directory systems with inconsistent structures
- All workflow logs mixed in shared `output/logs/` directory
- No workflow identification or naming system
- Impossible to map running processes to their output directories
- Dashboard cannot effectively monitor concurrent workflows

**Evidence:** Currently 16+ concurrent processes running with logs scattered across multiple output systems.

## New Unified Structure

```
orchestrator/
├── workflows/                    # All workflow executions
│   ├── active/                   # Currently running workflows
│   │   ├── workflow_NAME_ID/     # Individual workflow directory
│   │   │   ├── metadata.json     # Workflow info, start time, task file, etc.
│   │   │   ├── orchestrator.log  # Main workflow log
│   │   │   ├── agents/           # Agent-specific logs
│   │   │   │   ├── agent_TASK_ID_PID.log
│   │   │   │   └── agent_TASK_ID_PID.chatlog
│   │   │   ├── tasks/            # Task definitions and results
│   │   │   │   ├── TASK_ID.json  # Task definition
│   │   │   │   └── TASK_ID_result.json # Task result
│   │   │   ├── deliverables/     # Generated files
│   │   │   ├── checkpoints/      # State snapshots for resume
│   │   │   └── timeline.json     # Progress tracking
│   ├── completed/                # Finished workflows (moved from active/)
│   └── failed/                   # Failed workflows (moved from active/)
├── global/                       # System-wide orchestrator data
│   ├── registry.json             # Active workflow registry
│   ├── metrics.json              # Global performance metrics
│   └── system.log                # System-level events
└── archive/                      # Legacy structure preservation
    ├── output/                   # Current output/ directory
    ├── outputs/                  # Current outputs/ directory
    └── orchestrator_output/      # Current orchestrator_output/
```

## Workflow Identification System

### Workflow Naming Convention
```
workflow_{SOURCE}_{TIMESTAMP}_{HASH}
```

**Examples:**
- `workflow_documentation-build_20250908_143045_a7f2`
- `workflow_system-analysis_20250908_143112_b8e3`
- `workflow_main-tasks_20250908_143200_c9d4`

**Components:**
- **SOURCE**: Derived from task file name (remove `.json`, replace `_` with `-`)
- **TIMESTAMP**: Workflow start time (YYYYMMDD_HHMMSS)
- **HASH**: 4-character unique identifier (prevents collisions)

### Source Name Derivation Rules
- `create_documentation_workflow_task.json` → `documentation-workflow-task`
- `system_analysis_tasks.json` → `system-analysis-tasks`
- `main.py --tasks-file X` → derive from X filename
- `run_system_analysis.py` → `system-analysis`

## Metadata.json Structure

Each workflow directory contains a `metadata.json` file:

```json
{
  "workflow_id": "workflow_documentation-build_20250908_143045_a7f2",
  "workflow_name": "Documentation Build Workflow",
  "source_file": "create_documentation_workflow_task.json",
  "source_command": "python main.py --tasks-file create_documentation_workflow_task.json",
  "start_time": "2025-09-08T14:30:45Z",
  "end_time": null,
  "status": "running",
  "progress": {
    "total_tasks": 7,
    "completed_tasks": 2,
    "failed_tasks": 0,
    "active_tasks": ["dashboard_specifications_generation"],
    "pending_tasks": ["dashboard_architecture_design", "dashboard_backend_implementation"]
  },
  "agents": {
    "active_count": 2,
    "max_parallel": 3,
    "token_usage": 1234,
    "active_pids": [1246696, 1248536]
  },
  "process_info": {
    "main_pid": 1246696,
    "command": "python main.py --tasks-file create_documentation_workflow_task.json",
    "working_directory": "/home/opsvi/master_root/apps/agent-orchestrator"
  },
  "outputs": {
    "deliverables_count": 3,
    "total_log_size": "2.4MB",
    "checkpoint_count": 2
  }
}
```

## Timeline.json Structure

Progress tracking file updated in real-time:

```json
{
  "workflow_id": "workflow_documentation-build_20250908_143045_a7f2",
  "events": [
    {
      "timestamp": "2025-09-08T14:30:45Z",
      "event": "workflow_started",
      "data": {
        "total_tasks": 7,
        "max_parallel": 3
      }
    },
    {
      "timestamp": "2025-09-08T14:31:12Z",
      "event": "task_started",
      "task_id": "dashboard_specifications_generation",
      "agent_type": "technical-writer"
    },
    {
      "timestamp": "2025-09-08T14:35:23Z",
      "event": "task_completed",
      "task_id": "dashboard_specifications_generation",
      "duration_seconds": 251,
      "deliverables": ["PROJECT_REQUIREMENTS.md", "UI_SPECIFICATIONS.md"]
    }
  ],
  "statistics": {
    "total_runtime_seconds": 480,
    "estimated_completion_seconds": 320,
    "average_task_duration": 125,
    "completion_percentage": 28.5
  }
}
```

## Global Registry.json Structure

System-wide workflow tracking:

```json
{
  "last_updated": "2025-09-08T14:40:15Z",
  "active_workflows": {
    "workflow_documentation-build_20250908_143045_a7f2": {
      "status": "running",
      "start_time": "2025-09-08T14:30:45Z",
      "progress_percentage": 28.5,
      "active_agents": 2,
      "main_pid": 1246696
    },
    "workflow_system-analysis_20250908_143112_b8e3": {
      "status": "running",
      "start_time": "2025-09-08T14:31:12Z",
      "progress_percentage": 45.2,
      "active_agents": 3,
      "main_pid": 1248536
    }
  },
  "system_metrics": {
    "total_active_workflows": 2,
    "total_active_agents": 5,
    "token_pool_usage": "15/19",
    "system_load_average": 2.3
  }
}
```

## Implementation Requirements

### GenericOrchestrator Changes Required

1. **Workflow ID Generation**
   - Generate unique workflow ID at startup
   - Derive source name from command line arguments
   - Create workflow directory in `orchestrator/workflows/active/`

2. **Directory Structure Creation**
   ```python
   def create_workflow_directory(self, workflow_id):
       base_path = Path("orchestrator/workflows/active") / workflow_id
       (base_path / "agents").mkdir(parents=True, exist_ok=True)
       (base_path / "tasks").mkdir(parents=True, exist_ok=True)
       (base_path / "deliverables").mkdir(parents=True, exist_ok=True)
       (base_path / "checkpoints").mkdir(parents=True, exist_ok=True)
       return base_path
   ```

3. **Metadata Management**
   - Write initial metadata.json on startup
   - Update progress fields during execution
   - Move workflow to completed/failed on finish

4. **Log Routing**
   - Redirect orchestrator logs to `workflow_dir/orchestrator.log`
   - Route agent logs to `workflow_dir/agents/agent_{task_id}_{pid}.log`
   - Preserve agent chat logs separately

5. **Registry Updates**
   - Update global/registry.json on workflow start/stop
   - Maintain real-time system metrics
   - Clean up stale entries on process death

6. **Timeline Tracking**
   - Log workflow events (started, task_started, task_completed, failed)
   - Calculate progress percentages and ETAs
   - Update timeline.json in real-time

### Backward Compatibility Requirements

**Critical:** Existing workflows must continue functioning without modification.

1. **Legacy Output Support**
   - Continue writing to old output directories during transition period
   - Dashboard reads both old and new structures
   - No breaking changes to existing scripts

2. **Migration Strategy**
   - Phase 1: New workflows use new structure, old continue as-is
   - Phase 2: Background migration of old workflow data
   - Phase 3: Full transition, archive old directories

3. **API Compatibility**
   - All existing command-line interfaces remain unchanged
   - `main.py --tasks-file` continues working identically
   - Resume/checkpoint functionality preserved

## Dashboard Integration Points

### Real-time Monitoring Capabilities
1. **Active Workflow Detection**: Read `global/registry.json`
2. **Process Mapping**: Map PIDs to workflow directories via metadata
3. **Log Streaming**: Tail workflow-specific logs in real-time
4. **Progress Tracking**: Monitor timeline.json for completion estimates
5. **Deliverable Monitoring**: Watch deliverables/ directories for new files

### File System Watchers Required
- `orchestrator/workflows/active/` - New workflow detection
- `orchestrator/workflows/*/metadata.json` - Status changes
- `orchestrator/workflows/*/timeline.json` - Progress updates
- `orchestrator/workflows/*/deliverables/` - New file generation
- `orchestrator/global/registry.json` - System-wide changes

## Migration Implementation Plan

### Phase 1: Infrastructure Setup
- Create new directory structure
- Implement workflow ID generation
- Add metadata/timeline writing capabilities
- Maintain dual-write to old and new structures

### Phase 2: Dashboard Integration
- Update dashboard to read new structure
- Implement file system watchers
- Add backward compatibility for old workflows
- Test monitoring capabilities

### Phase 3: Full Migration
- Switch all new workflows to new structure only
- Migrate historical workflow data to archive/
- Remove dual-write capabilities
- Complete transition

## Testing Requirements

### Validation Criteria
1. **No Breaking Changes**: All existing workflows continue functioning
2. **Real-time Updates**: Dashboard reflects workflow changes within 1 second
3. **Process Mapping**: 100% accuracy mapping PIDs to workflows
4. **Performance**: No significant overhead from new structure
5. **Resume Capability**: Checkpoint/resume functions work with new structure

### Test Scenarios
1. **Concurrent Workflow Monitoring**: Start 5+ workflows simultaneously
2. **Legacy Compatibility**: Run old task files without modification
3. **Process Recovery**: Handle orchestrator crashes gracefully
4. **Migration Testing**: Verify old workflow data accessibility

## Current State Analysis

**Existing Output Directories to Handle:**
- `/output/logs/` - Mixed orchestrator logs from all workflows
- `/outputs/analysis/` - System analysis workflow results
- `/outputs/apps_audit/` - Application audit results
- `/orchestrator_output/TIMESTAMP/` - Some organized workflow outputs

**Active Workflows to Map:**
- 16+ concurrent processes currently running
- Multiple workflow types (documentation, analysis, audit, system tasks)
- Various entry points (main.py, run_system_analysis.py, resume_orchestrator.py)

**Implementation Priority:**
1. New workflow structure (highest priority)
2. Dashboard integration
3. Legacy migration (lowest priority - can be gradual)

This specification provides the foundation for creating a monitoring dashboard that can effectively track and manage concurrent orchestrator workflows.
