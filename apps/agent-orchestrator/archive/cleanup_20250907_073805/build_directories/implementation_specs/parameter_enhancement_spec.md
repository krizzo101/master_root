# Parameter Enhancement Specification

## Overview
This specification details the implementation of new parameters for dynamic agent architecture support while maintaining strict backward compatibility.

## Critical Safety Requirements
- **ALL new parameters MUST be optional with sensible defaults**
- **NO modifications to TokenPool parameters or behavior**
- **NO breaking changes to existing parameter signatures**
- **Must pass all existing tests without modification**

## Parameter Additions by Orchestrator

### 1. GenericOrchestrator Parameters

**File**: `src/generic_orchestrator.py`
**Function**: `__init__` (line 171-177)

#### Current Signature
```python
def __init__(
    self,
    output_dir: Path,
    max_parallel: int = 10,
    tokens: List[str] = None,
    use_optimizations: bool = True,
):
```

#### Enhanced Signature
```python
def __init__(
    self,
    output_dir: Path,
    max_parallel: int = 10,
    tokens: List[str] = None,
    use_optimizations: bool = True,
    # New parameters for dynamic architecture
    master_mcp_registry_path: Optional[Path] = None,
    agent_execution_profile: str = "standard",  # standard, minimal, research, full
    agent_debug_mode: bool = False,
    agent_base_work_dir: Optional[Path] = None,
    enable_dynamic_configs: bool = False,
    log_to_work_dir: bool = False,
):
```

#### Implementation Details
```python
# Add after line 179 (after output_dir setup)
self.master_mcp_registry_path = master_mcp_registry_path
self.agent_execution_profile = agent_execution_profile
self.agent_debug_mode = agent_debug_mode
self.agent_base_work_dir = agent_base_work_dir or output_dir / "agent_workspaces"
self.enable_dynamic_configs = enable_dynamic_configs
self.log_to_work_dir = log_to_work_dir

# Create agent work directory if needed
if self.enable_dynamic_configs:
    self.agent_base_work_dir.mkdir(parents=True, exist_ok=True)
```

### 2. UnifiedOrchestrator Parameters

**File**: `src/unified/unified_orchestrator.py`
**Class**: `UnifiedConfig` (line 65-113)

#### Current UnifiedConfig Fields
```python
@dataclass
class UnifiedConfig:
    output_dir: Path
    max_parallel: int = 10
    tokens: List[str] = None
    use_optimizations: bool = True
    # ... existing fields
```

#### Enhanced UnifiedConfig Fields
```python
@dataclass
class UnifiedConfig:
    # Existing fields
    output_dir: Path
    max_parallel: int = 10
    tokens: List[str] = None
    use_optimizations: bool = True

    # New dynamic architecture fields (add after line 83)
    master_mcp_registry_path: Optional[Path] = None
    agent_execution_profile: str = "standard"
    agent_debug_mode: bool = False
    agent_base_work_dir: Optional[Path] = None
    enable_dynamic_configs: bool = False
    log_to_work_dir: bool = False

    # Existing feature flags and other fields...
```

### 3. Enhanced Orchestrator Parameters

**File**: `src/enhanced_orchestrator.py` (if exists)
**Function**: `__init__`

#### Add Parameters (with defaults to maintain compatibility)
```python
def __init__(
    self,
    # ... existing parameters ...
    # New optional parameters at end
    master_mcp_registry_path: Optional[Path] = None,
    agent_execution_profile: str = "standard",
    agent_debug_mode: bool = False,
    agent_base_work_dir: Optional[Path] = None,
    enable_dynamic_configs: bool = False,
    log_to_work_dir: bool = False,
):
```

## Parameter Descriptions

### master_mcp_registry_path
- **Type**: `Optional[Path]`
- **Default**: `None`
- **Purpose**: Path to master MCP registry JSON file
- **Usage**: When provided, load MCP config from this file instead of generating minimal config
- **Integration Point**: Line 223 in generic_orchestrator.py

### agent_execution_profile
- **Type**: `str`
- **Default**: `"standard"`
- **Options**: `"minimal"`, `"standard"`, `"research"`, `"full"`
- **Purpose**: Determines which MCP servers to include in agent configs
- **Profiles**:
  - `minimal`: Only essential tools (shell_exec, time)
  - `standard`: Common tools (web_search, firecrawl, research_papers)
  - `research`: All research tools
  - `full`: All available MCP servers

### agent_debug_mode
- **Type**: `bool`
- **Default**: `False`
- **Purpose**: Enable debug logging and --debug flag for agents
- **Effect**: Adds `--debug` to claude command when True

### agent_base_work_dir
- **Type**: `Optional[Path]`
- **Default**: `None` (falls back to `output_dir/agent_workspaces`)
- **Purpose**: Base directory for agent-specific working directories
- **Usage**: Each agent gets `agent_base_work_dir/{task_id}/`

### enable_dynamic_configs
- **Type**: `bool`
- **Default**: `False`
- **Purpose**: Enable dynamic MCP config and workspace generation per agent
- **Effect**: Creates separate MCP configs and workspaces for each agent

### log_to_work_dir
- **Type**: `bool`
- **Default**: `False`
- **Purpose**: Redirect agent logs to their working directories
- **Effect**: Logs go to `{agent_work_dir}/agent.log` instead of central location

## Integration Points

### 1. MCP Config Loading (generic_orchestrator.py)

**Location**: Line 223-261
**Modification**:
```python
if use_optimizations:
    # NEW: Check for master registry first
    if self.master_mcp_registry_path and self.master_mcp_registry_path.exists():
        # Load from master registry
        with open(self.master_mcp_registry_path) as f:
            mcp_config = json.load(f)

        # Filter based on execution profile
        if self.agent_execution_profile != "full":
            mcp_config = self._filter_mcp_by_profile(
                mcp_config,
                self.agent_execution_profile
            )
    else:
        # Existing minimal research config
        research_config = Path(self.output_dir) / "research_mcp.json"
        minimal_research_config = { ... }  # existing code
```

### 2. Agent Execution (execute_agent method)

**Location**: Line 278-385
**Modifications**:

#### Dynamic Working Directory
```python
# Add after line 280 (session_id creation)
if self.enable_dynamic_configs:
    agent_work_dir = self.agent_base_work_dir / task.task_id
    agent_work_dir.mkdir(parents=True, exist_ok=True)

    # Generate agent-specific MCP config
    agent_mcp_config = agent_work_dir / "mcp_config.json"
    self._generate_agent_mcp_config(task, agent_mcp_config)
else:
    agent_work_dir = self.output_dir
```

#### Debug Mode Integration
```python
# Modify command building (around line 294)
cmd = self.claude_cmd.copy()

# Add debug flag if enabled
if self.agent_debug_mode:
    cmd.append("--debug")
```

#### Working Directory Parameter
```python
# Modify subprocess execution (line 333)
process = await asyncio.create_subprocess_exec(
    *cmd,
    env=env,
    cwd=str(agent_work_dir) if self.enable_dynamic_configs else None,  # NEW
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
)
```

### 3. Profile Filtering Function

**New Function** (add after line 276):
```python
def _filter_mcp_by_profile(self, config: Dict, profile: str) -> Dict:
    """Filter MCP config based on execution profile."""

    profile_servers = {
        "minimal": ["shell_exec", "time"],
        "standard": ["shell_exec", "time", "web_search", "firecrawl", "research_papers"],
        "research": ["shell_exec", "time", "web_search", "firecrawl",
                    "research_papers", "tech_docs", "knowledge"],
        "full": None  # Include all
    }

    if profile == "full" or profile not in profile_servers:
        return config

    allowed = profile_servers[profile]
    filtered = {
        "mcpServers": {
            k: v for k, v in config.get("mcpServers", {}).items()
            if k in allowed
        }
    }

    return filtered
```

## Backward Compatibility Matrix

| Scenario | Current Behavior | With New Parameters | Result |
|----------|------------------|---------------------|---------|
| No parameters changed | Works | Works (uses defaults) | ✓ Compatible |
| Only tokens provided | Works | Works | ✓ Compatible |
| Old test suite | Passes | Passes | ✓ Compatible |
| Existing scripts | Run | Run unchanged | ✓ Compatible |

## Testing Requirements

### Unit Tests to Add

1. **Parameter Default Tests**
   ```python
   def test_parameter_defaults():
       orch = GenericOrchestrator(output_dir=Path("/tmp/test"))
       assert orch.agent_execution_profile == "standard"
       assert orch.agent_debug_mode == False
       assert orch.enable_dynamic_configs == False
   ```

2. **Profile Filtering Tests**
   ```python
   def test_profile_filtering():
       # Test each profile filters correctly
   ```

3. **Dynamic Config Tests**
   ```python
   def test_dynamic_config_generation():
       # Test workspace creation
       # Test MCP config generation
   ```

### Integration Tests

1. Test with master registry
2. Test with different profiles
3. Test debug mode output
4. Test dynamic workspace creation

## Migration Guide

### For Existing Code
No changes required - all new parameters have defaults.

### For New Features
```python
# Example: Enable dynamic architecture
orchestrator = GenericOrchestrator(
    output_dir=Path("./output"),
    tokens=token_list,
    enable_dynamic_configs=True,
    agent_execution_profile="research",
    master_mcp_registry_path=Path("./master_mcp_registry.json")
)
```

## Validation Checklist

- [ ] All new parameters have default values
- [ ] No changes to required parameters
- [ ] TokenPool remains untouched
- [ ] Existing tests pass without modification
- [ ] New parameters properly initialized
- [ ] Debug logging doesn't break normal operation
- [ ] Profile filtering works correctly
- [ ] Dynamic configs generated properly
