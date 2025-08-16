"""
Planner agent for the Auto-Forge factory.
"""

import json
import logging
from typing import Any, Dict, List

from .base_agent import BaseAgent, AgentResult
from ...models.schemas import AgentType, AgentConfig


class PlannerAgent(BaseAgent):
    """Agent responsible for creating high-level development plans."""

    def _init_agent(self, **kwargs):
        """Initialize planner-specific attributes."""
        self.planning_strategies = {
            "agile": self._create_agile_plan,
            "waterfall": self._create_waterfall_plan,
            "iterative": self._create_iterative_plan,
        }

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """Execute the planning phase.

        Args:
            inputs: Input data containing project requirements and constraints

        Returns:
            AgentResult with planning results
        """
        try:
            self.update_progress(10, "Analyzing requirements")

            # Extract planning context
            planning_context = inputs.get("planning_context", {})
            requirements = planning_context.get("requirements", [])
            constraints = planning_context.get("constraints", {})

            self.update_progress(30, "Creating development plan")

            # Determine planning strategy based on constraints
            strategy = self._determine_planning_strategy(constraints)

            # Create the development plan
            plan = await self._create_development_plan(
                requirements, constraints, strategy
            )

            self.update_progress(70, "Validating plan")

            # Validate the plan
            validation_result = await self._validate_plan(
                plan, requirements, constraints
            )

            if not validation_result["valid"]:
                self.add_warning(
                    f"Plan validation issues: {validation_result['issues']}"
                )

            self.update_progress(90, "Finalizing plan")

            # Create plan artifacts
            artifacts = []

            # Main plan document
            plan_artifact = self.add_artifact(
                name="development_plan.md",
                content=self._format_plan_markdown(plan),
                artifact_type="documentation",
                plan_type=strategy,
                phases=len(plan["phases"]),
                estimated_duration=plan["estimated_duration"],
            )
            artifacts.append(plan_artifact)

            # Plan as JSON for programmatic access
            plan_json_artifact = self.add_artifact(
                name="development_plan.json",
                content=json.dumps(plan, indent=2),
                artifact_type="data",
                plan_type=strategy,
            )
            artifacts.append(plan_json_artifact)

            # Phase breakdown
            for i, phase in enumerate(plan["phases"]):
                phase_artifact = self.add_artifact(
                    name=f"phase_{i+1}_{phase['name'].lower().replace(' ', '_')}.md",
                    content=self._format_phase_markdown(phase),
                    artifact_type="documentation",
                    phase_number=i + 1,
                    phase_name=phase["name"],
                )
                artifacts.append(phase_artifact)

            self.update_progress(100, "Planning complete")

            return AgentResult(
                success=True,
                content=f"Development plan created successfully using {strategy} methodology",
                artifacts=artifacts,
                metadata={
                    "planning_strategy": strategy,
                    "total_phases": len(plan["phases"]),
                    "estimated_duration_hours": plan["estimated_duration"],
                    "plan_validation": validation_result,
                    "requirements_covered": len(plan["requirements_mapping"]),
                    "constraints_addressed": len(plan["constraints_addressed"]),
                },
                warnings=validation_result.get("issues", []),
            )

        except Exception as e:
            self.add_error(f"Planning failed: {e}")
            return AgentResult(
                success=False,
                content=f"Failed to create development plan: {e}",
                errors=[str(e)],
            )

    def _determine_planning_strategy(self, constraints: Dict[str, Any]) -> str:
        """Determine the best planning strategy based on constraints.

        Args:
            constraints: Project constraints

        Returns:
            Planning strategy name
        """
        deadline = constraints.get("deadline")
        budget = constraints.get("budget")
        architecture = constraints.get("architecture", "").lower()

        # Use agile for tight deadlines or uncertain requirements
        if deadline and "agile" in architecture:
            return "agile"

        # Use waterfall for well-defined requirements and stable scope
        if "waterfall" in architecture or "traditional" in architecture:
            return "waterfall"

        # Default to iterative for most cases
        return "iterative"

    async def _create_development_plan(
        self, requirements: List[str], constraints: Dict[str, Any], strategy: str
    ) -> Dict[str, Any]:
        """Create a comprehensive development plan.

        Args:
            requirements: Project requirements
            constraints: Project constraints
            strategy: Planning strategy

        Returns:
            Development plan dictionary
        """
        # Use the appropriate planning strategy
        plan_creator = self.planning_strategies.get(
            strategy, self._create_iterative_plan
        )
        return plan_creator(requirements, constraints)

    def _create_agile_plan(
        self, requirements: List[str], constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create an agile development plan.

        Args:
            requirements: Project requirements
            constraints: Project constraints

        Returns:
            Agile development plan
        """
        # Break requirements into user stories and sprints
        user_stories = self._create_user_stories(requirements)
        sprints = self._organize_into_sprints(user_stories, constraints)

        return {
            "methodology": "agile",
            "phases": [
                {
                    "name": "Sprint Planning",
                    "description": "Plan and prioritize user stories for each sprint",
                    "duration_hours": 4,
                    "deliverables": ["Sprint backlog", "Story points estimation"],
                    "dependencies": [],
                },
                {
                    "name": "Sprint 1 - Core Features",
                    "description": "Implement core functionality and basic features",
                    "duration_hours": 40,
                    "deliverables": ["Core application", "Basic UI", "Database schema"],
                    "dependencies": ["Sprint Planning"],
                    "user_stories": sprints[0] if sprints else [],
                },
                {
                    "name": "Sprint 2 - Enhanced Features",
                    "description": "Add advanced features and improvements",
                    "duration_hours": 40,
                    "deliverables": [
                        "Advanced features",
                        "API endpoints",
                        "Integration tests",
                    ],
                    "dependencies": ["Sprint 1 - Core Features"],
                    "user_stories": sprints[1] if len(sprints) > 1 else [],
                },
                {
                    "name": "Sprint 3 - Polish & Deploy",
                    "description": "Final testing, optimization, and deployment preparation",
                    "duration_hours": 32,
                    "deliverables": [
                        "Production-ready application",
                        "Documentation",
                        "Deployment config",
                    ],
                    "dependencies": ["Sprint 2 - Enhanced Features"],
                    "user_stories": sprints[2] if len(sprints) > 2 else [],
                },
            ],
            "estimated_duration": 116,  # Total hours
            "requirements_mapping": self._map_requirements_to_phases(requirements),
            "constraints_addressed": self._address_constraints(constraints),
            "risk_mitigation": self._identify_risks_and_mitigation(
                requirements, constraints
            ),
        }

    def _create_waterfall_plan(
        self, requirements: List[str], constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a waterfall development plan.

        Args:
            requirements: Project requirements
            constraints: Project constraints

        Returns:
            Waterfall development plan
        """
        return {
            "methodology": "waterfall",
            "phases": [
                {
                    "name": "Requirements Analysis",
                    "description": "Detailed analysis and documentation of all requirements",
                    "duration_hours": 16,
                    "deliverables": [
                        "Requirements specification",
                        "Use case diagrams",
                        "Acceptance criteria",
                    ],
                    "dependencies": [],
                },
                {
                    "name": "System Design",
                    "description": "High-level and detailed system design",
                    "duration_hours": 24,
                    "deliverables": [
                        "System architecture",
                        "Database design",
                        "API specification",
                    ],
                    "dependencies": ["Requirements Analysis"],
                },
                {
                    "name": "Implementation",
                    "description": "Code implementation and unit testing",
                    "duration_hours": 80,
                    "deliverables": ["Source code", "Unit tests", "Code documentation"],
                    "dependencies": ["System Design"],
                },
                {
                    "name": "Integration & Testing",
                    "description": "Integration testing and system testing",
                    "duration_hours": 32,
                    "deliverables": [
                        "Integration tests",
                        "System tests",
                        "Test reports",
                    ],
                    "dependencies": ["Implementation"],
                },
                {
                    "name": "Deployment",
                    "description": "Production deployment and user acceptance testing",
                    "duration_hours": 16,
                    "deliverables": [
                        "Production deployment",
                        "User documentation",
                        "Training materials",
                    ],
                    "dependencies": ["Integration & Testing"],
                },
            ],
            "estimated_duration": 168,  # Total hours
            "requirements_mapping": self._map_requirements_to_phases(requirements),
            "constraints_addressed": self._address_constraints(constraints),
            "risk_mitigation": self._identify_risks_and_mitigation(
                requirements, constraints
            ),
        }

    def _create_iterative_plan(
        self, requirements: List[str], constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create an iterative development plan.

        Args:
            requirements: Project requirements
            constraints: Project constraints

        Returns:
            Iterative development plan
        """
        return {
            "methodology": "iterative",
            "phases": [
                {
                    "name": "Initial Planning",
                    "description": "High-level planning and architecture design",
                    "duration_hours": 12,
                    "deliverables": [
                        "Project plan",
                        "Architecture overview",
                        "Technology stack",
                    ],
                    "dependencies": [],
                },
                {
                    "name": "Iteration 1 - MVP",
                    "description": "Build minimum viable product with core features",
                    "duration_hours": 48,
                    "deliverables": [
                        "MVP application",
                        "Basic functionality",
                        "Core tests",
                    ],
                    "dependencies": ["Initial Planning"],
                },
                {
                    "name": "Iteration 2 - Feature Enhancement",
                    "description": "Add additional features and improve existing functionality",
                    "duration_hours": 48,
                    "deliverables": [
                        "Enhanced features",
                        "Improved UI/UX",
                        "Additional tests",
                    ],
                    "dependencies": ["Iteration 1 - MVP"],
                },
                {
                    "name": "Iteration 3 - Optimization",
                    "description": "Performance optimization, security hardening, and final polish",
                    "duration_hours": 36,
                    "deliverables": [
                        "Optimized application",
                        "Security audit",
                        "Production readiness",
                    ],
                    "dependencies": ["Iteration 2 - Feature Enhancement"],
                },
                {
                    "name": "Final Integration",
                    "description": "Final integration testing and deployment preparation",
                    "duration_hours": 16,
                    "deliverables": [
                        "Production deployment",
                        "Documentation",
                        "Monitoring setup",
                    ],
                    "dependencies": ["Iteration 3 - Optimization"],
                },
            ],
            "estimated_duration": 160,  # Total hours
            "requirements_mapping": self._map_requirements_to_phases(requirements),
            "constraints_addressed": self._address_constraints(constraints),
            "risk_mitigation": self._identify_risks_and_mitigation(
                requirements, constraints
            ),
        }

    def _create_user_stories(self, requirements: List[str]) -> List[Dict[str, Any]]:
        """Convert requirements into user stories.

        Args:
            requirements: Project requirements

        Returns:
            List of user stories
        """
        user_stories = []

        for i, requirement in enumerate(requirements):
            user_stories.append(
                {
                    "id": f"US-{i+1:03d}",
                    "title": f"Implement {requirement.lower()}",
                    "description": f"As a user, I want {requirement.lower()} so that I can achieve my goals",
                    "acceptance_criteria": [
                        f"The system provides {requirement.lower()}",
                        f"The feature is accessible and functional",
                        f"Error handling is implemented for {requirement.lower()}",
                    ],
                    "story_points": 5,  # Default story points
                    "priority": "medium",
                }
            )

        return user_stories

    def _organize_into_sprints(
        self, user_stories: List[Dict[str, Any]], constraints: Dict[str, Any]
    ) -> List[List[Dict[str, Any]]]:
        """Organize user stories into sprints.

        Args:
            user_stories: List of user stories
            constraints: Project constraints

        Returns:
            List of sprints, each containing user stories
        """
        # Simple organization: distribute stories evenly across sprints
        num_sprints = 3
        stories_per_sprint = len(user_stories) // num_sprints

        sprints = []
        for i in range(num_sprints):
            start_idx = i * stories_per_sprint
            end_idx = (
                start_idx + stories_per_sprint
                if i < num_sprints - 1
                else len(user_stories)
            )
            sprints.append(user_stories[start_idx:end_idx])

        return sprints

    def _map_requirements_to_phases(
        self, requirements: List[str]
    ) -> Dict[str, List[str]]:
        """Map requirements to development phases.

        Args:
            requirements: Project requirements

        Returns:
            Mapping of phases to requirements
        """
        # Simple mapping: distribute requirements across phases
        phases = ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
        mapping = {phase: [] for phase in phases}

        for i, requirement in enumerate(requirements):
            phase_idx = i % len(phases)
            mapping[phases[phase_idx]].append(requirement)

        return mapping

    def _address_constraints(self, constraints: Dict[str, Any]) -> List[str]:
        """Address project constraints in the plan.

        Args:
            constraints: Project constraints

        Returns:
            List of constraint addresses
        """
        addresses = []

        if constraints.get("deadline"):
            addresses.append(
                f"Plan includes timeline management to meet deadline: {constraints['deadline']}"
            )

        if constraints.get("budget"):
            addresses.append(
                f"Resource allocation optimized for budget: ${constraints['budget']}"
            )

        if constraints.get("language"):
            addresses.append(
                f"Technology stack aligned with specified language: {constraints['language']}"
            )

        if constraints.get("framework"):
            addresses.append(
                f"Development approach tailored for framework: {constraints['framework']}"
            )

        if constraints.get("architecture"):
            addresses.append(
                f"Architecture decisions guided by constraint: {constraints['architecture']}"
            )

        return addresses

    def _identify_risks_and_mitigation(
        self, requirements: List[str], constraints: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Identify risks and mitigation strategies.

        Args:
            requirements: Project requirements
            constraints: Project constraints

        Returns:
            List of risk-mitigation pairs
        """
        risks = [
            {
                "risk": "Scope creep during development",
                "mitigation": "Clear requirements documentation and change control process",
            },
            {
                "risk": "Technical complexity exceeding estimates",
                "mitigation": "Proof of concept for complex features and buffer time allocation",
            },
            {
                "risk": "Integration challenges with external systems",
                "mitigation": "Early integration testing and API-first design approach",
            },
            {
                "risk": "Performance issues in production",
                "mitigation": "Performance testing throughout development and optimization phases",
            },
        ]

        # Add constraint-specific risks
        if constraints.get("deadline"):
            risks.append(
                {
                    "risk": "Tight deadline causing quality issues",
                    "mitigation": "Prioritize MVP features and implement continuous testing",
                }
            )

        if constraints.get("budget"):
            risks.append(
                {
                    "risk": "Budget constraints limiting resources",
                    "mitigation": "Efficient resource allocation and cost monitoring throughout project",
                }
            )

        return risks

    async def _validate_plan(
        self, plan: Dict[str, Any], requirements: List[str], constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate the development plan.

        Args:
            plan: Development plan
            requirements: Project requirements
            constraints: Project constraints

        Returns:
            Validation result
        """
        issues = []

        # Check if all requirements are addressed
        requirements_covered = len(plan.get("requirements_mapping", {}))
        if requirements_covered < len(requirements):
            issues.append(
                f"Only {requirements_covered}/{len(requirements)} requirements are explicitly mapped"
            )

        # Check timeline feasibility
        total_duration = plan.get("estimated_duration", 0)
        if total_duration > 200:  # More than 5 weeks at 40 hours/week
            issues.append("Plan duration may be too long for typical project timelines")

        # Check resource allocation
        phases = plan.get("phases", [])
        if not phases:
            issues.append("No development phases defined")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "total_duration_hours": total_duration,
            "phases_count": len(phases),
            "requirements_coverage": (
                requirements_covered / len(requirements) if requirements else 0
            ),
        }

    def _format_plan_markdown(self, plan: Dict[str, Any]) -> str:
        """Format the plan as markdown.

        Args:
            plan: Development plan

        Returns:
            Markdown formatted plan
        """
        lines = [
            f"# Development Plan - {plan['methodology'].title()} Methodology",
            "",
            f"**Estimated Duration:** {plan['estimated_duration']} hours",
            f"**Total Phases:** {len(plan['phases'])}",
            "",
            "## Phases",
            "",
        ]

        for i, phase in enumerate(plan["phases"], 1):
            lines.extend(
                [
                    f"### {i}. {phase['name']}",
                    f"**Duration:** {phase['duration_hours']} hours",
                    f"**Description:** {phase['description']}",
                    "",
                    "**Deliverables:**",
                ]
            )

            for deliverable in phase.get("deliverables", []):
                lines.append(f"- {deliverable}")

            if phase.get("dependencies"):
                lines.extend(
                    [
                        "",
                        "**Dependencies:**",
                    ]
                )
                for dep in phase["dependencies"]:
                    lines.append(f"- {dep}")

            lines.append("")

        # Add requirements mapping
        if plan.get("requirements_mapping"):
            lines.extend(["## Requirements Mapping", ""])

            for phase, reqs in plan["requirements_mapping"].items():
                lines.append(f"### {phase}")
                for req in reqs:
                    lines.append(f"- {req}")
                lines.append("")

        # Add risk mitigation
        if plan.get("risk_mitigation"):
            lines.extend(["## Risk Mitigation", ""])

            for risk in plan["risk_mitigation"]:
                lines.extend(
                    [
                        f"**Risk:** {risk['risk']}",
                        f"**Mitigation:** {risk['mitigation']}",
                        "",
                    ]
                )

        return "\n".join(lines)

    def _format_phase_markdown(self, phase: Dict[str, Any]) -> str:
        """Format a single phase as markdown.

        Args:
            phase: Phase information

        Returns:
            Markdown formatted phase
        """
        lines = [
            f"# {phase['name']}",
            "",
            f"**Duration:** {phase['duration_hours']} hours",
            f"**Description:** {phase['description']}",
            "",
            "## Deliverables",
            "",
        ]

        for deliverable in phase.get("deliverables", []):
            lines.append(f"- {deliverable}")

        if phase.get("dependencies"):
            lines.extend(["", "## Dependencies", ""])
            for dep in phase["dependencies"]:
                lines.append(f"- {dep}")

        if phase.get("user_stories"):
            lines.extend(["", "## User Stories", ""])
            for story in phase["user_stories"]:
                lines.extend(
                    [
                        f"### {story['id']}: {story['title']}",
                        f"**Description:** {story['description']}",
                        f"**Story Points:** {story['story_points']}",
                        f"**Priority:** {story['priority']}",
                        "",
                        "**Acceptance Criteria:**",
                    ]
                )
                for criterion in story.get("acceptance_criteria", []):
                    lines.append(f"- {criterion}")
                lines.append("")

        return "\n".join(lines)
