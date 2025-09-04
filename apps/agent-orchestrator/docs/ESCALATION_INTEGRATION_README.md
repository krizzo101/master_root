# Escalation Integration Layer

This document describes the complete integration layer between the escalation system and the existing orchestrator framework.

## Overview

The escalation integration provides seamless integration of intelligent escalation capabilities into the existing orchestrator framework while maintaining full backward compatibility.

## Key Components

### 1. EscalationAwareOrchestrator

The main orchestrator class that extends `EnhancedOrchestrator` with escalation capabilities.

```python
from escalation_integration import EscalationAwareOrchestrator, EscalationConfig

# Create escalation-aware orchestrator
config = EscalationConfig(
    enable_escalation=True,
    failure_threshold=3,
    enable_auto_replacement=True,
    enable_sub_swarm_delegation=True,
)

orchestrator = EscalationAwareOrchestrator(
    output_dir=Path("./output"),
    escalation_config=config,
)
```

### 2. EscalationConfig

Configuration class for escalation system settings.

```python
config = EscalationConfig(
    enable_escalation=True,              # Enable/disable escalation system
    enable_auto_replacement=True,        # Auto-spawn replacement agents
    enable_sub_swarm_delegation=True,    # Enable specialized sub-teams
    enable_manager_takeover=True,        # Allow manager intervention
    failure_threshold=3,                 # Escalate after N failures
    context_threshold=0.90,              # Escalate at 90% context usage
    time_threshold=1800,                 # Escalate after 30 minutes
    auto_enhance_on_failure=True,        # Learn from failures
    learn_from_escalations=True,         # Improve over time
)
```

### 3. EscalationAwareTask

Enhanced task class with escalation parameters.

```python
# Create escalation-aware task
task = orchestrator.create_escalation_aware_task(
    task_id="complex_analysis",
    task_type="research",
    prompt="Analyze complex system architecture...",
    # Escalation parameters
    escalation_enabled=True,
    complexity_level="high",
    specialist_types=["architect", "researcher", "analyzer"],
    required_permissions=["file_access", "system_info"],
    required_tools=["code_analysis", "documentation_search"],
)
```

## Integration with AgentTeamManager

The `AgentTeamManager` has been extended to support escalation:

```python
from agent_team_manager import AgentTeamManager
from escalation_integration import EscalationConfig

# Create team manager with escalation support
config = EscalationConfig(enable_escalation=True)
manager = AgentTeamManager(
    output_dir=Path("./teams"),
    enable_escalation=True,
    escalation_config=config,
)

# Launch team with escalation-aware tasks
task_definitions = [
    {
        "task_id": "research_task",
        "task_type": "research",
        "prompt": "Research the topic...",
        "escalation_enabled": True,
        "complexity_level": "medium",
        "specialist_types": ["researcher", "analyst"],
    }
]

team_id = manager.launch_monitored_team(task_definitions)

# Monitor team with escalation information
async for status in manager.monitor_continuously(team_id):
    print(f"Team {team_id}: {status.status}")
    print(f"Escalations: {status.escalation_count}")
    print(f"Active escalations: {status.active_escalations}")

    if status.status == "completed":
        break

# Get escalation dashboard
dashboard = await manager.get_escalation_dashboard()
print("Escalation metrics:", dashboard.get("escalation_metrics", {}))
```

## Backward Compatibility

The integration maintains full backward compatibility:

### Existing GenericOrchestrator Code

```python
# This continues to work unchanged
from generic_orchestrator import GenericOrchestrator, AgentTask

orchestrator = GenericOrchestrator(output_dir=Path("./output"))

tasks = [AgentTask(task_id="test", task_type="test", prompt="Test task")]
result = await orchestrator.run(lambda: tasks)
```

### Existing EnhancedOrchestrator Code

```python
# This continues to work unchanged
from enhanced_orchestrator import EnhancedOrchestrator, EnhancedAgentTask

orchestrator = EnhancedOrchestrator(
    output_dir=Path("./output"),
    enable_quality_gates=True,
    enable_monitoring=True,
)

tasks = [EnhancedAgentTask(task_id="test", task_type="test", prompt="Test task")]
result = await orchestrator.execute_batch(tasks)
```

### Existing AgentTeamManager Code

```python
# This continues to work unchanged
from agent_team_manager import AgentTeamManager

manager = AgentTeamManager(
    output_dir=Path("./teams"),
    enable_escalation=False,  # Explicitly disable if not wanted
)

# All existing methods work the same
team_id = manager.launch_monitored_team(task_definitions)
```

## Factory Functions

Pre-configured orchestrators for common use cases:

### Development Orchestrator

```python
from escalation_integration import create_development_orchestrator

orchestrator = create_development_orchestrator(
    output_dir=Path("./dev_output"),
    enable_escalation=True,  # Optimized for development work
)
```

### Research Orchestrator

```python
from escalation_integration import create_research_orchestrator

orchestrator = create_research_orchestrator(
    output_dir=Path("./research_output"),
    enable_escalation=True,  # Optimized for research tasks
)
```

### Production Orchestrator

```python
from escalation_integration import create_production_orchestrator

orchestrator = create_production_orchestrator(
    output_dir=Path("./prod_output"),
    enable_escalation=True,  # Conservative settings for production
)
```

### Team Manager Factories

```python
from agent_team_manager import (
    create_database_migration_team_manager,
    create_web_service_team_manager,
)

# Database migration team with escalation
db_manager = create_database_migration_team_manager(
    output_dir=Path("./db_teams"),
    database_url="postgresql://localhost:5432/mydb",
    enable_escalation=True,
)

# Web service team with escalation
web_manager = create_web_service_team_manager(
    output_dir=Path("./web_teams"),
    api_endpoints=["http://api.example.com"],
    enable_escalation=True,
)
```

## Manager Agent APIs

Manager agents can control escalations through these APIs:

### Get Escalation Dashboard

```python
# Get system-wide escalation information
dashboard = await orchestrator.get_escalation_dashboard()

print("Escalation stats:", dashboard["escalation_metrics"])
print("Pending escalations:", dashboard["pending_escalations"])
print("Active agents:", dashboard["active_intelligent_agents"])
```

### Handle Manual Escalation

```python
# Manager manually escalates a problem
escalation_id = await orchestrator.handle_manual_escalation(
    task_id="stuck_task",
    escalation_type="sub_swarm",
    reason="complex_debugging",
    description="Task is stuck on complex analysis",
    specialist_types_needed=["debugger", "analyst", "solution_architect"],
    time_budget=900,
)
```

### Resolve Escalation

```python
# Manager resolves an escalation
success = await orchestrator.resolve_escalation(
    escalation_id="escalation_123",
    resolution_type="replacement_spawned",
    new_agent_capabilities=["enhanced_analysis", "extended_context"],
)
```

## Escalation Patterns

The system implements several intelligent escalation patterns:

### Pattern 1: Escalation to Manager

- Agent tries solution 3 times
- If still blocked, escalates to manager
- Manager analyzes problem and provides guidance or spawns enhanced replacement

### Pattern 2: Sub-Swarm Delegation

- Complex problems are delegated to specialized teams
- Sub-swarm consists of specialist agents (troubleshoot, research, test, solution)
- Results are coordinated and returned to original agent

### Pattern 3: Intelligent Replacement

- Failed agents are replaced with enhanced capabilities
- Enhancement patterns are learned from previous escalations
- New agent preserves context and avoids previous failures

## Configuration Examples

### Conservative Production Configuration

```python
production_config = EscalationConfig(
    enable_escalation=True,
    failure_threshold=5,                 # Higher threshold
    enable_auto_replacement=False,       # Manual approval required
    enable_sub_swarm_delegation=True,
    enable_manager_takeover=True,
    auto_enhance_on_failure=False,       # Conservative enhancement
    time_threshold=3600,                 # 1 hour timeout
)
```

### Aggressive Development Configuration

```python
dev_config = EscalationConfig(
    enable_escalation=True,
    failure_threshold=2,                 # Lower threshold
    enable_auto_replacement=True,        # Automatic replacements
    enable_sub_swarm_delegation=True,
    auto_enhance_on_failure=True,        # Learn aggressively
    learn_from_escalations=True,
    context_threshold=0.85,              # Earlier context escalation
    time_threshold=900,                  # 15 minute timeout
)
```

### Research-Optimized Configuration

```python
research_config = EscalationConfig(
    enable_escalation=True,
    failure_threshold=3,                 # Standard threshold
    enable_sub_swarm_delegation=True,    # Research benefits from teams
    context_threshold=0.95,              # Research needs more context
    time_threshold=1800,                 # 30 minutes for research
    specialist_types=["researcher", "analyst", "synthesizer"],
)
```

## Testing

Run the integration tests to verify everything works:

```bash
python test_escalation_integration.py
```

Tests cover:
- Backward compatibility with existing code
- EscalationAwareOrchestrator functionality
- AgentTeamManager integration
- Configuration options
- Factory functions

## Migration Guide

### Upgrading Existing Code

1. **No changes required for basic usage** - existing code continues to work

2. **To add escalation to existing orchestrators:**
   ```python
   # Before
   orchestrator = EnhancedOrchestrator(output_dir=path)

   # After
   from escalation_integration import EscalationAwareOrchestrator, EscalationConfig

   config = EscalationConfig(enable_escalation=True)
   orchestrator = EscalationAwareOrchestrator(
       output_dir=path,
       escalation_config=config,
   )
   ```

3. **To add escalation to existing team managers:**
   ```python
   # Before
   manager = AgentTeamManager(output_dir=path)

   # After
   manager = AgentTeamManager(
       output_dir=path,
       enable_escalation=True,
       escalation_config=EscalationConfig(enable_escalation=True),
   )
   ```

### Best Practices

1. **Start with escalation disabled** for testing
2. **Use conservative settings** for production systems
3. **Monitor escalation metrics** to tune thresholds
4. **Use factory functions** for common configurations
5. **Test escalation patterns** with non-critical tasks first

## Architecture

The integration layer follows these design principles:

1. **Non-breaking integration** - Existing code works unchanged
2. **Opt-in escalation** - Features are disabled by default
3. **Configurable behavior** - All aspects can be tuned
4. **Manager-side control** - Management agents can monitor and control escalations
5. **Learning system** - Enhancement patterns improve over time

## File Structure

```
apps/agent-orchestrator/
├── src/
│   ├── generic_orchestrator.py          # Base orchestrator (unchanged)
│   ├── enhanced_orchestrator.py         # Enhanced orchestrator (unchanged)
│   ├── escalation_manager.py            # Escalation system (unchanged)
│   ├── escalation_integration.py        # NEW: Integration layer
│   └── agent_team_manager.py            # Extended with escalation support
├── test_escalation_integration.py       # Integration tests
└── ESCALATION_INTEGRATION_README.md     # This documentation
```

## Summary

The escalation integration layer provides:

✅ **Complete backward compatibility** - existing code works unchanged
✅ **Intelligent escalation patterns** - automatic problem resolution
✅ **Manager-side control** - APIs for monitoring and control
✅ **Configurable behavior** - tune for different use cases
✅ **Factory functions** - pre-configured common setups
✅ **Learning system** - improves over time
✅ **Production ready** - conservative defaults and comprehensive testing

This integration enables existing orchestrator code to gain escalation capabilities simply by changing the orchestrator class, while providing full control over escalation behavior through configuration.
