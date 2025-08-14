# Orchestrated Multi-Project Analysis Command

## Quick Start Command

Run this in Claude Code to start the orchestrated analysis with proper decoupling:

```python
await mcp__claude-code-wrapper__claude_run_async(
    task="""
# Master Orchestrator Agent Task

You are coordinating a comprehensive analysis of 5 projects to create a unified multi-agent system.

## Critical: Use Decoupled Execution Pattern

To prevent protocol violations, spawn child agents using fire-and-forget pattern:
1. Use claude_run_async for each project analysis
2. Each child agent is responsible for its own sub-agents
3. Collect results asynchronously using claude_status and claude_result
4. Continue working while children execute

## Projects to Analyze

### 1. ACCF (/home/opsvi/ACCF)
Analyze the Advanced Coordination & Consult Framework:
- Dynamic ensemble optimization (UnifiedOptimizationSystem)
- Multi-critic validation system
- Intelligent gatekeeper for context selection
- Project intelligence integration

### 2. OAMAT_SD (/home/opsvi/agent_world/src/applications/oamat_sd)
Analyze the O3 Smart Decomposition system:
- O3 master agent framework
- Task decomposition strategies
- Complexity analysis and modeling
- DAG-based orchestration

### 3. CodeGen (/home/opsvi/agent_world/src/applications/code_gen)
Analyze the AI Code Generation system:
- Critic agent implementations
- Code quality validation
- Project template generation
- Policy-based enforcement

### 4. SpecStory (/home/opsvi/agent_world/src/applications/specstory_intelligence)
Analyze the Conversation Intelligence system:
- Atomic parsing capabilities
- Conceptual synthesis
- Meta-conceptual analysis
- Review workflows

### 5. DocRuleGen (/home/opsvi/docRuleGen)
Analyze the Documentation Generation system:
- Rule-based generation engine
- Template systems
- Automated documentation workflows

## Execution Instructions

### Step 1: Spawn Analysis Agents (Decoupled)

For each project, spawn an independent analysis agent:

```python
# Example for ACCF
job1 = await claude_run_async(
    task="Analyze ACCF project focusing on ensemble optimization...",
    cwd="/home/opsvi/ACCF",
    outputFormat="json"
)

# Do the same for other projects
# Store job IDs for later collection
```

### Step 2: Monitor Without Blocking

While agents work:
1. Design the integration architecture
2. Plan implementation phases
3. Check status periodically:

```python
status = await claude_status(jobId=job1["jobId"])
```

### Step 3: Collect Results

When agents complete:
```python
result = await claude_result(jobId=job1["jobId"])
```

### Step 4: Synthesize Findings

Create a unified architecture combining:
- OAMAT_SD's task decomposition
- ACCF's ensemble optimization
- CodeGen's quality validation
- SpecStory's conversation intelligence
- DocRuleGen's documentation automation

## Expected Deliverables

1. **Architecture Design**
   - Unified orchestration layer
   - Integration points between systems
   - Shared resource management

2. **Implementation Roadmap**
   - Phase 1: Core integration (1 week)
   - Phase 2: Intelligence layer (2 weeks)
   - Phase 3: Optimization (1 week)

3. **Technical Specifications**
   - API interfaces
   - MCP tool definitions
   - Agent communication protocols

4. **Risk Assessment**
   - Integration challenges
   - Performance considerations
   - Mitigation strategies

## Success Criteria

✓ All 5 projects analyzed comprehensively
✓ No protocol violations (using decoupled execution)
✓ Actionable integration plan delivered
✓ Clear implementation roadmap provided
✓ Unified architecture documented

Begin by spawning the analysis agents using claude_run_async, then synthesize while they execute.
""",
    outputFormat="json",
    permissionMode="bypassPermissions"
)
```

## Alternative: Direct Synchronous Execution

If you prefer synchronous execution (blocking but simpler):

```python
await mcp__claude-code-wrapper__claude_run(
    task="[Same task as above]",
    outputFormat="json",
    permissionMode="bypassPermissions"
)
```

## What This Does

1. **Spawns a Master Orchestrator** that acts as your proxy
2. **Orchestrator spawns child agents** for each project (decoupled)
3. **Each child analyzes independently** without blocking the orchestrator
4. **Orchestrator monitors and collects** results asynchronously
5. **Synthesizes findings** into unified architecture
6. **Delivers comprehensive report** with integration roadmap

## Benefits

- **No Protocol Violations**: Fire-and-forget pattern prevents tool_result errors
- **Parallel Execution**: All projects analyzed simultaneously
- **Failure Isolation**: One agent failing doesn't affect others
- **Progressive Results**: Can process findings as they complete
- **Strategic Oversight**: Orchestrator maintains high-level perspective

## Monitoring Progress

After starting, you can check progress:

```python
# Check orchestrator status
await mcp__claude-code-wrapper__claude_dashboard()

# List all jobs
await mcp__claude-code-wrapper__claude_list_jobs()

# Get specific job status
await mcp__claude-code-wrapper__claude_status(jobId="<job-id>")
```

## Expected Timeline

- Spawn agents: Immediate
- Individual analyses: 5-10 minutes each
- Result collection: Progressive
- Synthesis: 2-3 minutes
- Total: ~15 minutes

## Output Location

Results will be available:
1. In the MCP response (JSON format)
2. Potentially written to `/tmp/orchestrator_analysis/`
3. Can be retrieved using `claude_result(jobId=...)`