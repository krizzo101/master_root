# Strategic Plan: Parallel Spawning & Architecture Refactoring

## Current State Analysis
- **Working**: Claude MCP server with recursive spawning capability
- **Limitation**: Jobs at same depth level execute sequentially, not in parallel
- **Issue**: Architectural problems with misplaced packages in shared libraries

## Phase 1: Enable Parallel Spawning at Same Depth (1-2 days)

### 1.1 Enhance RecursionManager
```python
# Add to recursion_manager.py
def get_siblings_at_depth(self, depth: int, parent_job_id: str) -> List[str]:
    """Get all sibling jobs at the same depth level"""
    
def can_spawn_parallel(self, depth: int) -> bool:
    """Check if we can spawn more parallel jobs at this depth"""
```

### 1.2 Modify JobManager for Parallel Execution
```python
# Enhance job_manager.py
async def execute_parallel_jobs(self, jobs: List[ClaudeJob]) -> Dict[str, Any]:
    """Execute multiple jobs in parallel at the same depth"""
    tasks = [self.execute_job_async(job) for job in jobs]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return dict(zip([job.id for job in jobs], results))
```

### 1.3 Add Batch Job Creation API
```python
# Add to server.py
@mcp.tool()
async def claude_run_batch(
    tasks: List[str],
    shared_context: Optional[Dict] = None,
    parentJobId: Optional[str] = None
) -> str:
    """Run multiple Claude Code tasks in parallel at the same depth"""
```

## Phase 2: Test & Validate Parallel Execution (1 day)

### 2.1 Create Test Suite
- Test parallel execution at same depth
- Verify resource limits are respected
- Confirm results aggregation works correctly

### 2.2 Performance Benchmarks
- Measure speedup from parallel execution
- Monitor resource usage
- Validate error handling

## Phase 3: Use Parallel Spawning for Architecture Refactoring (3-5 days)

### 3.1 Parallel Refactoring Tasks

#### Task Set A: Library Reorganization (Parallel)
```python
parallel_tasks = [
    "Move MCP-specific code from opsvi-shared to opsvi-mcp",
    "Extract Claude-specific code into dedicated package",
    "Reorganize database interfaces in opsvi-shared",
    "Clean up duplicate MCP clients across packages"
]
```

#### Task Set B: Code Migration (Parallel)
```python
migration_tasks = [
    "Migrate libs/opsvi-shared/opsvi_shared/mcp/* to libs/opsvi-mcp/opsvi_mcp/clients/",
    "Move libs/opsvi-shared/opsvi_shared/database/mcp_* to libs/opsvi-mcp/opsvi_mcp/database/",
    "Relocate Claude integration from opsvi-orch to opsvi-agents/",
    "Consolidate MCP tools from opsvi-ecosystem to opsvi-mcp/"
]
```

#### Task Set C: Dependency Updates (Parallel)
```python
dependency_tasks = [
    "Update imports in opsvi-ecosystem after MCP moves",
    "Fix imports in opsvi-asea after database moves", 
    "Update opsvi-orch references to Claude components",
    "Verify and fix all cross-package dependencies"
]
```

### 3.2 Coordination Strategy
```python
# Master orchestration script
async def refactor_architecture():
    # Phase 1: Analysis (sequential)
    analysis = await claude_run("Analyze all import dependencies")
    
    # Phase 2: Parallel refactoring
    results = await claude_run_batch([
        "Refactor libs/opsvi-mcp package structure",
        "Refactor libs/opsvi-shared package structure",
        "Refactor libs/opsvi-orch package structure",
        "Refactor libs/opsvi-ecosystem package structure"
    ])
    
    # Phase 3: Integration testing (parallel)
    tests = await claude_run_batch([
        "Test MCP server functionality",
        "Test database interfaces",
        "Test Claude integration",
        "Test ecosystem tools"
    ])
    
    # Phase 4: Final validation
    validation = await claude_run("Validate all changes and create PR")
```

## Phase 4: Architecture Target State

### 4.1 Clean Package Structure
```
libs/
├── opsvi-mcp/           # All MCP-related code
│   ├── clients/          # MCP client implementations
│   ├── servers/          # MCP server implementations
│   └── database/         # MCP-specific database interfaces
├── opsvi-shared/         # Truly shared utilities only
│   ├── utils/            # Generic utilities
│   └── core/             # Core abstractions
├── opsvi-agents/         # Agent implementations
│   ├── claude/           # Claude-specific code
│   ├── gemini/           # Gemini-specific code
│   └── openai/           # OpenAI-specific code
└── opsvi-ecosystem/      # Applications using agents
    └── applications/     # Clean app implementations
```

### 4.2 Migration Checklist
- [ ] No MCP code in opsvi-shared
- [ ] No Claude code in opsvi-orch
- [ ] No duplicate MCP clients
- [ ] Clear separation of concerns
- [ ] All tests passing
- [ ] Documentation updated

## Implementation Commands

### Step 1: Enable Parallel Spawning
```bash
# Update recursion manager for parallel support
claude_run "Add parallel spawning support to libs/opsvi-mcp/opsvi_mcp/servers/claude_code/recursion_manager.py"

# Update job manager for batch execution
claude_run "Add batch job execution to libs/opsvi-mcp/opsvi_mcp/servers/claude_code/job_manager.py"

# Add batch API endpoint
claude_run "Add claude_run_batch tool to libs/opsvi-mcp/opsvi_mcp/servers/claude_code/server.py"
```

### Step 2: Test Parallel Execution
```bash
# Create and run test suite
claude_run "Create parallel execution tests in libs/opsvi-mcp/tests/test_parallel_spawning.py"
```

### Step 3: Execute Architecture Refactoring
```bash
# Run the parallel refactoring
claude_run_batch([
    "Move all MCP clients from opsvi-shared to opsvi-mcp",
    "Extract Claude code from opsvi-orch to opsvi-agents",
    "Clean up duplicate implementations",
    "Update all import statements"
])
```

## Success Metrics
1. **Parallel Execution**: 3-5x speedup for multi-task operations
2. **Clean Architecture**: Zero misplaced packages
3. **Test Coverage**: 100% of moved code still functioning
4. **Documentation**: Complete migration guide

## Risk Mitigation
1. **Backup Strategy**: Git branches for each phase
2. **Rollback Plan**: Revert commits if issues arise
3. **Testing Protocol**: Test after each migration step
4. **Gradual Migration**: Move one package at a time

## Timeline
- **Phase 1**: 1-2 days (Parallel spawning)
- **Phase 2**: 1 day (Testing)
- **Phase 3**: 3-5 days (Architecture refactoring)
- **Total**: 5-8 days

## Next Immediate Actions
1. Implement `claude_run_batch` in server.py
2. Add parallel job tracking to JobManager
3. Create test script for parallel execution
4. Begin first refactoring batch