# Vendor-Provided Agent Patterns

This directory contains official patterns from major AI vendors and tool providers, extracted from `/home/opsvi/.reference/`.

## OpenAI Cookbook (12 files)

### Multi-Agent Investment Portfolio
**Source:** `openai-cookbook/examples/agents_sdk/multi-agent-portfolio-collaboration/`

- **pm.py** - Portfolio Manager agent
- **quant.py** - Quantitative analyst agent
- **fundamental.py** - Fundamental analysis agent
- **macro.py** - Macroeconomic analyst agent
- **editor.py** - Editor/reviewer agent
- **config.py** - Investment agents configuration

**Key Patterns:**
- Role-based specialization
- Agent collaboration for investment decisions
- Structured handoffs between agents

### Object-Oriented Agents
**Source:** `openai-cookbook/examples/object_oriented_agentic_approach/`

- **agent_signature.py** - Agent signature pattern
- **task_queue.py** - Task queue management
- Additional OOP agent patterns

**Key Patterns:**
- Object-oriented agent design
- Task queue for agent coordination
- Agent signature abstraction

## OpenAI Evals (3 files)

**Source:** `evals/evals/solvers/providers/openai/`

- **openai_solver.py** - Base OpenAI solver
- **openai_assistants_solver.py** - Assistants API solver
- **openai_solver_mixin.py** - Solver mixin patterns

**Key Patterns:**
- Solver abstraction for evaluations
- Assistants API integration
- Completion function patterns

## Deep Research MCP (1 file)

- **sample_mcp.py** - MCP server for deep research

**Key Pattern:**
- MCP server implementation for research tasks

## Valuable Vendor Insights

### 1. **Investment Agent Collaboration** (OpenAI Cookbook)
Shows how specialized agents collaborate on complex decisions:
```python
# From pm.py - Portfolio Manager coordinating specialists
agents = [
    QuantAnalyst(),
    FundamentalAnalyst(),
    MacroAnalyst()
]
consolidated_analysis = coordinate_agents(agents, market_data)
```

### 2. **Object-Oriented Agent Design** (OpenAI Cookbook)
Clean OOP patterns for agent implementation:
```python
# From agent_signature.py
class AgentSignature:
    def __init__(self, name, role, capabilities):
        self.name = name
        self.role = role
        self.capabilities = capabilities
```

### 3. **Solver Patterns** (OpenAI Evals)
Production-ready solver abstractions:
```python
# From openai_solver.py
class OpenAISolver(Solver):
    def solve(self, task):
        # Structured solving approach
```

## Integration with Our Design

These vendor patterns complement our collection:

1. **Role Specialization** - Investment agents show clear role boundaries
2. **Task Queues** - Object-oriented patterns for task management
3. **Solver Abstractions** - Clean interfaces for problem-solving agents
4. **Agent Signatures** - Metadata and capability descriptions

## Recommended Adoptions

### HIGH VALUE:
- Investment agent collaboration model (for financial/analytical tasks)
- Agent signature pattern (for capability discovery)
- Task queue management (for work distribution)

### MEDIUM VALUE:
- Solver abstractions (for standardized problem-solving)
- OOP agent patterns (for clean code structure)

### REFERENCE ONLY:
- Deep research MCP (specific to research tasks)

## Note
These are official patterns from OpenAI and other vendors, representing production-tested approaches. They're more conservative than experimental patterns but highly reliable.
