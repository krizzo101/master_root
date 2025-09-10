# Project-Context Parallel Implementation with Agent Orchestrator

## Strategy: Use 15 Parallel Agents to Build 21 Tools

### Phase 1: Database Setup (Single Agent)
```python
import sys
from pathlib import Path
sys.path.append('/home/opsvi/master_root/apps/agent-orchestrator/src')
from generic_orchestrator import GenericOrchestrator, AgentTask

orchestrator = GenericOrchestrator(
    output_dir=Path("/home/opsvi/master_root/apps/project-context"),
    max_parallel=15
)

# Database connection setup
db_task = AgentTask(
    task_id="setup_db_connections",
    task_type="development",
    prompt="""
    Create database connection module at src/project_context/db/connections.py:
    - PostgreSQL connection with asyncpg
    - Neo4j connection with async driver
    - Redis connection for Context Bridge
    - Connection pooling and error handling
    Use connection strings from UNIFIED_CONTEXT_SYSTEM_FINAL_DESIGN.md
    """,
    dependencies=[]
)
```

### Phase 2: Parallel Tool Implementation (15 Agents)

```python
# Create tasks for all 21 tools, grouped for parallel execution
tool_tasks = []

# Group 1: Discovery Tools (4 tools, 4 agents)
discovery_tools = [
    ("get_project_summary", "Overall project statistics"),
    ("find_files", "Search files by pattern"),
    ("get_file_info", "Detailed file information"),
    ("find_symbols", "Search functions/classes")
]

for tool_name, description in discovery_tools:
    tool_tasks.append(AgentTask(
        task_id=f"implement_{tool_name}",
        task_type="development",
        prompt=f"""
        Implement MCP tool '{tool_name}' in src/project_context/tools/discovery.py:
        - Description: {description}
        - Query PostgreSQL tables: context_items, code_elements
        - Query Neo4j for relationships if needed
        - Return JSON response with proper error handling
        - Use asyncpg for PostgreSQL queries
        - Follow the schema in UNIFIED_CONTEXT_SYSTEM_FINAL_DESIGN.md
        """,
        dependencies=["setup_db_connections"]
    ))

# Group 2: Architecture Tools (5 tools, 5 agents)
architecture_tools = [
    ("get_dependencies", "Project dependency graph"),
    ("find_agents", "Discover agent architectures"),
    ("get_entry_points", "Find CLI/main entries"),
    ("get_api_endpoints", "List API routes"),
    ("get_data_models", "Find data structures")
]

for tool_name, description in architecture_tools:
    tool_tasks.append(AgentTask(
        task_id=f"implement_{tool_name}",
        task_type="development",
        prompt=f"""
        Implement MCP tool '{tool_name}' in src/project_context/tools/architecture.py:
        - Description: {description}
        - Focus on Neo4j graph queries for relationships
        - Combine with PostgreSQL code_elements table
        - Implement efficient graph traversal
        """,
        dependencies=["setup_db_connections"]
    ))

# Group 3: Quality Tools (3 tools, 3 agents)
quality_tools = [
    ("get_tests", "Test file mapping"),
    ("get_config", "Configuration overview"),
    ("get_quality_metrics", "Code quality stats")
]

for tool_name, description in quality_tools:
    tool_tasks.append(AgentTask(
        task_id=f"implement_{tool_name}",
        task_type="development",
        prompt=f"""
        Implement MCP tool '{tool_name}' in src/project_context/tools/quality.py:
        - Description: {description}
        - Query monitoring_metrics for quality data
        - Aggregate from code_elements complexity scores
        """,
        dependencies=["setup_db_connections"]
    ))

# Group 4: Analysis Tools (4 tools, 3 agents)
analysis_tools = [
    ("get_call_graph", "Function relationships"),
    ("get_imports", "Import analysis"),
    ("get_complexity", "Complexity metrics"),
    ("get_documentation", "Doc coverage")
]

# Continue with remaining groups...

# Execute all tool implementations in parallel!
results = await orchestrator.execute_batch(tool_tasks)
```

### Phase 3: Integration Tasks (Parallel)

```python
integration_tasks = [
    AgentTask(
        task_id="context_bridge_integration",
        task_type="development",
        prompt="""
        Integrate Context Bridge in src/project_context/integrations/context_bridge.py:
        - Subscribe to IDE context events
        - Cache current IDE state
        - Merge IDE context with database queries
        """,
        dependencies=["setup_db_connections"]
    ),
    AgentTask(
        task_id="caching_layer",
        task_type="development",
        prompt="""
        Implement caching in src/project_context/core/cache.py:
        - Use aiocache for async caching
        - TTL: 60s for file data, 300s for project stats
        - Cache invalidation on changes
        """,
        dependencies=["setup_db_connections"]
    ),
    AgentTask(
        task_id="query_optimizer",
        task_type="development",
        prompt="""
        Create query optimizer in src/project_context/db/optimizer.py:
        - Batch similar queries
        - Use materialized views when available
        - Query plan caching
        """,
        dependencies=["setup_db_connections"]
    )
]

# Run integration tasks in parallel
await orchestrator.execute_batch(integration_tasks)
```

### Phase 4: Testing (Parallel)

```python
# Create test tasks for each tool group
test_tasks = []

for tool_group in ["discovery", "architecture", "quality", "analysis", "maintenance"]:
    test_tasks.append(AgentTask(
        task_id=f"test_{tool_group}_tools",
        task_type="testing",
        prompt=f"""
        Create comprehensive tests for {tool_group} tools:
        - Unit tests with mocked databases
        - Integration tests with real connections
        - Performance benchmarks
        - Test file: tests/test_{tool_group}_tools.py
        """,
        dependencies=[f"implement_{tool}" for tool in tool_group_mapping[tool_group]]
    ))

# Run all tests in parallel
await orchestrator.execute_batch(test_tasks)
```

## Execution Timeline

With 15 parallel agents:
- **Sequential approach**: 21 tools × 30 min = 10.5 hours
- **Parallel approach**: 2 hours total!

### Timeline:
- 0:00 - 0:30: Database setup (1 agent)
- 0:30 - 1:00: Tool implementation (15 agents working on 21 tools)
- 1:00 - 1:30: Integration tasks (3 agents)
- 1:30 - 2:00: Testing (5 agents)

## Benefits of Parallel Implementation

1. **Speed**: 5-10x faster development
2. **Consistency**: All tools follow same pattern
3. **Quality**: Each agent focuses on specific domain
4. **Testing**: Parallel test development
5. **Documentation**: Auto-generated from implementations

## Monitoring Progress

```python
# Monitor all agents
async def monitor_implementation():
    while orchestrator.running_agents:
        status = orchestrator.get_status()
        print(f"Running: {len(status['running'])}")
        print(f"Completed: {len(status['completed'])}")
        print(f"Failed: {len(status['failed'])}")

        for task_id, agent_status in status['running'].items():
            print(f"  {task_id}: {agent_status['progress']}%")

        await asyncio.sleep(5)
```

## Error Recovery

```python
# If any task fails, retry with more context
failed_tasks = [t for t in results if not t.success]
for task in failed_tasks:
    retry_task = AgentTask(
        task_id=f"{task.task_id}_retry",
        task_type=task.task_type,
        prompt=f"{task.prompt}\n\nPrevious error: {task.error}\nPlease fix the issue.",
        dependencies=task.dependencies
    )
    await orchestrator.execute_agent(retry_task)
```

## Complete Implementation Script

```python
#!/usr/bin/env python3
"""Parallel implementation of project-context using agent orchestrator"""

import asyncio
import sys
from pathlib import Path

sys.path.append('/home/opsvi/master_root/apps/agent-orchestrator/src')
from generic_orchestrator import GenericOrchestrator, AgentTask

async def implement_project_context():
    orchestrator = GenericOrchestrator(
        output_dir=Path("/home/opsvi/master_root/apps/project-context"),
        max_parallel=15
    )

    # Phase 1: Setup
    print("Phase 1: Setting up database connections...")
    await orchestrator.execute_agent(db_task)

    # Phase 2: Parallel tool implementation
    print("Phase 2: Implementing 21 tools in parallel...")
    await orchestrator.execute_batch(tool_tasks)

    # Phase 3: Integration
    print("Phase 3: Integration tasks...")
    await orchestrator.execute_batch(integration_tasks)

    # Phase 4: Testing
    print("Phase 4: Testing all tools...")
    await orchestrator.execute_batch(test_tasks)

    print("✅ Project-context implementation complete!")

if __name__ == "__main__":
    asyncio.run(implement_project_context())
```

---

**With 15 parallel agents, I can build all 21 tools simultaneously instead of sequentially!**
