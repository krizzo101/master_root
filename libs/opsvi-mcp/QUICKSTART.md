# Quick Start Guide - OPSVI MCP Servers

## Installation

### 1. Install the Package
```bash
cd /home/opsvi/master_root/libs/opsvi-mcp
pip install -e .
```

Or install dependencies manually:
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
# Required for Claude Code
export CLAUDE_CODE_TOKEN="your-claude-token"

# Required for OpenAI Codex
export OPENAI_API_KEY="your-openai-api-key"

# Optional for Cursor Agent
export CURSOR_WORKSPACE="/path/to/your/workspace"
export CURSOR_COMM_METHOD="websocket"  # or "file", "pipe", "cli"
```

## Running Individual Servers

### Claude Code V1 Server (Traditional)
```bash
# As a module
python -m opsvi_mcp.servers.claude_code

# Or using the entry point (after pip install -e .)
opsvi-claude-code
```

### Claude Code V2 Server (Fire-and-Forget)
```bash
# As a module
python -m opsvi_mcp.servers.claude_code_v2

# Or using the entry point (after pip install -e .)
opsvi-claude-code-v2
```

### Claude Code V3 Server (Multi-Agent)
```bash
# As a module
python -m opsvi_mcp.servers.claude_code_v3

# Or using the entry point (after pip install -e .)
opsvi-claude-code-v3
```

### OpenAI Codex Server
```bash
# As a module
python -m opsvi_mcp.servers.openai_codex

# Or using the entry point
opsvi-codex
```

### Cursor Agent Server
```bash
# As a module
python -m opsvi_mcp.servers.cursor_agent

# Or using the entry point
opsvi-cursor
```

### Unified Orchestrator (All Servers)
```bash
# As a module
python -m opsvi_mcp.servers.unified_orchestrator

# Or using the entry point
opsvi-orchestrator
```

## Testing the Installation

Run the test suite to verify everything is working:
```bash
cd /home/opsvi/master_root/libs/opsvi-mcp
python test_mcp_servers.py
```

## Basic Usage Examples

### Using Claude Code V1 for Traditional Execution

```python
from opsvi_mcp.servers.claude_code import ClaudeCodeServer

async def traditional_execution():
    server = ClaudeCodeServer()
    
    # Synchronous execution - waits for completion
    result = await server.claude_run(
        task="Create a Python calculator class",
        outputFormat="json"
    )
    print(result)
    
    # Async execution with job tracking
    job = await server.claude_run_async(
        task="Analyze project structure"
    )
    status = await server.claude_status(job["job_id"])
    print(f"Job status: {status}")
```

### Using Claude Code V3 for Multi-Agent Orchestration

```python
from opsvi_mcp.servers.claude_code_v3 import ClaudeCodeV3Server

async def multi_agent_execution():
    server = ClaudeCodeV3Server()
    
    # Auto-detect mode based on task
    result = await server.claude_run_v3(
        task="Create a production-ready authentication system with tests and documentation",
        auto_detect=True  # Will select FULL_CYCLE mode
    )
    print(f"Execution mode: {result['mode']}")
    print(f"Agents used: {result['agents']}")
    
    # Explicit mode selection
    result = await server.claude_run_v3(
        task="Debug and fix the login function",
        mode="DEBUG",  # Forces debug mode
        quality_level="high"
    )
    print(result)
    
    # Available modes:
    # RAPID - Quick prototype
    # CODE - Standard development
    # QUALITY - With review and tests
    # FULL_CYCLE - Complete with docs
    # TESTING - Test generation
    # DOCUMENTATION - Doc generation
    # DEBUG - Bug fixing
    # ANALYSIS - Code understanding
    # REVIEW - Code critique
    # RESEARCH - Information gathering
```

### Using OpenAI Codex for Code Generation

```python
from opsvi_mcp.servers.openai_codex import OpenAICodexServer

async def generate_code():
    server = OpenAICodexServer()
    
    # Generate code from description
    result = await server.codex_generate(
        prompt="Create a Python function to calculate fibonacci numbers",
        language="python"
    )
    print(result['result'])
```

### Using Cursor Agent for Diagrams

```python
from opsvi_mcp.servers.cursor_agent import CursorAgentServer

async def create_diagram():
    server = CursorAgentServer()
    
    # Create a flowchart
    result = await server.create_diagram(
        data="User login -> Validate credentials -> Generate token -> Return response",
        diagram_type="flowchart",
        theme="high-contrast"
    )
    print(result['result'])
```

### Using Claude Code V2 for Parallel Analysis

```python
from opsvi_mcp.servers.claude_code_v2 import ClaudeCodeV2Server

async def parallel_analysis():
    server = ClaudeCodeV2Server()
    
    # Spawn multiple agents
    jobs = await server.spawn_parallel_agents(
        tasks=[
            "Analyze security vulnerabilities",
            "Review code quality",
            "Generate documentation"
        ],
        output_dir="/tmp/analysis_results"
    )
    
    # Collect results when ready
    results = await server.collect_results(
        output_dir="/tmp/analysis_results"
    )
    print(results)
```

### Using the Unified Orchestrator

```python
from opsvi_mcp.servers.unified_orchestrator import UnifiedMCPOrchestrator

async def complete_workflow():
    orchestrator = UnifiedMCPOrchestrator()
    
    # Run a complete development workflow
    result = await orchestrator.analyze_and_implement(
        requirements="Build a REST API for user management",
        language="python",
        visualize=True
    )
    
    # Results include:
    # - Claude's analysis
    # - Codex's implementation
    # - Cursor's visualization
    print(result)
```

## Common Issues and Solutions

### Issue: "Module not found" errors
**Solution**: Ensure you're using the correct Python environment with dependencies installed:
```bash
which python  # Should point to the environment with packages
pip list | grep fastmcp  # Should show fastmcp installed
```

### Issue: Authentication errors
**Solution**: Check environment variables are set:
```bash
echo $CLAUDE_CODE_TOKEN
echo $OPENAI_API_KEY
```

### Issue: Cursor agent not connecting
**Solution**: Verify Cursor IDE is running and WebSocket port is available:
```bash
# Check if port 7070 is in use
lsof -i :7070
```

### Issue: Results not appearing
**Solution**: Check the results directory exists and has write permissions:
```bash
ls -la /tmp/claude_results/
ls -la /tmp/codex_cache/
```

## Configuration Files

### Main Configuration
Edit `/home/opsvi/master_root/libs/opsvi-mcp/opsvi_mcp/servers/unified_config.yaml` to customize server settings.

### Environment Variables
Create a `.env` file in your project root:
```env
CLAUDE_CODE_TOKEN=sk-ant-...
OPENAI_API_KEY=sk-...
CURSOR_WORKSPACE=/home/user/projects
CURSOR_COMM_METHOD=websocket
CLAUDE_RESULTS_DIR=/tmp/my_results
CODEX_MODEL=gpt-4
```

## Next Steps

1. **Explore the API**: Check the README.md for detailed API documentation
2. **Run Examples**: Try the example scripts in each server directory
3. **Build Workflows**: Create custom orchestrations for your needs
4. **Monitor Performance**: Use the dashboard and metrics endpoints
5. **Contribute**: Submit issues or PRs for improvements

## Support

- **Documentation**: See README.md for detailed documentation
- **Tests**: Run `pytest` for comprehensive testing
- **Issues**: Report bugs in the project issue tracker
- **Logs**: Check `/tmp/*_server.log` files for debugging