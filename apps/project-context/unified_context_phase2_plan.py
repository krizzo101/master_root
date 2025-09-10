#!/usr/bin/env python3
"""
ExecutionPlan for Unified Context System Phase 2: Core Ingestion (Week 3-4)
Building on the foundation from Phase 1 to implement comprehensive ingestion pipelines
"""
import os
import sys

sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator")

from execution_plan_schema import QualityGateType, TaskType
from execution_plan_template import ExecutionPlanBuilder
from execution_plan_validation import validate_execution_plan


def create_unified_context_phase2_plan():
    """
    Create ExecutionPlan for Unified Context System Phase 2: Core Ingestion (Week 3-4)
    Based on the design document requirements for comprehensive data ingestion
    """

    builder = ExecutionPlanBuilder("Unified Context System Phase 2: Core Ingestion")

    # === GIT HISTORY INGESTION ===

    builder.add_task(
        "research_git_integration",
        TaskType.RESEARCH_GENIUS,
        "Research Git history analysis patterns, commit parsing libraries, and integration strategies for extracting code evolution data",
        context={
            "focus_areas": [
                "GitPython vs pygit2 performance",
                "Commit analysis patterns",
                "Branch/merge tracking",
                "Performance optimization for large repos",
                "Incremental processing strategies",
            ]
        },
        phase_id="foundation_research",
    )

    builder.add_task(
        "design_git_adapter",
        TaskType.SOLUTION_ARCHITECT,
        "Design the Git history adapter architecture with commit analysis, branch tracking, and incremental processing",
        dependencies=["research_git_integration"],
        context={
            "adapter_features": [
                "Commit message parsing",
                "File change tracking",
                "Author/committer analysis",
                "Branch and merge detection",
                "Pull request correlation",
                "Incremental updates",
            ]
        },
    )

    builder.add_task(
        "implement_git_adapter",
        TaskType.DEVELOPMENT_SPECIALIST,
        "Implement the Git history adapter with comprehensive commit analysis and efficient incremental processing",
        dependencies=["design_git_adapter"],
        context={
            "implementation_files": [
                "src/ingestion/adapters/git_adapter.py",
                "src/ingestion/processors/commit_processor.py",
                "src/ingestion/analyzers/code_change_analyzer.py",
            ]
        },
    )

    # === ERROR LOG INGESTION ===

    builder.add_task(
        "design_error_log_system",
        TaskType.SOLUTION_ARCHITECT,
        "Design error log ingestion system with structured error parsing, stack trace analysis, and correlation detection",
        context={
            "error_sources": [
                "Application logs",
                "System logs",
                "Web server logs",
                "Database error logs",
                "CI/CD pipeline errors",
                "Container runtime errors",
            ]
        },
    )

    builder.add_task(
        "implement_error_adapter",
        TaskType.DEVELOPMENT_SPECIALIST,
        "Implement error log adapter with intelligent parsing, severity classification, and automatic correlation triggers",
        dependencies=["design_error_log_system"],
        context={
            "adapter_capabilities": [
                "Multi-format log parsing",
                "Stack trace extraction",
                "Error classification",
                "Frequency tracking",
                "Correlation triggers",
            ]
        },
    )

    # === CI/CD PIPELINE INTEGRATION ===

    builder.add_task(
        "research_cicd_integration",
        TaskType.RESEARCH_GENIUS,
        "Research CI/CD pipeline integration patterns for GitHub Actions, Jenkins, GitLab CI, and other systems",
        context={
            "integration_targets": [
                "GitHub Actions webhooks",
                "Jenkins API integration",
                "GitLab CI pipeline data",
                "Build artifact tracking",
                "Deployment correlation",
            ]
        },
    )

    builder.add_task(
        "implement_cicd_adapter",
        TaskType.DEVELOPMENT_SPECIALIST,
        "Implement CI/CD adapter with webhook handling, build status tracking, and deployment correlation",
        dependencies=["research_cicd_integration"],
        context={
            "webhook_support": [
                "GitHub Actions",
                "GitLab CI",
                "Jenkins",
                "Azure DevOps",
                "CircleCI",
            ]
        },
    )

    # === DEDUPLICATION SYSTEM ===

    builder.add_task(
        "design_deduplication_engine",
        TaskType.SOLUTION_ARCHITECT,
        "Design comprehensive deduplication system with content hashing, similarity detection, and intelligent merging",
        context={
            "deduplication_strategies": [
                "Content hash comparison",
                "Semantic similarity",
                "Time-window deduplication",
                "Cross-source correlation",
                "Intelligent merging rules",
            ]
        },
    )

    builder.add_task(
        "implement_deduplication",
        TaskType.DEVELOPMENT_SPECIALIST,
        "Implement deduplication engine with hash-based detection, similarity analysis, and automatic merge logic",
        dependencies=["design_deduplication_engine"],
        context={
            "implementation_components": [
                "Content hash processor",
                "Similarity calculator",
                "Merge rule engine",
                "Duplicate resolver",
                "Performance optimizer",
            ]
        },
    )

    # === EMBEDDING GENERATION SYSTEM ===

    builder.add_task(
        "research_embedding_optimization",
        TaskType.RESEARCH_GENIUS,
        "Research embedding generation optimization, model selection, and batch processing strategies for large-scale ingestion",
        context={
            "research_areas": [
                "OpenAI embeddings API optimization",
                "Local embedding models (sentence-transformers)",
                "Batch processing strategies",
                "Cost optimization",
                "Performance benchmarking",
            ]
        },
    )

    builder.add_task(
        "implement_embedding_system",
        TaskType.DEVELOPMENT_SPECIALIST,
        "Implement high-performance embedding generation system with batching, caching, and fallback strategies",
        dependencies=["research_embedding_optimization"],
        context={
            "system_features": [
                "Batch processing",
                "Rate limiting",
                "Cache management",
                "Fallback strategies",
                "Cost monitoring",
            ]
        },
    )

    # === RELATIONSHIP EXTRACTION ===

    builder.add_task(
        "design_relationship_extractor",
        TaskType.SOLUTION_ARCHITECT,
        "Design intelligent relationship extraction system with pattern recognition and automatic correlation detection",
        context={
            "relationship_types": [
                "File references in chat",
                "Function mentions in commits",
                "Error-to-code correlations",
                "Temporal relationships",
                "Causal chains",
            ]
        },
    )

    builder.add_task(
        "implement_relationship_extraction",
        TaskType.DEVELOPMENT_SPECIALIST,
        "Implement relationship extraction engine with NLP pattern matching and machine learning correlation detection",
        dependencies=["design_relationship_extractor"],
        context={
            "extraction_techniques": [
                "Regex pattern matching",
                "NLP entity extraction",
                "Semantic similarity",
                "Temporal correlation",
                "ML-based detection",
            ]
        },
    )

    # === INTEGRATION AND PERFORMANCE ===

    builder.add_task(
        "integrate_ingestion_pipeline",
        TaskType.API_INTEGRATION_SPECIALIST,
        "Integrate all ingestion adapters into unified pipeline with orchestration, monitoring, and error handling",
        dependencies=[
            "implement_git_adapter",
            "implement_error_adapter",
            "implement_cicd_adapter",
            "implement_deduplication",
            "implement_embedding_system",
            "implement_relationship_extraction",
        ],
        context={
            "integration_features": [
                "Pipeline orchestration",
                "Real-time monitoring",
                "Error handling",
                "Retry mechanisms",
                "Performance metrics",
            ]
        },
    )

    builder.add_task(
        "optimize_ingestion_performance",
        TaskType.PERFORMANCE_OPTIMIZER,
        "Optimize ingestion pipeline performance for high-throughput processing and concurrent operations",
        dependencies=["integrate_ingestion_pipeline"],
        context={
            "optimization_targets": [
                "1000+ items/second ingestion",
                "Concurrent pipeline processing",
                "Memory usage optimization",
                "Database connection pooling",
                "Batch processing efficiency",
            ]
        },
    )

    builder.add_task(
        "comprehensive_phase2_testing",
        TaskType.QA_TESTING_GURU,
        "Create and execute comprehensive test suite for all ingestion adapters and pipeline components",
        dependencies=["optimize_ingestion_performance"],
        context={
            "test_coverage": [
                "Adapter unit tests",
                "Integration testing",
                "Performance benchmarks",
                "Error handling validation",
                "End-to-end pipeline tests",
            ]
        },
    )

    # === QUALITY GATES ===

    # Performance validation gate
    builder.add_quality_gate(
        "ingestion_performance_validation",
        "Ingestion Performance Standards",
        "Validate ingestion pipeline meets performance requirements",
        QualityGateType.CUSTOM,
        {
            "ingestion_rate": "1000+ items/second",
            "concurrent_adapters": "5+ simultaneous",
            "deduplication_accuracy": ">95%",
            "embedding_throughput": "100+ items/second",
        },
    )

    # Data quality gate
    builder.add_quality_gate(
        "data_quality_validation",
        "Data Quality Standards",
        "Validate data integrity and relationship accuracy",
        QualityGateType.CUSTOM,
        {
            "relationship_accuracy": ">90%",
            "deduplication_precision": ">95%",
            "embedding_quality": "semantic similarity >0.8",
            "error_correlation": ">80% automatic detection",
        },
    )

    # Integration testing gate
    builder.add_quality_gate(
        "integration_testing_validation",
        "Integration Testing Standards",
        "Validate all adapters integrate properly with pipeline",
        QualityGateType.TEST_RESULTS,
        {
            "required_test_types": ["unit", "integration", "performance", "end-to-end"],
            "min_pass_rate": 95,
            "adapter_coverage": "100%",
        },
    )

    # === EXECUTION PHASES ===
    # Define stages with dependencies for controlled execution

    # Stage 1: Foundation & Research (parallel execution within stage)
    builder.add_phase(
        "foundation_research",
        "Foundation Research",
        "Research and analyze requirements for ingestion pipeline",
        max_parallel=4,  # Allow 4 parallel research tasks
        depends_on_phases=[],  # No dependencies - can start immediately
        gates=[],
    )

    # Stage 2: Core Implementation (depends on research completion)
    builder.add_phase(
        "core_implementation",
        "Core Implementation",
        "Implement core ingestion pipeline components",
        max_parallel=6,  # Allow 6 parallel implementation tasks
        depends_on_phases=["foundation_research"],  # Wait for research to complete
        gates=[],
    )

    # Stage 3: Integration & Testing (depends on core implementation)
    builder.add_phase(
        "integration_testing",
        "Integration & Testing",
        "Integrate components and validate functionality",
        max_parallel=4,  # Allow 4 parallel integration tasks
        depends_on_phases=["core_implementation"],  # Wait for implementation
        gates=["phase2_quality_validation", "pipeline_performance_validation"],
    )

    return builder.build()


def main():
    """Create and validate the Phase 2 execution plan"""
    print("🚀 Creating Unified Context System Phase 2 ExecutionPlan...")

    plan = create_unified_context_phase2_plan()

    print(
        f"📋 Phase 2 plan created with {len(plan.tasks)} tasks and {len(plan.quality_gates)} quality gates"
    )

    # Validate the plan
    print("\n🔍 Validating Phase 2 execution plan...")
    result = validate_execution_plan(plan)

    if result.success:
        print("✅ Phase 2 ExecutionPlan validation PASSED!")
        print(f"   Tasks: {len(plan.tasks)}")
        print(f"   Quality Gates: {len(plan.quality_gates)}")
        print(f"   Dependencies: {sum(len(task.dependencies) for task in plan.tasks)}")

        print("\n📊 Task breakdown by agent type:")
        task_types = {}
        for task in plan.tasks:
            agent_type = task.task_type.value
            task_types[agent_type] = task_types.get(agent_type, 0) + 1

        for agent_type, count in sorted(task_types.items()):
            print(f"   {agent_type}: {count} tasks")

        print("\n🎯 Phase 2 ready for execution after Phase 1 completion!")
        return plan

    else:
        print("❌ Phase 2 ExecutionPlan validation FAILED!")
        print(f"   Errors: {result.error_count}")
        for error in result.errors:
            print(f"   - {error}")
        return None


if __name__ == "__main__":
    main()
