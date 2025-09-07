#!/usr/bin/env python3
"""
ORCHESTRATOR ENHANCEMENT EXECUTION PLAN
Self-modifying orchestrator to add dynamic agent architecture
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.unified.enhanced_agent_task import EnhancedAgentTask
from src.unified.unified_orchestrator import create_standard_orchestrator


async def main():
    # Use enhanced orchestrator in minimal mode (same as successful previous run)
    # TokenLoader will handle token distribution automatically
    orchestrator = create_standard_orchestrator(
        output_dir=Path("orchestrator_enhancement"),
        max_parallel=7,  # All 7 agents can run in parallel
    )

    tasks = [
        # PHASE 1: ANALYSIS & VALIDATION
        EnhancedAgentTask(
            task_id="safety_validator",
            task_type="security-architect",
            prompt="""SAFETY VALIDATION FOR ORCHESTRATOR SELF-MODIFICATION

You are validating proposed changes to ALL orchestrators (generic, enhanced, unified) for safety and compatibility.

PROPOSED CHANGES TO ANALYZE:
1. Add dynamic agent architecture with cwd parameter and MCP config generation
2. Add comprehensive debug logging throughout all orchestrators
3. Add new orchestrator parameters for dynamic configuration
4. Add agent debug flag support
5. Move log/task output from orchestrator root to app work directories

CRITICAL SAFETY CHECKS:
- Will self-modification break the currently running enhanced orchestrator?
- Are the proposed parameter additions backward compatible?
- Will debug logging additions cause performance issues?
- Are there any circular dependency risks in dynamic config generation?
- Will moving logs break existing monitoring/tooling?

ANALYSIS REQUIRED:
1. Read ALL orchestrator files: generic_orchestrator.py, enhanced_orchestrator.py, unified_orchestrator.py
2. Check current parameter signatures and usage patterns
3. Identify potential breaking changes or conflicts
4. Assess risk of self-modification while running

DELIVERABLE:
Create safety_validation_report.md with:
- RISK LEVEL: LOW/MEDIUM/HIGH
- CRITICAL CONCERNS: List any show-stoppers
- COMPATIBILITY NOTES: Backward compatibility assessment
- ARCHITECT NOTES: Key considerations for solution architect
- DECISION: PROCEED or ABORT with reasoning

Store in current working directory. Be thorough but concise.""",
            dependencies=[],
        ),
        # PHASE 2: SOLUTION ARCHITECTURE
        EnhancedAgentTask(
            task_id="solution_architect",
            task_type="solution-architect",
            prompt="""SOLUTION ARCHITECTURE FOR ORCHESTRATOR ENHANCEMENT

You are designing the detailed implementation strategy for orchestrator enhancements.

INPUT TO REVIEW:
1. Read safety_validation_report.md for safety considerations
2. Analyze ALL orchestrator code to understand current architecture
3. Review proposed dynamic agent architecture requirements

REQUIREMENTS TO IMPLEMENT:
1. MASTER MCP REGISTRY: Merge /home/opsvi/master_root/.mcp.json and /home/opsvi/master_root/.mcp.json.backup.2025-09-07-00-24-14 into master_mcp_registry.json
2. ORCHESTRATOR PARAMETERS: Add parameters for dynamic architecture (master_mcp_registry_path, agent_execution_profile, agent_debug_mode, agent_base_work_dir, enable_dynamic_configs, log_to_work_dir)
3. DYNAMIC ARCHITECTURE: Add cwd parameter to subprocess execution, MCP config generation, directory creation, symlink logic
4. DEBUG LOGGING: Add comprehensive debug logging showing variable values, subprocess commands, token flow, error details
5. AGENT DEBUG FLAGS: Add --debug flag support for individual agents

DELIVERABLE:
Create detailed implementation specifications in implementation_specs/ directory:
- mcp_registry_builder_spec.md: Exact merge strategy, file locations, validation steps
- parameter_enhancement_spec.md: Exact parameter signatures, integration points, backward compatibility
- dynamic_architecture_spec.md: Specific functions to modify, logic flow, integration approach
- debug_enhancement_spec.md: Exact logging points, debug flag integration, format specifications

Each spec must be detailed enough that implementation agents can execute without needing to analyze or discover - just implement.

CRITICAL: Include file paths, function names, exact code patterns to look for, and specific implementation approaches.""",
            dependencies=["safety_validator"],
        ),
        # PHASE 3: IMPLEMENTATION SPECIALISTS
        EnhancedAgentTask(
            task_id="mcp_registry_builder",
            task_type="development-specialist",
            prompt="""MCP REGISTRY BUILDER IMPLEMENTATION

You are implementing the master MCP registry creation.

INSTRUCTIONS:
Read implementation_specs/mcp_registry_builder_spec.md for detailed specifications.

TASK:
1. Read /home/opsvi/master_root/.mcp.json (current simplified config)
2. Read /home/opsvi/master_root/.mcp.json.backup.2025-09-07-00-24-14 (complete backup)
3. Merge all MCP servers into comprehensive master_mcp_registry.json
4. Place result in /home/opsvi/master_root/.claude/master_mcp_registry.json
5. Validate no conflicts, duplicates, or malformed entries

DELIVERABLE:
- Complete master_mcp_registry.json file
- Brief report confirming successful merge and validation

Follow the architect's specifications exactly.""",
            dependencies=["solution_architect"],
        ),
        EnhancedAgentTask(
            task_id="orchestrator_parameter_specialist",
            task_type="development-specialist",
            prompt="""ORCHESTRATOR PARAMETER ENHANCEMENT IMPLEMENTATION

You are adding new parameters to ALL orchestrator classes.

INSTRUCTIONS:
Read implementation_specs/parameter_enhancement_spec.md for detailed specifications.

TASK:
Add these new parameters to GenericOrchestrator, EnhancedOrchestrator, and UnifiedOrchestrator:
- master_mcp_registry_path (default: /home/opsvi/master_root/.claude/master_mcp_registry.json)
- agent_execution_profile (default: "test")
- agent_debug_mode (default: False)
- agent_base_work_dir (default: /home/opsvi/master_root/apps/)
- enable_dynamic_configs (default: True)
- log_to_work_dir (default: True)

REQUIREMENTS:
- Maintain backward compatibility - all existing code must work unchanged
- Add proper parameter validation
- Update __init__ methods and class attributes
- Ensure parameters are passed through inheritance chain properly

DELIVERABLE:
Modified orchestrator files with new parameter support and brief implementation report.

Follow the architect's specifications exactly.""",
            dependencies=["solution_architect"],
        ),
        EnhancedAgentTask(
            task_id="dynamic_architecture_specialist",
            task_type="development-specialist",
            prompt="""DYNAMIC ARCHITECTURE IMPLEMENTATION

You are implementing the dynamic agent architecture features.

INSTRUCTIONS:
Read implementation_specs/dynamic_architecture_spec.md for detailed specifications.

TASK:
Implement dynamic architecture in ALL orchestrators:
1. Add cwd parameter to asyncio.create_subprocess_exec calls
2. Add dynamic MCP config generation logic (read master registry, generate custom configs)
3. Add directory creation logic for app directories
4. Add symlink logic for configs from .agent_exec/test/ to app directories
5. Modify log/task output to write to app work directories instead of orchestrator root
6. Add EnhancedAgentTask parameters: mcp_needs, work_dir_name, debug_mode

CRITICAL:
- Work directory should be agent_base_work_dir + work_dir_name (e.g., apps/demo-tool/)
- MCP configs generated dynamically based on mcp_needs parameter
- Logs written to work directory, not orchestrator root
- Backward compatibility maintained

DELIVERABLE:
Modified orchestrator files with dynamic architecture and implementation report.

Follow the architect's specifications exactly.""",
            dependencies=["solution_architect", "mcp_registry_builder"],
        ),
        EnhancedAgentTask(
            task_id="debug_enhancement_specialist",
            task_type="development-specialist",
            prompt="""DEBUG ENHANCEMENT IMPLEMENTATION

You are adding comprehensive debug logging and agent debug flag support.

INSTRUCTIONS:
Read implementation_specs/debug_enhancement_spec.md for detailed specifications.

TASK:
1. Add comprehensive debug logging to ALL orchestrators:
   - Variable values during execution
   - Subprocess command construction
   - Token acquisition/release details
   - MCP config generation steps
   - Working directory assignments
   - Error capture details
   - Task dependency resolution

2. Add --debug flag support for individual agents:
   - Modify agent command construction to include --debug when agent debug_mode is True
   - Add logic to handle debug flag per agent

3. Fix existing debug logging issue:
   - Currently sets logging.DEBUG but mostly uses logger.info()
   - Add actual logger.debug() calls throughout execution flow

DELIVERABLE:
Modified orchestrator files with comprehensive debug logging and agent debug support, plus implementation report.

Follow the architect's specifications exactly.""",
            dependencies=["solution_architect"],
        ),
        # PHASE 4: POST-IMPLEMENTATION VALIDATION
        EnhancedAgentTask(
            task_id="post_implementation_validator",
            task_type="qa-testing-guru",
            prompt="""POST-IMPLEMENTATION VALIDATION

You are validating that ALL orchestrator enhancements work correctly together.

VALIDATION TESTS REQUIRED:
1. PARAMETER VALIDATION:
   - Verify all orchestrators can instantiate with new parameters
   - Test backward compatibility - existing calls still work
   - Validate parameter defaults and validation logic

2. MCP REGISTRY VALIDATION:
   - Verify master_mcp_registry.json is well-formed
   - Check all servers from both source files are included
   - Test dynamic config generation produces valid .mcp.json files

3. DYNAMIC ARCHITECTURE VALIDATION:
   - Test cwd parameter works in subprocess execution
   - Verify directory creation logic works
   - Test symlink creation and cleanup
   - Validate logs write to correct directories

4. DEBUG LOGGING VALIDATION:
   - Test debug logging actually produces useful output
   - Verify agent debug flag support works
   - Check performance impact of debug logging

5. INTEGRATION VALIDATION:
   - Test complete orchestrator run with new architecture
   - Verify no breaking changes to existing functionality
   - Test self-modification safety (orchestrator still works after changes)

6. ERROR CONDITION TESTING:
   - Test with invalid parameters
   - Test with missing directories
   - Test with malformed MCP configs

DELIVERABLE:
Create comprehensive validation_report.md with:
- VALIDATION STATUS: PASS/FAIL for each test category
- PERFORMANCE METRICS: Any slowdowns introduced
- INTEGRATION RESULTS: End-to-end test results
- CRITICAL ISSUES: Any problems found requiring remediation
- FINAL RECOMMENDATION: Ready for production use or needs fixes

Run actual tests - don't just review code. Use the enhanced orchestrator with new features.

CRITICAL: If any major issues found, create specific remediation tasks for follow-up agents.""",
            dependencies=[
                "mcp_registry_builder",
                "orchestrator_parameter_specialist",
                "dynamic_architecture_specialist",
                "debug_enhancement_specialist",
            ],
        ),
    ]

    print("🚀 Starting Orchestrator Enhancement with 7-Agent SDLC Pipeline...")
    print("Phase 1: Safety Validation & Solution Architecture")
    print(
        "Phase 2: Implementation (MCP Registry, Parameters, Dynamic Architecture, Debug)"
    )
    print("Phase 3: Post-Implementation Validation & Testing")
    print("=" * 80)

    await orchestrator.run(lambda: tasks)

    print("=" * 80)
    print("✅ Orchestrator Enhancement Complete!")
    print("Check validation_report.md for final status and next steps.")


if __name__ == "__main__":
    asyncio.run(main())
