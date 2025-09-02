# Multi-Agent Reference Code Collection

This directory contains extracted reference code from multiple multi-agent implementations in the codebase. Use this as a reference library when building the new multi-agent orchestration solution.

## Directory Structure

### claude-code-server/
**Source:** `libs/opsvi-mcp/opsvi_mcp/servers/claude_code/`
- **server.py** - FastMCP-based MCP server with 8 tools for Claude Code execution
- **job_manager.py** - Job lifecycle management with subprocess execution
- **config.py** - Configuration management for the server
- **token_pool.py** - Token rotation and management
- **recursion_manager.py** - Recursion depth tracking and limits
- **parallel_enhancement.py** - Parallel job execution capabilities
- **models.py** - Data models for jobs and responses

**Key Patterns:**
- FastMCP server implementation
- Subprocess-based Claude Code execution
- Token pool rotation
- Job lifecycle management
- Git worktree isolation support

### multi-agent-monitor/
**Source:** `apps/multi-agent-monitor/`
- **orchestration/** - Complete orchestration subsystem
  - `token_pool.py` - SecureTokenPool with 15-token rotation
  - `worktree_manager.py` - Git worktree isolation for agents
  - `agent_coordinator.py` - Agent coordination logic
  - `task_manager.py` - Task distribution and management
- **models/** - Data models for agents and tasks
- **safety/** - Safety and rollback mechanisms
- **core/** - Core execution engines
  - `real_agent_executor.py` - Real agent execution
  - `swarm_executor.py` - Swarm coordination

**Key Patterns:**
- 15-token pool rotation for parallel execution
- Git worktree isolation per agent
- Safety mechanisms with rollback
- Swarm coordination patterns

### oamat-sd/
**Source:** `/home/opsvi/agent_world/src/applications/oamat_sd/`
- **smart_decomposition_agent.py** - Main orchestrator with O3 reasoning
- **execution_engine.py** - LangGraph StateGraph with Send API (3-5x performance)
- **agent_factory.py** - Dynamic agent creation with create_react_agent
- **o3_pipeline.py** - O3 reasoning and workflow generation
- **orchestration_interfaces.py** - ABC interfaces for orchestration
- **SMART_DECOMPOSITION_VISION.md** - Architecture vision document

**Key Patterns:**
- LangGraph Send API for parallel execution (CRITICAL: 3-5x performance)
- O3 reasoning for workflow generation
- Progressive autonomy system
- Dynamic agent creation
- Meta-intelligence architecture
- Strict enforcement patterns (Rules 950/956/997)

## Recommended Adoption Strategy

### HIGH VALUE - Adopt These:
1. **LangGraph Send API** (from OAMAT_SD)
   - Proven 3-5x performance improvement
   - Clean parallel execution pattern
   - See: `oamat-sd/execution_engine.py` lines 54-150

2. **Token Pool Management** (from multi-agent-monitor)
   - 15-token rotation for parallel Claude Code
   - Singleton pattern for global access
   - See: `multi-agent-monitor/orchestration/token_pool.py`

3. **Git Worktree Isolation** (from multi-agent-monitor)
   - Prevents agent conflicts
   - Complete workspace isolation
   - See: `multi-agent-monitor/orchestration/worktree_manager.py`

4. **FastMCP Server Pattern** (from claude-code-server)
   - Clean MCP tool implementation
   - Async/await patterns
   - See: `claude-code-server/server.py`

### MEDIUM VALUE - Consider These:
1. **Progressive Autonomy** (from OAMAT_SD)
   - Agents gain freedom through workflow stages
   - Reduces early-stage hallucination

2. **Job Manager Pattern** (from claude-code-server)
   - Clean job lifecycle management
   - Status tracking and cleanup

### LOW VALUE - Skip These:
1. **O3 Reasoning** - We're using Claude, not O3
2. **Complex Enforcement Rules** - Over-constraining
3. **Meta-Intelligence Philosophy** - Overengineered for our needs

## Integration Example

```python
# Combining the best patterns
from langgraph.constants import Send
from langgraph.graph import StateGraph

class MultiAgentOrchestrator:
    def __init__(self):
        # Token pool from multi-agent-monitor
        self.token_pool = SecureTokenPool(tokens=CLAUDE_TOKENS)

        # Worktree manager from multi-agent-monitor
        self.worktree_mgr = WorktreeManager()

        # LangGraph with Send API from OAMAT_SD
        self.graph = self._build_stategraph()

    def _build_stategraph(self):
        workflow = StateGraph(AgentState)

        # Send API pattern for parallel execution
        workflow.add_conditional_edges(
            "distribute",
            self._create_send_objects,
            ["execute_agent"]
        )

        return workflow.compile()
```

## Usage Notes

1. **Don't copy blindly** - Adapt patterns to our simpler architecture
2. **Test performance claims** - Verify 3-5x improvement with Send API
3. **Keep it simple** - We don't need all the complexity of OAMAT_SD
4. **Focus on Claude Code** - Our agents are Claude-based, not O3 or GPT

## File Organization

Files are organized by source system to maintain context about their original implementation and constraints. When borrowing code, consider the original context and adapt accordingly.
