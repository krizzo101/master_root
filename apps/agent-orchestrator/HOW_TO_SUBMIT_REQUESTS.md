# How to Submit Requests to Orchestrator

## Method 1: CLI Script (Recommended)
```bash
cd /home/opsvi/master_root/apps/agent-orchestrator

# System documentation task
python scripts/run_orchestrator_task.py \
  --task-type system-documentation \
  --app-name "my-app" \
  --app-root "/path/to/app"

# Custom workflow from JSON file
python scripts/run_orchestrator_task.py \
  --workflow-file /path/to/workflow.json

# Resume interrupted task
python scripts/run_orchestrator_task.py \
  --resume-checkpoint checkpoint_12345
```

## Method 2: Python API
```python
from src.generic_orchestrator import GenericOrchestrator, AgentTask

# Create tasks
tasks = [
    AgentTask(
        task_id="001_analyze",
        task_type="requirements-analyst",
        prompt="Analyze requirements for REST API",
        dependencies=[]
    ),
    AgentTask(
        task_id="002_implement",
        task_type="development-specialist",
        prompt="Implement the API",
        dependencies=["001_analyze"]
    )
]

# Execute
orchestrator = GenericOrchestrator()
await orchestrator.execute(tasks)
```

## Method 3: With DPO Enhancement
```python
from src.dpo.dpo_orchestrator_integration import DPOOrchestrator
from src.dpo.enhancement_config import DPOEnhancementConfig

# Set enhancement level
config = DPOEnhancementConfig()
config.dial(3)  # Balanced level

# Submit request (DPO enhances it)
dpo = DPOOrchestrator()
request = "Build a task management system"
# DPO analyzes, enhances, and generates executable workflow
```

## Method 4: JSON Workflow File
Create `workflow.json`:
```json
{
  "workflow_name": "my_project",
  "tasks": [
    {
      "task_id": "001",
      "task_type": "development-specialist",
      "prompt": "Build feature X",
      "dependencies": []
    }
  ]
}
```

Then run:
```bash
python scripts/run_orchestrator_task.py --workflow-file workflow.json
```

## Output Location
Results go to: `outputs/{task_type}_{timestamp}/`

## Available Task Types
- `system-documentation` - Generate complete docs
- `system-analysis` - Analyze codebase
- Custom workflows via JSON
