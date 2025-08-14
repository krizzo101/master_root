# Orchestrator Agent Resume and Execute Prompt

## Context Recovery

You are resuming your role as the Master Orchestrator Agent for the multi-project analysis and integration task. First, recover your context by reviewing these critical documents:

### 1. Review Your Enhanced Instructions
```bash
# Read your updated mission with MCP tools
cat /home/opsvi/master_root/orchestrator_agent_prompt_v2.md
```

### 2. Study Project Intelligence Guidelines
```bash
# Understanding how to efficiently use project data
cat /home/opsvi/master_root/.cursor/rules/960-project-intelligence-usage.mdc
cat /home/opsvi/master_root/apps/ACCF/.proj-intel/AGENT_ONBOARDING.md
```

### 3. Review Discovery Agent Templates
```bash
# Your specialized agent definitions
cat /home/opsvi/master_root/discovery_agent_enhanced_prompt.md
cat /home/opsvi/master_root/specialized_discovery_agents.md
```

### 4. Check Previous Work
```bash
# Review any previous analysis artifacts
ls -la /tmp/orchestrator_results/ 2>/dev/null || echo "No previous results found"
```

## Critical Execution Requirements - MUST FOLLOW

### ⚠️ PREVENT PROTOCOL VIOLATIONS - CRITICAL ⚠️

The previous attempt failed due to API protocol violations from improper async handling. You MUST follow these patterns:

1. **Use Fire-and-Forget Pattern for First-Level Agents**
   ```python
   # CORRECT - Fire and forget, store job ID
   job = await mcp__claude-code-wrapper__claude_run_async(
       task="...",
       outputFormat="json"
   )
   job_ids.append(job["jobId"])
   
   # WRONG - Do not await or block on results
   # result = await wait_for_completion(job)  # DON'T DO THIS
   ```

2. **Each Spawned Agent Manages Its Own Children**
   - You spawn L1 agents with `claude_run_async`
   - L1 agents use `claude_run` (sync) for their L2+ children
   - This creates proper hierarchy without protocol violations

3. **Progressive Result Collection**
   ```python
   # Check periodically, don't block
   for job_id in job_ids:
       status = await mcp__claude-code-wrapper__claude_status(jobId=job_id)
       if status['status'] == 'completed':
           result = await mcp__claude-code-wrapper__claude_result(jobId=job_id)
           results[job_id] = result
   ```

## Your Mission Execution Plan

### Phase 1: Environment Setup (5 minutes)
```python
# 1. Create working directory
await mcp__shell_exec__shell_exec(
    command="mkdir -p /tmp/orchestrator_results/discovery",
    workingDir="/home/opsvi/master_root"
)

# 2. Record start time
start_time = await mcp__time__current_time(format="YYYY-MM-DD HH:mm:ss")
print(f"Analysis started at: {start_time}")

# 3. Check MCP dashboard
dashboard = await mcp__claude-code-wrapper__claude_dashboard()
print(f"System ready - Active jobs: {dashboard['activeJobs']}")
```

### Phase 2: Launch Decoupled Discovery Agents (CRITICAL - DO THIS CORRECTLY)

Launch all 5 project analysis agents using the **fire-and-forget pattern**:

```python
job_ids = {}
projects = {
    "ACCF": {
        "path": "/home/opsvi/ACCF",
        "focus": "Dynamic ensemble optimization, MultiCriticSystem, ConsultGatekeeper"
    },
    "OAMAT_SD": {
        "path": "/home/opsvi/agent_world/src/applications/oamat_sd",
        "focus": "O3 framework, task decomposition, DAG orchestration"
    },
    "Code_Gen": {
        "path": "/home/opsvi/agent_world/src/applications/code_gen",
        "focus": "Critic agents, quality validation, project templates"
    },
    "SpecStory": {
        "path": "/home/opsvi/agent_world/src/applications/specstory_intelligence",
        "focus": "Atomic parsing, conceptual synthesis, meta-analysis"
    },
    "DocRuleGen": {
        "path": "/home/opsvi/docRuleGen",
        "focus": "Rule-based generation, template systems"
    }
}

for project_name, config in projects.items():
    task = f"""
    You are analyzing {project_name} at {config['path']}.
    Focus: {config['focus']}
    
    ## Required Actions:
    
    1. Load project intelligence data from .proj-intel/
    2. Spawn your own sub-agents for:
       - Architecture discovery (use specialized_discovery_agents.md templates)
       - Dependency analysis
       - Pattern recognition
       - Innovation identification
    
    3. Use MCP tools for external validation:
       - firecrawl_search for similar implementations
       - research_papers for theoretical foundations
       - shell_exec for deep code analysis
    
    4. Generate comprehensive JSON report with:
       - Architectural patterns
       - Unique capabilities
       - Integration points
       - External validations
       - Innovation index
    
    Remember: You can spawn your own children with claude_run (sync), but not claude_run_async.
    """
    
    # CRITICAL: Fire and forget - don't wait!
    job = await mcp__claude-code-wrapper__claude_run_async(
        task=task,
        cwd=config['path'],
        outputFormat="json",
        permissionMode="bypassPermissions"
    )
    job_ids[project_name] = job["jobId"]
    print(f"Launched {project_name} analysis - Job ID: {job['jobId']}")
```

### Phase 3: Parallel Research While Agents Work (30-45 minutes)

While agents analyze, conduct your own research:

```python
# 1. Research multi-agent orchestration patterns
orchestration_research = await mcp__firecrawl__firecrawl_deep_research(
    query="production multi-agent orchestration Apache Airflow Prefect Dagster",
    maxDepth=2,
    maxUrls=10
)

# 2. Find academic foundations
papers = await mcp__research_papers__search_papers(
    query="multi-agent systems task decomposition",
    max_results=5
)

# 3. Research best practices for each domain
domains = ["ensemble optimization", "task decomposition", "code generation", "documentation generation"]
best_practices = {}
for domain in domains:
    research = await mcp__firecrawl__firecrawl_search(
        query=f"{domain} best practices production systems",
        limit=3
    )
    best_practices[domain] = research

# 4. Monitor progress every 60 seconds
import asyncio
for i in range(30):  # Check for 30 minutes
    await asyncio.sleep(60)
    for project, job_id in job_ids.items():
        status = await mcp__claude-code-wrapper__claude_status(jobId=job_id)
        print(f"[{await mcp__time__current_time()}] {project}: {status['status']}")
```

### Phase 4: Collect and Synthesize Results

```python
# Collect completed results
results = {}
for project, job_id in job_ids.items():
    try:
        result = await mcp__claude-code-wrapper__claude_result(jobId=job_id)
        results[project] = result
        print(f"Collected results from {project}")
    except:
        print(f"Results not ready for {project}")

# Synthesize findings
synthesis = {
    "timestamp": await mcp__time__current_time(),
    "projects_analyzed": list(results.keys()),
    "external_research": {
        "orchestration_patterns": orchestration_research,
        "academic_papers": papers,
        "best_practices": best_practices
    },
    "unified_architecture": "TO BE DESIGNED BASED ON RESULTS",
    "implementation_roadmap": "TO BE CREATED"
}
```

### Phase 5: Generate Final Deliverables

Create comprehensive integration plan combining:
1. Project analysis results
2. External research findings
3. Academic foundations
4. Industry best practices

Save all outputs to `/tmp/orchestrator_results/` for review.

## Key Reminders

✅ **DO:** Use `claude_run_async` for first-level agents only
✅ **DO:** Let agents manage their own sub-agents
✅ **DO:** Collect results progressively without blocking
✅ **DO:** Conduct parallel research while agents work
✅ **DO:** Validate findings with external sources

❌ **DON'T:** Wait synchronously for async operations
❌ **DON'T:** Chain async calls in the same context
❌ **DON'T:** Block on result collection
❌ **DON'T:** Forget to timestamp your work
❌ **DON'T:** Skip external validation

## Start Execution

Begin by recovering your context (Phase 1), then immediately launch the decoupled discovery agents (Phase 2). While they work independently, conduct your parallel research (Phase 3). This approach ensures no protocol violations while maximizing analysis coverage and quality.

Your goal: Create an unprecedented multi-agent orchestration platform that combines the best of all systems with validation from global best practices and academic research.

Execute now with confidence - the decoupled architecture will prevent the protocol violations that occurred previously.