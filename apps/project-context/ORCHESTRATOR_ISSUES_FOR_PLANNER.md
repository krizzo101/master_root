# EnhancedOrchestrator Issues Report for Planner Agent

## Critical Issues Preventing Phase 1 Completion

### 1. **Module Import Path Problems**

**Error:** `ModuleNotFoundError: No module named 'generic_orchestrator'`

**Location:** `/home/opsvi/master_root/apps/agent-orchestrator/src/enhanced_orchestrator.py` line 20

**Problem:** The EnhancedOrchestrator tries to import with relative import:
```python
from generic_orchestrator import (
    AgentTask,
    DependencyManager,
    GenericOrchestrator,
    MessageBus,
    TokenPool,
)
```

**Root Cause:** Import assumes same directory, but path resolution fails when called from project-context

**Evidence:**
- GenericOrchestrator imports successfully when tested from src/ directory
- Import fails when called from `/home/opsvi/master_root/apps/project-context/`
- Path issue, not missing module

### 2. **Missing ExecutionPlan Adapter**

**Error:** Import failure for `src.execution_plan.adapter`

**Problem in:** `/home/opsvi/master_root/apps/project-context/execute_phase1_completion.py` line 16
```python
from src.execution_plan.adapter import ExecutionPlanAdapter
```

**Investigation Needed:**
- ExecutionPlanAdapter location/existence
- Proper import path for adapter functionality
- Alternative adapter patterns if missing

### 3. **Dependency Deadlock Issue**

**Symptom:** GenericOrchestrator fallback reports "Dependencies not met" for all tasks

**Error:** `WARNING:src.generic_orchestrator:Possible deadlock: 5 tasks pending`

**Problem:**
- Tasks depend on `implement_base_pipeline` which is completed
- But orchestrator doesn't recognize completion from different execution session
- Cross-session dependency resolution failing

## File Structure Analysis

```
/home/opsvi/master_root/apps/agent-orchestrator/
├── src/
│   ├── enhanced_orchestrator.py          ❌ Import issues
│   ├── generic_orchestrator.py           ✅ Works fine
│   └── enhanced_orchestrator_integration.py
├── execution_plan_template.py            ✅ Available
├── src/execution_plan_parser.py          ✅ Available
└── [ExecutionPlanAdapter location?]      ❓ Unknown

/home/opsvi/master_root/apps/project-context/
├── execute_phase1_completion.py          ❌ Import errors
├── phase1_completion_plan.py             ✅ Available
└── monitor_multi_phase.py               ✅ Available
```

## Required Fixes for Planner Agent

### Fix 1: Import Path Resolution
**Location:** `enhanced_orchestrator.py` line 20

**Current:**
```python
from generic_orchestrator import (
    AgentTask,
    DependencyManager,
    GenericOrchestrator,
    MessageBus,
    TokenPool,
)
```

**Fix Options:**
```python
# Option A: Relative import
from .generic_orchestrator import (...)

# Option B: Absolute import
from src.generic_orchestrator import (...)

# Option C: Dynamic import with path handling
import sys
sys.path.append(os.path.dirname(__file__))
from generic_orchestrator import (...)
```

### Fix 2: ExecutionPlan Adapter Resolution
**Investigation required:** Find or create ExecutionPlanAdapter

**Search commands for planner:**
```bash
cd /home/opsvi/master_root/apps/agent-orchestrator
find . -name "*adapter*" -exec grep -l "ExecutionPlan" {} \;
grep -r "class.*ExecutionPlanAdapter" .
grep -r "ExecutionPlanAdapter" . --include="*.py"
```

**If missing:** Create minimal adapter or use alternative conversion pattern

### Fix 3: Cross-Session Dependency Resolution
**Problem:** Orchestrator doesn't recognize completed tasks from previous sessions

**Solutions:**
1. **Task Status Persistence:** Modify orchestrator to check completed task files
2. **Dependency Override:** Skip completed dependencies
3. **Session Bridging:** Load previous session results

**Implementation pattern:**
```python
def check_completed_dependencies(task_id, dependencies):
    """Check if dependencies completed in previous sessions"""
    completed_dir = Path("phase1_execution_output/tasks")
    if not completed_dir.exists():
        return False

    for dep in dependencies:
        dep_file = completed_dir / f"{dep}.json"
        if dep_file.exists():
            # Verify completion status
            with open(dep_file) as f:
                data = json.load(f)
                if data.get('status') != 'completed':
                    return False
        else:
            return False
    return True
```

## Testing Commands for Planner

### Test Import Fixes
```bash
cd /home/opsvi/master_root/apps/agent-orchestrator/src
python -c "from enhanced_orchestrator import EnhancedOrchestrator; print('Success')"

cd /home/opsvi/master_root/apps/project-context
python -c "import sys; sys.path.append('../apps/agent-orchestrator/src'); from enhanced_orchestrator import EnhancedOrchestrator; print('Success')"
```

### Test Execution Plan Conversion
```bash
cd /home/opsvi/master_root/apps/project-context
python -c "
from phase1_completion_plan import create_phase1_completion_plan
plan = create_phase1_completion_plan()
print(f'Plan has {len(plan.tasks)} tasks, {len(plan.phases)} phases')
"
```

### Verify Completed Dependencies
```bash
cd /home/opsvi/master_root/apps/project-context
ls -la phase1_execution_output/tasks/implement_base_pipeline.json
jq '.status' phase1_execution_output/tasks/implement_base_pipeline.json
```

## Impact Analysis

### Lost Functionality with GenericOrchestrator Fallback:
- ❌ **Stage-based execution** (4 stages designed by planner)
- ❌ **Deterministic session IDs** for monitoring
- ❌ **Quality gates** validation
- ❌ **Enhanced error handling** and retry logic
- ❌ **Performance optimizations**
- ❌ **Cross-session dependency resolution**

### Benefits of Fixed EnhancedOrchestrator:
- ✅ **25% faster execution** with stage optimization
- ✅ **Predictable monitoring** with deterministic IDs
- ✅ **Quality validation** before phase transitions
- ✅ **Robust error handling** with circuit breakers
- ✅ **Production-ready execution** with monitoring

## Priority Actions for Planner

1. **CRITICAL:** Fix import paths in `enhanced_orchestrator.py`
2. **HIGH:** Resolve ExecutionPlanAdapter dependency
3. **HIGH:** Implement cross-session dependency checking
4. **MEDIUM:** Test complete execution flow
5. **LOW:** Optimize error handling and monitoring

## Current Workaround Status

**Fallback Execution:** Generic orchestrator fails with dependency deadlock
**Root Issue:** Cannot recognize that `implement_base_pipeline` completed in previous session
**Result:** All 5 remaining tasks marked as "Dependencies not met"

## Success Criteria for Fix

✅ **Import Resolution:** `from src.enhanced_orchestrator import EnhancedOrchestrator` works
✅ **Adapter Resolution:** ExecutionPlanAdapter converts plans to enhanced tasks
✅ **Dependency Recognition:** Completed tasks from previous session recognized
✅ **Stage Execution:** 4-stage execution with proper parallelization
✅ **Quality Gates:** Validation gates executed at stage transitions
✅ **Monitoring:** Deterministic session IDs enable predictable monitoring

**Expected Result:** Phase 1 completion in ~6 hours with 25% optimization vs sequential execution

---

**File Location:** `/home/opsvi/master_root/apps/project-context/ORCHESTRATOR_ISSUES_FOR_PLANNER.md`

**Status:** Ready for planner agent to diagnose and fix import/dependency issues
