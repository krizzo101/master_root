#!/usr/bin/env python3
"""
Orchestrator Invocation Script
Coordinates multi-project analysis using decoupled agents
"""

import os
import sys
import json
from pathlib import Path

# Add libs to path
sys.path.insert(0, "/home/opsvi/master_root/libs")

# Create the orchestrator task
ORCHESTRATOR_TASK = """You are the Master Orchestrator Agent coordinating a comprehensive multi-project analysis.

## Your Mission
Analyze and integrate capabilities from multiple projects to create a unified multi-agent orchestration system.

## Projects to Analyze

1. **ACCF** (/home/opsvi/ACCF)
   - Focus: Dynamic ensemble optimization, multi-critic system, intelligent gatekeeper
   - Key: UnifiedOptimizationSystem, ConsultGatekeeper, MultiCriticSystem

2. **OAMAT_SD** (/home/opsvi/agent_world/src/applications/oamat_sd)
   - Focus: O3 framework, smart task decomposition, complexity analysis
   - Key: O3 master agent, subdivision patterns, DAG orchestration

3. **CodeGen** (/home/opsvi/agent_world/src/applications/code_gen)
   - Focus: AI code generation, critic agents, quality validation
   - Key: Critic agents, project templates, validation policies

4. **SpecStory** (/home/opsvi/agent_world/src/applications/specstory_intelligence)
   - Focus: Conversation intelligence, conceptual synthesis
   - Key: Atomic parsing, meta-conceptual analysis, review workflows

5. **DocRuleGen** (/home/opsvi/docRuleGen)
   - Focus: Rule-based documentation generation
   - Key: Rule engine, template system, automated documentation

## Execution Strategy

### Phase 1: Spawn Decoupled Analysis Agents
Use the Claude Code MCP tool `spawn_parallel_agents` to create independent analysis agents:

```python
jobs = await mcp__claude-code-wrapper__spawn_parallel_agents(
    tasks=[
        # Task for each project analysis
    ],
    output_dir="/tmp/orchestrator_analysis",
    timeout=900
)
```

Each agent should:
1. Use project-intelligence data from .proj-intel/
2. Follow AGENT_ONBOARDING.md guidelines
3. Return standardized JSON reports

### Phase 2: Monitor Progress (Non-blocking)
While agents work:
1. Continue planning integration architecture
2. Design unified interfaces
3. Prepare synthesis framework

Periodically check results:
```python
results = await mcp__claude-code-wrapper__collect_results(
    output_dir="/tmp/orchestrator_analysis",
    include_partial=True
)
```

### Phase 3: Synthesize Findings
Once all agents complete:
1. Aggregate architectural insights
2. Identify integration patterns
3. Create implementation roadmap

## Output Requirements

Deliver a comprehensive integration plan including:
1. Unified architecture design combining all projects
2. Specific integration points and interfaces
3. Implementation phases with timeline
4. Risk assessment and mitigation strategies
5. Performance optimization recommendations

## Important Notes

- Use fire-and-forget pattern to prevent protocol violations
- Each spawned agent manages its own sub-agents
- Collect results asynchronously
- Handle partial failures gracefully
- Maintain high-level strategic thinking throughout

Begin by spawning the analysis agents, then proceed with synthesis while they work.
"""


def main():
    """Execute the orchestrator via Claude Code MCP"""

    print("=" * 70)
    print("ORCHESTRATOR AGENT INVOCATION")
    print("=" * 70)
    print("\nThis script will coordinate a comprehensive multi-project analysis")
    print("using decoupled agents to prevent protocol violations.\n")

    # Create output directory
    output_dir = Path("/tmp/orchestrator_analysis")
    output_dir.mkdir(exist_ok=True, parents=True)

    print(f"Output directory: {output_dir}")
    print("\nTask Summary:")
    print("- Analyze 5 projects using parallel agents")
    print("- Synthesize findings into unified architecture")
    print("- Create integration roadmap")
    print("\n" + "=" * 70)

    # Write task to file for reference
    task_file = output_dir / "orchestrator_task.md"
    with open(task_file, "w") as f:
        f.write(ORCHESTRATOR_TASK)

    print(f"\nTask written to: {task_file}")
    print("\nTo invoke the orchestrator, use this command in Claude Code:\n")

    print("```")
    print(f"mcp__claude-code-wrapper__claude_run(")
    print(f'    task="""{ORCHESTRATOR_TASK}""",')
    print(f'    outputFormat="json",')
    print(f'    permissionMode="bypassPermissions"')
    print(f")")
    print("```")

    print("\nOr use the async version for fire-and-forget execution:")
    print("```")
    print(f"mcp__claude-code-wrapper__claude_run_async(")
    print(f'    task="""{ORCHESTRATOR_TASK}""",')
    print(f'    outputFormat="json",')
    print(f'    permissionMode="bypassPermissions"')
    print(f")")
    print("```")

    print("\n" + "=" * 70)
    print("Ready to orchestrate!")
    print("=" * 70)


if __name__ == "__main__":
    main()
