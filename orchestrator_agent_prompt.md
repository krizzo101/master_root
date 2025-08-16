# Comprehensive Multi-Project Analysis and Integration Task

## Your Mission

You are tasked with analyzing and integrating multiple advanced agent systems to create a unified multi-agent orchestration platform. You will conduct deep analysis of 5 key projects and synthesize their capabilities into a cohesive architecture.

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

## Phase 1: Environment Preparation

Before starting analysis, ensure proper setup:

1. **Refresh Project Intelligence Data**:
   ```bash
   # For each project that needs fresh data
   cd /home/opsvi/ACCF && project-intelligence full-package
   cd /home/opsvi/agent_world/src/applications/oamat_sd && project-intelligence full-package
   cd /home/opsvi/agent_world/src/applications/code_gen && project-intelligence full-package
   cd /home/opsvi/agent_world/src/applications/specstory_intelligence && project-intelligence full-package
   cd /home/opsvi/docRuleGen && project-intelligence full-package
   ```

2. **Study Project Intelligence Usage**:
   - Read `/home/opsvi/master_root/.cursor/rules/960-project-intelligence-usage.mdc`
   - Read `/home/opsvi/master_root/apps/ACCF/.proj-intel/AGENT_ONBOARDING.md`
   - Understand how to use `.proj-intel/` artifacts efficiently

3. **Create Results Directory**:
   ```bash
   mkdir -p /tmp/orchestrator_results
   ```

## Phase 2: Spawn Decoupled Analysis Agents

Create comprehensive analysis tasks for each project and spawn them asynchronously:

### Projects to Analyze:

1. **ACCF** - Advanced Coordination & Consult Framework
   - Path: `/home/opsvi/ACCF`
   - Focus: Dynamic ensemble optimization, MultiCriticSystem, ConsultGatekeeper
   - Key files: `src/accf/agents/gatekeeper_agent.py`, `src/accf/tools/optimization/`

2. **OAMAT_SD** - O3 Smart Decomposition
   - Path: `/home/opsvi/agent_world/src/applications/oamat_sd`
   - Focus: O3 framework, task decomposition, complexity analysis
   - Key: Smart subdivision patterns, DAG orchestration

3. **Code_Gen** - AI Code Generation
   - Path: `/home/opsvi/agent_world/src/applications/code_gen`
   - Focus: Critic agents, quality validation, project templates
   - Key: Multi-layer validation, policy enforcement

4. **SpecStory Intelligence** - Conversation Analysis
   - Path: `/home/opsvi/agent_world/src/applications/specstory_intelligence`
   - Focus: Atomic parsing, conceptual synthesis, meta-analysis
   - Key: Conversation intelligence patterns

5. **DocRuleGen** - Documentation Generation
   - Path: `/home/opsvi/docRuleGen`
   - Focus: Rule-based generation, template systems
   - Key: Automated documentation workflows

### Spawning Pattern:

```python
# Store all job IDs
job_ids = []

# Spawn ACCF analyzer
job1 = await mcp__claude-code-wrapper__claude_run_async(
    task="""
    Analyze the ACCF project at /home/opsvi/ACCF with focus on:
    1. Dynamic ensemble optimization system (UnifiedOptimizationSystem)
    2. Multi-critic validation architecture
    3. ConsultGatekeeper intelligent context selection
    4. Project intelligence integration patterns
    
    Use the .proj-intel/ artifacts:
    - Load proj_intel_manifest.json for artifact list
    - Use reverse_index.json for quick file lookups
    - Stream file_elements.min.jsonl for metrics
    - Read agent_architecture.jsonl for agent details
    
    Return structured JSON with:
    - Core architectural patterns
    - Agent implementations and capabilities
    - Integration points and APIs
    - Unique optimization features
    - Recommendations for unified system
    """,
    cwd="/home/opsvi/ACCF",
    outputFormat="json",
    permissionMode="bypassPermissions"
)
job_ids.append(job1["jobId"])

# Repeat similar pattern for other 4 projects
# ... (spawn remaining agents)
```

## Phase 3: Parallel Work While Agents Execute

While analysis agents work independently, perform these tasks:

1. **Design Integration Architecture**:
   - Sketch unified orchestration layer
   - Plan API interfaces
   - Design agent communication protocols

2. **Monitor Progress** (every 30-60 seconds):
   ```python
   for job_id in job_ids:
       status = await mcp__claude-code-wrapper__claude_status(jobId=job_id)
       print(f"Job {job_id}: {status['status']}")
   ```

3. **Collect Completed Results**:
   ```python
   results = {}
   for job_id in job_ids:
       status = await mcp__claude-code-wrapper__claude_status(jobId=job_id)
       if status['status'] == 'completed':
           result = await mcp__claude-code-wrapper__claude_result(jobId=job_id)
           results[job_id] = result
   ```

## Phase 4: Synthesize Findings

Once all agents complete (or sufficient results are available):

### Create Unified Architecture:

1. **Orchestration Core**:
   - Combine OAMAT_SD's O3 framework with ACCF's ensemble optimization
   - Use Claude Code's recursion for multi-level execution
   - Integrate CodeGen's critic agents for quality gates

2. **Intelligence Layer**:
   - Apply SpecStory's conversation analysis
   - Use ACCF's Gatekeeper for context optimization
   - Add DocRuleGen for automated documentation

3. **Execution Framework**:
   - Claude Code MCP server as backbone
   - ACCF's specialized agent tools
   - OAMAT_SD's tool registry

### Generate Implementation Roadmap:

```
Phase 1 (Week 1): Core Integration
- Merge orchestration systems
- Integrate critic agents
- Set up unified MCP server

Phase 2 (Weeks 2-3): Intelligence Enhancement
- Add conversation intelligence
- Implement documentation generation
- Create learning loops

Phase 3 (Week 4): Optimization
- Performance tuning
- Resource optimization
- Production readiness
```

## Phase 5: Deliver Comprehensive Report

Create final deliverables:

1. **Executive Summary**: 2-3 paragraphs on findings and recommendations

2. **Technical Architecture**: Detailed design combining all systems

3. **Integration Specifications**:
   - API definitions
   - Agent profiles
   - Tool configurations
   - Workflow patterns

4. **Implementation Guide**:
   - Step-by-step integration plan
   - Code examples
   - Configuration templates

5. **Risk Assessment**:
   - Technical challenges
   - Mitigation strategies
   - Fallback plans

## Expected Outcomes

By completing this task, you will:

1. ✅ Have deep understanding of all 5 projects
2. ✅ Create unified architecture design
3. ✅ Provide actionable integration roadmap
4. ✅ Avoid protocol violations through proper async handling
5. ✅ Deliver comprehensive documentation

## Success Criteria

- All projects analyzed without errors
- No API protocol violations
- Complete synthesis of capabilities
- Clear, actionable recommendations
- Working prototype configurations

## Important Reminders

1. **Use project-intelligence data** - It's already generated in `.proj-intel/` folders
2. **Follow AGENT_ONBOARDING.md** - Use efficient data access patterns
3. **Spawn agents asynchronously** - Prevent blocking and protocol errors
4. **Collect results separately** - Don't wait inline for async operations
5. **Think strategically** - You're the orchestrator, not the implementer

Begin by reviewing the project intelligence usage guidelines, then spawn the analysis agents using the fire-and-forget pattern. While they work, design the integration architecture and monitor their progress. Finally, synthesize all findings into a comprehensive integration plan.

Remember: The goal is to create an unprecedented multi-agent orchestration platform that combines the best of all systems - smart decomposition, dynamic optimization, recursive execution, quality validation, conversation intelligence, and automated documentation.