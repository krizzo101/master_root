# OPSVI MCP Library

Advanced Model Context Protocol (MCP) server implementations for autonomous, multi-agent AI/ML operations systems.

## Overview

The OPSVI MCP library provides multiple versions of Claude Code servers and other AI integration servers, each optimized for different use cases:

- **Claude Code V1**: Traditional synchronous/async job management with tracking
- **Claude Code V2**: Fire-and-forget pattern for massive parallel agent spawning
- **Claude Code V3**: Intelligent multi-agent orchestration with automatic mode selection
- **OpenAI Codex**: Code generation and analysis using GPT-4
- **Cursor Agent**: Integration with Cursor IDE for visualizations
- **Context Bridge**: Knowledge sharing between different MCP servers

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    User/Client                       │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────┐
│                   MCP Protocol                       │
├──────────┬───────────┬───────────┬──────────────────┤
│  V1      │    V2     │    V3     │   Other Servers  │
│ (8 tools)│ (6 tools) │ (2 tools) │                  │
├──────────┼───────────┼───────────┼──────────────────┤
│ Sync/    │ Fire &    │ Multi-    │ Codex/Cursor/    │
│ Async    │ Forget    │ Agent     │ Context Bridge   │
└──────────┴───────────┴───────────┴──────────────────┘
```

## Quick Comparison

| Feature | Claude V1 | Claude V2 | Claude V3 |
|---------|-----------|-----------|-----------|
| **Tools** | 8 | 6 | 2 |
| **Pattern** | Traditional async | Fire-and-forget | Intelligent orchestration |
| **Best For** | Simple tasks, debugging | Parallel analysis | Production systems |
| **Recursion** | 3 levels | 3 levels (managed) | 5 levels (adaptive) |
| **Concurrency** | Fixed | High parallelism | Adaptive by depth |
| **Recovery** | Basic | Partial results | Checkpointing |
| **Mode Selection** | N/A | N/A | 10 automatic modes |

## Installation

### From Source
```bash
cd /home/opsvi/master_root/libs/opsvi-mcp
pip install -e .
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Required Environment Variables
```bash
# For Claude Code servers
export CLAUDE_CODE_TOKEN="your-claude-token"

# For OpenAI Codex
export OPENAI_API_KEY="your-openai-key"

# Optional configurations
export CLAUDE_RESULTS_DIR="/tmp/claude_results"
export CLAUDE_MAX_RECURSION_DEPTH="5"
export CLAUDE_ENABLE_MULTI_AGENT="true"
```

## Quick Start

### Claude Code V1 - Traditional Pattern
```python
# Synchronous execution
from opsvi_mcp.servers.claude_code import claude_run

result = await claude_run(
    task="Create a Python function",
    outputFormat="json"
)

# Asynchronous with tracking
job_id = await claude_run_async(task="Analyze codebase")
status = await claude_status(jobId=job_id)
result = await claude_result(jobId=job_id)
```

### Claude Code V2 - Fire-and-Forget
```python
# Start server
python -m opsvi_mcp.servers.claude_code_v2

# Spawn parallel agents
jobs = await spawn_parallel_agents([
    "Analyze security",
    "Review performance", 
    "Generate docs"
])

# Collect when ready
results = await collect_results(output_dir="/tmp/claude_results")
```

### Claude Code V3 - Intelligent Multi-Agent
```python
# Start server
python -m opsvi_mcp.servers.claude_code_v3

# Auto-detect best execution mode
result = await claude_run_v3(
    task="Create production-ready REST API with tests",
    auto_detect=True  # Automatically selects FULL_CYCLE mode
)

# Or specify mode explicitly
result = await claude_run_v3(
    task="Fix critical bug",
    mode="QUALITY",  # Forces quality mode with review
    quality_level="high"
)
```

## Available Execution Modes (V3)

| Mode | Description | Includes |
|------|-------------|----------|
| RAPID | Quick prototype | Basic implementation |
| CODE | Standard development | Implementation + validation |
| QUALITY | Quality-assured | Code + Review + Tests |
| FULL_CYCLE | Production-ready | Everything + Docs |
| TESTING | Test-focused | Test generation + coverage |
| DOCUMENTATION | Doc-focused | Comprehensive documentation |
| DEBUG | Bug fixing | Analysis + Fix + Validation |
| ANALYSIS | Understanding | Deep code analysis |
| REVIEW | Code critique | Quality assessment |
| RESEARCH | Information gathering | Research + synthesis |

## MCP Configuration

Add to `.mcp.json` or `.cursor/mcp.json`:

```json
{
  "claude-code": {
    "command": "python",
    "args": ["-m", "opsvi_mcp.servers.claude_code"],
    "env": {
      "CLAUDE_CODE_TOKEN": "your-token",
      "PYTHONPATH": "/home/opsvi/master_root/libs"
    }
  },
  "claude-code-v2": {
    "command": "python",
    "args": ["-m", "opsvi_mcp.servers.claude_code_v2"],
    "env": {
      "CLAUDE_CODE_TOKEN": "your-token",
      "CLAUDE_RESULTS_DIR": "/tmp/claude_results",
      "CLAUDE_MAX_CONCURRENT_L1": "10"
    }
  },
  "claude-code-v3": {
    "command": "python",
    "args": ["-m", "opsvi_mcp.servers.claude_code_v3"],
    "env": {
      "CLAUDE_CODE_TOKEN": "your-token",
      "CLAUDE_ENABLE_MULTI_AGENT": "true",
      "CLAUDE_MAX_RECURSION_DEPTH": "5"
    }
  }
}
```

## Server Features

### Claude Code V1 (8 Tools)
- `claude_run`: Synchronous task execution
- `claude_run_async`: Asynchronous with job ID
- `claude_status`: Check job status
- `claude_result`: Get completed results
- `claude_list_jobs`: List all jobs
- `claude_kill_job`: Terminate jobs
- `claude_dashboard`: System metrics
- `claude_recursion_stats`: Recursion statistics

### Claude Code V2 (6 Tools)
- `spawn_agent`: Fire-and-forget single agent
- `spawn_parallel_agents`: Spawn multiple agents
- `collect_results`: Gather completed results
- `check_agent_health`: Monitor agent status
- `kill_agent`: Terminate specific agent
- `aggregate_results`: Combine multiple results

### Claude Code V3 (2 Tools)
- `claude_run_v3`: Intelligent multi-mode execution
- `get_v3_status`: Server capabilities and configuration

## Troubleshooting

### Common Issues and Solutions

#### Context Bridge Pydantic Errors
```python
# Fixed by adding to config.py:
model_config = {
    "extra": "ignore",
    "env_prefix": "CONTEXT_BRIDGE_"
}
```

#### V2 Asyncio "Already Running" Error
```python
# Use direct MCP run instead of asyncio:
server.mcp.run()  # NOT asyncio.run(server.run())
```

#### JSON Output Corruption
```python
# Use stderr for all logging:
logging.StreamHandler(sys.stderr)
```

#### Import Errors
Servers use lazy imports to prevent initialization issues. Access through the parent module:
```python
import opsvi_mcp.servers
# Then access submodules
```

## Project Structure

```
opsvi-mcp/
├── opsvi_mcp/
│   ├── servers/
│   │   ├── claude_code/        # V1: Traditional
│   │   ├── claude_code_v2/     # V2: Fire-and-forget
│   │   ├── claude_code_v3/     # V3: Multi-agent
│   │   ├── openai_codex/       # GPT-4 integration
│   │   ├── cursor_agent/       # Cursor IDE
│   │   └── context_bridge/     # Knowledge sharing
│   ├── clients/                # MCP client examples
│   └── templates/              # Server templates
├── docs/                       # Documentation
├── tests/                      # Test suite
└── requirements.txt           # Dependencies
```

## Advanced Usage

### Orchestrating Multiple Servers
```python
from opsvi_mcp.servers.unified_orchestrator import UnifiedMCPOrchestrator

orchestrator = UnifiedMCPOrchestrator()

# Complete workflow across all servers
result = await orchestrator.analyze_and_implement(
    requirements="Build user authentication system",
    language="python",
    visualize=True  # Uses Cursor for diagrams
)
```

### Custom Agent Profiles (V2)
```python
await spawn_agent({
    "task": "Complex analysis",
    "agent_profile": "deep_analysis",
    "timeout": 600000,
    "output_dir": "/custom/path"
})
```

### Recovery from Timeouts (V3)
```python
# V3 automatically handles timeouts with checkpointing
result = await claude_run_v3(
    task="Very complex task",
    mode="FULL_CYCLE",
    enable_checkpointing=True,
    checkpoint_interval=60000  # 1 minute
)
```

## Performance Tuning

### Concurrency Settings
```bash
# V1: Traditional limits
export CLAUDE_MAX_CONCURRENT_JOBS=8

# V2: High parallelism
export CLAUDE_MAX_CONCURRENT_L1=10

# V3: Adaptive by depth
export CLAUDE_BASE_CONCURRENCY_D0=10
export CLAUDE_BASE_CONCURRENCY_D1=8
export CLAUDE_BASE_CONCURRENCY_D2=6
```

### Timeout Configuration
```bash
# Dynamic timeouts based on task complexity
export CLAUDE_ENABLE_ADAPTIVE_TIMEOUT=true
export CLAUDE_BASE_TIMEOUT=300000      # 5 minutes
export CLAUDE_MAX_TIMEOUT=1800000      # 30 minutes
```

## Development

### Running Tests
```bash
cd /home/opsvi/master_root/libs/opsvi-mcp
python -m pytest tests/
```

### Adding New Servers
1. Create directory under `opsvi_mcp/servers/`
2. Implement with FastMCP framework
3. Add configuration to unified config
4. Update orchestrator if needed
5. Document in this README

## Recent Updates

- **V3 Added**: Multi-agent orchestration with 10 execution modes
- **V2 Fixed**: Asyncio issues resolved with direct MCP run
- **Context Bridge Fixed**: Pydantic validation errors resolved
- **Lazy Imports**: Prevent initialization conflicts
- **Logging Fixed**: All output to stderr to prevent JSON corruption

## Contributing

Please ensure:
1. All code follows existing patterns
2. Tests are included for new features
3. Documentation is updated
4. Error handling is comprehensive
5. Logging uses stderr only

## Support

- Check `/tmp/*_server.log` files for debugging
- Review CLAUDE_CODE_TOOLS_GUIDE.md for detailed tool usage
- See docs/ directory for architecture details
- Report issues with full error logs and configuration

## License

Proprietary - OPSVI Internal Use