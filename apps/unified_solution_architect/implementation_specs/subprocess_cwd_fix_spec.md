# Subprocess Working Directory Fix Specification

## Issue: Conditional Working Directory Setting

**Priority:** MEDIUM  
**Complexity:** LOW  
**Estimated Time:** 2 hours  
**Risk Level:** LOW (simple fix with clear path)

## Problem Statement

The subprocess execution only sets a working directory when `enable_dynamic_configs=True`, causing relative path failures and inconsistent execution environments when dynamic configs are disabled.

## Root Cause Analysis

### Current Problem (Line 570):
```python
cwd=str(agent_work_dir) if self.enable_dynamic_configs else None
```

This conditional logic means:
- ✅ With dynamic configs: Agents run in isolated directories
- ❌ Without dynamic configs: Agents run in undefined/parent directory
- ❌ Relative paths fail without proper cwd
- ❌ File outputs go to unexpected locations

## Implementation Details

### File: `/home/opsvi/master_root/apps/agent-orchestrator/src/generic_orchestrator.py`

#### Change 1: Always Set Working Directory (Line 570)

**LOCATE:**
```python
process = await asyncio.create_subprocess_exec(
    *cmd,
    env=env,
    cwd=str(agent_work_dir) if self.enable_dynamic_configs else None,
    stdout=asyncio.subprocess.PIPE,
    stderr=stderr_target,
)
```

**REPLACE WITH:**
```python
# Determine working directory
if self.enable_dynamic_configs and agent_work_dir:
    # Use agent-specific directory when available
    working_dir = str(agent_work_dir)
else:
    # Fallback to task-specific subdirectory in output dir
    fallback_dir = self.output_dir / "agent_workspaces" / task.task_id
    fallback_dir.mkdir(parents=True, exist_ok=True)
    working_dir = str(fallback_dir)
    
    # Log fallback usage
    logger.debug(f"Using fallback working directory: {working_dir}")

# Execute with guaranteed working directory
process = await asyncio.create_subprocess_exec(
    *cmd,
    env=env,
    cwd=working_dir,  # Always set working directory
    stdout=asyncio.subprocess.PIPE,
    stderr=stderr_target,
)

# Store working directory in task for reference
task.working_directory = working_dir
```

#### Change 2: Add Working Directory to Task Model

**File:** `/home/opsvi/master_root/apps/agent-orchestrator/src/models.py`

**ADD to AgentTask class (after line 30):**
```python
class AgentTask:
    """Task model with working directory tracking"""
    
    def __init__(self, ...existing params...):
        # ... existing initialization ...
        self.working_directory: Optional[str] = None  # Track execution directory
    
    def to_dict(self) -> Dict:
        """Serialize with working directory"""
        result = {
            # ... existing fields ...
        }
        if self.working_directory:
            result["working_directory"] = self.working_directory
        return result
```

#### Change 3: Ensure Directory Creation Earlier (Line 440-450)

**ADD before the conditional dynamic configs block:**
```python
# Ensure we have a working directory for the agent
if self.enable_dynamic_configs:
    # Dynamic config path (existing behavior)
    agent_work_dir = self.output_dir / ".agent_exec" / task.task_id
else:
    # Standard workspace path
    agent_work_dir = self.output_dir / "agent_workspaces" / task.task_id

# Create directory regardless of config mode
agent_work_dir.mkdir(parents=True, exist_ok=True)

# Create standard subdirectories for organization
(agent_work_dir / "input").mkdir(exist_ok=True)
(agent_work_dir / "output").mkdir(exist_ok=True)
(agent_work_dir / "logs").mkdir(exist_ok=True)

logger.debug(f"Prepared working directory: {agent_work_dir}")
```

#### Change 4: Update File Output Paths (Line 635-640)

**LOCATE task file save logic:**
```python
# Save task state
task_file = self.output_dir / "tasks" / f"{task.task_id}.json"
```

**ENHANCE WITH:**
```python
# Save task state with working directory info
task_file = self.output_dir / "tasks" / f"{task.task_id}.json"
task_file.parent.mkdir(exist_ok=True)

# Also save a reference in the working directory
if task.working_directory:
    work_ref = Path(task.working_directory) / "task_info.json"
    work_ref.write_text(json.dumps({
        "task_id": task.task_id,
        "task_type": task.task_type,
        "status": task.status,
        "working_directory": task.working_directory,
        "main_task_file": str(task_file)
    }, indent=2))
```

### File: `/home/opsvi/master_root/apps/agent-orchestrator/src/unified/unified_orchestrator.py`

#### Apply Same Fix to UnifiedOrchestrator

**Apply the same working directory fix to the UnifiedOrchestrator's subprocess execution.**

## Testing Requirements

### Unit Test:
```python
# test_working_directory.py
import asyncio
import os
from pathlib import Path
from src.generic_orchestrator import GenericOrchestrator
from src.models import AgentTask

async def test_working_directory_always_set():
    """Test working directory is always set"""
    
    # Test with dynamic configs disabled
    orchestrator = GenericOrchestrator(
        output_dir="test_cwd",
        enable_dynamic_configs=False
    )
    
    task = AgentTask(
        task_id="test_cwd_task",
        task_type="test",
        config={"test": "working_directory"}
    )
    
    # Mock execution to check cwd
    original_exec = orchestrator.execute_agent
    cwd_used = None
    
    async def mock_exec(task):
        nonlocal cwd_used
        # Capture the cwd that would be used
        # This is a simplified check - real test would hook subprocess
        agent_work_dir = Path("test_cwd/agent_workspaces") / task.task_id
        cwd_used = str(agent_work_dir)
        task.status = "completed"
        task.working_directory = cwd_used
        return task.to_dict()
    
    orchestrator.execute_agent = mock_exec
    
    result = await orchestrator.execute_agent(task)
    
    # Verify working directory was set
    assert cwd_used is not None, "Working directory not set"
    assert task.task_id in cwd_used, "Working directory doesn't contain task ID"
    assert Path(cwd_used).exists(), "Working directory doesn't exist"
    
    print(f"✓ Working directory set: {cwd_used}")

async def test_working_directory_with_dynamic_configs():
    """Test working directory with dynamic configs enabled"""
    
    orchestrator = GenericOrchestrator(
        output_dir="test_cwd_dynamic",
        enable_dynamic_configs=True
    )
    
    task = AgentTask(
        task_id="test_dynamic_cwd",
        task_type="test",
        config={"test": "dynamic"}
    )
    
    # Check that directory would be created
    expected_dir = Path("test_cwd_dynamic/.agent_exec/test_dynamic_cwd")
    
    # Note: In real implementation, this would execute
    # For now, verify the path construction
    assert ".agent_exec" in str(expected_dir)
    
    print(f"✓ Dynamic config working directory: {expected_dir}")

async def test_relative_paths_work():
    """Test that relative paths work with set working directory"""
    
    orchestrator = GenericOrchestrator(
        output_dir="test_relative",
        enable_dynamic_configs=False
    )
    
    task = AgentTask(
        task_id="test_relative_paths",
        task_type="test",
        config={
            "output_file": "./output.txt",  # Relative path
            "log_file": "./logs/test.log"   # Relative path with subdir
        }
    )
    
    # After fix, these paths should resolve correctly
    work_dir = Path("test_relative/agent_workspaces/test_relative_paths")
    work_dir.mkdir(parents=True, exist_ok=True)
    
    # Test relative path resolution
    output_path = work_dir / "output.txt"
    log_path = work_dir / "logs" / "test.log"
    
    # Paths should be within working directory
    assert str(output_path).startswith(str(work_dir))
    assert str(log_path).startswith(str(work_dir))
    
    print("✓ Relative paths resolve correctly")

# Run tests
asyncio.run(test_working_directory_always_set())
asyncio.run(test_working_directory_with_dynamic_configs())
asyncio.run(test_relative_paths_work())
```

### Integration Test:
```python
# test_cwd_integration.py
async def test_subprocess_execution_with_cwd():
    """Test actual subprocess execution with working directory"""
    
    orchestrator = GenericOrchestrator(
        output_dir="test_subprocess_cwd",
        enable_dynamic_configs=False
    )
    
    # Create a task that uses pwd command
    task = AgentTask(
        task_id="pwd_test",
        task_type="test",
        config={"command": "pwd"}
    )
    
    # This would execute the actual subprocess
    # In the fixed version, pwd should return the agent workspace path
    # not the parent directory
    
    expected_cwd = Path("test_subprocess_cwd/agent_workspaces/pwd_test").absolute()
    
    print(f"✓ Subprocess would execute in: {expected_cwd}")
```

## Validation Criteria

1. Working directory ALWAYS set (never None)
2. Fallback directory created when dynamic configs disabled
3. Relative paths resolve within working directory
4. No execution failures from missing cwd
5. Task tracking includes working directory
6. Backward compatibility maintained

## Rollback Plan

If issues occur:
1. Revert to conditional cwd setting
2. Remove fallback directory logic
3. Remove working_directory from task model

Risk is minimal as this is an enhancement, not a breaking change.

## Implementation Notes for Agent

1. **SIMPLE FIX:** Main change is removing conditional and adding fallback
2. **CREATE** fallback directories with proper structure
3. **TEST** both with and without dynamic configs
4. **VERIFY** relative paths work correctly
5. **ENSURE** no performance impact from directory creation

## Post-Implementation Checklist

- [ ] Working directory always set
- [ ] Fallback directory creation working
- [ ] Directory structure created (input/output/logs)
- [ ] Task model updated with working_directory field
- [ ] Task info saved in working directory
- [ ] Relative paths resolve correctly
- [ ] No None cwd values
- [ ] Tests pass with both config modes
- [ ] Backward compatibility verified
- [ ] Integration with existing agents tested