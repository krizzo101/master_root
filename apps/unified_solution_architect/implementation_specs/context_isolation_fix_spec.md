# Context Isolation Fix Specification

## Issue: Agent Config Inheritance and Isolation Problems

**Priority:** HIGH  
**Complexity:** HIGH  
**Estimated Time:** 12 hours  
**Risk Level:** HIGH (can break existing workflows)

## Problem Statement

Agent tasks share configuration and environment context, causing cross-contamination between agents. Isolation only works when `enable_dynamic_configs=True`, leaving the default configuration vulnerable to context bleed.

## Root Cause Analysis

### Current Problems:
1. **Conditional Isolation:** Working directory only set when `enable_dynamic_configs=True`
2. **Shallow Config Copy:** Configurations not deep-copied between agents
3. **Shared Environment:** Environment variables persist across agents
4. **No Resource Namespacing:** Agents can interfere with each other's resources

### Critical Code Location:
```python
# Line 570 in generic_orchestrator.py
cwd=str(agent_work_dir) if self.enable_dynamic_configs else None
```

## Implementation Details

### Phase 1: Mandatory Agent Isolation

#### File: `/home/opsvi/master_root/apps/agent-orchestrator/src/generic_orchestrator.py`

**Change 1: Always Create Agent Workspace (Lines 441-477)**

**REPLACE:**
```python
# Create agent-specific working directory if using dynamic configs
if self.enable_dynamic_configs:
    agent_work_dir = self.output_dir / ".agent_exec" / task.task_id
    agent_work_dir.mkdir(parents=True, exist_ok=True)
```

**WITH:**
```python
# ALWAYS create agent-specific working directory for isolation
agent_work_dir = self.output_dir / ".agent_exec" / task.task_id
agent_work_dir.mkdir(parents=True, exist_ok=True)

# Clean up any previous runs
import shutil
if agent_work_dir.exists() and self.config.get("clean_workspace", True):
    shutil.rmtree(agent_work_dir)
    agent_work_dir.mkdir(parents=True, exist_ok=True)

# Create standard subdirectories
(agent_work_dir / "config").mkdir(exist_ok=True)
(agent_work_dir / "output").mkdir(exist_ok=True)
(agent_work_dir / "temp").mkdir(exist_ok=True)

logger.debug(f"Created isolated workspace: {agent_work_dir}")
```

**Change 2: Deep Copy Configuration (Line 445-460)**

**ADD AFTER agent_work_dir creation:**
```python
# Deep copy configuration to prevent contamination
import copy

# Create isolated config
isolated_config = copy.deepcopy(task.config) if task.config else {}

# Ensure config isolation
if "shared_resources" in isolated_config:
    # Remove shared resources from isolated config
    isolated_config["isolated_resources"] = isolated_config.pop("shared_resources")

# Add isolation metadata
isolated_config["isolation"] = {
    "workspace": str(agent_work_dir),
    "task_id": task.task_id,
    "isolated": True,
    "isolation_level": "full"
}

# Replace task config with isolated version
task.config = isolated_config
```

**Change 3: Environment Variable Isolation (Line 550-565)**

**REPLACE:**
```python
# Build environment with dynamic MCP config if enabled
env = os.environ.copy()

if self.enable_dynamic_configs and agent_mcp_config:
    env["MCP_CONFIG_PATH"] = str(agent_mcp_config)
    logger.info(f"Using agent-specific MCP config: {agent_mcp_config}")
```

**WITH:**
```python
# Build isolated environment for agent
import os

# Start with clean environment (minimal inheritance)
env = {
    # Essential system variables only
    "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
    "HOME": os.environ.get("HOME", "/tmp"),
    "USER": os.environ.get("USER", "agent"),
    "LANG": os.environ.get("LANG", "en_US.UTF-8"),
    "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
}

# Add Python path if needed
if "PYTHONPATH" in os.environ:
    env["PYTHONPATH"] = os.environ["PYTHONPATH"]

# Add agent-specific environment
env.update({
    "AGENT_TASK_ID": task.task_id,
    "AGENT_WORKSPACE": str(agent_work_dir),
    "AGENT_ISOLATION": "enabled",
    "AGENT_CONFIG_DIR": str(agent_work_dir / "config"),
    "AGENT_OUTPUT_DIR": str(agent_work_dir / "output"),
    "AGENT_TEMP_DIR": str(agent_work_dir / "temp"),
})

# Add MCP config if available
if agent_mcp_config:
    env["MCP_CONFIG_PATH"] = str(agent_mcp_config)
    logger.info(f"Using agent-specific MCP config: {agent_mcp_config}")

# Add task-specific environment overrides
if task.config and "environment" in task.config:
    # Sanitize and add task-specific env vars
    task_env = task.config["environment"]
    if isinstance(task_env, dict):
        for key, value in task_env.items():
            if key.startswith("AGENT_") or key in ["DEBUG", "VERBOSE"]:
                env[key] = str(value)

logger.debug(f"Created isolated environment with {len(env)} variables")
```

**Change 4: Fix Working Directory (Line 570)**

**REPLACE:**
```python
cwd=str(agent_work_dir) if self.enable_dynamic_configs else None,
```

**WITH:**
```python
cwd=str(agent_work_dir),  # Always use isolated workspace
```

### Phase 2: Resource Namespace Management

#### File: `/home/opsvi/master_root/apps/agent-orchestrator/src/models.py`

**ADD new class after AgentTask:**
```python
@dataclass
class IsolatedAgentTask(AgentTask):
    """
    Agent task with full isolation support
    """
    isolation_config: Dict[str, Any] = field(default_factory=dict)
    resource_namespace: str = ""
    environment_overrides: Dict[str, str] = field(default_factory=dict)
    workspace_path: Optional[Path] = None
    
    def __post_init__(self):
        super().__post_init__()
        # Generate unique namespace if not provided
        if not self.resource_namespace:
            import uuid
            self.resource_namespace = f"{self.task_id}_{uuid.uuid4().hex[:8]}"
    
    def get_isolated_path(self, relative_path: str) -> Path:
        """Get path within isolated workspace"""
        if self.workspace_path:
            return self.workspace_path / relative_path
        return Path(relative_path)
    
    def to_dict(self) -> Dict:
        """Serialize with isolation info"""
        result = super().to_dict()
        result.update({
            "isolation_config": self.isolation_config,
            "resource_namespace": self.resource_namespace,
            "environment_overrides": self.environment_overrides,
            "workspace_path": str(self.workspace_path) if self.workspace_path else None
        })
        return result
```

### Phase 3: Add Isolation Manager

#### File: `/home/opsvi/master_root/apps/agent-orchestrator/src/isolation_manager.py`

**CREATE NEW FILE:**
```python
"""
Isolation Manager for Agent Context Separation
"""
import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import copy
import tempfile
import json

logger = logging.getLogger(__name__)


class IsolationManager:
    """
    Manages isolation contexts for agent execution
    """
    
    def __init__(self, base_dir: Path, config: Dict[str, Any] = None):
        self.base_dir = Path(base_dir)
        self.config = config or {}
        self.active_contexts: Dict[str, Dict] = {}
        self.isolation_level = config.get("isolation_level", "full")
        
        # Create base isolation directory
        self.isolation_root = self.base_dir / ".isolation"
        self.isolation_root.mkdir(parents=True, exist_ok=True)
    
    def create_context(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create isolated execution context"""
        
        # Create unique workspace
        workspace = self.isolation_root / task_id
        workspace.mkdir(parents=True, exist_ok=True)
        
        # Set up directory structure
        dirs = {
            "config": workspace / "config",
            "data": workspace / "data",
            "output": workspace / "output",
            "temp": workspace / "temp",
            "logs": workspace / "logs"
        }
        
        for dir_path in dirs.values():
            dir_path.mkdir(exist_ok=True)
        
        # Create isolated config
        isolated_config = self._isolate_config(config)
        
        # Save config to workspace
        config_file = dirs["config"] / "task_config.json"
        config_file.write_text(json.dumps(isolated_config, indent=2))
        
        # Create context
        context = {
            "task_id": task_id,
            "workspace": workspace,
            "directories": dirs,
            "config": isolated_config,
            "environment": self._create_isolated_environment(task_id, workspace),
            "resources": self._allocate_resources(task_id),
            "created_at": os.path.getmtime(workspace)
        }
        
        self.active_contexts[task_id] = context
        logger.info(f"Created isolation context for {task_id}")
        
        return context
    
    def _isolate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create isolated configuration"""
        # Deep copy to prevent reference sharing
        isolated = copy.deepcopy(config)
        
        # Remove shared references
        keys_to_isolate = ["cache", "shared_state", "global_config"]
        for key in keys_to_isolate:
            if key in isolated:
                isolated[f"isolated_{key}"] = isolated.pop(key)
        
        # Add isolation markers
        isolated["_isolation"] = {
            "enabled": True,
            "level": self.isolation_level,
            "timestamp": os.times().elapsed
        }
        
        return isolated
    
    def _create_isolated_environment(self, task_id: str, workspace: Path) -> Dict[str, str]:
        """Create isolated environment variables"""
        env = {
            # Minimal system environment
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(workspace),
            "TMPDIR": str(workspace / "temp"),
            "TMP": str(workspace / "temp"),
            "TEMP": str(workspace / "temp"),
            
            # Agent-specific
            "AGENT_TASK_ID": task_id,
            "AGENT_WORKSPACE": str(workspace),
            "AGENT_ISOLATED": "true",
            "AGENT_ISOLATION_LEVEL": self.isolation_level
        }
        
        # Add Python environment if needed
        if "PYTHONPATH" in os.environ:
            # Create isolated Python path
            python_dir = workspace / "python"
            python_dir.mkdir(exist_ok=True)
            env["PYTHONPATH"] = f"{python_dir}:{os.environ['PYTHONPATH']}"
        
        return env
    
    def _allocate_resources(self, task_id: str) -> Dict[str, Any]:
        """Allocate isolated resources"""
        return {
            "namespace": f"isolated_{task_id}",
            "cpu_quota": self.config.get("cpu_quota", None),
            "memory_limit": self.config.get("memory_limit", None),
            "io_priority": self.config.get("io_priority", "normal"),
            "network_isolated": self.config.get("network_isolated", False)
        }
    
    def get_context(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get isolation context for task"""
        return self.active_contexts.get(task_id)
    
    def cleanup_context(self, task_id: str, preserve_output: bool = True):
        """Clean up isolation context"""
        context = self.active_contexts.get(task_id)
        if not context:
            return
        
        workspace = context["workspace"]
        
        if preserve_output:
            # Move output to permanent location
            output_dir = context["directories"]["output"]
            if output_dir.exists() and any(output_dir.iterdir()):
                preserve_dir = self.base_dir / "preserved" / task_id
                preserve_dir.mkdir(parents=True, exist_ok=True)
                shutil.copytree(output_dir, preserve_dir / "output", dirs_exist_ok=True)
                logger.info(f"Preserved output for {task_id} to {preserve_dir}")
        
        # Clean up workspace
        try:
            if workspace.exists():
                shutil.rmtree(workspace)
            del self.active_contexts[task_id]
            logger.info(f"Cleaned up isolation context for {task_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup context for {task_id}: {e}")
    
    def enforce_isolation(self, task_id: str) -> bool:
        """Enforce isolation constraints"""
        context = self.get_context(task_id)
        if not context:
            return False
        
        # Check workspace boundaries
        workspace = context["workspace"]
        if not workspace.exists():
            logger.error(f"Workspace violation for {task_id}: directory missing")
            return False
        
        # Verify no file access outside workspace
        # (This would need OS-level enforcement in production)
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get isolation manager statistics"""
        return {
            "active_contexts": len(self.active_contexts),
            "isolation_level": self.isolation_level,
            "contexts": list(self.active_contexts.keys()),
            "base_directory": str(self.base_dir),
            "total_workspaces": len(list(self.isolation_root.iterdir()))
        }
```

### Phase 4: Integration with Orchestrator

#### File: `/home/opsvi/master_root/apps/agent-orchestrator/src/generic_orchestrator.py`

**ADD at top of file:**
```python
from src.isolation_manager import IsolationManager
```

**ADD in __init__ method (after line 75):**
```python
# Initialize isolation manager
self.isolation_manager = IsolationManager(
    base_dir=self.output_dir,
    config={
        "isolation_level": "full",
        "clean_workspace": True,
        "preserve_output": True
    }
)
```

**MODIFY execute_agent method (Line 441):**
```python
# Create isolation context
isolation_context = self.isolation_manager.create_context(
    task.task_id,
    task.config or {}
)

# Use isolated workspace
agent_work_dir = Path(isolation_context["workspace"])
env = isolation_context["environment"]
task.config = isolation_context["config"]
```

**ADD cleanup in finally block (Line 630):**
```python
finally:
    # Clean up isolation context
    if hasattr(self, 'isolation_manager'):
        self.isolation_manager.cleanup_context(
            task.task_id,
            preserve_output=True
        )
```

## Testing Requirements

### Unit Test:
```python
# test_isolation.py
import asyncio
from pathlib import Path
from src.generic_orchestrator import GenericOrchestrator
from src.models import AgentTask

async def test_agent_isolation():
    """Test agent context isolation"""
    
    orchestrator = GenericOrchestrator(
        output_dir="test_isolation",
        enable_dynamic_configs=False  # Should still have isolation
    )
    
    # Create two tasks with conflicting configs
    task1 = AgentTask(
        task_id="task1",
        task_type="test",
        config={"shared_value": "task1_value", "environment": {"TEST_VAR": "1"}}
    )
    
    task2 = AgentTask(
        task_id="task2", 
        task_type="test",
        config={"shared_value": "task2_value", "environment": {"TEST_VAR": "2"}}
    )
    
    # Execute both tasks
    result1 = await orchestrator.execute_agent(task1)
    result2 = await orchestrator.execute_agent(task2)
    
    # Verify isolation
    assert task1.config["shared_value"] == "task1_value"
    assert task2.config["shared_value"] == "task2_value"
    
    # Check workspaces exist
    workspace1 = Path("test_isolation/.agent_exec/task1")
    workspace2 = Path("test_isolation/.agent_exec/task2")
    
    assert workspace1.exists()
    assert workspace2.exists()
    
    print("✓ Agent isolation working correctly")

asyncio.run(test_agent_isolation())
```

## Validation Criteria

1. **Every agent gets isolated workspace** regardless of config
2. **Configurations are deep-copied** preventing contamination
3. **Environment variables are isolated** per agent
4. **Working directory always set** to isolated workspace
5. **Resource namespacing** prevents conflicts
6. **Cleanup preserves outputs** while removing temp files

## Rollback Plan

1. Remove IsolationManager integration
2. Revert to conditional isolation
3. Remove deep copy operations
4. Restore original environment handling

## Implementation Notes for Agent

1. **CRITICAL:** Test with both `enable_dynamic_configs=True` and `False`
2. **IMPORTANT:** Verify no performance regression from deep copies
3. **REQUIRED:** Ensure backward compatibility with existing agents
4. **CHECK:** Validate file permissions in isolated workspaces
5. **TEST:** Run parallel agents to verify no interference

## Post-Implementation Checklist

- [ ] All agents get isolated workspaces
- [ ] Config deep copying implemented
- [ ] Environment isolation working
- [ ] Working directory always set
- [ ] IsolationManager integrated
- [ ] Cleanup preserves outputs
- [ ] No config contamination between agents
- [ ] Performance impact acceptable
- [ ] Backward compatibility maintained
- [ ] Integration tests pass