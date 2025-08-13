# MCP Server Integrations

This directory contains MCP (Model Context Protocol) server implementations for integrating various AI tools and services. The servers can work independently or be orchestrated together for complex workflows.

## Available Servers

### 1. Claude Code Server (`claude_code/` and `claude_code_v2/`)

**Purpose**: Recursive agent execution for complex multi-step tasks

**Versions**:
- **Original**: Traditional async/await pattern with job tracking
- **V2**: Fire-and-forget pattern with first-level decoupling (recommended)

**Key Features**:
- Recursive task decomposition
- Parallel agent execution
- Job management and monitoring
- Performance tracking

**MCP Tools**:
- `claude_run`: Synchronous execution
- `claude_run_async`: Asynchronous execution with job tracking
- `spawn_agent`: Fire-and-forget agent spawning (v2)
- `collect_results`: Collect results from spawned agents (v2)

### 2. OpenAI Codex Server (`openai_codex/`)

**Purpose**: Code generation, completion, and analysis using OpenAI's GPT-4

**Key Features**:
- Multiple operation modes (generate, complete, explain, refactor, debug, test, document, review, translate)
- Context file inclusion
- Response caching
- Streaming support

**MCP Tools**:
- `codex_complete`: Complete partial code
- `codex_generate`: Generate code from natural language
- `codex_explain`: Explain code functionality
- `codex_refactor`: Improve code quality
- `codex_debug`: Debug and fix code
- `codex_test`: Generate test cases
- `codex_document`: Generate documentation
- `codex_review`: Review code quality
- `codex_translate`: Translate between programming languages

### 3. Cursor Agent Server (`cursor_agent/`)

**Purpose**: Programmatic interaction with Cursor IDE agents

**Key Features**:
- Support for built-in agents (@diagram, @code_review, @documentation, etc.)
- Custom agent support from `.cursor/prompts/`
- Multiple communication methods (WebSocket, file-based, named pipe, CLI)
- High-contrast diagram generation with accessibility features

**MCP Tools**:
- `invoke_cursor_agent`: Invoke any Cursor agent
- `create_diagram`: Create diagrams using @diagram agent
- `review_code`: Review code using @code_review agent
- `generate_documentation`: Generate docs using @documentation agent
- `invoke_custom_agent`: Invoke custom agents
- `list_available_agents`: List all available agents

### 4. Context Bridge Server (`context_bridge/`)

**Purpose**: Bridge context between different MCP servers and tools

**Key Features**:
- Knowledge aggregation
- Context sharing between agents
- Neo4j integration support

## Unified Orchestrator

The `unified_orchestrator.py` provides integrated workflows that combine multiple servers:

### Orchestrated Workflows

1. **Analyze and Implement**
   - Claude analyzes requirements
   - Codex generates implementation
   - Cursor creates visualization

2. **Code Review Pipeline**
   - Cursor reviews code
   - Codex fixes identified issues
   - Claude verifies fixes

3. **Documentation Workflow**
   - Cursor generates documentation
   - Codex creates tests
   - Cursor creates flow diagrams

4. **Parallel Analysis**
   - Multiple perspectives analyzed simultaneously
   - Results aggregated from all servers

## Configuration

### Environment Variables

Required:
```bash
export CLAUDE_CODE_TOKEN="your-claude-token"
export OPENAI_API_KEY="your-openai-key"
```

Optional:
```bash
export CURSOR_WORKSPACE="/path/to/workspace"
export CURSOR_WS_PORT="7070"
export CODEX_MODEL="gpt-4"
export CLAUDE_RESULTS_DIR="/tmp/claude_results"
```

### Unified Configuration

See `unified_config.yaml` for complete configuration options:

```yaml
servers:
  claude_code:
    enabled: true
    version: v2
    config:
      # Claude configuration
  
  openai_codex:
    enabled: true
    config:
      # Codex configuration
  
  cursor_agent:
    enabled: true
    config:
      # Cursor configuration
```

## Usage Examples

### Standalone Server Usage

```python
# Claude Code V2
from opsvi_mcp.servers.claude_code_v2 import ClaudeCodeV2Server

server = ClaudeCodeV2Server()
await server.spawn_agent({
    "task": "Analyze the codebase",
    "output_dir": "/tmp/results"
})
```

```python
# OpenAI Codex
from opsvi_mcp.servers.openai_codex import OpenAICodexServer

server = OpenAICodexServer()
result = await server.codex_generate(
    prompt="Create a REST API for user management",
    language="python"
)
```

```python
# Cursor Agent
from opsvi_mcp.servers.cursor_agent import CursorAgentServer

server = CursorAgentServer()
result = await server.create_diagram(
    data={"system": "architecture"},
    diagram_type="flowchart"
)
```

### Orchestrated Usage

```python
from opsvi_mcp.servers.unified_orchestrator import UnifiedMCPOrchestrator

orchestrator = UnifiedMCPOrchestrator()

# Complete development workflow
result = await orchestrator.analyze_and_implement(
    requirements="Build a task management system",
    language="typescript",
    visualize=True
)

# Code review with fixes
result = await orchestrator.code_review_pipeline(
    code=my_code,
    language="python",
    fix_issues=True
)
```

## Communication Methods

### Cursor Agent Communication

1. **WebSocket** (Default)
   - Real-time bidirectional communication
   - Requires Cursor WebSocket server running

2. **File-based**
   - Writes requests to `.cursor/agent_requests/`
   - Reads responses from `.cursor/agent_outputs/`
   - Good for async operations

3. **Named Pipe** (Unix/Linux only)
   - Uses system pipes for communication
   - Low latency

4. **CLI**
   - Direct invocation via `cursor` command
   - Simplest but least flexible

## Architecture

```
┌─────────────────────────────────────────┐
│        Unified MCP Orchestrator         │
├─────────────┬───────────┬───────────────┤
│             │           │               │
│    Claude   │  OpenAI   │    Cursor     │
│    Code     │  Codex    │    Agent      │
│    Server   │  Server   │    Server     │
│             │           │               │
├─────────────┼───────────┼───────────────┤
│   FastMCP   │  FastMCP  │   FastMCP     │
└─────────────┴───────────┴───────────────┘
```

## Best Practices

1. **Use V2 Claude Code** for better scalability and protocol compliance
2. **Enable caching** for OpenAI Codex to reduce API costs
3. **Configure appropriate timeouts** for long-running operations
4. **Use WebSocket communication** with Cursor for real-time interactions
5. **Implement proper error handling** for network failures
6. **Monitor resource usage** with performance metrics

## Security Considerations

1. **API Keys**: Store securely in environment variables or secrets management
2. **Agent Permissions**: Configure allowed/blocked agents in Cursor config
3. **File Access**: Limit context file access to specific directories
4. **Network Security**: Use TLS for WebSocket connections in production
5. **Input Validation**: Validate all inputs before passing to agents

## Troubleshooting

### Claude Code Issues
- Check `CLAUDE_CODE_TOKEN` is set
- Verify recursion limits aren't exceeded
- Check `/tmp/claude_results/` for output files

### OpenAI Codex Issues
- Verify `OPENAI_API_KEY` is valid
- Check API rate limits
- Clear cache if getting stale results

### Cursor Agent Issues
- Ensure Cursor IDE is running
- Check WebSocket port availability
- Verify agent names are correct (include @ prefix)

## Contributing

To add a new MCP server:

1. Create a new directory under `servers/`
2. Implement the server following the pattern:
   - `__init__.py`: Package initialization
   - `config.py`: Configuration dataclass
   - `models.py`: Pydantic models
   - `server.py`: FastMCP server implementation
3. Add configuration to `unified_config.yaml`
4. Update `unified_orchestrator.py` to include the new server
5. Document the integration in this README

## License

See the main project LICENSE file.