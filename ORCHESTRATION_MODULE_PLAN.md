# Orchestration Module Development Plan for V1

## Current State Analysis

### 1. **Existing Orchestration Resources**

#### ✅ **Already Have LangGraph Interface**
- `/libs/opsvi-shared/opsvi_shared/interfaces/orchestration/langgraph_interface.py`
- Provides basic LangGraph StateGraph setup
- Includes Send API support (critical for parallel execution)
- Has checkpointing and streaming

#### ⚠️ **Have Skeleton Package**
- `/libs/opsvi-orchestration/` - Basic structure exists but incomplete
- Has broken imports in `__init__.py`
- Missing actual orchestration implementations

#### ❌ **NOT Extracted from OAMAT_SD**
- The OAMAT_SD patterns are still in `/agent_world/src/applications/oamat_sd/`
- NOT yet generalized into reusable libs
- Critical patterns like Send API usage not extracted

### 2. **Where Orchestration Modules Should Go**

Based on the libs structure, orchestration should be organized as:

```
libs/
├── opsvi-orchestration/          # Main orchestration package
│   └── opsvi_orchestration/
│       ├── patterns/             # NEW: Reusable patterns
│       │   ├── __init__.py
│       │   ├── langgraph_patterns.py  # Extract from OAMAT_SD
│       │   ├── send_api.py            # Parallel execution patterns
│       │   └── recursive_orchestration.py
│       ├── executors/            # NEW: Execution engines
│       │   ├── __init__.py
│       │   ├── parallel_executor.py   # From OAMAT subdivision_executor
│       │   └── recursive_executor.py  # For Claude recursion
│       └── managers/             # NEW: Job/task management
│           ├── __init__.py
│           ├── job_manager.py
│           └── recursion_manager.py
```

### 3. **What Needs to be Developed**

## Phase 1: Extract OAMAT_SD Patterns

### A. **Core LangGraph Patterns Module**
```python
# libs/opsvi-orchestration/opsvi_orchestration/patterns/langgraph_patterns.py

from langgraph.constants import Send
from langgraph.graph import StateGraph, END, START
from typing import List, Dict, Any, Callable

class ParallelOrchestrationPattern:
    """
    Extract the Send API pattern from OAMAT_SD execution_engine.py
    
    Key patterns to extract:
    - Send object creation for parallel execution
    - State dict handling (not TypedDict)
    - Conditional edges with Send routing
    """
    
    @staticmethod
    def create_parallel_sends(
        target_node: str,
        tasks: List[Dict[str, Any]]
    ) -> List[Send]:
        """Create Send objects for parallel execution"""
        return [Send(target_node, task) for task in tasks]
    
    @staticmethod
    def build_parallel_graph(
        state_type: type,
        node_functions: Dict[str, Callable],
        parallel_routing_func: Callable
    ) -> StateGraph:
        """Build graph with parallel execution pattern"""
        workflow = StateGraph(state_type)
        
        # Add nodes
        for name, func in node_functions.items():
            workflow.add_node(name, func)
        
        # Add parallel routing
        workflow.add_conditional_edges(
            "coordinator",
            parallel_routing_func,  # Returns Send objects
            # Send objects execute in parallel
        )
        
        return workflow
```

### B. **Recursive Orchestration Module**
```python
# libs/opsvi-orchestration/opsvi_orchestration/patterns/recursive_orchestration.py

class RecursiveOrchestrationPattern:
    """
    Combine V1 recursion with LangGraph Send API
    
    Features:
    - Depth tracking
    - Parent-child relationships
    - Fork bomb prevention
    - Parallel child spawning
    """
    
    def create_recursive_graph(self):
        """Build graph that supports recursive node spawning"""
        workflow = StateGraph(RecursiveJobState)
        
        # Nodes can spawn child nodes
        workflow.add_node("parent", self._parent_node)
        workflow.add_node("child", self._child_node)
        
        # Parallel child spawning via Send
        workflow.add_conditional_edges(
            "parent",
            self._spawn_children,  # Returns Send objects
        )
        
        # Children can spawn grandchildren
        workflow.add_conditional_edges(
            "child",
            self._spawn_grandchildren,
        )
        
        return workflow
```

## Phase 2: Create Shared Executors

### A. **Parallel Executor** (from subdivision_executor.py)
```python
# libs/opsvi-orchestration/opsvi_orchestration/executors/parallel_executor.py

class ParallelExecutor:
    """
    Generic parallel execution using LangGraph Send API
    Extracted from OAMAT_SD subdivision_executor.py
    """
    
    async def execute_parallel_tasks(
        self,
        tasks: List[Dict],
        executor_func: Callable,
        aggregator_func: Callable
    ):
        """Execute tasks in parallel and aggregate results"""
        # Build dynamic graph
        graph = self._build_parallel_graph(tasks, executor_func)
        
        # Execute with Send API parallelism
        results = await graph.ainvoke({"tasks": tasks})
        
        # Aggregate results
        return aggregator_func(results)
```

### B. **Recursive Executor** (for Claude V1)
```python
# libs/opsvi-orchestration/opsvi_orchestration/executors/recursive_executor.py

class RecursiveClaudeExecutor:
    """
    Execute Claude instances recursively with parallel spawning
    """
    
    def __init__(self, max_depth=5, max_concurrent={0:1, 1:10, 2:50}):
        self.max_depth = max_depth
        self.max_concurrent = max_concurrent
        self.graph = self._build_recursive_graph()
    
    async def execute_with_recursion(self, task: str, parent_id: str = None):
        """Execute task with recursive child spawning"""
        state = {
            "task": task,
            "parent_id": parent_id,
            "depth": self._get_depth(parent_id),
        }
        
        # Validate recursion limits
        if not self._can_spawn(state):
            raise RecursionLimitError()
        
        # Execute through graph
        return await self.graph.ainvoke(state)
```

## Phase 3: Integration with V1

### A. **Enhanced V1 Job Manager**
```python
# libs/opsvi-mcp/opsvi_mcp/servers/claude_code/enhanced_job_manager.py

from opsvi_orchestration.executors import RecursiveClaudeExecutor
from opsvi_orchestration.patterns import ParallelOrchestrationPattern

class EnhancedJobManager:
    """V1 Job Manager enhanced with LangGraph orchestration"""
    
    def __init__(self):
        self.executor = RecursiveClaudeExecutor()
        self.orchestrator = ParallelOrchestrationPattern()
    
    async def execute_batch_async(
        self,
        tasks: List[str],
        parent_job_id: str = None
    ) -> List[str]:
        """
        New batch execution using LangGraph Send API
        Spawns all children in parallel
        """
        # Create Send objects for parallel spawning
        sends = self.orchestrator.create_parallel_sends(
            "claude_executor",
            [{"task": t, "parent_id": parent_job_id} for t in tasks]
        )
        
        # Execute through LangGraph
        results = await self.executor.execute_parallel(sends)
        
        return [r["job_id"] for r in results]
```

### B. **New MCP Tools for V1**
```python
# Add to V1 server.py

@mcp.tool()
async def claude_run_batch_async(
    tasks: List[str],
    parentJobId: Optional[str] = None
) -> str:
    """
    Spawn multiple Claude instances in parallel
    Uses LangGraph Send API for true parallelism
    """
    job_ids = await enhanced_job_manager.execute_batch_async(
        tasks=tasks,
        parent_job_id=parentJobId
    )
    
    return json.dumps({
        "jobIds": job_ids,
        "count": len(job_ids),
        "status": "all_spawned_parallel"
    })
```

## Implementation Steps

### Step 1: Extract Core Patterns (Week 1)
1. Copy execution_engine.py patterns to `opsvi-orchestration/patterns/`
2. Copy subdivision_executor.py patterns
3. Generalize for reuse
4. Add proper error handling

### Step 2: Build Executors (Week 2)
1. Create ParallelExecutor class
2. Create RecursiveExecutor class
3. Integrate with existing RecursionManager
4. Add resource limits

### Step 3: Integrate with V1 (Week 3)
1. Create EnhancedJobManager
2. Add batch spawning tools
3. Update MCP configuration
4. Test recursive parallel execution

### Step 4: Testing & Documentation (Week 4)
1. Unit tests for patterns
2. Integration tests for executors
3. End-to-end tests with Claude
4. Documentation and examples

## Benefits of This Approach

1. **Reusable Components**: Extract OAMAT_SD patterns once, use everywhere
2. **Clean Architecture**: Separation of concerns (patterns, executors, managers)
3. **Proven Patterns**: Using battle-tested code from OAMAT_SD
4. **Incremental Migration**: Can enhance V1 without breaking existing functionality
5. **Future-Proof**: Other projects can use the same orchestration libraries

## Critical Success Factors

1. **Preserve OAMAT_SD Rules**:
   - NO asyncio.gather (use Send API)
   - State as dict, not TypedDict
   - Separate node and routing functions

2. **Maintain V1 Compatibility**:
   - Keep existing tools working
   - Add new batch tools alongside
   - Backward compatible

3. **Enable True Parallelism**:
   - Send API for parallel spawning
   - Each level can spawn multiple children
   - Results aggregate properly

## Next Actions

1. **Create the directory structure** in `libs/opsvi-orchestration/`
2. **Extract the first pattern** from OAMAT_SD execution_engine.py
3. **Create a simple test** to verify LangGraph Send API works
4. **Build the recursive executor** with depth tracking
5. **Integrate with V1** via new batch tools

This modular approach ensures we build reusable orchestration components that can be shared across all OPSVI projects, not just V1.