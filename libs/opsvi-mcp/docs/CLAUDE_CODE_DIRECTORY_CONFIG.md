# Claude Code Directory Access & Configuration Behavior

## Executive Summary

This document details Claude Code's directory access controls, configuration hierarchy, and how starting location influences behavior - crucial for multi-agent orchestration with isolated environments.

---

## Directory Access Control

### 1. Adding Directory Access

**Command-line Flag:**
```bash
--add-dir <directories...>  # Add directories to allowed access list
```

**Example:**
```bash
claude --add-dir /tmp/workspace /var/data --prompt "Analyze files"
```

### 2. Restricting Directory Access

**Current Findings:**
- **No `--remove-dir` flag exists** (as of current version)
- Cannot explicitly restrict below default permissions via CLI
- Must use configuration files for restrictions

**Restriction Methods:**

1. **Via Settings File:**
```json
{
  "permissions": {
    "allow": ["/specific/path/only"],  // Whitelist approach
    "additionalDirectories": [],       // No extras
    "defaultMode": "default"           // Require approval
  }
}
```

2. **Via Strict MCP Config:**
```bash
--strict-mcp-config  # Only use specified MCP servers, ignore defaults
```

### 3. Default Directory Access

**Global Settings Location:** `~/.claude/settings.json`

**Default Permissions (from investigation):**
```json
{
  "permissions": {
    "allow": ["*"],  // All directories by default
    "additionalDirectories": ["/tmp", "/home/user/projects"],
    "defaultMode": "bypassPermissions"  // Or "default", "acceptEdits"
  }
}
```

**Permission Modes:**
- `default` - Ask for permission for each operation
- `acceptEdits` - Auto-accept file modifications
- `bypassPermissions` - Skip all permission checks
- `plan` - Planning mode only, no actual changes

---

## Configuration Hierarchy

### 1. Configuration Search Order

```
1. Project-specific: ./.claude/settings.json (highest priority)
2. Global user: ~/.claude/settings.json
3. Command-line flags: --settings, --add-dir, etc.
4. Environment variables: CLAUDE_*
5. Built-in defaults (lowest priority)
```

### 2. Working Directory Influence

**Key Finding:** The directory where Claude Code is started SIGNIFICANTLY affects behavior.

#### Starting from Project Root (has .claude/)
```bash
cd /home/user/myproject  # Has .claude/settings.json
claude --prompt "task"

# Uses:
# 1. /home/user/myproject/.claude/settings.json (project-specific)
# 2. ~/.claude/settings.json (global fallback)
```

#### Starting from Non-Project Directory
```bash
cd /tmp  # No .claude/ directory
claude --prompt "task"

# Uses:
# 1. ~/.claude/settings.json (global only)
# 2. Built-in defaults
```

### 3. Configuration Isolation Strategy

**Discovered Pattern:** Can create isolated environments with custom configs!

```bash
# Scenario 1: High-security agent
/agents/high-security/.claude/settings.json:
{
  "permissions": {
    "allow": ["/secure/data/readonly"],
    "additionalDirectories": [],
    "defaultMode": "default"
  }
}

# Scenario 2: Build agent
/agents/builder/.claude/settings.json:
{
  "permissions": {
    "allow": ["*"],
    "additionalDirectories": ["/tmp/build", "/var/cache"],
    "defaultMode": "bypassPermissions"
  }
}

# Scenario 3: Testing agent
/agents/tester/.claude/settings.json:
{
  "permissions": {
    "allow": ["/tests", "/tmp/test_output"],
    "additionalDirectories": [],
    "defaultMode": "acceptEdits"
  }
}
```

---

## Orchestration Implications

### 1. Spawn Location Strategy

```python
class AgentSpawner:
    """Spawn agents from specific directories for config isolation"""
    
    AGENT_CONFIGS = {
        "secure": "/agents/secure",      # Restricted access
        "builder": "/agents/builder",    # Full access
        "analyzer": "/agents/analyzer",  # Read-only access
        "tester": "/agents/tester"      # Test directories only
    }
    
    async def spawn_with_config(self, agent_type: str, task: str):
        config_dir = self.AGENT_CONFIGS[agent_type]
        
        # Change to config directory before spawning
        original_dir = os.getcwd()
        os.chdir(config_dir)
        
        try:
            # Spawn from directory with specific .claude/settings.json
            result = await spawn_claude(task)
        finally:
            os.chdir(original_dir)
        
        return result
```

### 2. Dynamic Configuration Generation

```python
def create_isolated_agent_env(
    agent_id: str,
    allowed_dirs: List[str],
    permission_mode: str = "default"
) -> str:
    """Create isolated environment with custom permissions"""
    
    # Create agent-specific directory
    agent_dir = f"/tmp/agents/{agent_id}"
    os.makedirs(f"{agent_dir}/.claude", exist_ok=True)
    
    # Write custom settings
    settings = {
        "permissions": {
            "allow": allowed_dirs,
            "additionalDirectories": [],
            "defaultMode": permission_mode
        },
        "model": "opus",
        "enableAllProjectMcpServers": False  # Isolate MCP too
    }
    
    with open(f"{agent_dir}/.claude/settings.json", "w") as f:
        json.dump(settings, f, indent=2)
    
    return agent_dir
```

### 3. Permission Scenarios

#### Scenario A: Read-Only Analysis Agent
```json
{
  "permissions": {
    "allow": ["/project/src"],
    "additionalDirectories": [],
    "defaultMode": "default"  // Will fail on write attempts
  }
}
```

#### Scenario B: Sandboxed Testing Agent
```json
{
  "permissions": {
    "allow": ["/tmp/sandbox_${AGENT_ID}"],
    "additionalDirectories": [],
    "defaultMode": "bypassPermissions"
  }
}
```

#### Scenario C: Cross-Project Agent
```json
{
  "permissions": {
    "allow": ["/projects/*/src"],  // Multiple projects
    "additionalDirectories": ["/shared/libs"],
    "defaultMode": "acceptEdits"
  }
}
```

---

## Implementation Patterns

### 1. Agent Isolation Pattern

```python
class IsolatedAgentManager:
    """Manage agents with isolated configurations"""
    
    def __init__(self):
        self.base_dir = "/var/claude_agents"
        self.ensure_base_structure()
    
    def ensure_base_structure(self):
        """Create base directory structure for agents"""
        
        # Standard agent types with preset configs
        for agent_type in ["secure", "standard", "privileged"]:
            agent_dir = f"{self.base_dir}/{agent_type}"
            os.makedirs(f"{agent_dir}/.claude", exist_ok=True)
            self.write_standard_config(agent_type, agent_dir)
    
    def spawn_isolated_agent(
        self,
        task: str,
        agent_type: str = "standard",
        custom_dirs: Optional[List[str]] = None
    ):
        """Spawn agent with isolated configuration"""
        
        if custom_dirs:
            # Create temporary isolated environment
            agent_id = str(uuid.uuid4())
            agent_dir = self.create_custom_env(agent_id, custom_dirs)
        else:
            # Use preset configuration
            agent_dir = f"{self.base_dir}/{agent_type}"
        
        # Spawn from isolated directory
        env = os.environ.copy()
        env["AGENT_START_DIR"] = agent_dir
        
        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            "--output-format", "json",
            "--prompt", task
        ]
        
        # Execute from agent directory for config isolation
        process = subprocess.Popen(
            cmd,
            cwd=agent_dir,  # Critical: start from config directory
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        return process
```

### 2. Configuration Inheritance Pattern

```python
def merge_configs(
    global_config: Dict,
    project_config: Dict,
    agent_config: Dict
) -> Dict:
    """Merge configurations with proper precedence"""
    
    # Start with global
    merged = copy.deepcopy(global_config)
    
    # Override with project settings
    deep_merge(merged, project_config)
    
    # Override with agent-specific settings
    deep_merge(merged, agent_config)
    
    # Command-line flags would override all
    
    return merged
```

### 3. Security Patterns

```python
class SecureAgentSpawner:
    """Spawn agents with security constraints"""
    
    def spawn_readonly_agent(self, task: str, allowed_path: str):
        """Spawn agent that can only read from specific path"""
        
        config = {
            "permissions": {
                "allow": [allowed_path],
                "additionalDirectories": [],
                "defaultMode": "default"  # Will reject writes
            }
        }
        
        return self.spawn_with_config(config, task)
    
    def spawn_sandboxed_agent(self, task: str):
        """Spawn agent in temporary sandbox"""
        
        sandbox = f"/tmp/sandbox_{uuid.uuid4()}"
        os.makedirs(sandbox)
        
        config = {
            "permissions": {
                "allow": [sandbox],
                "additionalDirectories": [],
                "defaultMode": "bypassPermissions"
            }
        }
        
        return self.spawn_with_config(config, task, cwd=sandbox)
```

---

## Key Findings

### 1. Directory Restriction Limitations
- **Cannot reduce permissions via CLI** below configured defaults
- Must use configuration files for restrictions
- No `--remove-dir` or `--deny-dir` flags exist

### 2. Working Directory Matters
- Claude looks for `.claude/` in current directory first
- Falls back to `~/.claude/` if not found
- Starting location determines which config is used

### 3. Configuration Isolation Works
- Can create isolated environments with custom configs
- Each agent can have different permission sets
- Enables security boundaries between agents

### 4. Permission Modes Are Powerful
- `default` mode enforces approval (good for security)
- `bypassPermissions` enables automation
- `plan` mode for dry runs

### 5. Orchestration Opportunities
- Spawn agents from different directories for different configs
- Create temporary isolated environments per agent
- Use directory structure to organize agent types

---

## Best Practices

### 1. Security
- Start high-security agents from restricted config directories
- Never use `allow: ["*"]` for untrusted tasks
- Use `default` permission mode when uncertain

### 2. Isolation
- Create separate directories for different agent types
- Use temporary directories for experimental agents
- Clean up temporary configs after use

### 3. Organization
```
/var/claude_agents/
├── secure/
│   └── .claude/settings.json    # Minimal permissions
├── standard/
│   └── .claude/settings.json    # Balanced permissions
├── privileged/
│   └── .claude/settings.json    # Full access
└── temp/
    └── {agent_id}/              # Temporary per-agent configs
        └── .claude/settings.json
```

### 4. Testing
- Test permission boundaries before production
- Verify agents can't escape their sandboxes
- Monitor file access patterns

---

## Implementation Examples

### Example 1: Multi-Tenant System
```python
# Each tenant gets isolated environment
/tenants/
├── tenant_a/
│   └── .claude/settings.json  # Access to /data/tenant_a only
├── tenant_b/
│   └── .claude/settings.json  # Access to /data/tenant_b only
└── shared/
    └── .claude/settings.json  # Access to /data/shared only
```

### Example 2: CI/CD Pipeline
```python
# Different stages with different permissions
/ci/
├── checkout/
│   └── .claude/settings.json  # Read from repo only
├── build/
│   └── .claude/settings.json  # Read source, write build/
├── test/
│   └── .claude/settings.json  # Read build/, write test-results/
└── deploy/
    └── .claude/settings.json  # Read build/, write to deployment
```

### Example 3: Development vs Production
```python
# Environment-specific configurations
/environments/
├── development/
│   └── .claude/settings.json  # Permissive, all projects
├── staging/
│   └── .claude/settings.json  # Restricted to staging data
└── production/
    └── .claude/settings.json  # Minimal, audit mode
```

---

## Future Considerations

### 1. Requested Features
- `--remove-dir` flag for runtime restriction
- `--sandbox` flag for automatic isolation
- `--config-dir` to specify config location
- Permission inheritance controls

### 2. Potential Patterns
- Config templating system
- Dynamic permission adjustment
- Role-based access control (RBAC)
- Audit logging of directory access

### 3. Integration Ideas
- Kubernetes ConfigMaps for configs
- Docker volumes for isolation
- HashiCorp Vault for secrets
- Policy engines for permissions

---

## Conclusion

Claude Code's directory and configuration behavior enables sophisticated agent isolation and permission management through strategic use of working directories and configuration files. While CLI flags are limited for restriction, the configuration file approach provides powerful control for orchestration scenarios.

The ability to spawn agents from different directories with different `.claude/settings.json` files enables:
- Security isolation
- Multi-tenant support
- Environment-specific behavior
- Sandboxed execution
- Permission-based agent roles

This should be leveraged in V2/V3 orchestration for secure, isolated agent execution.