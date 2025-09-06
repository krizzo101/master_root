#!/usr/bin/env python3
"""
Launch Real-Time Multi-Agent Collaboration System Development
15 specialized agents building collaborative agent capabilities
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from collaboration_system_tasks import COLLABORATION_TASKS

from src.generic_orchestrator import AgentTask, GenericOrchestrator


async def run_collaboration_development(max_parallel: int = 8, output_dir: str = None):
    """Launch 15-agent collaboration system development session"""

    print("🚀 REAL-TIME MULTI-AGENT COLLABORATION SYSTEM DEVELOPMENT")
    print("=" * 70)
    print(f"📋 15 Specialized Agents | Max Parallel: {max_parallel}")
    print(f"🎯 Mission: Build collaborative agent capabilities")
    print()

    # Setup output directory
    if not output_dir:
        output_dir = f"collaboration_dev_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    orchestrator_output = Path(output_dir)

    print(f"📁 Output Directory: {orchestrator_output}")
    print()

    # Setup orchestrator with higher parallelism for development work
    orchestrator = GenericOrchestrator(
        output_dir=orchestrator_output, max_parallel=max_parallel
    )

    # Convert to AgentTask objects
    agent_tasks = []
    for task_data in COLLABORATION_TASKS:
        agent_task = AgentTask(
            task_id=task_data["task_id"],
            task_type=task_data["task_type"],
            prompt=task_data["prompt"],
            context={
                "team": task_data["team"],
                "role": task_data["role"],
                "dependencies": task_data["dependencies"],
                "expected_outputs": task_data["expected_outputs"],
            },
        )
        agent_tasks.append(agent_task)

    # Display team organization
    teams = {}
    for task in agent_tasks:
        team_name = task.context["team"]
        if team_name not in teams:
            teams[team_name] = []
        teams[team_name].append(task.context["role"])

    print("👥 TEAM ORGANIZATION:")
    for team_name, roles in teams.items():
        print(f"  🏢 {team_name} ({len(roles)} agents):")
        for role in roles:
            print(f"    • {role}")
    print()

    # Define result processor for collaboration development
    async def process_development_results(tasks, results):
        """Process results from collaboration development agents"""
        print("\n" + "=" * 70)
        print("🎉 COLLABORATION SYSTEM DEVELOPMENT RESULTS")
        print("=" * 70)

        # Organize results by team
        team_results = {}
        for task, result in zip(tasks, results):
            team_name = task.context["team"]
            if team_name not in team_results:
                team_results[team_name] = []
            team_results[team_name].append(
                {
                    "role": task.context["role"],
                    "status": "✅ Success" if result.get("success") else "❌ Failed",
                    "summary": result.get("summary", "No summary available"),
                    "outputs": task.context.get("expected_outputs", []),
                    "result": result,
                }
            )

        # Display results by team
        total_success = 0
        total_components = 0

        for team_name, team_tasks in team_results.items():
            print(f"\n🏢 {team_name.upper()} TEAM:")
            print("-" * 50)

            for task_result in team_tasks:
                print(f"  {task_result['status']} {task_result['role']}")
                if task_result["result"].get("success"):
                    total_success += 1
                    print(f"    📝 {task_result['summary'][:100]}...")
                    print(f"    📋 Outputs: {', '.join(task_result['outputs'])}")
                else:
                    print(
                        f"    ⚠️  Error: {task_result['result'].get('error', 'Unknown error')}"
                    )
                total_components += 1
                print()

        print("=" * 70)
        print("📊 DEVELOPMENT SESSION SUMMARY:")
        print(f"  ✅ Successful Components: {total_success}/{total_components}")
        print(f"  🏢 Teams Involved: {len(team_results)}")
        print(f"  🎯 Completion Rate: {(total_success/total_components)*100:.1f}%")

        if total_success >= 12:  # 80% success rate
            print(f"  🎉 COLLABORATION SYSTEM DEVELOPMENT: MAJOR SUCCESS!")
        elif total_success >= 9:  # 60% success rate
            print(f"  ✅ COLLABORATION SYSTEM DEVELOPMENT: GOOD PROGRESS")
        else:
            print(f"  ⚠️  COLLABORATION SYSTEM DEVELOPMENT: NEEDS MORE WORK")

        print()
        print("🚀 NEXT STEPS:")
        if total_success >= 12:
            print("  • Integration testing and system validation")
            print("  • Performance optimization and tuning")
            print("  • Create demonstration scenarios")
            print("  • Deploy for real-world testing")
        else:
            print("  • Review failed components and address issues")
            print("  • Re-run failed tasks with refined requirements")
            print("  • Focus on critical path components first")

        return {
            "team_results": team_results,
            "total_success": total_success,
            "total_components": total_components,
            "completion_rate": (total_success / total_components) * 100,
        }

    # Create task generator
    def task_generator():
        return agent_tasks

    print("🚀 LAUNCHING 15-AGENT COLLABORATION DEVELOPMENT SESSION")
    print(f"📋 Debug logs: {orchestrator.log_file}")
    print("=" * 70)
    print()

    try:
        results = await orchestrator.run(
            task_generator=task_generator, result_processor=process_development_results
        )

        print("\n" + "=" * 70)
        print("🎉 COLLABORATION SYSTEM DEVELOPMENT SESSION COMPLETE!")
        print("=" * 70)
        print(f"📁 Results: {orchestrator_output}")
        print(f"📋 Logs: {orchestrator.log_file}")
        print(f"🎯 Mission: Real-Time Multi-Agent Collaboration System")

        # Store results summary
        summary_file = orchestrator_output / "development_summary.json"
        import json

        with open(summary_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"📊 Summary: {summary_file}")

        return results

    except Exception as e:
        print(f"\n❌ Development session failed: {e}")
        print(f"📋 Check debug logs: {orchestrator.log_file}")
        raise


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Launch collaboration system development"
    )
    parser.add_argument(
        "--parallel", type=int, default=8, help="Max parallel agents (default: 8)"
    )
    parser.add_argument("--output", type=str, help="Output directory")

    args = parser.parse_args()

    print("🎯 REAL-TIME MULTI-AGENT COLLABORATION SYSTEM")
    print("Building the future of agent collaboration...")
    print()

    # Run the development session
    asyncio.run(
        run_collaboration_development(
            max_parallel=args.parallel, output_dir=args.output
        )
    )


if __name__ == "__main__":
    main()
