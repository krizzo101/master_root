#!/usr/bin/env python3
"""
PHASE 2: UNIFIED ORCHESTRATOR CRITICAL FIXES
Using the newly enhanced orchestrator to fix the 6 critical UnifiedOrchestrator issues
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.enhanced_orchestrator import EnhancedOrchestrator
from src.unified.unified_orchestrator import EnhancedAgentTask


async def main():
    # Use the Enhanced Orchestrator (working) to fix Unified Orchestrator (broken)
    # Load tokens from token tool
    from src.token_loader import load_tokens

    tokens = load_tokens()

    orchestrator = EnhancedOrchestrator(
        output_dir=Path("unified_orchestrator_fixes"),
        max_parallel=5,  # 5 critical fixes in parallel
        tokens=tokens,  # Provide explicit tokens
        # NEW ENHANCED FEATURES from Phase 1
        master_mcp_registry_path=Path(
            "/home/opsvi/master_root/.claude/master_mcp_registry.json"
        ),
        agent_execution_profile="standard",
        agent_debug_mode=False,  # Disable agent debug for clean JSON output
        agent_base_work_dir=Path("/home/opsvi/master_root/apps/"),
        enable_dynamic_configs=True,  # Use dynamic MCP configs
        log_to_work_dir=True,  # Logs in work directories
    )

    tasks = [
        # PHASE 1: VALIDATION & ANALYSIS
        EnhancedAgentTask(
            task_id="unified_issue_validator",
            task_type="qa-testing-guru",
            prompt="""UNIFIED ORCHESTRATOR CRITICAL ISSUE VALIDATION

REFERENCE MATERIALS - READ THESE FIRST:
1. /home/opsvi/master_root/apps/agent-orchestrator/UNIFIED_ORCHESTRATOR_VALIDATION_REPORT.md
2. /home/opsvi/master_root/apps/agent-orchestrator/orchestrator_validation_suite.py (validation plan that generated the failure logs)
3. /home/opsvi/master_root/apps/agent-orchestrator/unified_orchestrator_validation_20250906_220122/ (actual failure evidence)
4. /home/opsvi/master_root/apps/agent-orchestrator/tests/integration/test_unified_orchestrator.py

You are validating the 6 critical UnifiedOrchestrator issues that need fixing.

CRITICAL ISSUES TO VALIDATE (from validation report):

1. **Missing get_metrics() Method**
   - Status: May already be fixed
   - Location: src/unified/unified_orchestrator.py
   - Validation: Check if method exists and returns proper metrics

2. **Task Execution Engine Problems**
   - Issue: Empty error strings instead of actual errors
   - Location: src/generic_orchestrator.py error handling logic
   - Impact: Tasks fail with no diagnostic information

3. **Enhanced Feature Module Loading Failures**
   - Missing modules: QualityGatesModule, MonitoringModule, CollaborationModule, ExecutionPlanModule
   - Root cause: Broken imports or missing files
   - Location: src/unified/unified_orchestrator.py module loading

4. **Agent Context Isolation Problems**
   - Issue: Config inheritance problems between agents
   - Impact: Cross-agent config leakage
   - Solution needed: Isolated .agent_exec/ contexts

5. **Task Type Validation Failures**
   - Issue: Invalid task types like 'test-remediation-specialist'
   - Solution needed: Update task type taxonomy

6. **Subprocess Working Directory Missing**
   - Issue: No cwd parameter in subprocess calls
   - Impact: Relative paths don't resolve correctly
   - Location: Agent execution code

VALIDATION TASKS:
1. Read and analyze ALL orchestrator files
2. Identify which issues are already fixed vs still broken
3. Assess the scope and complexity of remaining fixes
4. Determine dependency order for fixes
5. Create detailed analysis for solution architect

DELIVERABLE:
Create unified_issues_analysis.md with:
- CURRENT STATUS: Which issues are fixed/broken
- ROOT CAUSE ANALYSIS: Detailed technical analysis
- COMPLEXITY ASSESSMENT: Difficulty level for each fix
- FIX DEPENDENCIES: What order fixes should be applied
- RECOMMENDATIONS: Approach for solution architect

Be thorough but focus on actionable technical details for the implementation agents.""",
            dependencies=[],
            # NEW ENHANCED FEATURES
            mcp_needs=[
                "knowledge",
                "thinking",
            ],  # Only needs knowledge and thinking tools
            work_dir_name="unified_orchestrator_fixes",
            debug_mode=False,  # Disable debug to get clean JSON output
        ),
        # PHASE 2: SOLUTION ARCHITECTURE
        EnhancedAgentTask(
            task_id="unified_solution_architect",
            task_type="solution-architect",
            prompt="""UNIFIED ORCHESTRATOR SOLUTION ARCHITECTURE

REFERENCE MATERIALS - READ THESE FIRST:
1. /home/opsvi/master_root/apps/agent-orchestrator/UNIFIED_ORCHESTRATOR_VALIDATION_REPORT.md
2. /home/opsvi/master_root/apps/agent-orchestrator/orchestrator_validation_suite.py
3. /home/opsvi/master_root/apps/agent-orchestrator/unified_orchestrator_validation_20250906_220122/
4. unified_issues_analysis.md (from validator agent)

You are designing the specific implementation strategy for fixing UnifiedOrchestrator issues.

INPUT TO REVIEW:
1. Read unified_issues_analysis.md for detailed issue analysis
2. Review current orchestrator code structure
3. Understand the dependency relationships between fixes
4. Study the original validation plan and failure patterns

YOUR TASK:
Design the exact implementation approach for each remaining issue:

1. **Create Implementation Specifications**:
   - One spec file per critical issue
   - Exact file paths, function names, code patterns to modify
   - Specific implementation approaches
   - Integration points with existing code

2. **Design Implementation Order**:
   - Dependency-aware fix sequence
   - Parallel vs sequential implementation plan
   - Risk mitigation for each change

3. **Create Agent Work Packages**:
   - Detailed prompts for implementation agents
   - Clear success criteria for each fix
   - Testing and validation requirements

DELIVERABLE:
Create detailed specs in implementation_specs/ directory:
- error_capture_fix_spec.md: Fix empty error string problems
- module_loading_fix_spec.md: Fix enhanced feature module imports
- context_isolation_fix_spec.md: Fix agent config inheritance issues
- task_validation_fix_spec.md: Fix invalid task type problems
- subprocess_cwd_fix_spec.md: Add working directory support

Each spec must be detailed enough that implementation agents can execute without analysis - just implement.

Include exact code changes, file locations, and integration approaches.""",
            dependencies=["unified_issue_validator"],
            mcp_needs=["knowledge", "thinking"],
            work_dir_name="unified_orchestrator_fixes",
            debug_mode=False,  # Clean JSON output
        ),
        # PHASE 3: IMPLEMENTATION SPECIALISTS (can run in parallel)
        EnhancedAgentTask(
            task_id="error_capture_specialist",
            task_type="development-specialist",
            prompt="""ERROR CAPTURE FIX IMPLEMENTATION

REFERENCE MATERIALS - READ THESE FIRST:
1. /home/opsvi/master_root/apps/agent-orchestrator/UNIFIED_ORCHESTRATOR_VALIDATION_REPORT.md
2. /home/opsvi/master_root/apps/agent-orchestrator/unified_orchestrator_validation_20250906_220122/ (failure evidence)
3. implementation_specs/error_capture_fix_spec.md (from solution architect)

Read implementation_specs/error_capture_fix_spec.md for exact specifications.

TASK: Fix the error capture problem where tasks fail but show empty error strings.

EXPECTED ISSUES TO FIX:
- Empty stderr causing empty error messages
- JSON parsing errors from invalid stdout
- CLI input errors not properly captured
- Process failure with no diagnostic information

REQUIREMENTS:
- Maintain backward compatibility
- Ensure all error conditions provide useful diagnostics
- Test with various failure scenarios
- Update error handling logic in generic_orchestrator.py

COMPREHENSIVE TESTING & VERIFICATION REQUIRED:
1. **Code Path Analysis**: Trace through EVERY logical execution path in error handling
2. **Edge Case Testing**: Test empty stderr, JSON parsing failures, CLI input errors, subprocess crashes
3. **Integration Testing**: Verify error capture works with actual agent execution
4. **Regression Testing**: Ensure existing functionality still works
5. **Performance Testing**: Confirm error handling doesn't impact performance

ISSUE IDENTIFICATION REQUIREMENT:
If you discover additional issues during implementation that cannot be corrected in this run:
- Provide detailed explanation of WHAT the issue is
- Explain WHY it cannot be fixed in this run
- Include all technical details necessary for the next implementation plan
- Specify exact code locations, dependencies, and complexity assessment

DELIVERABLE:
- Modified orchestrator files with improved error capture
- Comprehensive test report with all code paths verified
- Documentation of all changes and any issues discovered
- Complete verification that solution works as intended

Follow the architect's specifications exactly.""",
            dependencies=["unified_solution_architect"],
            mcp_needs=["knowledge"],
            work_dir_name="unified_orchestrator_fixes",
            debug_mode=False,  # Clean JSON output
        ),
        EnhancedAgentTask(
            task_id="module_loading_specialist",
            task_type="development-specialist",
            prompt="""MODULE LOADING FIX IMPLEMENTATION

Read implementation_specs/module_loading_fix_spec.md for exact specifications.

TASK: Fix the enhanced feature module loading failures in UnifiedOrchestrator.

EXPECTED MODULES TO FIX:
- QualityGatesModule import failures
- MonitoringModule import failures
- CollaborationModule import failures
- ExecutionPlanModule import failures

APPROACHES TO IMPLEMENT:
- Fix import paths
- Write full implementations for any missing modules
- Implement complete module functionality as designed
- Update module registry functionality

REQUIREMENTS:
- UnifiedOrchestrator should load without import errors
- Enhanced features must work completely as designed
- All modules must be fully functional implementations
- Maintain modular architecture design with complete functionality

COMPREHENSIVE TESTING & VERIFICATION REQUIRED:
1. **Module Integration Testing**: Test ALL module loading paths and graceful fallbacks
2. **Feature Functionality Testing**: Verify every implemented feature works completely
3. **Cross-Module Testing**: Test module interactions and dependencies
4. **Performance Testing**: Measure module loading impact and runtime performance
5. **Code Path Analysis**: Trace through every module loading scenario

ISSUE IDENTIFICATION REQUIREMENT:
If you discover additional issues during implementation that cannot be corrected in this run:
- Provide detailed explanation of WHAT the issue is
- Explain WHY it cannot be fixed in this run
- Include all technical details necessary for the next implementation plan
- Specify exact code locations, dependencies, and complexity assessment

DELIVERABLE:
- Fixed module loading in unified_orchestrator.py
- Complete implementations of any missing modules
- Comprehensive test report verifying ALL functionality works
- Documentation of all implementations and any issues discovered

Follow the architect's specifications exactly.""",
            dependencies=["unified_solution_architect"],
            mcp_needs=["knowledge"],
            work_dir_name="unified_orchestrator_fixes",
            debug_mode=False,  # Clean JSON output
        ),
        EnhancedAgentTask(
            task_id="context_isolation_specialist",
            task_type="development-specialist",
            prompt="""AGENT CONTEXT ISOLATION FIX IMPLEMENTATION

Read implementation_specs/context_isolation_fix_spec.md for exact specifications.

TASK: Fix agent context isolation to prevent cross-agent config leakage.

EXPECTED FIXES:
- Create isolated .agent_exec/ contexts per agent
- Fix config inheritance problems
- Ensure agents don't interfere with each other
- Implement proper context cleanup

APPROACHES:
- Dynamic .agent_exec/[agent_id]/ directory creation
- Agent-specific config file generation
- Context cleanup after agent completion
- Subprocess environment isolation

REQUIREMENTS:
- Each agent runs in isolated context
- No config leakage between agents
- Proper cleanup of temporary contexts
- Maintain orchestrator functionality

DELIVERABLE:
- Modified orchestrator with context isolation
- Context creation and cleanup logic
- Test report confirming isolation works
- Documentation of changes made

Follow the architect's specifications exactly.""",
            dependencies=["unified_solution_architect"],
            mcp_needs=["knowledge"],
            work_dir_name="unified_orchestrator_fixes",
            debug_mode=False,  # Clean JSON output
        ),
        EnhancedAgentTask(
            task_id="task_validation_specialist",
            task_type="development-specialist",
            prompt="""TASK TYPE VALIDATION FIX IMPLEMENTATION

Read implementation_specs/task_validation_fix_spec.md for exact specifications.

TASK: Fix invalid task type validation failures.

EXPECTED FIXES:
- Remove invalid task types like 'test-remediation-specialist'
- Update task type taxonomy with valid agent types
- Fix task validation logic
- Ensure all task types map to valid agents

VALID AGENT TYPES TO USE:
- security-architect, solution-architect, requirements-analyst
- development-specialist, qa-testing-guru, performance-optimizer
- api-integration-specialist, database-specialist
- business-analyst, technical-writer
- research-genius, code-analyzer

REQUIREMENTS:
- All task types must be valid and supported
- Update any hardcoded task type references
- Ensure task validation doesn't reject valid types
- Maintain agent type consistency

COMPREHENSIVE TESTING & VERIFICATION REQUIRED:
1. **Task Type Coverage Testing**: Test ALL valid task types are accepted
2. **Validation Logic Testing**: Verify invalid types are properly rejected
3. **Agent Type Mapping Testing**: Confirm all task types map to valid agents
4. **Integration Testing**: Test task creation with new validation logic
5. **Code Path Analysis**: Trace through every validation scenario

ISSUE IDENTIFICATION REQUIREMENT:
If you discover additional issues during implementation that cannot be corrected in this run:
- Provide detailed explanation of WHAT the issue is
- Explain WHY it cannot be fixed in this run
- Include all technical details necessary for the next implementation plan
- Specify exact code locations, dependencies, and complexity assessment

DELIVERABLE:
- Updated task type taxonomy with complete validation
- Fixed validation logic with comprehensive testing
- Complete verification report confirming all scenarios work
- Documentation of all changes and any issues discovered

Follow the architect's specifications exactly.""",
            dependencies=["unified_solution_architect"],
            mcp_needs=["knowledge"],
            work_dir_name="unified_orchestrator_fixes",
            debug_mode=False,  # Clean JSON output
        ),
        # PHASE 4: FINAL VALIDATION
        EnhancedAgentTask(
            task_id="unified_fixes_validator",
            task_type="qa-testing-guru",
            prompt="""UNIFIED ORCHESTRATOR FIXES VALIDATION

You are validating that ALL UnifiedOrchestrator critical fixes work correctly together.

VALIDATION TESTS REQUIRED:

1. **get_metrics() Method Test**:
   - Verify method exists and returns proper metrics
   - Test with various orchestrator states

2. **Error Capture Test**:
   - Test tasks that fail with various error conditions
   - Verify error messages are captured and useful
   - Test JSON parsing error scenarios

3. **Module Loading Test**:
   - Test UnifiedOrchestrator initialization
   - Verify enhanced features load or degrade gracefully
   - Test module registry functionality

4. **Context Isolation Test**:
   - Run multiple agents with different configs
   - Verify no config leakage between agents
   - Test context cleanup

5. **Task Type Validation Test**:
   - Test all valid task types are accepted
   - Verify invalid task types are rejected properly
   - Test task creation and validation logic

6. **Integration Test**:
   - Run a complete UnifiedOrchestrator workflow
   - Test with various feature combinations
   - Verify backward compatibility maintained

7. **Performance Test**:
   - Measure initialization time
   - Test with multiple agents
   - Verify no performance regressions

DELIVERABLE:
Create unified_fixes_validation_report.md with:
- VALIDATION STATUS: PASS/FAIL for each test category
- INTEGRATION RESULTS: End-to-end test results
- PERFORMANCE METRICS: Any performance impact
- CRITICAL ISSUES: Any remaining problems
- PRODUCTION READINESS: Final recommendation

Run actual tests using the fixed UnifiedOrchestrator. If major issues found, create specific remediation tasks.

This validation determines if UnifiedOrchestrator is ready for production use.""",
            dependencies=[
                "error_capture_specialist",
                "module_loading_specialist",
                "context_isolation_specialist",
                "task_validation_specialist",
            ],
            mcp_needs=["knowledge", "thinking"],
            work_dir_name="unified_orchestrator_fixes",
            debug_mode=False,  # Clean JSON output
        ),
    ]

    print("🚀 Starting Phase 2: UnifiedOrchestrator Critical Fixes...")
    print("Using Enhanced Orchestrator with Dynamic Architecture")
    print("Phase 1: Issue Validation & Solution Architecture")
    print("Phase 2: Parallel Implementation (4 specialists)")
    print("Phase 3: Final Integration Validation")
    print("=" * 80)

    await orchestrator.run(lambda: tasks)

    print("=" * 80)
    print("✅ UnifiedOrchestrator Critical Fixes Complete!")
    print("Check unified_fixes_validation_report.md for production readiness status.")


if __name__ == "__main__":
    asyncio.run(main())
