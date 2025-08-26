#!/usr/bin/env python3
"""
Team Orchestration Command
==========================
Manage agent teams for different project types and workflows.

Usage:
    /team-orchestrate create <project_name> --type <type>
    /team-orchestrate execute <project_name> [--phases <phases>]
    /team-orchestrate status <project_name>
    /team-orchestrate list
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Optional

# Add app path
sys.path.insert(0, "/home/opsvi/master_root")

from apps.multi_agent_monitor.src.orchestration import (
    AgentTeamOrchestrator,
    ProjectType,
    WorkflowTemplate,
)


class TeamOrchestrationCommand:
    """CLI for agent team orchestration"""

    def __init__(self):
        self.orchestrator = AgentTeamOrchestrator()
        self.workflows_dir = Path(".claude/workflows")

    async def create_team(self, project_name: str, project_type: str):
        """Create a new agent team"""
        try:
            # Map string to ProjectType enum
            type_map = {
                "web": ProjectType.WEB_APP,
                "web_app": ProjectType.WEB_APP,
                "mobile": ProjectType.MOBILE_APP,
                "cli": ProjectType.CLI_TOOL,
                "microservices": ProjectType.MICROSERVICES,
                "data": ProjectType.DATA_PIPELINE,
                "ml": ProjectType.MACHINE_LEARNING,
                "infra": ProjectType.INFRASTRUCTURE,
                "refactor": ProjectType.REFACTORING,
                "migration": ProjectType.MIGRATION,
                "docs": ProjectType.DOCUMENTATION,
            }

            project_enum = type_map.get(project_type.lower())
            if not project_enum:
                print(f"❌ Unknown project type: {project_type}")
                print(f"Available types: {', '.join(type_map.keys())}")
                return

            team = await self.orchestrator.create_team(
                project_name=project_name, project_type=project_enum
            )

            print(
                f"""
╔══════════════════════════════════════════════════════╗
║         AGENT TEAM CREATED SUCCESSFULLY              ║
╚══════════════════════════════════════════════════════╝

📋 Team Configuration:
  • Project: {team.project_name}
  • Type: {team.project_type.value}
  • Team Size: {len(team.team_members)} agents
  • Workflow Phases: {len(team.workflow_phases)}
  • Token Allocation: Optimized for {min(6, len(team.team_members))} parallel agents

👥 Team Members:
"""
            )
            for i, member in enumerate(team.team_members, 1):
                print(f"  {i}. {member.value}")

            print(
                f"""
📁 Workspace: /tmp/agent_teams/{project_name}

Next Steps:
  1. Execute workflow: /team-orchestrate execute {project_name}
  2. Check status: /team-orchestrate status {project_name}
"""
            )

        except Exception as e:
            print(f"❌ Error creating team: {e}")

    async def execute_workflow(
        self, project_name: str, phases: Optional[List[str]] = None
    ):
        """Execute workflow for a project"""
        try:
            print(
                f"""
╔══════════════════════════════════════════════════════╗
║         EXECUTING AGENT TEAM WORKFLOW                ║
╚══════════════════════════════════════════════════════╝

🚀 Starting workflow for: {project_name}
"""
            )

            # Get requirements from user or use default
            requirements = input(
                "Enter project requirements (or press Enter for default): "
            ).strip()
            if not requirements:
                requirements = f"Build a complete solution for {project_name}"

            # Execute workflow
            results = await self.orchestrator.execute_workflow(
                project_name=project_name,
                requirements=requirements,
                phases_to_run=phases,
            )

            # Display results
            print(
                f"""
✅ Workflow Execution Complete!

📊 Results Summary:
  • Started: {results['started_at']}
  • Completed: {results.get('completed_at', 'In Progress')}
  • Status: {results['status']}
  • Phases Completed: {len(results['phases'])}

📈 Phase Results:
"""
            )
            for phase_name, phase_results in results["phases"].items():
                successful = sum(
                    1 for r in phase_results if r.get("status") == "completed"
                )
                total = len(phase_results)
                print(f"  • {phase_name}: {successful}/{total} tasks completed")

            print(
                f"""
📁 Output Location: /tmp/agent_teams/{project_name}
📄 Full Report: /tmp/agent_teams/{project_name}/workflow_results.json
"""
            )

        except Exception as e:
            print(f"❌ Error executing workflow: {e}")

    def get_status(self, project_name: str):
        """Get status of a project team"""
        try:
            status = self.orchestrator.get_team_status(project_name)

            if "error" in status:
                print(f"❌ {status['error']}")
                return

            print(
                f"""
╔══════════════════════════════════════════════════════╗
║         TEAM STATUS REPORT                          ║
╚══════════════════════════════════════════════════════╝

📋 Project: {project_name}
📊 Status: {status.get('status', 'Unknown')}
"""
            )

            if status["status"] == "completed":
                print(f"  • Started: {status.get('started_at', 'N/A')}")
                print(f"  • Completed: {status.get('completed_at', 'N/A')}")
                print(f"  • Phases: {len(status.get('phases', {}))}")
            elif status["status"] == "configured":
                config = status.get("config", {})
                print(f"  • Type: {config.get('project_type', 'N/A')}")
                print(f"  • Team Size: {len(config.get('team_members', []))}")
                print(f"  • Created: {config.get('created_at', 'N/A')}")
                print("\n  ⚠️ Workflow not yet executed")

        except Exception as e:
            print(f"❌ Error getting status: {e}")

    def list_teams(self):
        """List all agent teams"""
        try:
            workspace = Path("/tmp/agent_teams")
            if not workspace.exists():
                print("No teams created yet.")
                return

            print(
                """
╔══════════════════════════════════════════════════════╗
║         ACTIVE AGENT TEAMS                          ║
╚══════════════════════════════════════════════════════╝
"""
            )

            teams_found = False
            for project_dir in workspace.iterdir():
                if project_dir.is_dir():
                    teams_found = True
                    config_file = project_dir / "team_config.json"
                    if config_file.exists():
                        with open(config_file, "r") as f:
                            config = json.load(f)

                        status = "✅ Configured"
                        results_file = project_dir / "workflow_results.json"
                        if results_file.exists():
                            status = "🚀 Executed"

                        print(
                            f"""
📁 {project_dir.name}
  • Type: {config.get('project_type', 'N/A')}
  • Team Size: {len(config.get('team_members', []))}
  • Status: {status}
  • Created: {config.get('created_at', 'N/A')[:10]}
"""
                        )

            if not teams_found:
                print("No teams found.")

        except Exception as e:
            print(f"❌ Error listing teams: {e}")

    def show_help(self):
        """Show help information"""
        print(
            """
╔══════════════════════════════════════════════════════╗
║         AGENT TEAM ORCHESTRATION HELP               ║
╚══════════════════════════════════════════════════════╝

📚 Available Commands:

1. CREATE A TEAM:
   /team-orchestrate create <project_name> --type <type>

   Types: web, mobile, cli, microservices, data, ml,
          infra, refactor, migration, docs

   Example: /team-orchestrate create my_app --type web

2. EXECUTE WORKFLOW:
   /team-orchestrate execute <project_name> [--phases phase1,phase2]

   Example: /team-orchestrate execute my_app
   Example: /team-orchestrate execute my_app --phases Discovery,Design

3. CHECK STATUS:
   /team-orchestrate status <project_name>

   Example: /team-orchestrate status my_app

4. LIST TEAMS:
   /team-orchestrate list

   Shows all created agent teams

5. HELP:
   /team-orchestrate help

   Shows this help message

📋 Workflow Templates Available:
  • app_development.yaml - Full application development
  • system_design.yaml - System architecture design
  • project_reorganization.yaml - Code refactoring

🎯 Benefits:
  • Parallel execution with 6 tokens
  • Specialized agent roles
  • Structured workflows
  • Automatic coordination
  • Progress tracking
"""
        )


async def main():
    """Main entry point"""
    cmd = TeamOrchestrationCommand()

    if len(sys.argv) < 2:
        cmd.show_help()
        return

    command = sys.argv[1].lower()

    if command == "create":
        if len(sys.argv) < 4:
            print("Usage: /team-orchestrate create <project_name> --type <type>")
            return

        project_name = sys.argv[2]
        project_type = sys.argv[4] if sys.argv[3] == "--type" else "web"
        await cmd.create_team(project_name, project_type)

    elif command == "execute":
        if len(sys.argv) < 3:
            print(
                "Usage: /team-orchestrate execute <project_name> [--phases phase1,phase2]"
            )
            return

        project_name = sys.argv[2]
        phases = None

        if len(sys.argv) > 4 and sys.argv[3] == "--phases":
            phases = sys.argv[4].split(",")

        await cmd.execute_workflow(project_name, phases)

    elif command == "status":
        if len(sys.argv) < 3:
            print("Usage: /team-orchestrate status <project_name>")
            return

        project_name = sys.argv[2]
        cmd.get_status(project_name)

    elif command == "list":
        cmd.list_teams()

    elif command == "help":
        cmd.show_help()

    else:
        print(f"Unknown command: {command}")
        cmd.show_help()


if __name__ == "__main__":
    asyncio.run(main())
