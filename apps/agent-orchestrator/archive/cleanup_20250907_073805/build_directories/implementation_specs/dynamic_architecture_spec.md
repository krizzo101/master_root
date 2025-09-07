# Dynamic Architecture Specification

## Overview
This specification details the implementation of dynamic agent architecture features including per-agent working directories, dynamic MCP configuration generation, and isolated execution environments.

## Core Components

### 1. Dynamic Working Directory System

#### Directory Structure
```
output_dir/
├── agent_workspaces/          # Base for all agent workspaces
│   ├── {task_id_1}/           # Per-agent workspace
│   │   ├── mcp_config.json    # Agent-specific MCP config
│   │   ├── workspace/         # Agent working directory
│   │   ├── logs/              # Agent logs
│   │   └── .env               # Agent-specific environment
│   └── {task_id_2}/
│       └── ...
├── tasks/                     # Task results (existing)
├── logs/                      # Orchestrator logs (existing)
└── messages/                  # Message bus (existing)
```

#### Implementation Location
**File**: `src/generic_orchestrator.py`
**Function**: `execute_agent` (line 278-385)

### 2. Per-Agent MCP Configuration

#### Dynamic Config Generation Function

**Add new method after line 485**:
```python
def _generate_agent_mcp_config(
    self,
    task: AgentTask,
    output_path: Path,
    profile: Optional[str] = None
) -> None:
    """
    Generate agent-specific MCP configuration.

    Args:
        task: The agent task
        output_path: Where to write the config
        profile: Override execution profile for this agent
    """

    # Start with base config
    if self.master_mcp_registry_path and self.master_mcp_registry_path.exists():
        with open(self.master_mcp_registry_path) as f:
            base_config = json.load(f)
    else:
        base_config = self._get_default_mcp_config()

    # Apply profile filtering
    profile = profile or self.agent_execution_profile
    config = self._filter_mcp_by_profile(base_config, profile)

    # Task-specific customizations
    if task.task_type == "research":
        # Ensure research tools are included
        self._ensure_research_tools(config)
    elif task.task_type == "monitoring":
        # Add monitoring-specific tools
        self._add_monitoring_tools(config)

    # Update working directories in config
    for server_name, server_config in config.get("mcpServers", {}).items():
        if "cwd" in server_config:
            # Update to agent-specific directory
            server_config["cwd"] = str(output_path.parent / "workspace")

        # Update environment variables
        if "env" not in server_config:
            server_config["env"] = {}

        server_config["env"]["AGENT_TASK_ID"] = task.task_id
        server_config["env"]["AGENT_WORK_DIR"] = str(output_path.parent)

    # Write config
    output_path.write_text(json.dumps(config, indent=2))

    logger.debug(f"Generated MCP config for {task.task_id}: {output_path}")
```

### 3. Execute Agent Modifications

#### Modified execute_agent Method

**Location**: Line 278-385
**Key Changes**:

```python
async def execute_agent(self, task: AgentTask) -> Dict:
    """Execute a single agent task with dynamic architecture support."""

    session_id = str(uuid.uuid4())

    # Pre-execution hook
    if self.pre_execute_hook:
        await self.pre_execute_hook(task)

    # NEW: Setup agent workspace
    if self.enable_dynamic_configs:
        agent_workspace = await self._setup_agent_workspace(task)
        agent_mcp_config = agent_workspace / "mcp_config.json"
        agent_work_dir = agent_workspace / "workspace"
        agent_log_dir = agent_workspace / "logs"

        # Generate agent-specific MCP config
        self._generate_agent_mcp_config(task, agent_mcp_config)

        # Update command to use agent-specific config
        cmd = self.claude_cmd.copy()

        # Replace MCP config path
        if "--mcp-config" in cmd:
            idx = cmd.index("--mcp-config")
            cmd[idx + 1] = str(agent_mcp_config)
        else:
            cmd.extend(["--mcp-config", str(agent_mcp_config)])

        # Add workspace directory
        cmd.extend(["--add-dir", str(agent_work_dir)])

        # Setup logging redirect if enabled
        log_file = None
        if self.log_to_work_dir:
            log_file = agent_log_dir / f"agent_{task.task_id}.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Use default paths
        agent_work_dir = self.output_dir
        cmd = self.claude_cmd.copy()
        log_file = None

    # Add debug flag if enabled
    if self.agent_debug_mode:
        cmd.append("--debug")

    # ... rest of existing execution code ...

    # Modified subprocess call
    process = await asyncio.create_subprocess_exec(
        *cmd,
        env=env,
        cwd=str(agent_work_dir),  # NEW: Use agent work dir
        stdout=asyncio.subprocess.PIPE if not log_file else await aiofiles.open(log_file, 'w'),
        stderr=asyncio.subprocess.PIPE,
    )
```

### 4. Workspace Management Functions

**Add after line 485**:

```python
async def _setup_agent_workspace(self, task: AgentTask) -> Path:
    """
    Setup isolated workspace for an agent.

    Returns:
        Path to agent workspace directory
    """

    workspace_root = self.agent_base_work_dir / task.task_id
    workspace_root.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (workspace_root / "workspace").mkdir(exist_ok=True)
    (workspace_root / "logs").mkdir(exist_ok=True)
    (workspace_root / "data").mkdir(exist_ok=True)

    # Create symlinks to shared resources if needed
    shared_data = self.output_dir / "shared_data"
    if shared_data.exists():
        target = workspace_root / "shared"
        if not target.exists():
            target.symlink_to(shared_data)

    # Create agent-specific .env file
    env_file = workspace_root / ".env"
    env_content = [
        f"AGENT_ID={task.task_id}",
        f"AGENT_TYPE={task.task_type}",
        f"WORKSPACE_ROOT={workspace_root}",
        f"OUTPUT_DIR={self.output_dir}",
    ]
    env_file.write_text("\n".join(env_content))

    logger.debug(f"Setup workspace for {task.task_id}: {workspace_root}")

    return workspace_root

async def _cleanup_agent_workspace(self, task: AgentTask, preserve: bool = True):
    """
    Cleanup or archive agent workspace.

    Args:
        task: The completed task
        preserve: If True, archive instead of delete
    """

    workspace = self.agent_base_work_dir / task.task_id

    if not workspace.exists():
        return

    if preserve:
        # Archive workspace
        archive_dir = self.output_dir / "archived_workspaces"
        archive_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = archive_dir / f"{task.task_id}_{timestamp}"

        import shutil
        shutil.move(str(workspace), str(archive_path))
        logger.info(f"Archived workspace: {archive_path}")
    else:
        # Delete workspace
        import shutil
        shutil.rmtree(workspace)
        logger.info(f"Deleted workspace: {workspace}")
```

### 5. Symlink Logic for Shared Resources

```python
def _setup_shared_resources(self) -> None:
    """Setup shared resources accessible to all agents."""

    shared_dir = self.output_dir / "shared_data"
    shared_dir.mkdir(exist_ok=True)

    # Common data directories
    (shared_dir / "references").mkdir(exist_ok=True)
    (shared_dir / "templates").mkdir(exist_ok=True)
    (shared_dir / "libraries").mkdir(exist_ok=True)

    # Create README
    readme = shared_dir / "README.md"
    readme.write_text("""
# Shared Resources

This directory contains resources shared across all agents:
- references/: Common reference materials
- templates/: Reusable templates
- libraries/: Shared code libraries

Agents access this via symlink: workspace/shared/
    """)
```

### 6. Environment Variable Injection

```python
def _prepare_agent_environment(self, task: AgentTask, base_env: Dict) -> Dict:
    """
    Prepare environment variables for agent execution.

    Args:
        task: The agent task
        base_env: Base environment (os.environ.copy())

    Returns:
        Modified environment dictionary
    """

    env = base_env.copy()

    # Add agent-specific variables
    env["AGENT_TASK_ID"] = task.task_id
    env["AGENT_TASK_TYPE"] = task.task_type

    if self.enable_dynamic_configs:
        workspace = self.agent_base_work_dir / task.task_id
        env["AGENT_WORKSPACE"] = str(workspace)
        env["AGENT_MCP_CONFIG"] = str(workspace / "mcp_config.json")

        # Load .env file if exists
        env_file = workspace / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env[key.strip()] = value.strip()

    # Debug mode environment
    if self.agent_debug_mode:
        env["AGENT_DEBUG"] = "1"
        env["CLAUDE_DEBUG"] = "1"

    return env
```

### 7. Integration with Subprocess Execution

**Modify line 333-339**:

```python
# Prepare environment
env = os.environ.copy()
env["CLAUDE_CODE_TOKEN"] = token

# NEW: Add agent-specific environment
if self.enable_dynamic_configs:
    env = self._prepare_agent_environment(task, env)

# Execute with dynamic working directory
process = await asyncio.create_subprocess_exec(
    *cmd,
    env=env,
    cwd=str(agent_work_dir) if self.enable_dynamic_configs else None,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
)
```

## Configuration Examples

### 1. Basic Dynamic Configuration
```python
orchestrator = GenericOrchestrator(
    output_dir=Path("./output"),
    tokens=token_list,
    enable_dynamic_configs=True
)
```

### 2. Full Dynamic Architecture
```python
orchestrator = GenericOrchestrator(
    output_dir=Path("./output"),
    tokens=token_list,
    enable_dynamic_configs=True,
    agent_base_work_dir=Path("./agent_workspaces"),
    master_mcp_registry_path=Path("./master_mcp.json"),
    agent_execution_profile="research",
    log_to_work_dir=True
)
```

### 3. Task-Specific Configuration
```python
task = AgentTask(
    task_id="research_001",
    task_type="research",
    prompt="Research async patterns",
    context={
        "mcp_profile_override": "full",  # Override profile for this task
        "preserve_workspace": True,      # Don't delete after completion
    }
)
```

## File System Impact

### Created Directories
```
agent_workspaces/
├── {task_id}/
│   ├── mcp_config.json
│   ├── workspace/
│   ├── logs/
│   ├── data/
│   ├── shared -> ../../../shared_data
│   └── .env
```

### Symlink Creation
- `shared` -> Points to `output_dir/shared_data`
- Created only if shared_data exists
- Provides read-only access to shared resources

## Performance Considerations

1. **Workspace Creation Overhead**: ~50ms per agent
2. **MCP Config Generation**: ~10ms per agent
3. **Symlink Creation**: Negligible
4. **Cleanup Operations**: Can be async/deferred

## Error Handling

### Workspace Creation Failures
```python
try:
    workspace = await self._setup_agent_workspace(task)
except OSError as e:
    logger.error(f"Failed to create workspace for {task.task_id}: {e}")
    # Fallback to default directory
    workspace = self.output_dir
```

### MCP Config Generation Failures
```python
try:
    self._generate_agent_mcp_config(task, config_path)
except Exception as e:
    logger.warning(f"Failed to generate MCP config: {e}")
    # Use default config
```

## Testing Requirements

### Unit Tests
1. Test workspace creation
2. Test MCP config generation
3. Test symlink creation
4. Test environment variable injection
5. Test cleanup operations

### Integration Tests
1. Test full dynamic execution
2. Test fallback behavior
3. Test concurrent agent isolation
4. Test resource sharing via symlinks

## Migration Path

### Phase 1: Add Functions
- Add all new functions without modifying execute_agent
- Test functions in isolation

### Phase 2: Optional Integration
- Add enable_dynamic_configs check
- Preserve existing behavior when disabled

### Phase 3: Gradual Enablement
- Enable for specific task types first
- Monitor performance and correctness
- Expand to all tasks

## Validation Checklist

- [ ] Workspace creation is atomic
- [ ] MCP configs are valid JSON
- [ ] Symlinks work across filesystems
- [ ] Environment variables properly injected
- [ ] Cleanup doesn't delete shared resources
- [ ] Fallback behavior works correctly
- [ ] No interference between concurrent agents
- [ ] Logs properly redirected when enabled
