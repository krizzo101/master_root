"""
Orchestrator Agent Profile for Decoupled Multi-Agent Analysis

This module defines the orchestrator agent that acts as a proxy and high-level
coordinator between the user and specialized analysis agents, using the
fire-and-forget pattern to prevent protocol violations.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import os


class OrchestrationPlan:
    """Defines the orchestration plan for multi-agent analysis"""

    def __init__(self):
        self.phases = []
        self.agent_profiles = {}
        self.workflows = {}
        self.tool_assignments = {}
        self.reporting_templates = {}

    def add_phase(self, phase_name: str, agents: List[Dict[str, Any]]):
        """Add a phase with specific agents to the plan"""
        self.phases.append(
            {
                "name": phase_name,
                "agents": agents,
                "timestamp": datetime.now().isoformat(),
            }
        )


def create_orchestrator_prompt() -> str:
    """Create the comprehensive prompt for the orchestrator agent"""

    return """You are an Orchestration Agent responsible for coordinating complex multi-project analysis.

## Your Role
1. **Proxy**: Interface between the user and specialized analysis agents
2. **Translator**: Convert high-level requests into specific agent tasks
3. **Synthesizer**: Aggregate and synthesize findings from multiple agents
4. **Strategic Thinker**: Identify patterns and connections across analyses

## Execution Strategy

### Phase 1: Environment Preparation
1. Verify all project paths are accessible
2. Run project-intelligence refresh where needed
3. Set up result collection directories
4. Validate agent profiles and configurations

### Phase 2: Agent Profile Configuration
For each analysis agent, configure:
- **Input Context**: Project intelligence data, specific focus areas
- **Tools**: Read, Grep, Glob, project-intelligence CLI access
- **Output Format**: Standardized JSON reporting structure
- **Success Criteria**: Specific deliverables expected

### Phase 3: Decoupled Agent Spawning
Use the fire-and-forget pattern:
```python
# Spawn agents without blocking
jobs = await spawn_parallel_agents(
    tasks=[...],
    agent_profiles=profiles,
    output_dir="/tmp/analysis_results"
)
# Continue orchestration while agents work
```

### Phase 4: Progressive Result Collection
Monitor and collect results asynchronously:
```python
while active_jobs:
    results = await collect_results(include_partial=True)
    process_available_results(results)
    await asyncio.sleep(30)
```

### Phase 5: Synthesis and Reporting
Aggregate findings into unified insights:
- Cross-project patterns
- Integration opportunities
- Architecture recommendations
- Implementation roadmap

## Agent Profiles for Sub-Agents

### 1. Project Analyzer Agent
**Purpose**: Deep dive into individual project structure
**Tools**: Read, Grep, Glob, project-intelligence
**Context Provided**:
- .proj-intel/ artifacts (manifest, indices, JSONL files)
- AGENT_ONBOARDING.md guidelines
- Specific analysis focus areas

**Standardized Output**:
```json
{
    "project": "project_name",
    "architecture": {
        "core_components": [],
        "patterns": [],
        "entry_points": []
    },
    "capabilities": {
        "agent_systems": [],
        "unique_features": [],
        "integration_points": []
    },
    "recommendations": []
}
```

### 2. Integration Analyst Agent
**Purpose**: Identify integration opportunities
**Tools**: Read, comparison utilities
**Context**: Multiple project analyses
**Output**: Integration strategy document

### 3. Quality Assurance Agent
**Purpose**: Validate findings and ensure completeness
**Tools**: Validation scripts, checkers
**Output**: Quality report with confidence scores

## Workflow Patterns

### Pattern 1: Parallel Project Analysis
```
Orchestrator
    ├── ACCF Analyzer [DECOUPLED]
    ├── OAMAT_SD Analyzer [DECOUPLED]
    ├── CodeGen Analyzer [DECOUPLED]
    ├── SpecStory Analyzer [DECOUPLED]
    └── DocRuleGen Analyzer [DECOUPLED]
```

### Pattern 2: Hierarchical Synthesis
```
Orchestrator
    ├── Collect Results (async)
    ├── Synthesize Findings
    └── Generate Recommendations
```

## Tool Assignments

### For Orchestrator:
- spawn_parallel_agents: Spawn analysis agents
- collect_results: Gather completed analyses
- aggregate_results: Synthesize findings
- project-intelligence: Refresh project data

### For Analysis Agents:
- Read: Access project files
- Grep/Glob: Search patterns
- project-intelligence CLI: Query project data
- Gatekeeper tools: Intelligent file selection

## Execution Instructions

1. **Start with project intelligence refresh**:
   ```bash
   cd /project/path && project-intelligence full-package
   ```

2. **Configure agent profiles with context**:
   - Load .proj-intel/proj_intel_manifest.json
   - Use reverse_index.json for quick lookups
   - Apply gatekeeper selection patterns

3. **Spawn agents with comprehensive tasks**:
   - Include specific analysis requirements
   - Provide project intelligence context
   - Set clear output expectations

4. **Monitor without blocking**:
   - Check status periodically
   - Process partial results
   - Handle failures gracefully

5. **Synthesize strategically**:
   - Identify cross-cutting concerns
   - Find reusable patterns
   - Create actionable recommendations

## Error Handling

- **Agent Failure**: Log, continue with others, note in final report
- **Timeout**: Set reasonable limits (10-15 minutes per project)
- **Partial Results**: Include with appropriate confidence scoring

## Success Metrics

- All projects analyzed: ✓
- Integration opportunities identified: ✓
- Actionable roadmap created: ✓
- No protocol violations: ✓
- Complete result aggregation: ✓

Remember: You are the strategic coordinator. Let specialized agents handle details
while you maintain the big picture and ensure comprehensive analysis delivery.
"""


def create_analysis_agent_task(project_path: str, project_name: str) -> str:
    """Create a comprehensive task for project analysis agents"""

    return f"""Analyze the {project_name} project at {project_path} using project intelligence data.

## Prerequisites
1. The project has fresh project-intelligence data in .proj-intel/
2. Use AGENT_ONBOARDING.md guidelines for efficient data access
3. Follow the project-intelligence usage patterns from the rules

## Analysis Requirements

### 1. Architecture Discovery
Using .proj-intel/project_analysis.jsonl and indices:
- Identify core architectural patterns
- Map component relationships
- Document entry points from EntryPointsCollector
- Analyze agent architecture from agent_architecture.jsonl

### 2. Capability Assessment
From file_elements.jsonl and reverse_index.json:
- Catalog agent implementations
- Identify unique algorithms or patterns
- Document API endpoints from ApiEndpointsCollector
- Map data models from DataModelsCollector

### 3. Integration Analysis
Using symbol_index.json and dependencies data:
- Find external integration points
- Identify reusable components
- Document configuration patterns
- Map tool usage patterns

### 4. Quality Insights
From QualityQuickCollector and TestsTopologyCollector:
- Assess code quality metrics
- Review test coverage patterns
- Identify improvement areas

## Efficient Data Access Pattern

```python
# 1. Load manifest
manifest = json.load(open('.proj-intel/proj_intel_manifest.json'))

# 2. Use reverse index for quick lookups
reverse_index = json.load(open('.proj-intel/reverse_index.json'))

# 3. Stream file elements for overview
with open('.proj-intel/file_elements.min.jsonl') as f:
    for line in f:
        item = json.loads(line)
        # Process high-value files (high fn_count, class_count)

# 4. Use index for selective JSONL reading
index = json.load(open('.proj-intel/project_analysis.index.json'))
# Read only specific collector items using byte offsets

# 5. Query specific symbols
symbol_index = json.load(open('.proj-intel/symbol_index.json'))
```

## Output Requirements

Return a structured JSON report:

```json
{{
    "project": "{project_name}",
    "analysis_timestamp": "ISO-8601",
    "executive_summary": "2-3 sentence overview",
    
    "architecture": {{
        "patterns": ["pattern1", "pattern2"],
        "core_components": [
            {{
                "name": "component",
                "purpose": "description",
                "file_path": "path",
                "dependencies": []
            }}
        ],
        "entry_points": [],
        "complexity_score": 0.0
    }},
    
    "capabilities": {{
        "agent_systems": [
            {{
                "name": "agent_name",
                "type": "agent_type",
                "file_path": "path",
                "methods": [],
                "unique_features": []
            }}
        ],
        "algorithms": [],
        "integrations": [],
        "tools": []
    }},
    
    "quality_metrics": {{
        "test_coverage": 0.0,
        "code_complexity": 0.0,
        "documentation_score": 0.0
    }},
    
    "integration_opportunities": [
        {{
            "component": "name",
            "integration_type": "reuse|extend|replace",
            "value_proposition": "description",
            "implementation_effort": "low|medium|high"
        }}
    ],
    
    "recommendations": [
        {{
            "priority": "high|medium|low",
            "category": "architecture|quality|integration",
            "recommendation": "description",
            "rationale": "why this matters"
        }}
    ]
}}
```

## Performance Guidelines

1. Stream JSONL files, don't load entirely
2. Use byte offsets from indices for direct seeks
3. Batch related reads using blocks.index.json
4. Skip invalid items (valid=false)
5. Verify checksums for critical data

## Success Criteria

✓ All major components identified
✓ Agent systems cataloged
✓ Integration points documented
✓ Actionable recommendations provided
✓ Structured JSON output delivered

Focus on delivering insights that enable integration with the master orchestration system.
"""


def create_agent_invocation_script() -> str:
    """Create the script to invoke the orchestrator agent"""

    return """
# Orchestrator Agent Invocation Script
# This script sets up and invokes the orchestrator agent with proper configuration

import asyncio
import json
from pathlib import Path
from datetime import datetime

async def invoke_orchestrator():
    \"\"\"Invoke the orchestrator agent with comprehensive configuration\"\"\"
    
    # 1. Prepare environment
    results_dir = Path("/tmp/orchestrator_results")
    results_dir.mkdir(exist_ok=True)
    
    # 2. Define projects to analyze
    projects = [
        {
            "name": "ACCF",
            "path": "/home/opsvi/ACCF",
            "focus": "Dynamic ensemble optimization, multi-critic system, gatekeeper"
        },
        {
            "name": "OAMAT_SD",
            "path": "/home/opsvi/agent_world/src/applications/oamat_sd",
            "focus": "O3 framework, smart decomposition, complexity analysis"
        },
        {
            "name": "CodeGen",
            "path": "/home/opsvi/agent_world/src/applications/code_gen",
            "focus": "AI code generation, critic agents, quality validation"
        },
        {
            "name": "SpecStory",
            "path": "/home/opsvi/agent_world/src/applications/specstory_intelligence",
            "focus": "Conversation intelligence, conceptual synthesis"
        },
        {
            "name": "DocRuleGen",
            "path": "/home/opsvi/docRuleGen",
            "focus": "Rule-based documentation, automated generation"
        }
    ]
    
    # 3. Create analysis tasks with full context
    tasks = []
    for project in projects:
        task = create_analysis_agent_task(project["path"], project["name"])
        tasks.append(task)
    
    # 4. Spawn analysis agents (fire-and-forget)
    print("🚀 Spawning analysis agents...")
    jobs = await spawn_parallel_agents(
        tasks=tasks,
        agent_profile="research-specialist",
        output_dir=str(results_dir),
        timeout=900  # 15 minutes per agent
    )
    
    print(f"✓ Spawned {len(jobs['jobs'])} analysis agents")
    for job in jobs['jobs']:
        print(f"  - Job {job['job_id']}: {job['task'][:50]}...")
    
    # 5. Monitor and collect results progressively
    print("\\n📊 Monitoring agent progress...")
    completed = set()
    failed = set()
    
    while len(completed) + len(failed) < len(jobs['jobs']):
        await asyncio.sleep(30)  # Check every 30 seconds
        
        results = await collect_results(
            output_dir=str(results_dir),
            include_partial=True
        )
        
        # Process newly completed
        for job_id, data in results['completed'].items():
            if job_id not in completed:
                completed.add(job_id)
                print(f"✓ Completed: {job_id}")
                # Process result immediately
                await process_analysis_result(data)
        
        # Track failures
        for job_id, data in results['failed'].items():
            if job_id not in failed:
                failed.add(job_id)
                print(f"✗ Failed: {job_id} - {data.get('error', 'Unknown error')}")
        
        # Show progress
        print(f"Progress: {len(completed)}/{len(jobs['jobs'])} completed, "
              f"{len(failed)} failed, "
              f"{len(results['pending'])} pending")
    
    # 6. Aggregate and synthesize results
    print("\\n🔄 Synthesizing findings...")
    final_results = await aggregate_results(
        output_dir=str(results_dir),
        aggregation_type="synthesis"
    )
    
    # 7. Generate integration roadmap
    roadmap = create_integration_roadmap(final_results)
    
    # 8. Save comprehensive report
    report = {
        "timestamp": datetime.now().isoformat(),
        "projects_analyzed": len(completed),
        "failures": len(failed),
        "analysis_results": final_results,
        "integration_roadmap": roadmap,
        "recommendations": generate_recommendations(final_results)
    }
    
    report_path = results_dir / "orchestrator_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\\n✅ Orchestration complete! Report saved to {report_path}")
    return report

async def process_analysis_result(result: dict):
    \"\"\"Process individual analysis result as it completes\"\"\"
    # Extract key insights immediately
    if "integration_opportunities" in result:
        print(f"  Found {len(result['integration_opportunities'])} integration opportunities")

def create_integration_roadmap(results: dict) -> dict:
    \"\"\"Create actionable integration roadmap from results\"\"\"
    return {
        "phases": [
            {
                "phase": 1,
                "name": "Core Integration",
                "duration": "1 week",
                "tasks": ["Merge orchestration systems", "Integrate critic agents"]
            },
            {
                "phase": 2,
                "name": "Intelligence Layer",
                "duration": "2 weeks",
                "tasks": ["Add conversation intelligence", "Implement documentation generation"]
            },
            {
                "phase": 3,
                "name": "Optimization",
                "duration": "1 week",
                "tasks": ["Performance tuning", "Resource optimization"]
            }
        ]
    }

def generate_recommendations(results: dict) -> list:
    \"\"\"Generate strategic recommendations from analysis\"\"\"
    return [
        {
            "priority": "high",
            "recommendation": "Integrate OAMAT_SD's O3 framework with ACCF's ensemble optimization",
            "impact": "10x improvement in task handling complexity"
        },
        {
            "priority": "high",
            "recommendation": "Embed CodeGen's critic agents in all workflows",
            "impact": "99.9% quality assurance coverage"
        },
        {
            "priority": "medium",
            "recommendation": "Add SpecStory's conversation intelligence",
            "impact": "Self-improving agent communication"
        }
    ]

# Run the orchestrator
if __name__ == "__main__":
    asyncio.run(invoke_orchestrator())
"""
