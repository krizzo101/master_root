# Architecture Refactoring Plan
## Balancing Immediate Needs with Long-term Architecture

## Current Situation

We have architectural debt but NEED a working Claude MCP server NOW to help fix the architecture itself. This creates a bootstrap problem: we need the tool to fix the tools.

## Phased Approach

### Phase 0: Document Current State (DONE ✅)
- Identified all architectural issues
- Documented what's wrong and why
- Created this plan

### Phase 1: Get MCP Server Working (PRIORITY 1) 🚨
**Goal**: Functional Claude MCP server with parallel spawning capability
**Timeline**: Immediate (1-2 days)
**Approach**: Pragmatic - make it work now, refactor later

#### Actions:
1. **Keep the current mixed architecture temporarily**
2. **Focus on making parallel spawning work**:
   - Fix any remaining bugs in the Send API implementation
   - Test actual Claude CLI spawning
   - Verify parallel execution works
   - Get the MCP server responding correctly

3. **Create working tests**:
   ```bash
   # Test parallel execution
   claude_run_batch_async(tasks=[
     "analyze libs/opsvi-comm",
     "analyze libs/opsvi-coord", 
     "analyze libs/opsvi-orch"
   ])
   ```

4. **Document minimum viable usage**:
   - How to start the MCP server
   - How to call parallel spawn functions
   - How to collect results

**Deliverable**: Working `claude_code` MCP server that can spawn 10+ Claude instances in parallel

### Phase 2: Use MCP Server to Help Refactor (PRIORITY 2) 🔧
**Goal**: Use our working tool to accelerate the refactoring
**Timeline**: 1 week
**Approach**: Eat our own dog food

#### Parallel Tasks for Claude Instances:
```python
refactoring_tasks = [
    "Create opsvi-claude package with all Claude CLI interaction code",
    "Extract Claude-specific code from opsvi-orch into opsvi-claude",
    "Extract Claude-specific code from opsvi-mcp into opsvi-claude",
    "Create abstract base classes in opsvi-foundation",
    "Clean up all template/boilerplate code in opsvi-comm",
    "Clean up all template/boilerplate code in opsvi-coord",
    "Define proper interfaces for executors in opsvi-foundation",
    "Create plugin architecture for opsvi-orch executors",
    "Separate workflow orchestration from execution orchestration",
    "Fix all exception hierarchies to use opsvi-foundation",
    "Create comprehensive test suites for each package",
    "Document dependency rules and architecture guidelines"
]
```

### Phase 3: Clean Architecture Implementation (PRIORITY 3) 📐
**Goal**: Proper separation of concerns
**Timeline**: 2 weeks (using parallel Claude instances)

#### New Package Structure:
```
libs/
├── opsvi-foundation/      # Base classes, interfaces, exceptions
│   ├── interfaces/
│   ├── exceptions/
│   └── base/
│
├── opsvi-claude/          # NEW: Claude-specific library
│   ├── client/            # CLI wrapper
│   ├── executor/          # Process spawning
│   ├── auth/              # Token handling
│   └── parser/            # Output parsing
│
├── opsvi-exec/            # NEW: Execution patterns (from opsvi-orch)
│   ├── patterns/          # Send API, parallel, recursive
│   ├── executors/         # Abstract executors
│   └── managers/          # Job management
│
├── opsvi-workflow/        # NEW: High-level orchestration (from opsvi-orch)
│   ├── dag/               # DAG management
│   ├── pipeline/          # Pipeline orchestration
│   └── celery/            # Celery integration
│
├── opsvi-mcp/             # MCP protocol implementations (cleaned)
│   └── servers/
│       └── claude_code/   # Uses opsvi-claude, opsvi-exec
│
└── opsvi-apps/            # Application assemblies
    └── claude-parallel/   # The working parallel Claude spawner
```

### Phase 4: Migration Without Breaking (PRIORITY 4) 🔄
**Goal**: Migrate without disrupting the working MCP server
**Timeline**: 1 week

1. **Create new packages alongside old ones**
2. **Gradually move code with forwarding imports**
3. **Update MCP server to use new packages**
4. **Deprecate old packages**
5. **Remove old packages**

## Tracking Plan

### Use Our Own Tool for Project Management

Create a meta-task that the Claude MCP server manages:
```python
project = {
    "name": "Architecture Refactoring",
    "phases": [
        {
            "name": "Phase 1: Get MCP Working",
            "tasks": [...],
            "assigned_to": "single_claude_instance"
        },
        {
            "name": "Phase 2: Parallel Refactoring", 
            "tasks": [...],
            "assigned_to": "parallel_claude_instances"
        }
    ]
}
```

### Success Metrics

1. **Phase 1 Success**: Can spawn 10+ Claude instances that work in parallel
2. **Phase 2 Success**: Refactoring tasks completed 10x faster than serial
3. **Phase 3 Success**: Clean architecture with no cross-contamination
4. **Phase 4 Success**: Zero downtime migration

## The Critical Path

```mermaid
graph LR
    A[Fix Current MCP] --> B[Test Parallel Spawning]
    B --> C[Use MCP to Refactor]
    C --> D[Clean Architecture]
    D --> E[Migrate Without Breaking]
```

## Immediate Next Steps (DO RIGHT NOW)

1. **Test the current MCP server**:
   ```bash
   cd libs/opsvi-mcp
   python -m opsvi_mcp.servers.claude_code
   ```

2. **Fix any immediate bugs preventing parallel execution**

3. **Create a simple test script**:
   ```python
   # test_parallel.py
   from opsvi_mcp.servers.claude_code import parallel_spawn
   
   tasks = [
       "Write a hello world in Python",
       "Write a hello world in JavaScript",
       "Write a hello world in Go"
   ]
   
   results = parallel_spawn(tasks)
   print(results)
   ```

4. **Once working, immediately use it to accelerate refactoring**

## Why This Plan Works

1. **Pragmatic**: Gets us a working tool immediately
2. **Self-accelerating**: Uses the tool to fix itself
3. **Non-breaking**: Maintains working system throughout
4. **Tracked**: Every task is documented and assignable
5. **Parallel**: Leverages the very feature we're building

## Anti-patterns to Avoid

❌ Don't try to fix architecture before having working tool
❌ Don't break the working MCP server during refactoring
❌ Don't do refactoring serially when we have parallel capability
❌ Don't lose track of tasks - document everything
❌ Don't mix concerns while fixing - separate packages clearly

## The Bootstrap Solution

The key insight: **We need the hammer to build the hammer.**

So we:
1. Get a rough but working hammer (Phase 1)
2. Use it to build better tools (Phase 2)
3. Use those tools to build the final architecture (Phase 3)
4. Seamlessly transition (Phase 4)

This way we never lose momentum and can use parallel Claude instances to do in days what would take weeks serially.