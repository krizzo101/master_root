#!/usr/bin/env python3
"""
Execute Production Validation - Final Testing Before Phase 2
Comprehensive system validation using orchestrator for production readiness
"""
import asyncio
import sys
from pathlib import Path

# Add paths for imports
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator")
sys.path.append("/home/opsvi/master_root/apps/project-context")

from src.generic_orchestrator import AgentTask, GenericOrchestrator
from src.token_loader import TokenLoader


def create_production_validation_tasks():
    """
    Create production validation tasks to verify system readiness
    Focus: End-to-end validation, performance, and production readiness
    """

    agent_tasks = []

    # Task 1: System Integration Validation
    integration_validation_prompt = """TASK: Validate complete system integration and end-to-end functionality

SPECIALIST ROLE: You are acting as a qa-testing-guru agent.

CONTEXT:
- Phase 1 Status: All 5 tasks completed (Chat Adapter, Code Adapter, MCP Integration, Testing, Documentation)
- System Components: All adapters, MCP tools, database, monitoring fully implemented
- Validation Target: End-to-end system functionality and production readiness
- Critical Systems: Database connectivity, MCP server, chat/code adapters, embeddings

REQUIREMENTS:
1. End-to-end integration testing:
   - Test complete data flow: input → processing → storage → retrieval
   - Validate chat adapter: JSONL ingestion, entity extraction, embeddings
   - Validate code adapter: AST parsing, complexity analysis, file watching
   - Validate MCP integration: All 7 ingestion pipeline tools functional
   - Test cross-adapter relationships and data consistency

2. Database and schema validation:
   - PostgreSQL + TimescaleDB + pgvector connectivity
   - Schema integrity and constraint validation
   - Vector embeddings storage and retrieval
   - Performance under realistic data volumes

3. MCP tools comprehensive testing:
   - Test all 21 MCP tools (analysis, architecture, quality, etc.)
   - Validate ingestion pipeline tools integration
   - Test error handling and recovery scenarios
   - Validate tool response accuracy and performance

4. Performance validation:
   - Response time benchmarks for all operations
   - Memory usage under normal and high load
   - Concurrent operation handling
   - Resource cleanup and garbage collection

DELIVERABLES:
- Complete end-to-end integration test results
- Database and schema validation report
- MCP tools functionality verification
- Performance benchmark results
- Production readiness assessment

WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context"""

    agent_tasks.append(
        AgentTask(
            task_id="system_integration_validation",
            task_type="qa-testing-guru",
            prompt=integration_validation_prompt,
            dependencies=[],
            context={"phase": "production_validation", "priority": "critical"},
        )
    )

    # Task 2: Production Deployment Validation
    deployment_validation_prompt = """TASK: Validate production deployment readiness and operational requirements

SPECIALIST ROLE: You are acting as a devops-automation agent.

CONTEXT:
- System Status: Complete Phase 1 implementation with all components tested
- Deployment Target: Production-ready system with operational monitoring
- Infrastructure: Database, MCP server, monitoring, documentation complete
- Requirements: Validate deployment procedures, monitoring, and maintenance

REQUIREMENTS:
1. Deployment readiness validation:
   - Configuration management and environment variables
   - Database setup and migration procedures
   - Service dependencies and startup sequences
   - Port configurations and network connectivity

2. Monitoring and observability:
   - Log aggregation and structured logging
   - Performance metrics collection
   - Error tracking and alerting
   - Health check endpoints and monitoring

3. Operational procedures validation:
   - Backup and recovery procedures
   - Update and maintenance workflows
   - Security configuration and best practices
   - Documentation completeness for operations

4. Performance and scalability assessment:
   - Resource requirements and scaling limits
   - Bottleneck identification and mitigation
   - Load testing results and capacity planning
   - Disaster recovery and failover procedures

DELIVERABLES:
- Production deployment readiness checklist
- Monitoring and observability setup validation
- Operational procedures documentation
- Performance and scalability assessment
- Security and compliance validation

WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context"""

    agent_tasks.append(
        AgentTask(
            task_id="production_deployment_validation",
            task_type="devops-automation",
            prompt=deployment_validation_prompt,
            dependencies=["system_integration_validation"],
            context={"phase": "production_validation", "priority": "high"},
        )
    )

    # Task 3: Security and Compliance Validation
    security_validation_prompt = """TASK: Validate security posture and compliance requirements for production

SPECIALIST ROLE: You are acting as a security-architect agent.

CONTEXT:
- System Status: Complete Phase 1 implementation ready for production
- Security Scope: Database security, API security, data protection, access controls
- Compliance: Data handling, privacy, logging, audit requirements
- Critical Assets: Database, embeddings, chat logs, code analysis data

REQUIREMENTS:
1. Security architecture validation:
   - Database access controls and encryption
   - API authentication and authorization
   - Network security and firewall requirements
   - Data encryption at rest and in transit

2. Data protection and privacy:
   - Sensitive data identification and classification
   - Data retention and deletion policies
   - Access logging and audit trails
   - Privacy compliance (data anonymization, consent)

3. Vulnerability assessment:
   - Code security review for common vulnerabilities
   - Dependency security analysis
   - Configuration security validation
   - Input validation and sanitization

4. Compliance and governance:
   - Logging and audit trail completeness
   - Data handling compliance requirements
   - Access control policy validation
   - Security monitoring and incident response

DELIVERABLES:
- Security architecture validation report
- Data protection and privacy assessment
- Vulnerability assessment and mitigation plan
- Compliance and governance validation
- Security monitoring and incident response procedures

WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context"""

    agent_tasks.append(
        AgentTask(
            task_id="security_compliance_validation",
            task_type="security-architect",
            prompt=security_validation_prompt,
            dependencies=["production_deployment_validation"],
            context={"phase": "production_validation", "priority": "high"},
        )
    )

    # Task 4: Final Production Readiness Assessment
    final_assessment_prompt = """TASK: Generate final production readiness assessment and go/no-go recommendation

SPECIALIST ROLE: You are acting as a solution-architect agent.

CONTEXT:
- Validation Status: System integration, deployment, and security validations complete
- Assessment Target: Overall production readiness and Phase 2 transition approval
- Stakeholders: Development team, operations, management
- Decision: Go/No-Go for Phase 2 transition and production deployment

REQUIREMENTS:
1. Comprehensive readiness assessment:
   - Aggregate all validation results and findings
   - Assess system maturity and reliability
   - Evaluate performance and scalability characteristics
   - Review operational readiness and support capabilities

2. Risk assessment and mitigation:
   - Identify remaining risks and their impact
   - Evaluate mitigation strategies and contingencies
   - Assess rollback and recovery capabilities
   - Review monitoring and alerting coverage

3. Phase 2 transition readiness:
   - Evaluate foundation readiness for Phase 2 requirements
   - Assess scalability for increased workloads
   - Review integration points for future enhancements
   - Validate architecture flexibility for extensions

4. Go/No-Go recommendation:
   - Clear recommendation with supporting rationale
   - Timeline for production deployment
   - Prerequisites and dependencies for Phase 2
   - Success metrics and monitoring requirements

DELIVERABLES:
- Final production readiness assessment report
- Risk assessment and mitigation plan
- Phase 2 transition readiness evaluation
- Go/No-Go recommendation with timeline
- Success metrics and monitoring requirements

WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context"""

    agent_tasks.append(
        AgentTask(
            task_id="final_production_assessment",
            task_type="solution-architect",
            prompt=final_assessment_prompt,
            dependencies=["security_compliance_validation"],
            context={"phase": "production_validation", "priority": "critical"},
        )
    )

    return agent_tasks


async def main():
    """Execute production validation tasks"""

    print("🔍 PRODUCTION VALIDATION - FINAL TESTING PHASE")
    print("=" * 60)
    print("📋 Purpose: Validate system readiness before Phase 2 transition")
    print("🎯 Focus: Integration, Deployment, Security, Final Assessment")
    print()

    # Initialize token loader
    print("🔧 Initializing token loader...")
    token_loader = TokenLoader()
    tokens = token_loader.load_tokens()
    print(f"✅ Loaded {len(tokens)} tokens")
    print()

    # Create orchestrator
    print("🎼 Initializing orchestrator...")
    orchestrator = GenericOrchestrator(
        max_parallel=3,  # Conservative for validation tasks
        output_dir=Path("production_validation_output"),
    )
    print("✅ Orchestrator ready")
    print()

    # Create validation tasks
    print("📝 Creating validation tasks...")
    tasks = create_production_validation_tasks()
    print(f"✅ Created {len(tasks)} validation tasks")
    for task in tasks:
        deps = task.dependencies if task.dependencies else "none"
        print(f"   • {task.task_id} ({task.task_type}) - deps: {deps}")
    print()

    # Execute validation
    print("🚀 Starting production validation...")
    print("📊 Expected timeline:")
    print("   Stage 1: System Integration Validation (15-20 minutes)")
    print("   Stage 2: Deployment Validation (10-15 minutes)")
    print("   Stage 3: Security Validation (10-15 minutes)")
    print("   Stage 4: Final Assessment (10-15 minutes)")
    print("   Total: ~45-65 minutes")
    print()

    try:
        results = await orchestrator.execute_batch(tasks)

        print("\n" + "=" * 60)
        print("✅ PRODUCTION VALIDATION - RESULTS")
        print("=" * 60)

        # Count successes and failures
        successful = 0
        failed = 0

        for result in results:
            if hasattr(result, "success") and result.success:
                successful += 1
                print(f"✅ {result.task_id}: SUCCESS")
            elif hasattr(result, "is_error") and not result.get("is_error", True):
                successful += 1
                print(f"✅ {result.task_id}: SUCCESS")
            else:
                failed += 1
                print(f"❌ {result.task_id}: FAILED")

        print()
        print(f"📊 Final Results: {successful} successful, {failed} failed")

        if failed == 0:
            print("🎉 ALL VALIDATION TESTS PASSED!")
            print("✅ System is READY for Phase 2 transition")
        else:
            print("⚠️  Some validation tests failed - review required")

        print()
        print("📁 Detailed results saved to: production_validation_output/")

    except Exception as e:
        print(f"❌ Validation execution failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    asyncio.run(main())
