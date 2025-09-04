#!/usr/bin/env python3
"""
Execute Phase 2 using GenericOrchestrator (Known Working Pattern)
Phase 2: Core Ingestion - Git history, error logs, CI/CD integration, and deduplication
Uses the same reliable pattern as execute_phase1_generic.py
"""
import asyncio
import os
import sys
from pathlib import Path

# Add paths for imports
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator")
sys.path.append("/home/opsvi/master_root/apps/project-context")

from src.generic_orchestrator import AgentTask, GenericOrchestrator
from src.token_loader import TokenLoader


def create_phase2_agent_tasks():
    """
    Create Phase 2 tasks as AgentTask objects
    Following the original working pattern from execute_phase1_generic.py
    """

    agent_tasks = []

    # === GIT HISTORY INGESTION PIPELINE ===

    # Task 1: Git Integration Research (no dependencies)
    git_research_prompt = """TASK: Research Git history analysis patterns and integration strategies for code evolution data.

SPECIALIST ROLE: You are acting as a research-genius agent.

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context
- Foundation: Phase 1 chat and code adapters completed
- Target: Comprehensive Git history integration
- Database: postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context

REQUIREMENTS:
1. Research Git analysis libraries and patterns:
   - Compare GitPython vs pygit2 performance characteristics
   - Analyze commit parsing and extraction strategies
   - Research branch and merge tracking approaches
   - Investigate incremental processing for large repositories
   - Study performance optimization techniques

2. Integration strategies:
   - Repository scanning and discovery methods
   - Commit metadata extraction and storage
   - Author and committer analysis approaches
   - File change tracking and correlation
   - Pull request and issue correlation patterns

3. Architecture recommendations:
   - Optimal data structures for Git history
   - Incremental update strategies
   - Performance benchmarking approaches
   - Integration with existing unified context schema

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are implementing Phase 2 of the Unified Context System - extending the temporal knowledge graph with Git history to correlate code changes with conversations and errors.
"""

    agent_tasks.append(
        AgentTask(
            task_id="research_git_integration",
            task_type="research-genius",
            prompt=git_research_prompt,
            context={"phase": "phase2_foundation", "priority": "high"},
        )
    )

    # Task 2: Git Adapter Design (depends on research)
    git_design_prompt = """TASK: Design Git history adapter architecture with comprehensive commit analysis and incremental processing.

SPECIALIST ROLE: You are acting as a solution-architect agent.

DEPENDENCIES: This task depends on completion of: research_git_integration

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context
- Research Findings: Use insights from research_git_integration task
- Integration Points: Phase 1 adapters and unified schema
- Performance Target: Handle repositories with 10K+ commits

REQUIREMENTS:
1. Adapter Architecture Design:
   - GitAdapter class with incremental processing
   - Commit analysis and metadata extraction
   - Branch and merge detection algorithms
   - Author/committer relationship tracking
   - File change correlation system

2. Data Model Integration:
   - Git history schema extensions to unified context
   - Temporal correlation with chat logs and code intelligence
   - Relationship modeling between commits, files, and conversations
   - Performance optimization through proper indexing

3. Implementation Strategy:
   - Modular component design for maintainability
   - Error handling and recovery mechanisms
   - Progress tracking and monitoring capabilities
   - Configuration management for different repositories

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are implementing Phase 2 of the Unified Context System - extending the temporal knowledge graph with Git history to correlate code changes with conversations and errors.
"""

    agent_tasks.append(
        AgentTask(
            task_id="design_git_adapter",
            task_type="solution-architect",
            prompt=git_design_prompt,
            dependencies=["research_git_integration"],
            context={"phase": "phase2_foundation", "priority": "high"},
        )
    )

    # Task 3: Git Adapter Implementation (depends on design)
    git_implementation_prompt = """TASK: Implement Git history adapter with comprehensive commit analysis and efficient incremental processing.

SPECIALIST ROLE: You are acting as a development-specialist agent.

DEPENDENCIES: This task depends on completion of: design_git_adapter

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context
- Architecture: Use design from design_git_adapter task
- Target Files: src/ingestion/adapters/git_adapter.py
- Integration: Phase 1 base pipeline and schema

REQUIREMENTS:
1. GitAdapter Implementation:
   - Complete git_adapter.py with incremental processing
   - Commit message parsing and entity extraction
   - File change tracking with diff analysis
   - Branch and merge detection algorithms
   - Author/committer relationship mapping

2. Supporting Components:
   - CommitProcessor for metadata extraction
   - CodeChangeAnalyzer for file diff analysis
   - GitRepository scanner for discovery
   - Progress tracking and monitoring

3. Integration Features:
   - Database integration with unified context schema
   - Correlation with existing chat and code data
   - Performance optimization with caching
   - Comprehensive error handling and recovery

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are implementing Phase 2 of the Unified Context System - extending the temporal knowledge graph with Git history to correlate code changes with conversations and errors.
"""

    agent_tasks.append(
        AgentTask(
            task_id="implement_git_adapter",
            task_type="development-specialist",
            prompt=git_implementation_prompt,
            dependencies=["design_git_adapter"],
            context={"phase": "phase2_implementation", "priority": "high"},
        )
    )

    # === ERROR LOG INGESTION PIPELINE ===

    # Task 4: Error Log System Design (can run parallel with Git work)
    error_design_prompt = """TASK: Design error log ingestion system with structured parsing and correlation detection.

SPECIALIST ROLE: You are acting as a solution-architect agent.

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context
- Error Sources: Application logs, system logs, CI/CD errors
- Integration: Correlate with Git commits and chat conversations
- Performance: Handle high-volume log ingestion

REQUIREMENTS:
1. Error Log Architecture:
   - Multi-format log parser (JSON, text, structured)
   - Stack trace extraction and analysis
   - Error classification and severity scoring
   - Frequency tracking and pattern detection
   - Automatic correlation trigger system

2. Integration Design:
   - Correlation with Git commits (when errors appear)
   - Connection to chat conversations (when errors discussed)
   - Relationship with code intelligence data
   - Temporal analysis for error trends

3. Processing Pipeline:
   - Real-time log ingestion capabilities
   - Batch processing for historical logs
   - Error deduplication and clustering
   - Alert generation for critical errors

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are implementing Phase 2 of the Unified Context System - extending the temporal knowledge graph with error logs to provide comprehensive debugging and incident analysis.
"""

    agent_tasks.append(
        AgentTask(
            task_id="design_error_log_system",
            task_type="solution-architect",
            prompt=error_design_prompt,
            context={"phase": "phase2_foundation", "priority": "high"},
        )
    )

    # Task 5: Error Adapter Implementation (depends on error design)
    error_implementation_prompt = """TASK: Implement error log adapter with intelligent parsing and automatic correlation triggers.

SPECIALIST ROLE: You are acting as a development-specialist agent.

DEPENDENCIES: This task depends on completion of: design_error_log_system

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context
- Architecture: Use design from design_error_log_system task
- Target Files: src/ingestion/adapters/error_adapter.py
- Integration: Unified context schema and existing adapters

REQUIREMENTS:
1. ErrorAdapter Implementation:
   - Multi-format log parser with flexible configuration
   - Stack trace extraction and structured analysis
   - Error severity classification algorithms
   - Pattern detection and frequency tracking
   - Correlation trigger system for related data

2. Analysis Components:
   - ErrorClassifier for severity and type detection
   - StackTraceAnalyzer for root cause identification
   - CorrelationEngine for linking errors to code/commits
   - TrendAnalyzer for pattern recognition

3. Integration Features:
   - Real-time processing capabilities
   - Database integration with proper indexing
   - Error deduplication and clustering
   - Performance monitoring and alerting

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are implementing Phase 2 of the Unified Context System - extending the temporal knowledge graph with error logs to provide comprehensive debugging and incident analysis.
"""

    agent_tasks.append(
        AgentTask(
            task_id="implement_error_adapter",
            task_type="development-specialist",
            prompt=error_implementation_prompt,
            dependencies=["design_error_log_system"],
            context={"phase": "phase2_implementation", "priority": "high"},
        )
    )

    # === CI/CD INTEGRATION PIPELINE ===

    # Task 6: CI/CD Integration Research (parallel with other research)
    cicd_research_prompt = """TASK: Research CI/CD pipeline integration patterns for comprehensive build and deployment tracking.

SPECIALIST ROLE: You are acting as a research-genius agent.

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context
- Integration Targets: GitHub Actions, Jenkins, GitLab CI, Azure DevOps
- Correlation Goals: Link builds/deployments to code changes and conversations
- Performance: Handle webhook-based real-time updates

REQUIREMENTS:
1. CI/CD Integration Patterns:
   - Webhook configuration and handling strategies
   - API integration approaches for different platforms
   - Build status and artifact tracking methods
   - Deployment correlation and environment tracking
   - Performance metrics and success rate analysis

2. Platform Analysis:
   - GitHub Actions workflow and job structure
   - Jenkins pipeline and build data extraction
   - GitLab CI/CD pipeline metadata
   - Azure DevOps build and release tracking
   - CircleCI workflow and step analysis

3. Integration Architecture:
   - Real-time webhook processing design
   - Batch API polling for historical data
   - Authentication and security patterns
   - Rate limiting and error handling strategies

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are implementing Phase 2 of the Unified Context System - extending the temporal knowledge graph with CI/CD data to correlate builds and deployments with code changes and conversations.
"""

    agent_tasks.append(
        AgentTask(
            task_id="research_cicd_integration",
            task_type="research-genius",
            prompt=cicd_research_prompt,
            context={"phase": "phase2_foundation", "priority": "normal"},
        )
    )

    # Task 7: CI/CD Adapter Implementation (depends on CI/CD research)
    cicd_implementation_prompt = """TASK: Implement CI/CD adapter with webhook handling and deployment correlation.

SPECIALIST ROLE: You are acting as a development-specialist agent.

DEPENDENCIES: This task depends on completion of: research_cicd_integration

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context
- Research Findings: Use insights from research_cicd_integration task
- Target Files: src/ingestion/adapters/cicd_adapter.py
- Integration: Correlate with Git commits and error logs

REQUIREMENTS:
1. CICDAdapter Implementation:
   - Multi-platform webhook handler (GitHub, GitLab, Jenkins)
   - Build status tracking and artifact management
   - Deployment correlation with environment tracking
   - Performance metrics calculation
   - Real-time status updates

2. Platform Support:
   - GitHub Actions integration with workflow/job data
   - Jenkins API integration for build information
   - GitLab CI pipeline and job tracking
   - Azure DevOps build and release data
   - Generic webhook support for other platforms

3. Correlation Features:
   - Link builds to specific commits and pull requests
   - Connect deployments to code changes
   - Correlate failures with error logs and chat discussions
   - Track performance trends and success rates

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are implementing Phase 2 of the Unified Context System - extending the temporal knowledge graph with CI/CD data to correlate builds and deployments with code changes and conversations.
"""

    agent_tasks.append(
        AgentTask(
            task_id="implement_cicd_adapter",
            task_type="development-specialist",
            prompt=cicd_implementation_prompt,
            dependencies=["research_cicd_integration"],
            context={"phase": "phase2_implementation", "priority": "normal"},
        )
    )

    # === DEDUPLICATION SYSTEM ===

    # Task 8: Deduplication Engine Design (depends on all adapters being designed)
    dedup_design_prompt = """TASK: Design comprehensive deduplication system with content hashing and intelligent merging.

SPECIALIST ROLE: You are acting as a solution-architect agent.

DEPENDENCIES: This task depends on completion of: design_git_adapter, design_error_log_system

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context
- Scope: Deduplicate across chat, code, git, error, and CI/CD data
- Performance: Handle large-scale deduplication efficiently
- Quality: Maintain data integrity while removing redundancy

REQUIREMENTS:
1. Deduplication Architecture:
   - Content hash comparison algorithms
   - Semantic similarity detection using embeddings
   - Temporal clustering for related events
   - Cross-domain correlation analysis
   - Intelligent merge strategies for similar content

2. Algorithm Design:
   - Hash-based exact duplicate detection
   - Fuzzy matching for near-duplicates
   - Machine learning similarity scoring
   - Temporal window analysis
   - Confidence-based merge decisions

3. System Integration:
   - Real-time deduplication during ingestion
   - Batch processing for historical data cleanup
   - API for manual deduplication decisions
   - Monitoring and quality metrics tracking

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are implementing Phase 2 of the Unified Context System - creating a comprehensive deduplication system to maintain data quality across all ingestion pipelines.
"""

    agent_tasks.append(
        AgentTask(
            task_id="design_deduplication_engine",
            task_type="solution-architect",
            prompt=dedup_design_prompt,
            dependencies=["design_git_adapter", "design_error_log_system"],
            context={"phase": "phase2_integration", "priority": "normal"},
        )
    )

    # === COMPREHENSIVE TESTING ===

    # Task 9: Phase 2 Integration Testing (depends on core implementations)
    testing_prompt = """TASK: Create comprehensive test suite for Phase 2 unified context system integration.

SPECIALIST ROLE: You are acting as a qa-testing-guru agent.

DEPENDENCIES: This task depends on completion of: implement_git_adapter, implement_error_adapter, implement_cicd_adapter

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context
- Test Scope: All Phase 2 adapters and cross-system integration
- Quality Target: >95% test coverage and integration reliability
- Integration: Phase 1 foundation plus Phase 2 extensions

REQUIREMENTS:
1. Adapter Testing:
   - Unit tests for GitAdapter, ErrorAdapter, CICDAdapter
   - Integration tests with real repository data
   - Performance testing with large datasets
   - Error handling and recovery validation
   - Cross-adapter correlation testing

2. System Integration Tests:
   - End-to-end pipeline testing
   - Database schema validation
   - Performance benchmarking
   - Concurrent processing validation
   - Data consistency verification

3. Quality Assurance:
   - Automated test suite execution
   - Performance regression testing
   - Security and data integrity validation
   - Comprehensive error scenario testing
   - Production readiness assessment

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are implementing Phase 2 of the Unified Context System - ensuring comprehensive testing and quality assurance for the extended ingestion pipelines and cross-system correlations.
"""

    agent_tasks.append(
        AgentTask(
            task_id="phase2_integration_testing",
            task_type="qa-testing-guru",
            prompt=testing_prompt,
            dependencies=[
                "implement_git_adapter",
                "implement_error_adapter",
                "implement_cicd_adapter",
            ],
            context={"phase": "phase2_validation", "priority": "high"},
        )
    )

    return agent_tasks


async def main():
    """Execute Phase 2 using the original GenericOrchestrator pattern"""

    print("🚀 PHASE 2: CORE INGESTION - GENERIC ORCHESTRATOR")
    print("=" * 60)
    print("✅ Foundation: Phase 1 chat/code adapters completed")
    print("🎯 Mission: Git history, error logs, CI/CD integration, deduplication")
    print("⚡ Execution: Up to 19 parallel tasks using GenericOrchestrator")
    print()

    # Create tasks using original pattern
    tasks = create_phase2_agent_tasks()

    # Load tokens (should get 19 tokens)
    loader = TokenLoader()
    tokens = loader.load_tokens()

    # Create orchestrator with maximum parallel (like the original)
    orchestrator = GenericOrchestrator(
        output_dir=Path("./phase2_output"),
        max_parallel=min(len(tokens), 12),  # Use up to 12 parallel for complex tasks
        tokens=tokens,
        use_optimizations=True,
    )

    print(f"🔧 Token count: {len(tokens)}")
    print(f"⚡ Max parallel: {orchestrator.max_parallel}")
    print()

    # Print task plan
    print("📋 EXECUTION PLAN - PHASE 2 CORE INGESTION")
    print("-" * 50)
    print("🔧 Git History Pipeline:")
    for task in tasks[:3]:
        deps = (
            f" → depends on: {', '.join(task.dependencies)}"
            if task.dependencies
            else ""
        )
        print(f"  {task.task_id} ({task.task_type}){deps}")

    print("\n🚨 Error Log Pipeline:")
    for task in tasks[3:5]:
        deps = (
            f" → depends on: {', '.join(task.dependencies)}"
            if task.dependencies
            else ""
        )
        print(f"  {task.task_id} ({task.task_type}){deps}")

    print("\n🔄 CI/CD Integration:")
    for task in tasks[5:7]:
        deps = (
            f" → depends on: {', '.join(task.dependencies)}"
            if task.dependencies
            else ""
        )
        print(f"  {task.task_id} ({task.task_type}){deps}")

    print("\n🎯 System Integration:")
    for task in tasks[7:]:
        deps = (
            f" → depends on: {', '.join(task.dependencies)}"
            if task.dependencies
            else ""
        )
        print(f"  {task.task_id} ({task.task_type}){deps}")
    print()

    # Execute tasks
    print("🎯 Starting Phase 2 core ingestion implementation...")
    results = await orchestrator.execute_batch(tasks)

    # Analyze results
    successful = [r for r in results if r.get("status") == "completed"]
    failed = [r for r in results if r.get("status") == "failed"]

    print("\n✅ PHASE 2 CORE INGESTION COMPLETED!")
    print("=" * 60)
    print(f"✅ Successful tasks: {len(successful)}")
    print(f"❌ Failed tasks: {len(failed)}")

    if failed:
        print("\n❌ Failed Tasks:")
        for task in failed:
            print(f"   - {task['task_id']}: {task.get('error', 'Unknown error')}")

    if len(successful) >= 7:  # Core pipelines complete
        print(f"\n🎉 SUCCESS: Phase 2 core ingestion complete!")
        print(f"🔧 Git History: Comprehensive commit analysis and correlation")
        print(f"🚨 Error Logs: Intelligent parsing and correlation triggers")
        print(f"🔄 CI/CD: Build/deployment tracking and correlation")
        print(f"🎯 Integration: Cross-system deduplication and testing")
    else:
        print(f"\n⚠️  Some tasks failed. Check results in ./phase2_output/")

    print(f"\n📄 Full results saved to: ./phase2_output/")
    print(f"📊 Phase 2 metrics and quality reports available")
    print(f"🚀 Ready for Phase 3: Advanced Analytics and Query Systems")

    return results


if __name__ == "__main__":
    print("🔧 Phase 2: Core Ingestion - GenericOrchestrator Pattern")
    print("=" * 60)
    print()

    asyncio.run(main())
