# Critical Commands and Code Snippets

## Testing V2 Server
```bash
# Start V2 server with fixes
export PYTHONPATH=/home/opsvi/master_root/libs
export CLAUDE_CODE_TOKEN="test-token"
/home/opsvi/miniconda/bin/python -m opsvi_mcp.servers.claude_code_v2
```

## V2 Parameter Fix Pattern
```python
# OLD - Pydantic Model
async def spawn_agent(request: SpawnAgentRequest) -> Dict[str, Any]:
    task = request.task
    
# NEW - Simple Parameters
async def spawn_agent(
    task: str,
    agent_profile: Optional[str] = None,
    output_dir: Optional[str] = None,
    timeout: int = 600,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
```

## Multi-Agent Orchestration
```python
# Task routing implementation
from opsvi_mcp.servers.multi_agent_orchestrator import orchestrate_task

async def route_task(task):
    if task.context_size > 500_000:
        return await orchestrate_task(task, preferred_agent="gemini_cli")
    elif task.requires_deep_reasoning:
        return await orchestrate_task(task, preferred_agent="claude_code")
    elif task.needs_sandbox:
        return await spawn_codex_sandbox(task)
    else:
        # Round-robin between primaries
        agent = random.choice(["claude_code", "gemini_cli"])
        return await orchestrate_task(task, preferred_agent=agent)
```

## Gemini CLI Integration
```bash
# Install Gemini CLI
curl https://gemini.google.com/cli/install -fsSL | bash

# Configure MCP servers
cat > gemini-settings.json << EOF
{
  "mcpServers": {
    "github": {
      "command": "npm",
      "args": ["run", "mcp-server-github"]
    }
  }
}
EOF

# Run with MCP
gemini --mcp-server --config gemini-settings.json
```

## Quick Status Check
```python
# Check all server statuses
servers = {
    "claude_code": {"status": "active", "reliability": 0.95},
    "claude_code_v2": {"status": "active", "tools": 6},
    "claude_code_v3": {"status": "active", "modes": 10},
    "gemini_cli": {"status": "active", "quota": "1000/day"},
    "openai_codex": {"status": "experimental", "sandboxes": True},
    "cursor_cli": {"status": "blocked", "bug": "CI=1 hang"}
}

for server, info in servers.items():
    print(f"{server}: {info['status']}")
```

## Environment Setup
```bash
# Complete environment for all servers
export CLAUDE_CODE_TOKEN="your-token"
export OPENAI_API_KEY="your-key"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/creds"
export PYTHONPATH="/home/opsvi/master_root/libs"
export CLAUDE_RESULTS_DIR="/tmp/claude_results"
export CLAUDE_ENABLE_MULTI_AGENT="true"
export CLAUDE_MAX_RECURSION_DEPTH="5"
export GEMINI_CLI_CONFIG="./gemini-settings.json"
```

## File Locations
- V2 Server: `/home/opsvi/master_root/libs/opsvi-mcp/opsvi_mcp/servers/claude_code_v2/server.py`
- V3 Config: `/home/opsvi/master_root/libs/opsvi-mcp/opsvi_mcp/servers/claude_code_v3/config.py`
- MCP Config: `/home/opsvi/master_root/.mcp.json` and `.cursor/mcp.json`
- Test Reports: `/home/opsvi/master_root/mcp_server_test_report.md`
- Session Docs: `/home/opsvi/master_root/libs/opsvi-mcp/SESSION_PRESERVATION.md`