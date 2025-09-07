# 🔍 HOW AGENTS DISCOVER & USE THE ORCHESTRATOR

**The Critical Question**: How do agents know to use the orchestrator and set up complex scenarios like parallel execution tests?

## 🎯 DISCOVERY PROCESS FOR NEW AGENTS

### **1. Auto-Discovery Through Knowledge Base**

When agents start a session, they should query the knowledge base for orchestrator information:

```python
# Essential startup queries every agent should run
mcp__knowledge__knowledge_query(
    query_type="search",
    search_text="orchestrator parallel agent coordination",
    limit=5
)
```

**What this reveals**:
- Orchestrator location: `/home/opsvi/master_root/apps/agent-orchestrator/`
- Current validation status: 100% success rate, production-ready
- Key capabilities: parallel execution, token management, dependency handling

### **2. File System Discovery**

Agents can discover the orchestrator through systematic exploration:

```python
# Look for orchestrator directories
find /home/opsvi/master_root -name "*orchestrator*" -type d

# Expected result: /home/opsvi/master_root/apps/agent-orchestrator/
```

### **3. Documentation Discovery**

Once found, agents should read key documentation files in priority order:

```bash
# Priority 1: Usage and setup
apps/agent-orchestrator/ORCHESTRATOR_USAGE_README.md
apps/agent-orchestrator/HOW_AGENTS_DISCOVER_AND_USE_ORCHESTRATOR.md (this file)

# Priority 2: Examples and tutorials
apps/agent-orchestrator/docs/TUTORIALS.md
apps/agent-orchestrator/examples/README.md

# Priority 3: Technical details
apps/agent-orchestrator/README.md
apps/agent-orchestrator/docs/ARCHITECTURE.md
```

---

## 🚀 QUICK SETUP FOR NEW AGENTS

### **Step 1: Basic Validation Test**

Before attempting complex scenarios, validate the orchestrator works:

```python
#!/usr/bin/env python3
"""Minimal orchestrator validation for new agents"""

import asyncio
from pathlib import Path
import sys

# Add orchestrator to Python path
sys.path.append('/home/opsvi/master_root/apps/agent-orchestrator/src')

from generic_orchestrator import GenericOrchestrator, AgentTask

async def basic_orchestrator_test():
    """Test if orchestrator is working with minimal setup"""

    # 1. Initialize orchestrator
    orchestrator = GenericOrchestrator(
        output_dir=Path("./test_output"),
        max_parallel=2  # Start small
    )

    # 2. Create simple test task
    task = AgentTask(
        task_id="validation_test",
        task_type="general-purpose",
        prompt="Say 'Hello from orchestrator!' and confirm you are working"
    )

    # 3. Execute and validate
    try:
        results = await orchestrator.execute_batch([task])
        print("✅ Orchestrator is working!")
        print(f"Result: {results[0].get('result', 'No result')}")
        return True
    except Exception as e:
        print(f"❌ Orchestrator failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(basic_orchestrator_test())
```

### **Step 2: Token Pool Validation**

Check if you have sufficient tokens for parallel execution:

```python
async def check_token_pool():
    """Validate token pool configuration"""
    from token_loader import TokenLoader

    loader = TokenLoader()
    tokens = loader.load_tokens()

    print(f"Token pool size: {len(tokens)}")
    if len(tokens) >= 2:
        print("✅ Sufficient tokens for parallel execution")
        return True
    else:
        print("❌ Need at least 2 tokens for orchestrator")
        return False
```

### **Step 3: Multi-Agent Test**

Once validated, test multi-agent coordination:

```python
async def multi_agent_test():
    """Test coordinating multiple specialized agents"""

    orchestrator = GenericOrchestrator(
        output_dir=Path("./multi_agent_test"),
        max_parallel=3
    )

    # Create diverse agent tasks
    tasks = [
        AgentTask(
            task_id="researcher",
            task_type="research-genius",
            prompt="Research the benefits of multi-agent systems"
        ),
        AgentTask(
            task_id="analyzer",
            task_type="solution-architect",
            prompt="Analyze coordination patterns in distributed systems"
        ),
        AgentTask(
            task_id="documenter",
            task_type="technical-writer",
            prompt="Create a brief summary of agent coordination principles"
        )
    ]

    # Execute parallel coordination
    results = await orchestrator.execute_batch(tasks)

    print(f"✅ Multi-agent coordination complete!")
    print(f"Agents executed: {len(results)}")

    return results
```

---

## 📚 LEARNING THE ORCHESTRATOR PATTERNS

### **Pattern 1: Independent Parallel Tasks**

Use this when tasks can run simultaneously without dependencies:

```python
# Example: Parallel research on different topics
tasks = [
    AgentTask("research_ai", "research-genius", "Research AI trends"),
    AgentTask("research_cloud", "research-genius", "Research cloud computing"),
    AgentTask("research_security", "research-genius", "Research cybersecurity")
]

# All 3 execute in parallel
results = await orchestrator.execute_batch(tasks)
```

### **Pattern 2: Sequential Dependencies**

Use this when tasks must complete in order:

```python
# Example: Research → Design → Implement → Test
tasks = [
    AgentTask("research", "research-genius", "Research requirements"),
    AgentTask("design", "solution-architect", "Design system", dependencies=["research"]),
    AgentTask("implement", "development-specialist", "Implement design", dependencies=["design"]),
    AgentTask("test", "qa-testing-guru", "Test implementation", dependencies=["implement"])
]

# Executes in order with parallelism where possible
results = await orchestrator.execute_batch(tasks)
```

### **Pattern 3: Mixed Parallel + Sequential**

Advanced pattern combining both approaches:

```python
# Example: Parallel research, then coordinated implementation
tasks = [
    # Phase 1: Parallel research (no dependencies)
    AgentTask("research_frontend", "research-genius", "Research UI frameworks"),
    AgentTask("research_backend", "research-genius", "Research API patterns"),
    AgentTask("research_database", "research-genius", "Research data models"),

    # Phase 2: Coordinated implementation (depends on research)
    AgentTask("implement_ui", "development-specialist",
              "Implement UI based on research",
              dependencies=["research_frontend"]),
    AgentTask("implement_api", "development-specialist",
              "Implement API based on research",
              dependencies=["research_backend"]),
    AgentTask("implement_db", "database-specialist",
              "Implement database based on research",
              dependencies=["research_database"]),

    # Phase 3: Integration (depends on implementations)
    AgentTask("integration", "solution-architect",
              "Integrate all components",
              dependencies=["implement_ui", "implement_api", "implement_db"])
]

results = await orchestrator.execute_batch(tasks)
```

---

## 🧪 ADVANCED TESTING SCENARIOS

### **Comprehensive Parallel Testing** (like our demo)

```python
async def comprehensive_testing():
    """Full parallel execution testing with timing analysis"""

    class OrchestatorTester:
        def __init__(self):
            self.orchestrator = GenericOrchestrator(
                output_dir=Path("./comprehensive_test"),
                max_parallel=3
            )

        def create_test_tasks(self):
            """Create diverse tasks for testing"""
            return [
                AgentTask("code_analysis", "research-genius",
                         "Analyze the orchestrator codebase structure"),
                AgentTask("file_count", "development-specialist",
                         "Count and categorize all Python files"),
                AgentTask("git_history", "solution-architect",
                         "Analyze git history and recent changes"),
                AgentTask("test_generation", "qa-testing-guru",
                         "Generate unit tests for key components"),
                AgentTask("documentation", "technical-writer",
                         "Create usage documentation summary")
            ]

        async def run_comprehensive_test(self):
            """Execute comprehensive parallel test"""
            tasks = self.create_test_tasks()

            print(f"🚀 Testing {len(tasks)} agents in parallel...")
            start_time = time.time()

            results = await self.orchestrator.execute_batch(tasks)

            end_time = time.time()
            duration = end_time - start_time

            print(f"✅ Test complete in {duration:.2f}s")
            print(f"Success rate: {len(results)}/{len(tasks)} agents")

            return results

    tester = OrchestatorTester()
    return await tester.run_comprehensive_test()
```

### **Edge Case Testing**

```python
async def edge_case_testing():
    """Test edge cases: more agents than tokens"""

    orchestrator = GenericOrchestrator(
        output_dir=Path("./edge_test"),
        max_parallel=3
    )

    # Create more tasks than max_parallel (tests batching)
    edge_tasks = []
    for i in range(7):  # More than max_parallel=3
        edge_tasks.append(AgentTask(
            task_id=f"edge_task_{i+1}",
            task_type="general-purpose",
            prompt=f"Task {i+1}: Generate {(i+1)*5} random words"
        ))

    print(f"🧪 Testing {len(edge_tasks)} agents with batching...")
    results = await orchestrator.execute_batch(edge_tasks)

    print(f"✅ Edge case handled: {len(results)} agents completed")
    return results
```

---

## 📖 KNOWLEDGE BASE PATTERNS

Agents should store and query orchestrator knowledge:

### **Store Orchestrator Findings**

```python
# After successful orchestrator use, store the experience
mcp__knowledge__knowledge_store(
    content="Successfully used GenericOrchestrator for parallel agent coordination. "
           "Key patterns: independent tasks run in parallel, dependencies create "
           "sequential execution, token pool enables 3-5 concurrent agents.",
    knowledge_type="WORKFLOW",
    tags="orchestrator,multi-agent,parallel-execution"
)
```

### **Query for Orchestrator Patterns**

```python
# Before starting complex work, check for orchestrator patterns
results = mcp__knowledge__knowledge_query(
    query_type="search",
    search_text="orchestrator multi-agent parallel patterns",
    limit=5
)

if results['results']:
    print("Found existing orchestrator patterns:")
    for result in results['results']:
        print(f"- {result['summary']}")
```

---

## 🎯 AGENT DECISION FRAMEWORK

### **When to Use the Orchestrator**

**✅ USE ORCHESTRATOR when**:
- Task requires 2+ specialized agents (research + implementation)
- Work can be parallelized (multiple independent subtasks)
- Task has clear dependencies (research → design → implement)
- Need coordination between different agent types
- Task is complex enough to benefit from specialization

**❌ DON'T USE ORCHESTRATOR when**:
- Single agent can handle the entire task efficiently
- Task is simple and doesn't require coordination
- No parallelization benefits (purely sequential work)
- Only have 1 token available

### **Quick Decision Tree**

```
Can this task be broken into 2+ specialized roles?
├─ Yes → Can any parts run in parallel?
│   ├─ Yes → ✅ USE ORCHESTRATOR (parallel pattern)
│   └─ No → ✅ USE ORCHESTRATOR (sequential pattern)
└─ No → ❌ Single agent is fine
```

---

## 🚀 GETTING STARTED CHECKLIST

For any new agent discovering the orchestrator:

- [ ] **1. Run knowledge base query** for orchestrator info
- [ ] **2. Find orchestrator directory** (`apps/agent-orchestrator/`)
- [ ] **3. Read core documentation** (usage guides, tutorials)
- [ ] **4. Validate basic functionality** (single task test)
- [ ] **5. Check token pool** (need 2+ tokens)
- [ ] **6. Test multi-agent coordination** (2-3 agents)
- [ ] **7. Try parallel execution** (independent tasks)
- [ ] **8. Test dependencies** (sequential tasks)
- [ ] **9. Store experience in knowledge base**
- [ ] **10. Use for actual work** with confidence

---

## 🎉 SUCCESS INDICATORS

You know you're using the orchestrator correctly when you see:

- **Multiple agents working simultaneously** (logs show parallel execution)
- **Specialized agent types** handling appropriate tasks
- **Clear dependency chains** (research → design → implement)
- **Efficient token usage** (parallel batches, proper cycling)
- **Structured output** (organized results per agent)
- **Timing improvements** (parallel execution faster than sequential)

---

**The orchestrator is production-ready and validated. Any agent can discover and use these patterns immediately for multi-agent coordination.**
