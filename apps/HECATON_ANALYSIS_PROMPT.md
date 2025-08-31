# HECATON Multi-Agent Orchestration System - Deep Analysis Request

## Executive Summary
HECATON is a sophisticated multi-agent orchestration framework designed to execute parallel Claude Code tasks using LangGraph's Send API. The system aims to provide 3-5x performance improvements through true parallel execution but currently has critical issues preventing proper operation.

## What HECATON Is Supposed to Do

### Core Functionality
1. **Parallel Agent Execution**: Spawn multiple Claude Code processes simultaneously using isolated git worktrees
2. **Token Management**: Manage a pool of CLAUDE_CODE_TOKEN credentials for parallel authentication
3. **Send API Integration**: Use LangGraph's Send API for true parallel node execution without asyncio limitations
4. **Worktree Isolation**: Each agent operates in its own git worktree to prevent conflicts
5. **Performance Monitoring**: Track and report execution metrics for optimization
6. **Agent Specialization**: Support different agent types (code, test, research, review, docs)

### Architecture Components
```
HECATON System Architecture:
├── Orchestration Layer (Send API)
│   ├── SendAPIOrchestrator: LangGraph-based parallel coordinator
│   ├── State Management: OrchestrationState dataclass
│   └── Routing Logic: Send objects for parallel dispatch
├── Execution Layer
│   ├── RealClaudeSubprocessExecutor: Spawns actual Claude CLI processes
│   ├── ClaudeCommandFactory: Builds optimized Claude commands
│   └── Process Management: Async subprocess handling
├── Resource Layer
│   ├── SecureTokenPool: Round-robin token distribution
│   ├── WorktreeManager: Git worktree creation/cleanup
│   └── PerformanceMonitor: Metrics collection
└── Agent Layer
    ├── AgentRegistry: Agent type management
    └── Specialized Agents: Code, Test, Research, Review, Docs
```

## Current Working State

### What Works
- ✅ Basic CLI structure and argument parsing
- ✅ Component initialization (token pool, worktree manager)
- ✅ Simple mode execution (sequential, single agent)
- ✅ Git worktree creation and cleanup
- ✅ UUID generation for Claude session IDs
- ✅ Import structure after fixes

### What's Broken

#### 1. Send API Implementation Issues
**Problem**: LangGraph Send API not executing parallel nodes correctly
- **Symptom**: Error "Expected dict, got [Send(...)]" initially, then "dict object has no attribute 'results'"
- **Root Cause**: Mismatch between how Send objects are returned and how LangGraph expects them
- **Location**: `/src/hecaton/orchestration/send_api.py` lines 183-205

#### 2. Command Prompt Missing
**Problem**: Claude command missing the actual task prompt
- **Symptom**: "Error: Input must be provided either through stdin or as a prompt argument when using --print"
- **Root Cause**: Complex prompt handling logic in command builder and executor
- **Location**: `/src/hecaton/agents/real_claude_executor.py` lines 143-165

#### 3. State Aggregation Failure
**Problem**: Aggregate function cannot access results from parallel executions
- **Symptom**: "'dict' object has no attribute 'results'"
- **Root Cause**: State not properly propagated between parallel nodes
- **Location**: `/src/hecaton/orchestration/send_api.py` lines 258-305

#### 4. Duplicate Worktree Creation
**Problem**: Same worktree being created multiple times in parallel
- **Symptom**: "fatal: '/tmp/hecaton_worktrees/agent_0_code_XXXX' already exists"
- **Root Cause**: Race condition or duplicate Send execution
- **Location**: Interaction between Send routing and worktree creation

## Identified Technical Issues

### LangGraph Integration
1. **Send API Pattern**: The current implementation doesn't match LangGraph's expected pattern for Send-based parallelism
2. **Conditional Edges**: Using `add_conditional_edges` but the routing function returns Send objects incorrectly
3. **State Updates**: Parallel nodes updating state aren't properly merged back

### Command Building
1. **Prompt Passing**: The logic for passing prompts via command line vs stdin is overly complex
2. **Command Array**: The command array construction doesn't properly include the prompt after "--"

### Process Execution
1. **Async/Sync Mismatch**: Using `asyncio.new_event_loop()` inside sync functions causes issues
2. **Error Handling**: Exceptions in parallel execution aren't properly propagated

## Deep Analysis Request

Please perform a comprehensive analysis of the attached HECATON codebase (`hecaton_complete.tar.gz`) focusing on:

### 1. LangGraph Send API Correction
- Analyze the current Send API implementation in `orchestration/send_api.py`
- Identify the exact pattern LangGraph expects for parallel execution
- Determine how state should be passed and merged between parallel nodes
- Fix the routing function and node return types

### 2. Command Execution Pipeline
- Trace the complete flow from task creation to Claude process spawning
- Identify where the prompt gets lost or malformed
- Simplify the command building logic in `ClaudeCommandFactory`
- Ensure prompts are properly passed for both short and long inputs

### 3. State Management
- Analyze how `OrchestrationState` flows through the graph
- Fix the aggregation function to properly collect results
- Ensure parallel nodes can update state without conflicts

### 4. Testing Strategy
- Create a minimal test that proves Send API works
- Build up to full parallel execution testing
- Ensure both simple and send-api modes function correctly

## Expected Deliverable

Please provide an **actionable, agent-optimized prompt** that a development agent can execute to:

1. **Fix all identified issues** with specific code changes
2. **Add missing functionality** for proper Send API integration
3. **Simplify complex logic** where it's causing problems
4. **Include verification steps** to prove each fix works
5. **Provide test commands** that demonstrate successful parallel execution

The prompt should be structured for maximum agent effectiveness:
- Clear, numbered steps
- Specific file paths and line numbers
- Exact code replacements
- Test commands between fixes
- Success criteria for each step

## Additional Context

### Environment
- Python 3.11+
- LangGraph 0.1.0+
- Git worktrees supported
- Claude CLI available at `claude` command
- Tokens via CLAUDE_CODE_TOKEN environment variable

### Recent Fix Attempts
1. Changed Send import from `langgraph.constants` to `langgraph.types`
2. Split planning and routing into separate functions
3. Fixed UUID generation for session IDs
4. Attempted various Send return patterns

### Test Commands
```bash
# Simple mode (works)
python -m hecaton run "Create hello world" --agents 1 --mode simple

# Send API mode (broken)
python -m hecaton run "Create hello world" --agents 2 --mode send-api

# Self-test (broken)
python -m hecaton test
```

## Success Criteria

The system is considered fixed when:
1. `python -m hecaton test` passes without errors
2. Send API mode successfully executes 2+ agents in parallel
3. All agents complete their tasks and results are aggregated
4. No worktree conflicts or command errors occur
5. Performance shows measurable improvement over sequential execution

---

**Please analyze the attached codebase and provide the detailed remediation prompt as specified above.**
