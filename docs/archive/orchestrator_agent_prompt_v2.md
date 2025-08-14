# Enhanced Multi-Project Analysis and Integration Task (v2)

## Your Mission

You are tasked with analyzing and integrating multiple advanced agent systems to create a unified multi-agent orchestration platform. You will conduct deep analysis of 5 key projects and synthesize their capabilities into a cohesive architecture.

## Available MCP Tools (ENHANCED)

You now have access to powerful MCP tools that will significantly enhance your analysis:

### 1. **claude-code-wrapper** - Recursive Agent Spawning
- `mcp__claude-code-wrapper__claude_run_async` - Fire-and-forget agent spawning
- `mcp__claude-code-wrapper__claude_status` - Check job status
- `mcp__claude-code-wrapper__claude_result` - Get completed results
- `mcp__claude-code-wrapper__claude_dashboard` - System performance metrics

### 2. **firecrawl** - Web Research & Documentation
- `mcp__firecrawl__firecrawl_scrape` - Scrape documentation pages
- `mcp__firecrawl__firecrawl_search` - Search for relevant information
- `mcp__firecrawl__firecrawl_deep_research` - Conduct deep research on topics
- **USE THIS** to research best practices for:
  - Multi-agent orchestration patterns
  - Task decomposition strategies
  - Quality assurance frameworks
  - Documentation generation approaches

### 3. **time** - Temporal Management
- `mcp__time__current_time` - Track analysis timing
- **USE THIS** to timestamp your findings and track execution duration

### 4. **thinking** - Sequential Reasoning
- Extended thinking capabilities for complex analysis
- **USE THIS** for deep architectural reasoning

### 5. **shell_exec** - Direct Command Execution
- Execute commands in `/home/opsvi/master_root`
- **USE THIS** for running project-intelligence commands

### 6. **db** - Neo4j Graph Database
- `mcp__db__*` - Query graph database
- **USE THIS** to explore project relationships and dependencies if available

### 7. **research_papers** - Academic Research
- Access to arxiv papers
- **USE THIS** to find relevant research on:
  - Multi-agent systems
  - Task orchestration algorithms
  - Ensemble optimization methods

## Critical Execution Requirements

### IMPORTANT: Prevent Protocol Violations

The previous agent encountered API errors due to improper handling of asynchronous tool calls. To avoid this:

1. **Use Fire-and-Forget Pattern for First-Level Agents Only**
   - When spawning analysis agents, use `mcp__claude-code-wrapper__claude_run_async` 
   - Immediately store job IDs and continue working
   - DO NOT wait for results inline - collect them separately

2. **Each Spawned Agent Manages Its Own Children**
   - First-level agents are responsible for their sub-agents
   - They should use synchronous `claude_run` for their children
   - This creates a hierarchy: You → L1 Agents (async) → L2+ Agents (sync)

3. **Progressive Result Collection**
   - Check status periodically using `mcp__claude-code-wrapper__claude_status`
   - Collect completed results with `mcp__claude-code-wrapper__claude_result`
   - Continue synthesis work while agents execute

## Phase 0: Research Best Practices (NEW)

Before analyzing projects, gather external knowledge:

### 1. Research Multi-Agent Orchestration Patterns
```python
research_result = await mcp__firecrawl__firecrawl_deep_research(
    query="multi-agent orchestration patterns task decomposition ensemble optimization",
    maxDepth=3,
    maxUrls=20
)
# Extract best practices and patterns
```

### 2. Search for Academic Papers
```python
papers = await mcp__research_papers__search(
    query="multi-agent systems coordination",
    max_results=5
)
# Review relevant research for theoretical foundations
```

### 3. Timestamp Your Analysis
```python
start_time = await mcp__time__current_time(format="YYYY-MM-DD HH:mm:ss")
# Use throughout to track progress
```

## Phase 1: Environment Preparation (ENHANCED)

### 1. Refresh Project Intelligence Data Using shell_exec:
```python
# Use mcp__shell_exec for each project
await mcp__shell_exec__execute(
    command="cd /home/opsvi/ACCF && project-intelligence full-package",
    cwd="/home/opsvi/master_root"
)
# Repeat for other projects
```

### 2. Study Project Intelligence Usage:
- Read `/home/opsvi/master_root/.cursor/rules/960-project-intelligence-usage.mdc`
- Read `/home/opsvi/master_root/apps/ACCF/.proj-intel/AGENT_ONBOARDING.md`

### 3. Create Results Directory:
```python
await mcp__shell_exec__execute(
    command="mkdir -p /tmp/orchestrator_results",
    cwd="/home/opsvi/master_root"
)
```

## Phase 2: Spawn Decoupled Analysis Agents (ENHANCED)

Create comprehensive analysis tasks with enhanced instructions:

### Enhanced Task Template for Each Agent:
```python
analysis_task = f"""
Analyze the {project_name} project at {project_path} with these enhanced capabilities:

## Available MCP Tools for Your Analysis

1. **firecrawl** - Research similar projects and best practices:
   - Use firecrawl_search to find related implementations
   - Use firecrawl_deep_research for architectural patterns
   
2. **time** - Track your analysis timing:
   - Record start and end times
   - Measure performance of different operations

3. **shell_exec** - Run analysis commands:
   - Execute grep, find, and other analysis tools
   - Run tests if available

4. **thinking** - Deep reasoning about architecture

## Enhanced Analysis Requirements

### 1. Architecture Discovery
- Use project-intelligence data from .proj-intel/
- Research similar architectures using firecrawl
- Compare with best practices from academic papers

### 2. Capability Assessment
- Catalog all agent implementations
- Search for similar implementations online
- Identify unique innovations

### 3. Integration Analysis
- Map integration points
- Research integration patterns
- Identify optimization opportunities

### 4. External Validation
- Search for similar projects using firecrawl
- Compare approaches with research papers
- Validate design decisions against best practices

### 5. Performance Metrics
- Use time MCP to track analysis duration
- Measure code complexity
- Benchmark against industry standards

## Output Requirements (Enhanced)

Return comprehensive JSON including:
- Timestamp (using time MCP)
- External references found (via firecrawl)
- Comparison with best practices
- Performance metrics
- Integration recommendations with confidence scores
"""
```

### Spawn with Enhanced Configuration:
```python
# Store all job IDs
job_ids = []

# Example: Spawn ACCF analyzer with enhanced capabilities
job1 = await mcp__claude-code-wrapper__claude_run_async(
    task=analysis_task.format(
        project_name="ACCF",
        project_path="/home/opsvi/ACCF"
    ),
    cwd="/home/opsvi/ACCF",
    outputFormat="json",
    permissionMode="bypassPermissions"
)
job_ids.append(job1["jobId"])
```

## Phase 3: Parallel Research While Agents Execute (NEW)

While analysis agents work, conduct parallel research:

### 1. Research Industry Best Practices
```python
# Research orchestration patterns
orchestration_research = await mcp__firecrawl__firecrawl_deep_research(
    query="production multi-agent orchestration systems Apache Airflow Prefect",
    maxDepth=2
)

# Research quality assurance
qa_research = await mcp__firecrawl__firecrawl_search(
    query="code quality validation critic agents automated testing",
    limit=10
)
```

### 2. Query Academic Literature
```python
# Find relevant papers
papers = await mcp__research_papers__search(
    query="ensemble optimization distributed systems",
    max_results=10
)
```

### 3. Monitor Dashboard
```python
# Check system performance
dashboard = await mcp__claude-code-wrapper__claude_dashboard()
# Use metrics to optimize resource allocation
```

### 4. Track Progress with Timestamps
```python
for job_id in job_ids:
    status = await mcp__claude-code-wrapper__claude_status(jobId=job_id)
    current_time = await mcp__time__current_time()
    print(f"[{current_time}] Job {job_id}: {status['status']}")
```

## Phase 4: Enhanced Synthesis (IMPROVED)

### 1. Collect and Validate Results
```python
# Collect all results
results = {}
for job_id in job_ids:
    result = await mcp__claude-code-wrapper__claude_result(jobId=job_id)
    results[job_id] = result

# Validate against external research
validation = compare_with_best_practices(results, orchestration_research)
```

### 2. Create Evidence-Based Architecture
Combine findings with external research:
- Project capabilities (from analysis)
- Industry best practices (from firecrawl)
- Academic foundations (from research_papers)
- Performance benchmarks (from time tracking)

### 3. Generate Data-Driven Roadmap
Use all data sources to create roadmap:
```
Phase 1: Foundation (Week 1)
- Implement patterns validated by research
- Apply best practices from industry leaders
- Set up performance monitoring

Phase 2: Integration (Weeks 2-3)
- Merge capabilities using proven patterns
- Implement quality gates from research
- Add monitoring and metrics

Phase 3: Optimization (Week 4)
- Apply optimization algorithms from papers
- Benchmark against industry standards
- Fine-tune based on metrics
```

## Phase 5: Comprehensive Report with External Validation

### Enhanced Deliverables:

1. **Executive Summary**
   - Findings from 5 projects
   - Validation against industry standards
   - Academic research support

2. **Technical Architecture**
   - Design backed by research
   - Performance projections
   - Risk assessment with mitigations

3. **Implementation Guide**
   - Step-by-step plan
   - Code examples
   - External references and citations

4. **Research Appendix**
   - Relevant papers and articles
   - Industry case studies
   - Best practices compilation

5. **Performance Metrics**
   - Analysis duration (via time MCP)
   - Complexity measurements
   - Projected performance gains

## Enhanced Success Criteria

- ✅ All projects analyzed with external validation
- ✅ Best practices researched and incorporated
- ✅ Academic foundations established
- ✅ Performance metrics collected
- ✅ No protocol violations
- ✅ Evidence-based recommendations
- ✅ Industry-standard architecture delivered

## Tool Usage Summary

### Primary Analysis Tools:
- **claude-code-wrapper**: Spawn and manage analysis agents
- **shell_exec**: Run project-intelligence and analysis commands
- **Read/Grep/Glob**: Direct file analysis

### Research Enhancement Tools:
- **firecrawl**: Research best practices and similar projects
- **research_papers**: Academic foundation and algorithms
- **thinking**: Deep architectural reasoning

### Support Tools:
- **time**: Track execution and create timestamps
- **db**: Explore relationships if Neo4j data exists

## Execution Flow

1. Start timestamp → Research best practices → Spawn agents
2. While agents work → Conduct parallel research → Monitor progress
3. Collect results → Validate against research → Synthesize findings
4. Create architecture → Generate roadmap → Deliver report

Begin by using the firecrawl tool to research multi-agent orchestration best practices, then proceed with the enhanced analysis workflow. This will result in a superior, evidence-based integration strategy backed by both practical analysis and external validation.