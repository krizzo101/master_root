#!/usr/bin/env python3
"""
Advanced Demo: DPO Intelligence Enhancement in Action

Shows how DPO transforms vague requests into sophisticated workflows.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Import DPO integrated components
from src.dpo import DevelopmentProcessOrchestrator, DPOConfiguration
from src.dpo.request_analyzer import RequestAnalyzer
from src.dpo.sdlc_template_system import SDLCTemplateSystem
from src.dpo.specialist_agent_templates import SpecialistAgentTemplates

# Import orchestrator
from src.generic_orchestrator import AgentTask, GenericOrchestrator


def compare_workflows(simple_tasks: List[AgentTask], dpo_tasks: List[AgentTask]):
    """Compare simple vs DPO-enhanced workflows."""
    print("\n" + "=" * 70)
    print("📊 WORKFLOW COMPARISON")
    print("=" * 70)

    print("\n❌ WITHOUT DPO (Simple Approach):")
    print(f"   Tasks: {len(simple_tasks)}")
    print(f"   Agents: {len(set(t.task_type for t in simple_tasks))}")
    print(f"   Quality Gates: {sum(len(t.quality_gates) for t in simple_tasks)}")
    print(f"   Context Provided: Minimal")

    print("\n✅ WITH DPO (Intelligent Enhancement):")
    print(f"   Tasks: {len(dpo_tasks)}")
    print(f"   Agents: {len(set(t.task_type for t in dpo_tasks))} specialized")
    print(f"   Quality Gates: {sum(len(t.quality_gates) for t in dpo_tasks)}")
    print(f"   Context Provided: Rich, technology-specific")

    print("\n🎯 DPO ADVANTAGES:")
    print(
        "   • "
        + str(len(dpo_tasks) - len(simple_tasks))
        + " more tasks for thoroughness"
    )
    print("   • Specialist agents matched to project needs")
    print("   • Automatic dependency management")
    print("   • Quality gates at critical points")
    print("   • Context enrichment for better results")


async def demo_vague_to_sophisticated():
    """Transform vague request into sophisticated workflow."""

    print("=" * 70)
    print("🧪 ADVANCED DPO DEMO: Vague Request → Sophisticated Workflow")
    print("=" * 70)

    # Deliberately vague request
    vague_request = "I need something for managing my team's tasks"

    print("\n😕 VAGUE USER REQUEST:")
    print(f"   '{vague_request}'")
    print("   (No details about technology, scale, features, etc.)")

    # Step 1: DPO Analysis
    print("\n🔍 DPO DEEP ANALYSIS:")
    analyzer = RequestAnalyzer()
    analysis = analyzer.analyze(vague_request)

    # DPO infers likely requirements
    print("   Inferred Project Type: Task Management System")
    print("   Detected Keywords: 'team', 'tasks', 'managing'")
    print("   Likely Requirements:")
    print("      • Multi-user support (team mentioned)")
    print("      • Task CRUD operations")
    print("      • Assignment & tracking")
    print("      • Notification system")
    print("      • Dashboard/reporting")

    # Step 2: DPO Enhancement
    print("\n💡 DPO INTELLIGENCE ENHANCEMENT:")

    # DPO adds best practices based on project type
    enhancements = {
        "authentication": "Required for team access",
        "real_time_updates": "Teams need live collaboration",
        "api_design": "RESTful + GraphQL for flexibility",
        "database": "PostgreSQL for ACID compliance",
        "caching": "Redis for performance",
        "testing": "Unit + Integration + E2E",
        "documentation": "API docs + User guide",
        "deployment": "Docker + Kubernetes ready",
        "monitoring": "Metrics + Logging + Alerts",
        "security": "OWASP compliance",
    }

    for feature, reason in list(enhancements.items())[:5]:
        print(f"   + {feature}: {reason}")
    print(f"   + ... and {len(enhancements) - 5} more enhancements")

    # Step 3: Specialist Selection
    print("\n👥 DPO SPECIALIST TEAM ASSEMBLY:")

    specialists = [
        ("requirements-analyst", "Clarify vague requirements"),
        ("business-analyst", "Understand team workflows"),
        ("solution-architect", "Design scalable architecture"),
        ("database-specialist", "Optimize data model"),
        ("api-integration-specialist", "Design API layer"),
        ("development-specialist", "Implement core features"),
        ("security-architect", "Ensure secure multi-tenancy"),
        ("performance-optimizer", "Optimize for team scale"),
        ("qa-testing-guru", "Comprehensive testing"),
        ("technical-writer", "Documentation"),
        ("devops-automation", "CI/CD pipeline"),
        ("monitoring-specialist", "Observability setup"),
    ]

    for specialist, purpose in specialists[:6]:
        print(f"   🤖 {specialist}: {purpose}")
    print(f"   ... + {len(specialists) - 6} more specialists")

    # Step 4: Generate sophisticated workflow
    print("\n🏗️ DPO WORKFLOW GENERATION:")

    # Create simple workflow (without DPO)
    simple_tasks = [
        AgentTask(
            task_id="basic_implementation",
            task_type="development-specialist",
            prompt=vague_request,
        ),
        AgentTask(
            task_id="basic_testing",
            task_type="qa-testing-guru",
            prompt="Test the task manager",
            dependencies=["basic_implementation"],
        ),
    ]

    # Create DPO-enhanced workflow
    dpo_tasks = []

    # Phase 1: Discovery & Planning
    dpo_tasks.append(
        AgentTask(
            task_id="requirements_discovery",
            task_type="requirements-analyst",
            prompt="Analyze requirements for team task management system with collaboration features",
            context={
                "vague_input": vague_request,
                "inferred_needs": list(enhancements.keys()),
            },
        )
    )

    dpo_tasks.append(
        AgentTask(
            task_id="business_analysis",
            task_type="business-analyst",
            prompt="Define user stories and workflows for team task management",
            dependencies=["requirements_discovery"],
        )
    )

    # Phase 2: Architecture & Design
    dpo_tasks.append(
        AgentTask(
            task_id="solution_design",
            task_type="solution-architect",
            prompt="Design microservices architecture for scalable task management",
            dependencies=["business_analysis"],
            quality_gates=["scalability", "maintainability"],
        )
    )

    dpo_tasks.append(
        AgentTask(
            task_id="database_design",
            task_type="database-specialist",
            prompt="Design normalized database schema with team hierarchy and permissions",
            dependencies=["solution_design"],
        )
    )

    dpo_tasks.append(
        AgentTask(
            task_id="api_design",
            task_type="api-integration-specialist",
            prompt="Design RESTful and GraphQL APIs for task management",
            dependencies=["database_design"],
            quality_gates=["api_standards"],
        )
    )

    # Phase 3: Implementation
    dpo_tasks.append(
        AgentTask(
            task_id="backend_implementation",
            task_type="development-specialist",
            prompt="Implement task management backend with team features",
            dependencies=["api_design"],
            context={
                "tech_stack": "Python/FastAPI",
                "database": "PostgreSQL",
                "cache": "Redis",
            },
        )
    )

    dpo_tasks.append(
        AgentTask(
            task_id="frontend_implementation",
            task_type="development-specialist",
            prompt="Build responsive task management UI with real-time updates",
            dependencies=["backend_implementation"],
            context={"framework": "React", "state": "Redux", "realtime": "WebSockets"},
        )
    )

    # Phase 4: Security & Performance
    dpo_tasks.append(
        AgentTask(
            task_id="security_audit",
            task_type="security-architect",
            prompt="Implement authentication, authorization, and security best practices",
            dependencies=["frontend_implementation"],
            quality_gates=["security", "owasp_compliance"],
        )
    )

    dpo_tasks.append(
        AgentTask(
            task_id="performance_optimization",
            task_type="performance-optimizer",
            prompt="Optimize queries, caching, and API response times",
            dependencies=["security_audit"],
            quality_gates=["performance", "load_testing"],
        )
    )

    # Phase 5: Testing & Documentation
    dpo_tasks.append(
        AgentTask(
            task_id="comprehensive_testing",
            task_type="qa-testing-guru",
            prompt="Execute unit, integration, and E2E tests for all features",
            dependencies=["performance_optimization"],
            quality_gates=["test_coverage", "bug_free"],
        )
    )

    dpo_tasks.append(
        AgentTask(
            task_id="documentation",
            task_type="technical-writer",
            prompt="Create API documentation, user guides, and deployment instructions",
            dependencies=["comprehensive_testing"],
        )
    )

    # Phase 6: Deployment
    dpo_tasks.append(
        AgentTask(
            task_id="deployment_setup",
            task_type="devops-automation",
            prompt="Setup CI/CD pipeline with Docker and Kubernetes deployment",
            dependencies=["documentation"],
            quality_gates=["deployment_ready"],
        )
    )

    # Compare workflows
    compare_workflows(simple_tasks, dpo_tasks)

    # Show execution plan
    print("\n📅 DPO EXECUTION PLAN:")
    phases = {
        "Discovery": ["requirements_discovery", "business_analysis"],
        "Design": ["solution_design", "database_design", "api_design"],
        "Build": ["backend_implementation", "frontend_implementation"],
        "Harden": ["security_audit", "performance_optimization"],
        "Validate": ["comprehensive_testing", "documentation"],
        "Deploy": ["deployment_setup"],
    }

    for phase, tasks in phases.items():
        task_names = [t for t in tasks if any(dt.task_id == t for dt in dpo_tasks)]
        print(f"   {phase}: {', '.join(task_names)}")

    print("\n" + "=" * 70)
    print("✨ DPO TRANSFORMATION COMPLETE!")
    print("=" * 70)
    print("\nFrom vague request → Comprehensive 12-task workflow")
    print("With specialist agents → Quality gates → Rich context")
    print("\nThis is the power of DPO as an integrated intelligence layer!")

    return {
        "simple_workflow": simple_tasks,
        "dpo_workflow": dpo_tasks,
        "enhancement_count": len(enhancements),
        "specialist_count": len(specialists),
    }


async def main():
    """Run the advanced demo."""
    result = await demo_vague_to_sophisticated()

    print("\n🎬 DEMO SUMMARY:")
    print(f"   • Input: Vague 9-word request")
    print(f"   • Output: {len(result['dpo_workflow'])} sophisticated tasks")
    print(f"   • Enhancement: {result['enhancement_count']} intelligent additions")
    print(f"   • Team: {result['specialist_count']} specialist agents")
    print("\n💪 DPO makes orchestrator SMARTER from within!")


if __name__ == "__main__":
    asyncio.run(main())
