#!/usr/bin/env python3
"""
Agent Team Orchestrator
=======================
Comprehensive framework for organizing and tasking agent teams for different use cases:
- App Development
- System Design
- Project Reorganization
- Related Team Efforts

This orchestrator leverages existing SDLC agents and commands to create structured workflows.
"""

import asyncio
import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml


class ProjectType(Enum):
    """Types of projects the orchestrator can handle"""

    WEB_APP = "web_app"
    MOBILE_APP = "mobile_app"
    CLI_TOOL = "cli_tool"
    MICROSERVICES = "microservices"
    DATA_PIPELINE = "data_pipeline"
    MACHINE_LEARNING = "machine_learning"
    INFRASTRUCTURE = "infrastructure"
    REFACTORING = "refactoring"
    MIGRATION = "migration"
    DOCUMENTATION = "documentation"


class TeamRole(Enum):
    """Specialized roles that agents can take"""

    # Core Development Roles
    ARCHITECT = "solution-architect"
    BACKEND_DEV = "development-specialist"
    FRONTEND_DEV = "development-specialist"
    DATABASE_ENG = "database-specialist"
    DEVOPS = "devops-automation"

    # Quality & Testing
    QA_ENGINEER = "qa-testing-guru"
    SECURITY = "security-architect"
    PERFORMANCE = "performance-optimizer"

    # Analysis & Planning
    REQUIREMENTS = "requirements-analyst"
    BUSINESS = "business-analyst"
    RESEARCHER = "research-genius"

    # Specialized
    API_SPECIALIST = "api-integration-specialist"
    REFACTOR_EXPERT = "refactoring-master"
    CODE_REVIEWER = "reviewer-critic"
    TECH_WRITER = "technical-writer"

    # Leadership
    PROJECT_MANAGER = "ceo-team-manager"
    EXCELLENCE = "excellence-optimizer"


@dataclass
class AgentTask:
    """Represents a single task for an agent"""

    task_id: str
    agent_role: TeamRole
    description: str
    dependencies: List[str] = field(default_factory=list)
    required_outputs: List[str] = field(default_factory=list)
    timeout: int = 600
    priority: int = 1
    status: str = "pending"
    result: Optional[Dict] = None


@dataclass
class TeamConfiguration:
    """Configuration for an agent team"""

    project_name: str
    project_type: ProjectType
    team_members: List[TeamRole]
    workflow_phases: List[str]
    token_allocation: Dict[TeamRole, int]  # Maps roles to token numbers (1-6)
    parallel_groups: List[List[str]]  # Groups of tasks that can run in parallel


class WorkflowTemplate:
    """Pre-defined workflow templates for different project types"""

    @staticmethod
    def get_web_app_workflow() -> Dict[str, Any]:
        """Full-stack web application workflow"""
        return {
            "phases": [
                {
                    "name": "Discovery & Requirements",
                    "agents": [
                        {
                            "role": TeamRole.REQUIREMENTS,
                            "task": "Gather and document functional requirements",
                        },
                        {
                            "role": TeamRole.RESEARCHER,
                            "task": "Research technology stack and frameworks",
                        },
                        {
                            "role": TeamRole.BUSINESS,
                            "task": "Define business logic and user flows",
                        },
                    ],
                    "parallel": True,
                },
                {
                    "name": "Architecture & Design",
                    "agents": [
                        {
                            "role": TeamRole.ARCHITECT,
                            "task": "Design system architecture and components",
                        },
                        {
                            "role": TeamRole.DATABASE_ENG,
                            "task": "Design database schema and relationships",
                        },
                        {
                            "role": TeamRole.API_SPECIALIST,
                            "task": "Design API contracts and integrations",
                        },
                    ],
                    "parallel": True,
                },
                {
                    "name": "Implementation",
                    "agents": [
                        {
                            "role": TeamRole.BACKEND_DEV,
                            "task": "Implement backend services and APIs",
                        },
                        {
                            "role": TeamRole.FRONTEND_DEV,
                            "task": "Build frontend components and UI",
                        },
                        {
                            "role": TeamRole.DATABASE_ENG,
                            "task": "Implement database layer and migrations",
                        },
                    ],
                    "parallel": True,
                },
                {
                    "name": "Quality & Security",
                    "agents": [
                        {
                            "role": TeamRole.QA_ENGINEER,
                            "task": "Create and run test suites",
                        },
                        {
                            "role": TeamRole.SECURITY,
                            "task": "Security audit and hardening",
                        },
                        {
                            "role": TeamRole.PERFORMANCE,
                            "task": "Performance optimization",
                        },
                    ],
                    "parallel": True,
                },
                {
                    "name": "Deployment",
                    "agents": [
                        {
                            "role": TeamRole.DEVOPS,
                            "task": "Create CI/CD pipeline and deployment",
                        },
                        {
                            "role": TeamRole.TECH_WRITER,
                            "task": "Generate documentation",
                        },
                    ],
                    "parallel": True,
                },
            ]
        }

    @staticmethod
    def get_microservices_workflow() -> Dict[str, Any]:
        """Microservices architecture workflow"""
        return {
            "phases": [
                {
                    "name": "Domain Analysis",
                    "agents": [
                        {
                            "role": TeamRole.ARCHITECT,
                            "task": "Define bounded contexts and service boundaries",
                        },
                        {
                            "role": TeamRole.REQUIREMENTS,
                            "task": "Map functional requirements to services",
                        },
                    ],
                    "parallel": True,
                },
                {
                    "name": "Service Design",
                    "agents": [
                        {
                            "role": TeamRole.API_SPECIALIST,
                            "task": "Design inter-service communication",
                        },
                        {
                            "role": TeamRole.DATABASE_ENG,
                            "task": "Design data partitioning strategy",
                        },
                        {
                            "role": TeamRole.SECURITY,
                            "task": "Design service mesh and security",
                        },
                    ],
                    "parallel": True,
                },
                {
                    "name": "Service Implementation",
                    "agents": [
                        {
                            "role": TeamRole.BACKEND_DEV,
                            "task": "Implement core services",
                            "instances": 3,
                        },
                        {
                            "role": TeamRole.API_SPECIALIST,
                            "task": "Implement API gateway",
                        },
                    ],
                    "parallel": True,
                },
                {
                    "name": "Orchestration",
                    "agents": [
                        {
                            "role": TeamRole.DEVOPS,
                            "task": "Kubernetes deployment and service mesh",
                        },
                        {
                            "role": TeamRole.PERFORMANCE,
                            "task": "Load balancing and scaling",
                        },
                    ],
                    "parallel": True,
                },
            ]
        }

    @staticmethod
    def get_refactoring_workflow() -> Dict[str, Any]:
        """Code refactoring and modernization workflow"""
        return {
            "phases": [
                {
                    "name": "Analysis",
                    "agents": [
                        {
                            "role": TeamRole.CODE_REVIEWER,
                            "task": "Analyze existing codebase",
                        },
                        {
                            "role": TeamRole.PERFORMANCE,
                            "task": "Identify performance bottlenecks",
                        },
                        {
                            "role": TeamRole.SECURITY,
                            "task": "Security vulnerability assessment",
                        },
                    ],
                    "parallel": True,
                },
                {
                    "name": "Planning",
                    "agents": [
                        {
                            "role": TeamRole.REFACTOR_EXPERT,
                            "task": "Create refactoring plan",
                        },
                        {
                            "role": TeamRole.ARCHITECT,
                            "task": "Design target architecture",
                        },
                    ],
                    "parallel": False,
                },
                {
                    "name": "Execution",
                    "agents": [
                        {
                            "role": TeamRole.REFACTOR_EXPERT,
                            "task": "Execute refactoring",
                            "instances": 2,
                        },
                        {"role": TeamRole.QA_ENGINEER, "task": "Regression testing"},
                    ],
                    "parallel": True,
                },
            ]
        }


class AgentTeamOrchestrator:
    """Main orchestrator for managing agent teams"""

    def __init__(self, workspace: Path = Path("/tmp/agent_teams")):
        self.workspace = workspace
        self.workspace.mkdir(exist_ok=True)
        self.sessions_dir = self.workspace / ".sessions"
        self.sessions_dir.mkdir(exist_ok=True)

        # Load existing agent configurations
        self.agent_configs = self._load_agent_configs()

        # Token pool management (6 tokens available)
        self.available_tokens = set(range(1, 7))
        self.token_assignments = {}

        # Active teams and tasks
        self.active_teams = {}
        self.task_queue = asyncio.Queue()

    def _load_agent_configs(self) -> Dict[str, Dict]:
        """Load agent configurations from .claude/agents/"""
        configs = {}
        agents_dir = Path(".claude/agents")

        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.md"):
                agent_name = agent_file.stem
                configs[agent_name] = {"path": str(agent_file), "name": agent_name}

        return configs

    async def create_team(
        self,
        project_name: str,
        project_type: ProjectType,
        custom_config: Optional[Dict] = None,
    ) -> TeamConfiguration:
        """Create a new agent team for a project"""

        # Get workflow template
        if project_type == ProjectType.WEB_APP:
            workflow = WorkflowTemplate.get_web_app_workflow()
        elif project_type == ProjectType.MICROSERVICES:
            workflow = WorkflowTemplate.get_microservices_workflow()
        elif project_type == ProjectType.REFACTORING:
            workflow = WorkflowTemplate.get_refactoring_workflow()
        else:
            workflow = custom_config or WorkflowTemplate.get_web_app_workflow()

        # Extract team members from workflow
        team_members = []
        for phase in workflow["phases"]:
            for agent in phase["agents"]:
                role = agent["role"]
                instances = agent.get("instances", 1)
                for _ in range(instances):
                    team_members.append(role)

        # Allocate tokens to team members
        token_allocation = {}
        for i, member in enumerate(team_members[:6]):  # Max 6 parallel
            token_allocation[member] = (i % 6) + 1

        # Define parallel groups
        parallel_groups = []
        for phase in workflow["phases"]:
            if phase.get("parallel", True):
                group = [f"{phase['name']}_{i}" for i in range(len(phase["agents"]))]
                parallel_groups.append(group)

        team_config = TeamConfiguration(
            project_name=project_name,
            project_type=project_type,
            team_members=team_members,
            workflow_phases=[p["name"] for p in workflow["phases"]],
            token_allocation=token_allocation,
            parallel_groups=parallel_groups,
        )

        self.active_teams[project_name] = team_config

        # Create project workspace
        project_dir = self.workspace / project_name
        project_dir.mkdir(exist_ok=True)

        # Save team configuration
        config_file = project_dir / "team_config.json"
        with open(config_file, "w") as f:
            json.dump(
                {
                    "project_name": project_name,
                    "project_type": project_type.value,
                    "team_members": [m.value for m in team_members],
                    "workflow_phases": team_config.workflow_phases,
                    "created_at": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

        print(f"✅ Created team for {project_name} with {len(team_members)} agents")

        return team_config

    async def execute_workflow(
        self,
        project_name: str,
        requirements: str,
        phases_to_run: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute the full workflow for a project"""

        if project_name not in self.active_teams:
            raise ValueError(f"No team found for project {project_name}")

        team_config = self.active_teams[project_name]
        project_dir = self.workspace / project_name

        results = {
            "project": project_name,
            "started_at": datetime.now().isoformat(),
            "phases": {},
            "status": "running",
        }

        # Get workflow based on project type
        if team_config.project_type == ProjectType.WEB_APP:
            workflow = WorkflowTemplate.get_web_app_workflow()
        elif team_config.project_type == ProjectType.MICROSERVICES:
            workflow = WorkflowTemplate.get_microservices_workflow()
        else:
            workflow = WorkflowTemplate.get_refactoring_workflow()

        # Execute each phase
        for phase in workflow["phases"]:
            phase_name = phase["name"]

            if phases_to_run and phase_name not in phases_to_run:
                continue

            print(f"\n🚀 Executing Phase: {phase_name}")

            # Create tasks for this phase
            phase_tasks = []
            for agent_config in phase["agents"]:
                role = agent_config["role"]
                task_desc = agent_config["task"]
                instances = agent_config.get("instances", 1)

                for i in range(instances):
                    task = AgentTask(
                        task_id=f"{phase_name}_{role.value}_{i}",
                        agent_role=role,
                        description=f"{task_desc} (Instance {i+1})"
                        if instances > 1
                        else task_desc,
                        timeout=agent_config.get("timeout", 600),
                    )
                    phase_tasks.append(task)

            # Execute tasks in parallel or sequence
            if phase.get("parallel", True):
                phase_results = await self._execute_parallel_tasks(
                    phase_tasks, project_dir
                )
            else:
                phase_results = await self._execute_sequential_tasks(
                    phase_tasks, project_dir
                )

            results["phases"][phase_name] = phase_results

        results["completed_at"] = datetime.now().isoformat()
        results["status"] = "completed"

        # Save results
        results_file = project_dir / "workflow_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)

        return results

    async def _execute_parallel_tasks(
        self, tasks: List[AgentTask], project_dir: Path
    ) -> List[Dict]:
        """Execute tasks in parallel using available tokens"""

        async def run_agent_task(task: AgentTask, token_num: int) -> Dict:
            """Run a single agent task"""
            agent_dir = project_dir / task.agent_role.value
            agent_dir.mkdir(exist_ok=True)

            # Build command based on agent role
            if task.agent_role.value in self.agent_configs:
                agent_config_path = self.agent_configs[task.agent_role.value]["path"]
            else:
                agent_config_path = ".claude/agents/AGENT_TEMPLATE.md"

            # Prepare environment with specific token
            env = os.environ.copy()
            if "ANTHROPIC_API_KEY" in env:
                del env["ANTHROPIC_API_KEY"]

            # Use the assigned token
            token_key = f"CLAUDE_CODE_TOKEN{token_num}"
            if token_key in os.environ:
                env["CLAUDE_CODE_TOKEN"] = os.environ[token_key]
            elif "CLAUDE_CODE_TOKEN" in os.environ:
                env["CLAUDE_CODE_TOKEN"] = os.environ["CLAUDE_CODE_TOKEN"]

            # Build the task prompt
            prompt = f"""
            Role: {task.agent_role.value}
            Task: {task.description}

            Project Directory: {agent_dir}

            Please execute this task following the agent configuration from {agent_config_path}.
            Create all necessary files in the project directory.
            """

            # Execute with Claude
            cmd = [
                "claude",
                "--print",
                "--output-format",
                "text",
                "--dangerously-skip-permissions",
                prompt,
            ]

            start_time = datetime.now()

            try:
                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(agent_dir),
                )

                stdout, stderr = await asyncio.wait_for(
                    result.communicate(), timeout=task.timeout
                )

                task.status = "completed"
                task.result = {
                    "output": stdout.decode() if stdout else "",
                    "duration": (datetime.now() - start_time).total_seconds(),
                    "token_used": token_num,
                }

            except Exception as e:
                task.status = "failed"
                task.result = {"error": str(e)}

            return {
                "task_id": task.task_id,
                "status": task.status,
                "result": task.result,
            }

        # Execute all tasks in parallel with token management
        parallel_tasks = []
        for i, task in enumerate(tasks[:6]):  # Max 6 parallel
            token_num = (i % 6) + 1
            parallel_tasks.append(run_agent_task(task, token_num))

        results = await asyncio.gather(*parallel_tasks, return_exceptions=True)

        # Handle remaining tasks if more than 6
        if len(tasks) > 6:
            for i, task in enumerate(tasks[6:]):
                token_num = (i % 6) + 1
                result = await run_agent_task(task, token_num)
                results.append(result)

        return results

    async def _execute_sequential_tasks(
        self, tasks: List[AgentTask], project_dir: Path
    ) -> List[Dict]:
        """Execute tasks sequentially"""
        results = []

        for i, task in enumerate(tasks):
            token_num = (i % 6) + 1
            result = await self._execute_parallel_tasks([task], project_dir)
            results.extend(result)

        return results

    def get_team_status(self, project_name: str) -> Dict:
        """Get current status of a team"""
        if project_name not in self.active_teams:
            return {"error": "Team not found"}

        project_dir = self.workspace / project_name

        # Check for results file
        results_file = project_dir / "workflow_results.json"
        if results_file.exists():
            with open(results_file, "r") as f:
                return json.load(f)

        # Check for config file
        config_file = project_dir / "team_config.json"
        if config_file.exists():
            with open(config_file, "r") as f:
                config = json.load(f)
                return {"status": "configured", "config": config}

        return {"status": "unknown"}

    def list_available_agents(self) -> List[str]:
        """List all available agent types"""
        return list(self.agent_configs.keys())

    def get_workflow_templates(self) -> Dict[str, List[str]]:
        """Get all available workflow templates"""
        return {
            ProjectType.WEB_APP.value: [
                "Discovery",
                "Design",
                "Implementation",
                "Quality",
                "Deployment",
            ],
            ProjectType.MICROSERVICES.value: [
                "Domain Analysis",
                "Service Design",
                "Implementation",
                "Orchestration",
            ],
            ProjectType.REFACTORING.value: ["Analysis", "Planning", "Execution"],
        }


# CLI Interface for testing
async def main():
    """Example usage of the Agent Team Orchestrator"""

    orchestrator = AgentTeamOrchestrator()

    # Example: Create a web app team
    team = await orchestrator.create_team(
        project_name="ecommerce_platform", project_type=ProjectType.WEB_APP
    )

    print(f"\n📋 Team Configuration:")
    print(f"  - Project: {team.project_name}")
    print(f"  - Type: {team.project_type.value}")
    print(f"  - Team Size: {len(team.team_members)}")
    print(f"  - Phases: {', '.join(team.workflow_phases)}")

    # Execute workflow
    print("\n🔄 Executing Workflow...")
    results = await orchestrator.execute_workflow(
        project_name="ecommerce_platform",
        requirements="Build a full-stack e-commerce platform with user auth, product catalog, and payment processing",
    )

    print(f"\n✅ Workflow Complete!")
    print(f"  - Duration: {results.get('completed_at', 'N/A')}")
    print(f"  - Phases Completed: {len(results['phases'])}")


if __name__ == "__main__":
    asyncio.run(main())
