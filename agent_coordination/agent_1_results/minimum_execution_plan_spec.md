# MINIMUM EXECUTION PLAN SPECIFICATION

**Agent 1 Final Deliverable**
**Date**: 2025-09-04
**Based on**: Actual testing of working orchestrator capabilities

## CURRENT SYSTEM CAPABILITIES

The GenericOrchestrator can successfully execute ExecutionPlan-like structures with these constraints:

## MINIMAL WORKING EXECUTIONPLAN FORMAT

```json
{
  "plan_id": "unique_plan_identifier",
  "name": "Human Readable Plan Name",
  "description": "What this plan accomplishes",
  "tasks": [
    {
      "task_id": "unique_task_id",
      "task_type": "agent_type",
      "prompt": "Detailed task description",
      "dependencies": ["prerequisite_task_id"],
      "context": {}
    }
  ]
}
```

## SUPPORTED FIELDS

### Plan Level
- ✅ `plan_id`: Plan identifier
- ✅ `name`: Plan name
- ✅ `description`: Plan description
- ✅ `tasks`: Array of task definitions

### Task Level
- ✅ `task_id`: Unique task identifier
- ✅ `task_type`: Agent type (maps to Claude agent selection)
- ✅ `prompt`: Task description/instructions
- ✅ `dependencies`: Array of task IDs this task depends on
- ✅ `context`: Additional task context (passed as metadata)

## EXECUTION BEHAVIOR

### Dependency Resolution
- ✅ Tasks wait for all dependencies to complete before starting
- ✅ Circular dependencies prevented (would fail execution)
- ✅ Independent tasks can run in parallel

### Task Execution
- ✅ Each task creates one Claude conversation
- ✅ Results captured in structured JSON format
- ✅ Status tracking: `pending` → `running` → `completed`/`failed`

### Output Format
```json
{
  "task_id": "task_identifier",
  "status": "completed",
  "result": {
    "type": "result",
    "duration_ms": 27140,
    "content": "Task output here...",
    "session_id": "claude_session_id"
  }
}
```

## CURRENT LIMITATIONS

### Not Supported Yet
- ❌ Execution modes (parallel/sequential/mixed)
- ❌ Quality gates validation
- ❌ Plan phases or stages
- ❌ Plan-level configuration
- ❌ Plan resumption/recovery
- ❌ Advanced monitoring

### Workarounds Available
- **Execution control**: Use dependencies to force sequential execution
- **Validation**: Manual result inspection post-execution
- **Monitoring**: Check log files and JSON outputs

## CONVERSION PROCESS

**ExecutionPlan JSON** → **AgentTask objects** → **GenericOrchestrator.execute_batch()**

```python
# Minimal conversion example
def convert_plan_to_tasks(execution_plan):
    tasks = []
    for task_data in execution_plan["tasks"]:
        task = AgentTask(
            task_id=task_data["task_id"],
            task_type=task_data["task_type"],
            prompt=task_data["prompt"],
            dependencies=task_data.get("dependencies", []),
            context=task_data.get("context", {})
        )
        tasks.append(task)
    return tasks
```

## RECOMMENDED USAGE

### For Agent 3 Implementation
1. Start with this minimal spec
2. Build validation for required fields
3. Implement the conversion function
4. Extend with additional ExecutionPlan features

### For Immediate Use
Current orchestrator can execute ExecutionPlan-like structures by:
1. Converting JSON to AgentTask objects
2. Using GenericOrchestrator.execute_batch()
3. Processing results as needed

## TESTING EVIDENCE

All functionality confirmed by `basic_functionality_tests.py`:
- ✅ Task creation from plan structure
- ✅ Dependency resolution
- ✅ Parallel and sequential execution
- ✅ Result capture and formatting

**Confidence**: High - Tested with working examples
