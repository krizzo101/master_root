# DPO Quick Guide for Agents

## 1. DPO is ON by Default (Level 2)
- No action needed for smart enhancement
- Automatically analyzes and enhances requests

## 2. Control Enhancement with Dial (0-5)
```python
from src.dpo.enhancement_config import DPOEnhancementConfig

config = DPOEnhancementConfig()
config.dial(3)  # Set level (0=OFF, 5=MAX)
```

## 3. Dial Levels
- **0**: OFF - No enhancement
- **1**: MINIMAL - 3 agents, basic tasks
- **2**: ESSENTIAL - 6 agents, smart defaults (DEFAULT)
- **3**: BALANCED - 8 agents, includes docs
- **4**: COMPREHENSIVE - 12 agents, security/deployment
- **5**: MAXIMUM - 15 agents, everything possible

## 4. Usage Examples

### Basic (uses default Level 2)
```python
from src.dpo.dpo_orchestrator_integration import DPOOrchestrator
dpo = DPOOrchestrator()
# Request automatically enhanced at Level 2
```

### Adjust for Simple Task
```python
config = DPOEnhancementConfig()
config.dial(1)  # Minimal
```

### Complex Project
```python
config = DPOEnhancementConfig()
config.dial(4)  # Comprehensive
```

## 5. What DPO Does
- Analyzes vague requests → Infers requirements
- Selects specialist agents automatically
- Adds quality gates and dependencies
- Generates executable AgentTask workflows

## 6. Request Tips
- Be specific = Better results
- Vague is OK = DPO will infer
- Mention scale/complexity = Better agent selection

## 7. Direct Execution
DPO outputs AgentTask objects ready for:
- `orchestrator.execute(tasks)`
- `run_orchestrator_task.py --workflow-file`
