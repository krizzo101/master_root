# CollaborativeOrchestrator Migration Guide

## Overview

The `CollaborativeOrchestrator` extends the `GenericOrchestrator` to provide real-time agent collaboration while maintaining full backwards compatibility. This guide shows how to migrate from traditional orchestration to collaborative execution.

## Key Features

### ✅ **Backwards Compatibility**
- All existing `GenericOrchestrator` code works unchanged
- Drop-in replacement with same API
- Zero breaking changes to existing functionality

### 🚀 **New Collaboration Features**
- **Real-time messaging** between agents during execution
- **Shared workspaces** for collaborative file editing
- **Intelligent team formation** based on agent capabilities
- **Multiple collaboration modes** (shared, handoff, review)
- **Event-driven coordination** with full audit trails

### 🎯 **Execution Modes**
- **Traditional Mode**: Existing isolated agent execution (default)
- **Collaborative Mode**: Agents communicate and share workspaces
- **Hybrid Mode**: Mix collaborative and traditional tasks
- **Team Mode**: Organize agents into specialized teams

## Migration Strategies

### Strategy 1: Drop-in Replacement (Zero Changes)

Simply replace `GenericOrchestrator` with `CollaborativeOrchestrator`:

```python
# Before
from generic_orchestrator import GenericOrchestrator, AgentTask

orchestrator = GenericOrchestrator(
    output_dir=Path("./output"),
    max_parallel=5
)

# After - no other changes needed!
from collaborative_orchestrator import CollaborativeOrchestrator, run_traditional
from generic_orchestrator import AgentTask

orchestrator = CollaborativeOrchestrator(
    output_dir=Path("./output"),
    max_parallel=5
    # No collaboration_config = traditional mode
)

# Use traditional interface for backwards compatibility
results = await run_traditional(
    orchestrator=orchestrator,
    task_generator=generate_tasks,
    result_processor=process_results
)
```

### Strategy 2: Gradual Collaboration (Hybrid Mode)

Enable collaboration for specific tasks while keeping others traditional:

```python
from collaborative_orchestrator import CollaborativeOrchestrator, CollaborativeTask

orchestrator = CollaborativeOrchestrator(
    output_dir=Path("./output"),
    max_parallel=5,
    collaboration_config=CollaborationConfig(
        enable_messaging=True,
        enable_shared_workspace=True
    )
)

# Enable hybrid mode
orchestrator.enable_hybrid_mode()

tasks = [
    # Traditional task (no changes)
    CollaborativeTask(
        task_id="individual_task",
        task_type="research",
        prompt="Research topic independently",
        collaboration_enabled=False  # Traditional execution
    ),

    # Collaborative task (new features)
    CollaborativeTask(
        task_id="team_task",
        task_type="synthesis",
        prompt="Synthesize research collaboratively",
        collaboration_enabled=True,  # Enable collaboration
        required_capabilities=["synthesis", "coordination"]
    )
]

results = await orchestrator.run_collaborative(tasks=tasks)
```

### Strategy 3: Full Collaboration

Enable all collaboration features for maximum team efficiency:

```python
from collaborative_orchestrator import (
    CollaborativeOrchestrator,
    CollaborativeTask,
    CollaborationConfig
)

# Full collaboration configuration
collaboration_config = CollaborationConfig(
    enable_messaging=True,
    enable_shared_workspace=True,
    enable_team_formation=True,
    team_formation_mode="skill-based",
    max_team_size=8,
    message_retention_hours=48,
    workspace_sync_interval=0.5
)

orchestrator = CollaborativeOrchestrator(
    output_dir=Path("./output"),
    max_parallel=5,
    collaboration_config=collaboration_config
)

# All tasks collaborative by default
tasks = [
    CollaborativeTask(
        task_id="research_team",
        task_type="research",
        prompt="Collaborative research with real-time sharing",
        collaboration_enabled=True,
        required_capabilities=["research", "analysis"],
        collaboration_mode="shared"  # Agents work together
    ),

    CollaborativeTask(
        task_id="review_team",
        task_type="review",
        prompt="Review and improve research findings",
        dependencies=["research_team"],
        collaboration_enabled=True,
        collaboration_mode="review"  # Review other agents' work
    )
]

results = await orchestrator.run_collaborative(tasks=tasks)
```

## Task Migration

### Traditional AgentTask → CollaborativeTask

```python
# Before: GenericOrchestrator AgentTask
from generic_orchestrator import AgentTask

task = AgentTask(
    task_id="analysis_task",
    task_type="analysis",
    prompt="Analyze data independently",
    dependencies=["data_collection"]
)

# After: CollaborativeOrchestrator CollaborativeTask
from collaborative_orchestrator import CollaborativeTask

task = CollaborativeTask(
    # Same base fields (backwards compatible)
    task_id="analysis_task",
    task_type="analysis",
    prompt="Analyze data with team collaboration",
    dependencies=["data_collection"],

    # New collaboration fields (optional)
    collaboration_enabled=True,
    required_capabilities=["analysis", "statistics"],
    collaboration_mode="shared",
    team_id="analytics_team"
)
```

## Configuration Options

### CollaborationConfig Parameters

```python
collaboration_config = CollaborationConfig(
    # Messaging system
    enable_messaging=True,              # Enable agent-to-agent messaging
    message_retention_hours=24,         # How long to keep messages

    # Shared workspaces
    enable_shared_workspace=True,       # Enable shared file workspaces
    workspace_sync_interval=1.0,        # Workspace sync frequency (seconds)

    # Team formation
    enable_team_formation=True,         # Enable intelligent team formation
    team_formation_mode="auto",         # auto, manual, skill-based
    max_team_size=10,                   # Maximum agents per team

    # Execution settings
    collaboration_timeout=300.0         # Max time for collaborative tasks
)
```

### Collaboration Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `shared` | Agents work together simultaneously | Brainstorming, collaborative analysis |
| `handoff` | Sequential task passing between agents | Pipeline processing, staged development |
| `review` | Agents review and improve others' work | Quality assurance, peer review |

## Advanced Features

### Manual Team Assignment

```python
# Assign specific agents to tasks
task = CollaborativeTask(
    task_id="specialized_task",
    task_type="architecture",
    prompt="Design system architecture",
    assigned_agents=["architect_001", "senior_dev_002"],
    team_id="architecture_team"
)
```

### Capability-Based Team Formation

```python
# Register agent capabilities
await orchestrator.register_collaborative_agent(
    agent_id="data_scientist_001",
    skills=["python", "machine_learning", "statistics"],
    specializations=["data_analysis", "model_training"]
)

# Task automatically matched to capable agents
task = CollaborativeTask(
    task_id="ml_analysis",
    task_type="analysis",
    prompt="Perform machine learning analysis",
    required_capabilities=["machine_learning", "statistics"],
    collaboration_mode="shared"
)
```

### Shared Workspace Usage

Agents automatically get access to shared workspaces:

```python
# In agent prompt, agents can use:
"""
SHARED WORKSPACE: /path/to/shared/workspace
You can read from and write to the shared workspace.
Other agents can see your changes in real-time.

Create files, share analysis, collaborate on documents.
"""
```

## Monitoring and Analytics

### Collaboration Insights

```python
results = await orchestrator.run_collaborative(tasks=tasks)

# Access collaboration analytics
print(f"Collaboration Events: {len(results['collaboration_events'])}")
print(f"Messages Exchanged: {len(results['message_history'])}")

# Event types: task_started, task_completed, message_sent, team_formed
for event in results['collaboration_events']:
    print(f"{event['timestamp']}: {event['event_type']} - {event['agent_id']}")
```

### Workspace Analysis

```python
# Collaboration summary saved automatically
summary_file = output_dir / "collaboration_summary.json"
with open(summary_file) as f:
    summary = json.load(f)

print(f"Active Agents: {len(summary['active_agents'])}")
print(f"Shared Workspaces: {summary['shared_workspaces']}")
print(f"Team Formations: {summary['team_assignments']}")
```

## Performance Considerations

### Resource Usage

- **Traditional Mode**: Zero overhead vs GenericOrchestrator
- **Collaborative Mode**: ~5-10% overhead for messaging and coordination
- **Shared Workspaces**: Additional disk I/O for file synchronization
- **Memory**: ~50MB additional for collaboration infrastructure

### Scaling Recommendations

| Agents | Mode | Max Parallel | Workspace Sync |
|--------|------|--------------|----------------|
| 1-5 | Any | 5 | 0.5s |
| 6-15 | Collaborative | 8 | 1.0s |
| 16-50 | Team-based | 10 | 2.0s |
| 50+ | Hybrid | 15 | 5.0s |

## Best Practices

### 1. Start Simple
```python
# Begin with backwards compatibility
orchestrator = CollaborativeOrchestrator(output_dir=output_dir)
# Existing code works unchanged
```

### 2. Gradual Adoption
```python
# Try hybrid mode first
orchestrator.enable_hybrid_mode()
# Mix collaborative and traditional tasks
```

### 3. Capability Matching
```python
# Define clear agent capabilities
required_capabilities=["python", "fastapi", "testing"]
# Enables optimal team formation
```

### 4. Appropriate Collaboration Modes
```python
# Use shared mode for brainstorming
collaboration_mode="shared"

# Use handoff mode for pipelines
collaboration_mode="handoff"

# Use review mode for quality assurance
collaboration_mode="review"
```

### 5. Monitor Performance
```python
# Track collaboration effectiveness
results = await orchestrator.run_collaborative(tasks)
effectiveness = len(results['collaboration_events']) / len(tasks)
print(f"Collaboration intensity: {effectiveness:.2f} events per task")
```

## Troubleshooting

### Common Issues

**Q: Tasks not collaborating as expected?**
- Ensure `collaboration_enabled=True` on tasks
- Check that `CollaborationConfig` has required features enabled
- Verify agents have compatible capabilities

**Q: Performance degradation?**
- Reduce `workspace_sync_interval` for less frequent syncing
- Use hybrid mode to limit collaborative tasks
- Check `max_team_size` isn't too large

**Q: Backwards compatibility broken?**
- Use `run_traditional()` function for existing code
- Don't set `collaboration_config` parameter
- Convert to `AgentTask` instead of `CollaborativeTask` if needed

**Q: Shared workspace not working?**
- Ensure `enable_shared_workspace=True` in config
- Check output directory permissions
- Verify workspace directory creation in logs

### Debug Mode

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check collaboration events
for event in results['collaboration_events']:
    if event['event_type'] == 'error':
        print(f"Collaboration error: {event}")
```

## Examples Repository

Complete examples available in:
- `examples/collaborative_orchestrator_example.py` - Full demonstration
- `examples/migration_examples/` - Step-by-step migration examples
- `examples/collaboration_patterns/` - Common collaboration patterns

## Support

For questions and issues:
1. Check the examples in `examples/collaborative_orchestrator_example.py`
2. Review this migration guide
3. Enable debug logging for detailed troubleshooting
4. File issues with collaboration logs and configuration

The CollaborativeOrchestrator maintains complete backwards compatibility while adding powerful collaboration features. Start with traditional mode and gradually adopt collaboration features as needed.
