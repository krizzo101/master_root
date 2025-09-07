# Agent Manager Template & Guidelines

**For agents using the orchestrator to manage other agents**

## 🎯 Core Principle: Agent-First Design
Build for **agent consumption**, not human interfaces. All monitoring, status, and communication should be **programmatically accessible**.

---

## 📋 Pre-Launch Checklist

### 1. **Pre-Define Agent UUIDs** ⚠️ CRITICAL
```python
import uuid

# Generate UUIDs BEFORE launching agents
agent_uuids = {
    "database_specialist": str(uuid.uuid4()),
    "migration_agent": str(uuid.uuid4()),
    "integration_tester": str(uuid.uuid4())
}

# Pass UUIDs to orchestrator
for task in tasks:
    task.session_id = agent_uuids[task.task_id]
```

**Why**: Enables precise monitoring of specific agent logs instead of searching/guessing.

### 2. **Define Monitoring Strategy**
```python
monitoring_config = {
    "check_interval": 15,  # seconds
    "log_paths": [f"~/.claude/projects/-{cwd}/{uuid}.jsonl" for uuid in agent_uuids.values()],
    "health_checks": ["context_usage", "duration", "progress", "errors"],
    "escalation_thresholds": {
        "context_usage": 0.9,
        "max_duration_multiplier": 1.25,
        "error_count": 3
    }
}
```

### 3. **Prepare Resource Conflict Matrix**
```python
resource_matrix = {
    "database_specialist": ["postgresql", "port_5432"],
    "migration_agent": ["postgresql", "context_items_populator.py"],
    "integration_tester": ["postgresql", "port_8080"]
}
# Alert if multiple agents claim same resource
```

---

## 🔄 Execution Pattern

### Phase 1: Launch with Monitoring
```python
# 1. Launch orchestrator in background
orchestrator_process = launch_orchestrator_background(tasks)

# 2. Immediately start monitoring
monitor_task = asyncio.create_task(monitor_agent_progress(agent_uuids))

# 3. Define quality gates
gates = define_quality_gates(tasks)
```

### Phase 2: Real-Time Management
```python
async def manage_agents():
    while not all_agents_complete():
        # Check each agent's status
        for agent_id, uuid in agent_uuids.items():
            status = await get_agent_status(uuid)

            # Automated responses
            if status.context_usage > 0.9:
                await initiate_handoff(agent_id, uuid)
            if status.duration > expected_duration * 1.25:
                await escalate_stuck_agent(agent_id)
            if status.errors > 2:
                await investigate_agent_errors(agent_id, uuid)

        await asyncio.sleep(15)  # Check every 15 seconds
```

### Phase 3: Results Compilation
```python
async def compile_results():
    results = {}
    for agent_id, uuid in agent_uuids.items():
        # Get structured output
        results[agent_id] = await extract_agent_deliverables(uuid)

        # Validate quality gates
        if not validate_deliverable(results[agent_id]):
            await request_rework(agent_id)

    return synthesize_final_results(results)
```

---

## 📊 Agent Status API (Standard Format)

### Status Query Response
```json
{
    "agent_id": "database_specialist",
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "status": "running|completed|failed|stuck",
    "health": {
        "context_usage": 0.67,
        "duration_seconds": 1847,
        "expected_duration": 2700,
        "progress_indicators": ["step_1_complete", "step_2_in_progress"],
        "error_count": 0,
        "last_activity_seconds_ago": 23
    },
    "resources": {
        "claimed": ["postgresql", "port_5432"],
        "conflicts": []
    },
    "dependencies": {
        "waiting_for": [],
        "blocking": ["migration_agent", "integration_tester"]
    },
    "deliverables": {
        "expected": ["database_validation_report.json", "connection_test_results.json"],
        "completed": ["database_validation_report.json"],
        "missing": ["connection_test_results.json"]
    }
}
```

---

## 🚨 Automated Escalation Rules

### Context Window Management
```python
if agent_status.context_usage > 0.9:
    # Emergency handoff
    handoff_data = extract_agent_state(agent_uuid)
    new_agent_uuid = str(uuid.uuid4())
    spawn_successor_agent(handoff_data, new_agent_uuid)
    graceful_shutdown(agent_uuid)

elif agent_status.context_usage > 0.8:
    # Prepare for handoff
    notify_agent_prepare_handoff(agent_uuid)
```

### Duration Monitoring
```python
if agent_status.duration > expected_duration * 1.25:
    # Investigate why agent is stuck
    recent_activity = get_recent_agent_activity(agent_uuid)
    if not recent_activity:
        escalate_stuck_agent(agent_id)
    else:
        extend_expected_duration(agent_id, recent_activity)
```

### Error Handling
```python
if agent_status.error_count > 2:
    error_analysis = analyze_agent_errors(agent_uuid)
    if error_analysis.is_recoverable:
        provide_error_guidance(agent_uuid, error_analysis.solution)
    else:
        terminate_and_restart_agent(agent_uuid)
```

---

## 🔗 Inter-Agent Communication Protocol

### Result Passing
```python
# Agent A completes, passes results to dependent Agent B
class AgentResultPackage:
    def __init__(self, source_agent_id, deliverables, metadata):
        self.source = source_agent_id
        self.deliverables = deliverables  # File paths, data, configs
        self.metadata = metadata  # Context, instructions, warnings
        self.timestamp = datetime.utcnow()
        self.validation_hash = generate_hash(deliverables)

# Pass to dependent agents
await orchestrator.pass_results_to_dependents(result_package)
```

### Quality Gate Validation
```python
def validate_quality_gate(gate_name, agent_results):
    validation_rules = quality_gates[gate_name]

    for rule in validation_rules:
        if not rule.validate(agent_results):
            return QualityGateFailure(rule, agent_results)

    return QualityGateSuccess(gate_name)

# Example usage
gate_result = validate_quality_gate("database_ready", db_specialist_results)
if gate_result.passed:
    launch_dependent_agents(["migration_agent", "integration_tester"])
```

---

## 📁 File Structure Template

```
project/
├── orchestration_manager.py          # Main manager agent logic
├── agent_configs/                    # Task definitions
│   ├── database_specialist.json
│   ├── migration_agent.json
│   └── integration_tester.json
├── monitoring/                       # Agent monitoring tools
│   ├── status_api.py
│   ├── health_checker.py
│   └── log_analyzer.py
├── quality_gates/                    # Validation rules
│   ├── database_ready.py
│   ├── migration_complete.py
│   └── integration_validated.py
├── results/                          # Agent outputs
│   ├── agent_reports/
│   └── final_synthesis.json
└── logs/                            # Manager agent logs
    └── orchestration.log
```

---

## 🎯 Success Metrics for Manager Agents

### Orchestration KPIs
- **Agent Utilization**: % of time agents are productive vs waiting/stuck
- **Dependency Efficiency**: Average wait time for blocked agents
- **Quality Gate Success**: % of deliverables passing validation on first attempt
- **Context Efficiency**: Average context usage at handoff (target: 85%)
- **Error Recovery Rate**: % of agent errors resolved automatically

### Agent Health Metrics
- **Agent Lifespan**: Average productive time before handoff needed
- **Resource Conflict Rate**: Conflicts per 100 agent-hours
- **Escalation Rate**: % of agents requiring manual intervention
- **Handoff Success Rate**: % of successful agent-to-agent handoffs

---

## ⚠️ Common Pitfalls to Avoid

1. **UUID Generation**: Never generate UUIDs inside the orchestrator - always pre-define
2. **Resource Conflicts**: Always check resource matrix before parallel launches
3. **Context Monitoring**: Monitor context usage proactively, not reactively
4. **Quality Gates**: Define validation criteria before launching dependent agents
5. **Error Handling**: Plan for agent failures - don't assume success
6. **Human Interfaces**: Build for agent consumption, not human readability

---

## 🚀 Advanced Patterns

### Adaptive Agent Sizing
```python
# Adjust agent complexity based on available context
if available_context > 150000:
    task.complexity = "high"  # Can handle complex multi-step tasks
else:
    task.complexity = "focused"  # Single-purpose, direct tasks
```

### Dynamic Dependency Resolution
```python
# Adjust dependencies based on actual results
if database_validation.performance_issues:
    # Add performance tuning agent before migration
    insert_dependency("performance_tuner", before="migration_agent")
```

### Predictive Handoffs
```python
# Predict handoff needs before hitting limits
predicted_tokens = estimate_remaining_tokens(agent_uuid, current_task_progress)
if predicted_tokens > available_context * 0.9:
    schedule_preemptive_handoff(agent_uuid)
```

---

**This template ensures manager agents can orchestrate complex multi-agent workflows with full visibility and control.**
