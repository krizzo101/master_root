#!/usr/bin/env python3
"""
Script to automatically update Phase 2 and Phase 3 plans with proper phase assignments
"""
import re
import sys
from pathlib import Path

# Phase assignment rules based on task patterns
PHASE2_TASK_ASSIGNMENTS = {
    # Stage 1: Research tasks (foundation_research)
    "foundation_research": [
        "research_git_integration",
        "research_cicd_integration",
        "research_error_tracking",
        "research_monitoring_integration",
    ],
    # Stage 2: Design and Core Implementation (core_implementation)
    "core_implementation": [
        "design_git_adapter",
        "implement_git_adapter",
        "design_error_adapter",
        "implement_error_adapter",
        "implement_base_pipeline",
        "implement_chat_adapter",
        "implement_code_adapter",
        "design_cicd_adapter",
        "implement_cicd_adapter",
        "design_monitoring_adapter",
        "implement_monitoring_adapter",
    ],
    # Stage 3: Integration and Testing (integration_testing)
    "integration_testing": [
        "integrate_adapters",
        "optimize_pipeline_performance",
        "comprehensive_adapter_testing",
        "validate_end_to_end_pipeline",
    ],
}

PHASE3_TASK_ASSIGNMENTS = {
    # Stage 1: Research & Analysis (advanced_research)
    "advanced_research": [
        "research_ml_correlation",
        "research_temporal_analysis",
        "research_semantic_similarity",
        "analyze_ml_integration",
    ],
    # Stage 2: ML/AI Implementation (intelligence_implementation)
    "intelligence_implementation": [
        "implement_semantic_analyzer",
        "implement_ml_correlation_engine",
        "implement_temporal_correlation",
        "implement_pattern_detector",
        "implement_causal_chains",
        "design_intelligence_api",
        "implement_intelligence_api",
    ],
    # Stage 3: Advanced Features (advanced_features)
    "advanced_features": [
        "implement_predictive_analytics",
        "implement_anomaly_detection",
        "implement_recommendation_engine",
        "implement_advanced_search",
        "implement_real_time_correlation",
        "comprehensive_ml_testing",
        "optimize_intelligence_performance",
        "validate_intelligence_accuracy",
        "create_intelligence_documentation",
    ],
}


def update_phase2_assignments(file_path: Path) -> bool:
    """Update Phase 2 plan with phase assignments"""

    print(f"📝 Updating {file_path.name}...")

    try:
        content = file_path.read_text()

        # Update each task assignment
        for phase_id, task_ids in PHASE2_TASK_ASSIGNMENTS.items():
            for task_id in task_ids:
                # Pattern to match add_task calls for this task_id
                pattern = (
                    rf'(builder\.add_task\(\s*"{task_id}",.*?\n.*?\n.*?)(\n.*?\),)'
                )

                def replace_func(match):
                    task_content = match.group(1)
                    closing = match.group(2)

                    # Check if phase_id already exists
                    if "phase_id=" in task_content:
                        return match.group(0)  # Already has phase_id

                    # Add phase_id before the closing
                    return f'{task_content},\n        phase_id="{phase_id}",{closing}'

                content = re.sub(pattern, replace_func, content, flags=re.DOTALL)

        # Write updated content
        file_path.write_text(content)
        print(
            f"   ✅ Updated task assignments for {len(sum(PHASE2_TASK_ASSIGNMENTS.values(), []))} tasks"
        )
        return True

    except Exception as e:
        print(f"   ❌ Error updating {file_path.name}: {e}")
        return False


def update_phase3_assignments(file_path: Path) -> bool:
    """Update Phase 3 plan with phase assignments"""

    print(f"📝 Updating {file_path.name}...")

    try:
        content = file_path.read_text()

        # First, add the phase definitions if they don't exist
        if "builder.add_phase(" not in content:
            # Find the return builder.build() line
            build_pattern = r"(\n\s+return builder\.build\(\))"

            phase_definitions = """
    # === EXECUTION PHASES ===
    # Define stages with dependencies for controlled execution

    # Stage 1: Advanced Research & Analysis
    builder.add_phase(
        "advanced_research",
        "Advanced Research & Analysis",
        "Research ML/AI technologies and analyze requirements",
        max_parallel=4,  # Allow 4 parallel research tasks
        depends_on_phases=[],  # No dependencies - can start immediately
        gates=[]
    )

    # Stage 2: Intelligence Implementation
    builder.add_phase(
        "intelligence_implementation",
        "Intelligence Implementation",
        "Implement ML/AI correlation and intelligence features",
        max_parallel=6,  # Allow 6 parallel implementation tasks
        depends_on_phases=["advanced_research"],  # Wait for research to complete
        gates=[]
    )

    # Stage 3: Advanced Features & Optimization
    builder.add_phase(
        "advanced_features",
        "Advanced Features & Optimization",
        "Implement advanced features and optimize performance",
        max_parallel=5,  # Allow 5 parallel advanced tasks
        depends_on_phases=["intelligence_implementation"],  # Wait for core intelligence
        gates=["phase3_quality_validation", "intelligence_accuracy_validation"]
    )
"""

            content = re.sub(build_pattern, phase_definitions + r"\1", content)

        # Update each task assignment
        for phase_id, task_ids in PHASE3_TASK_ASSIGNMENTS.items():
            for task_id in task_ids:
                # Pattern to match add_task calls for this task_id
                pattern = (
                    rf'(builder\.add_task\(\s*"{task_id}",.*?\n.*?\n.*?)(\n.*?\),)'
                )

                def replace_func(match):
                    task_content = match.group(1)
                    closing = match.group(2)

                    # Check if phase_id already exists
                    if "phase_id=" in task_content:
                        return match.group(0)  # Already has phase_id

                    # Add phase_id before the closing
                    return f'{task_content},\n        phase_id="{phase_id}",{closing}'

                content = re.sub(pattern, replace_func, content, flags=re.DOTALL)

        # Write updated content
        file_path.write_text(content)
        print(
            f"   ✅ Updated task assignments for {len(sum(PHASE3_TASK_ASSIGNMENTS.values(), []))} tasks"
        )
        return True

    except Exception as e:
        print(f"   ❌ Error updating {file_path.name}: {e}")
        return False


def main():
    """Main function to update both phase plans"""

    print("🚀 UPDATING EXECUTIONPLAN PHASE ASSIGNMENTS")
    print("=" * 50)

    base_dir = Path("/home/opsvi/master_root/apps/project-context")

    phase2_file = base_dir / "unified_context_phase2_plan.py"
    phase3_file = base_dir / "unified_context_phase3_plan.py"

    success_count = 0

    # Update Phase 2
    if phase2_file.exists():
        if update_phase2_assignments(phase2_file):
            success_count += 1
    else:
        print(f"❌ Phase 2 file not found: {phase2_file}")

    # Update Phase 3
    if phase3_file.exists():
        if update_phase3_assignments(phase3_file):
            success_count += 1
    else:
        print(f"❌ Phase 3 file not found: {phase3_file}")

    print(f"\n🎯 SUMMARY: {success_count}/2 files updated successfully")

    if success_count == 2:
        print("✅ Both Phase 2 and Phase 3 plans now use proper ExecutionPhase staging!")
        print()
        print("💡 Test with:")
        print(
            "   python -c \"from unified_context_phase2_plan import create_unified_context_phase2_plan; p=create_unified_context_phase2_plan(); print(f'Phases: {len(p.phases)}')\""
        )
        return True
    else:
        print("❌ Some files failed to update - check errors above")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
