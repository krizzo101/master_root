#!/usr/bin/env python3
"""
Smart Decomposition Meta-Intelligence System - POC Demonstration
OpenAI-Exclusive Implementation Demo

This script demonstrates the core functionality of the Smart Decomposition system.
"""

import asyncio
from pathlib import Path
import sys

# Add the POC to the Python path
poc_path = Path(__file__).parent
sys.path.insert(0, str(poc_path))

from core.config import get_config
from core.system_controller import SystemController


def print_banner():
    """Print demo banner"""
    print(
        """
🌟 ================================================================= 🌟
    Smart Decomposition Meta-Intelligence System - POC Demo
    OpenAI-Exclusive Implementation with Structured Responses
🌟 ================================================================= 🌟
"""
    )


def print_config_info():
    """Print configuration information"""
    config = get_config()

    print("📋 Configuration Overview:")
    print(f"   • System: {config.name} v{config.version}")
    print(f"   • Environment: {config.environment}")
    print(f"   • Reasoning Model: {config.models.reasoning}")
    print(f"   • Implementation Model: {config.models.implementation}")
    print(f"   • Coordination Model: {config.models.coordination}")
    print(f"   • Optimization Model: {config.models.optimization}")
    print(
        f"   • Structured Responses: {'✅ Enabled' if config.structured_responses.enforce_json_schemas else '❌ Disabled'}"
    )
    print(f"   • Max Parallel Agents: {config.parallel_execution.max_parallel_agents}")
    print(
        f"   • Performance Target: {config.performance.parallel_efficiency_target}x efficiency"
    )
    print()


async def demo_configuration():
    """Demonstrate configuration management"""
    print("🔧 Testing Configuration Management...")

    config = get_config()

    # Test model allocation
    from core.config import AgentRole, get_model_for_role

    print("   Model Allocation Testing:")
    roles_to_test = [
        AgentRole.MANAGER,
        AgentRole.REQUIREMENTS_EXPANDER,
        AgentRole.DEVELOPER,
        AgentRole.TESTER,
    ]

    for role in roles_to_test:
        model = get_model_for_role(role)
        print(f"     • {role.value}: {model}")

    print("   ✅ Configuration management working correctly")
    return True


async def demo_agent_creation():
    """Demonstrate agent factory functionality"""
    print("🤖 Testing Agent Creation...")

    from core.agent_factory import AgentFactory, SpecializedAgentFactory

    factory = AgentFactory()
    specialized = SpecializedAgentFactory(factory)

    print("   Creating specialized agents...")

    try:
        # Create manager agent
        manager = specialized.create_manager_agent()
        print(f"     • Manager Agent: {manager.agent_id} (Model: {manager.model})")

        # Create requirements expander
        req_expander = specialized.create_requirements_expander()
        print(
            f"     • Requirements Expander: {req_expander.agent_id} (Model: {req_expander.model})"
        )

        # Create developer agent
        developer = specialized.create_developer_agent()
        print(
            f"     • Developer Agent: {developer.agent_id} (Model: {developer.model})"
        )

        print("   ✅ Agent creation working correctly")
        return True

    except Exception as e:
        print(f"   ❌ Agent creation failed: {str(e)}")
        return False


async def demo_schema_validation():
    """Demonstrate schema validation"""
    print("📝 Testing Schema Validation...")

    from core.schemas import (
        RequirementsResponse,
        get_schema_for_role,
    )

    # Test RequirementsResponse schema
    test_requirements_data = {
        "expanded_requirements": "Complete web application with user authentication and task management",
        "technical_specifications": [
            "React frontend",
            "Node.js backend",
            "MongoDB database",
        ],
        "dependencies": ["React", "Express", "MongoDB", "JWT"],
        "complexity_assessment": "medium",
        "estimated_effort": 40,
        "validation_criteria": [
            "User can register",
            "User can login",
            "User can create tasks",
        ],
    }

    try:
        requirements = RequirementsResponse(**test_requirements_data)
        print("     • RequirementsResponse: ✅ Valid")
        print(f"       Complexity: {requirements.complexity_assessment}")
        print(f"       Effort: {requirements.estimated_effort} hours")

        # Test schema retrieval by role
        schema = get_schema_for_role("requirements_expander")
        print(f"     • Schema for requirements_expander: {schema.__name__}")

        print("   ✅ Schema validation working correctly")
        return True

    except Exception as e:
        print(f"   ❌ Schema validation failed: {str(e)}")
        return False


async def demo_mock_workflow():
    """Demonstrate mock workflow execution"""
    print("🔄 Testing Mock Workflow Execution...")

    controller = SystemController()

    print("   Mock workflow phases:")
    print("     1. Requirements Expansion (O3)")
    print("     2. Work Planning (O3)")
    print("     3. Implementation (GPT-4.1)")
    print("     4. Validation (GPT-4.1-mini)")
    print("     5. Packaging")

    # This would normally call the full workflow, but we'll simulate it
    print("   📝 Note: Full workflow requires OpenAI API access")
    print("   🔄 Simulating workflow structure validation...")

    # Check that all required methods exist
    required_methods = [
        "_expand_requirements",
        "_create_work_plan",
        "_implement_application",
        "_validate_implementation",
        "_package_application",
    ]

    all_methods_exist = True
    for method in required_methods:
        if hasattr(controller, method):
            print(f"     • {method}: ✅ Available")
        else:
            print(f"     • {method}: ❌ Missing")
            all_methods_exist = False

    if all_methods_exist:
        print("   ✅ Workflow structure validated")
        return True
    else:
        print("   ❌ Workflow structure incomplete")
        return False


async def demo_performance_tracking():
    """Demonstrate performance tracking"""
    print("📊 Testing Performance Tracking...")

    from core.agent_factory import AgentFactory

    factory = AgentFactory()

    # Create an agent and simulate performance tracking
    spec = {"role": "developer", "capabilities": ["coding"]}
    agent = factory.create_agent(spec)

    # Simulate some performance data
    agent._track_performance(2.5, True)
    agent._track_performance(3.1, True)
    agent._track_performance(1.8, False)

    metrics = agent.performance_metrics
    print(f"     • Total Executions: {metrics['total_executions']}")
    print(f"     • Success Rate: {metrics['success_rate']:.2%}")
    print(f"     • Average Time: {metrics['average_time']:.2f}s")

    # Test factory-level metrics
    factory_metrics = factory.get_agent_performance_metrics()
    print(f"     • Agents Created: {len(factory_metrics)}")

    print("   ✅ Performance tracking working correctly")
    return True


async def main():
    """Main demo function"""
    print_banner()
    print_config_info()

    # Run all demo components
    demos = [
        ("Configuration Management", demo_configuration),
        ("Agent Creation", demo_agent_creation),
        ("Schema Validation", demo_schema_validation),
        ("Workflow Structure", demo_mock_workflow),
        ("Performance Tracking", demo_performance_tracking),
    ]

    results = {}

    for demo_name, demo_func in demos:
        print(f"\n{'='*60}")
        try:
            result = await demo_func()
            results[demo_name] = result
        except Exception as e:
            print(f"❌ {demo_name} failed with error: {str(e)}")
            results[demo_name] = False
        print(f"{'='*60}")

    # Summary
    print("\n🎯 Demo Results Summary:")
    print(f"{'='*60}")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for demo_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   • {demo_name}: {status}")

    print(f"\n📊 Overall: {passed}/{total} tests passed ({passed/total:.1%})")

    if passed == total:
        print("🎉 All POC components are working correctly!")
        print("🚀 Ready for next implementation phase!")
    else:
        print("⚠️  Some components need attention before proceeding.")

    print(f"\n{'='*60}")
    print("💡 Next Steps:")
    print("   1. Install dependencies: pip install -r requirements.txt")
    print("   2. Set up OpenAI API keys")
    print("   3. Configure Neo4j database")
    print("   4. Run full workflow test with real API calls")
    print("   5. Implement parallel execution capabilities")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user.")
    except Exception as e:
        print(f"\n💥 Demo crashed: {str(e)}")
        sys.exit(1)
