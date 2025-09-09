#!/usr/bin/env python3
"""
DPO Intelligence Integration Module

Integrates the Intelligence Review Engine with the Development Process Orchestrator (DPO)
to provide seamless enhancement of development requests before workflow generation.

Author: Agent Orchestrator Team
Date: September 2025
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# from .enhanced_token_pool import EnhancedTokenPool  # Not needed for basic DPO
# from generic_orchestrator import AgentTask, GenericOrchestrator  # Import from agent-orchestrator instead

# Setup import paths
try:
    from ._path_setup import setup_paths
except ImportError:
    from _path_setup import setup_paths
setup_paths()

# Import from agent-orchestrator
from generic_orchestrator import AgentTask, GenericOrchestrator

# Import core components - handle both relative and absolute
try:
    from .intelligence_review_engine_enhanced import EnhancementIntelligenceEngine
except ImportError:
    from intelligence_review_engine_enhanced import EnhancementIntelligenceEngine

logger = logging.getLogger(__name__)


@dataclass
class DPORequest:
    """Development Process Orchestrator request structure"""

    request_id: str
    user_request: str
    project_type: str  # api, web_app, cli, library, integration
    complexity_level: str  # simple, moderate, complex
    project_context: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    enhancement_preferences: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EnhancedDPOWorkflow:
    """Enhanced DPO workflow with intelligence-driven improvements"""

    workflow_id: str
    original_request: DPORequest
    enhancement_result: Dict[str, Any]
    workflow_phases: List[Dict[str, Any]]
    agent_assignments: Dict[str, List[str]]  # Phase -> Agent IDs
    quality_gates: List[Dict[str, Any]]
    estimated_timeline: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


class DPOIntelligenceIntegration:
    """
    Integrates Intelligence Review Engine with DPO for enhanced workflow generation
    """

    # Workflow templates enhanced with intelligence
    ENHANCED_WORKFLOW_TEMPLATES = {
        "web_app": {
            "base_phases": [
                "requirements_discovery",
                "architecture_design",
                "frontend_implementation",
                "backend_implementation",
                "integration",
                "testing",
                "documentation",
                "deployment",
            ],
            "intelligence_hooks": {
                "requirements_discovery": ["research-genius", "innovation-analyst"],
                "architecture_design": ["solution-architect", "performance-optimizer"],
                "frontend_implementation": [
                    "development-accelerator",
                    "integration-specialist",
                ],
                "backend_implementation": [
                    "performance-optimizer",
                    "integration-specialist",
                ],
                "integration": ["integration-specialist"],
                "testing": ["development-accelerator"],
                "deployment": ["development-accelerator", "performance-optimizer"],
            },
        },
        "api": {
            "base_phases": [
                "api_design",
                "data_modeling",
                "implementation",
                "security",
                "testing",
                "documentation",
                "deployment",
            ],
            "intelligence_hooks": {
                "api_design": ["solution-architect", "innovation-analyst"],
                "data_modeling": ["solution-architect", "performance-optimizer"],
                "implementation": ["development-accelerator", "performance-optimizer"],
                "security": ["innovation-analyst"],
                "testing": ["development-accelerator"],
                "deployment": ["integration-specialist", "development-accelerator"],
            },
        },
        "cli": {
            "base_phases": [
                "command_design",
                "core_implementation",
                "ui_implementation",
                "testing",
                "packaging",
                "documentation",
            ],
            "intelligence_hooks": {
                "command_design": ["solution-architect", "innovation-analyst"],
                "core_implementation": [
                    "development-accelerator",
                    "performance-optimizer",
                ],
                "ui_implementation": ["development-accelerator"],
                "packaging": ["development-accelerator", "integration-specialist"],
            },
        },
    }

    def __init__(
        self, orchestrator: Optional[GenericOrchestrator] = None, output_dir: str = None
    ):
        """Initialize DPO Intelligence Integration"""
        self.orchestrator = orchestrator
        self.intelligence_engine = EnhancementIntelligenceEngine(
            orchestrator=orchestrator, parallel_agents=6
        )
        self.output_dir = (
            Path(output_dir) if output_dir else Path("output/dpo_enhanced")
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("DPO Intelligence Integration initialized")

    async def process_dpo_request(self, request: DPORequest) -> EnhancedDPOWorkflow:
        """
        Process a DPO request with intelligence enhancement

        Args:
            request: The DPO request to process

        Returns:
            Enhanced DPO workflow with intelligence-driven improvements
        """
        start_time = datetime.now()
        logger.info(f"Processing DPO request: {request.request_id}")

        # Phase 1: Intelligence Review
        logger.info("Phase 1: Running intelligence review...")
        enhancement_result = await self._run_intelligence_review(request)

        # Phase 2: Generate Enhanced Workflow
        logger.info("Phase 2: Generating enhanced workflow...")
        workflow_phases = self._generate_enhanced_workflow(request, enhancement_result)

        # Phase 3: Assign Agents
        logger.info("Phase 3: Assigning specialist agents...")
        agent_assignments = self._assign_specialist_agents(
            workflow_phases, enhancement_result
        )

        # Phase 4: Define Quality Gates
        logger.info("Phase 4: Defining quality gates...")
        quality_gates = self._define_quality_gates(workflow_phases, enhancement_result)

        # Phase 5: Estimate Timeline
        logger.info("Phase 5: Estimating timeline...")
        timeline = self._estimate_timeline(workflow_phases, request.constraints)

        # Create enhanced workflow
        workflow = EnhancedDPOWorkflow(
            workflow_id=f"DPO_{request.request_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            original_request=request,
            enhancement_result=enhancement_result,
            workflow_phases=workflow_phases,
            agent_assignments=agent_assignments,
            quality_gates=quality_gates,
            estimated_timeline=timeline,
            metadata={
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "total_agents": sum(
                    len(agents) for agents in agent_assignments.values()
                ),
                "total_phases": len(workflow_phases),
                "enhancement_count": enhancement_result["metadata"][
                    "enhancements_selected"
                ],
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Save workflow
        self._save_workflow(workflow)

        logger.info(f"Enhanced DPO workflow created: {workflow.workflow_id}")

        return workflow

    async def _run_intelligence_review(self, request: DPORequest) -> Dict[str, Any]:
        """Run intelligence review on the request"""
        # Determine optimization goals based on project type
        optimization_goals = self._determine_optimization_goals(request)

        # Run intelligence engine
        result = await self.intelligence_engine.enhance_with_intelligence(
            original_request=request.user_request,
            project_context=request.project_context,
            optimization_goals=optimization_goals,
            constraints=request.constraints,
        )

        return result

    def _determine_optimization_goals(self, request: DPORequest) -> List[str]:
        """Determine optimization goals based on request"""
        goals = []

        # Based on project type
        if request.project_type == "web_app":
            goals.extend(["user_experience", "scalability", "performance"])
        elif request.project_type == "api":
            goals.extend(["performance", "security", "documentation"])
        elif request.project_type == "cli":
            goals.extend(["usability", "performance", "packaging"])

        # Based on complexity
        if request.complexity_level == "complex":
            goals.extend(["maintainability", "testing", "monitoring"])

        # Based on constraints
        if request.constraints.get("timeline") == "aggressive":
            goals.append("development_speed")

        if request.constraints.get("budget") == "limited":
            goals.append("cost_optimization")

        # User preferences
        if request.enhancement_preferences:
            if request.enhancement_preferences.get("prioritize_innovation"):
                goals.append("innovation")
            if request.enhancement_preferences.get("prioritize_performance"):
                goals.append("performance")

        return list(set(goals))  # Remove duplicates

    def _generate_enhanced_workflow(
        self, request: DPORequest, enhancement_result: Dict
    ) -> List[Dict[str, Any]]:
        """Generate enhanced workflow phases"""
        # Get base template
        template = self.ENHANCED_WORKFLOW_TEMPLATES.get(
            request.project_type, self.ENHANCED_WORKFLOW_TEMPLATES["web_app"]
        )

        workflow_phases = []

        # Get enhancement roadmap
        roadmap = enhancement_result.get("implementation_roadmap", {})
        enhancement_phases = roadmap.get("phases", [])

        # Merge base phases with enhancement phases
        for idx, base_phase in enumerate(template["base_phases"]):
            phase = {
                "phase_id": f"phase_{idx + 1}",
                "name": base_phase.replace("_", " ").title(),
                "type": base_phase,
                "agents": [],
                "enhancements": [],
                "deliverables": [],
                "success_criteria": [],
                "estimated_duration": "1 week",
            }

            # Add relevant enhancements to this phase
            if idx < len(enhancement_phases):
                enhancement_phase = enhancement_phases[idx]
                phase["enhancements"] = enhancement_phase.get("enhancements", [])[:3]
                phase["deliverables"].extend(
                    enhancement_phase.get("key_deliverables", [])[:2]
                )
                phase["estimated_duration"] = enhancement_phase.get(
                    "estimated_duration", "1 week"
                )

            # Add intelligence hooks
            if base_phase in template["intelligence_hooks"]:
                phase["intelligence_agents"] = template["intelligence_hooks"][
                    base_phase
                ]

            # Add specific enhancements based on category
            phase = self._enhance_phase_with_intelligence(phase, enhancement_result)

            workflow_phases.append(phase)

        # Add additional phases for major enhancements
        major_enhancements = [
            e
            for e in enhancement_result.get("enhancement_plan", [])
            if e.score.impact_score > 0.8
        ]

        if major_enhancements:
            innovation_phase = {
                "phase_id": f"phase_{len(workflow_phases) + 1}",
                "name": "Innovation & Advanced Features",
                "type": "innovation",
                "agents": ["innovation-analyst", "integration-specialist"],
                "enhancements": [e.to_dict() for e in major_enhancements[:3]],
                "deliverables": [
                    "Advanced feature implementation",
                    "Integration testing",
                ],
                "success_criteria": [
                    "All advanced features functional",
                    "Performance targets met",
                ],
                "estimated_duration": "2 weeks",
            }
            workflow_phases.append(innovation_phase)

        return workflow_phases

    def _enhance_phase_with_intelligence(
        self, phase: Dict, enhancement_result: Dict
    ) -> Dict:
        """Enhance a workflow phase with intelligence insights"""
        phase_type = phase["type"]

        # Add relevant quick wins
        quick_wins = enhancement_result.get("quick_wins", [])
        relevant_wins = [
            qw for qw in quick_wins if self._is_relevant_to_phase(qw, phase_type)
        ]

        if relevant_wins:
            phase["quick_wins"] = relevant_wins[:2]
            phase["deliverables"].append(f"Implement {len(relevant_wins)} quick wins")

        # Add performance optimizations
        if "implementation" in phase_type or "backend" in phase_type:
            perf_enhancements = [
                e
                for e in enhancement_result.get("enhancements_by_category", {}).get(
                    "performance-optimizer", []
                )
            ]
            if perf_enhancements:
                phase["performance_optimizations"] = perf_enhancements[:2]
                phase["success_criteria"].append("Performance benchmarks achieved")

        # Add integrations
        if "integration" in phase_type:
            integrations = enhancement_result.get("enhancements_by_category", {}).get(
                "integration-specialist", []
            )
            if integrations:
                phase["integrations"] = integrations[:3]
                phase["deliverables"].append(
                    f"Complete {len(integrations[:3])} integrations"
                )

        return phase

    def _is_relevant_to_phase(self, enhancement: Dict, phase_type: str) -> bool:
        """Check if enhancement is relevant to phase"""
        category = enhancement.get("category", "")

        relevance_map = {
            "requirements_discovery": ["research-genius", "innovation-analyst"],
            "architecture_design": ["solution-architect"],
            "implementation": ["development-accelerator", "performance-optimizer"],
            "frontend_implementation": ["development-accelerator"],
            "backend_implementation": [
                "performance-optimizer",
                "integration-specialist",
            ],
            "testing": ["development-accelerator"],
            "deployment": ["integration-specialist", "development-accelerator"],
            "documentation": ["development-accelerator"],
        }

        return category in relevance_map.get(phase_type, [])

    def _assign_specialist_agents(
        self, workflow_phases: List[Dict], enhancement_result: Dict
    ) -> Dict[str, List[str]]:
        """Assign specialist agents to workflow phases"""
        assignments = {}
        agent_counter = 0

        for phase in workflow_phases:
            phase_agents = []

            # Base agents for phase type
            base_agent_count = self._get_base_agent_count(phase["type"])
            for i in range(base_agent_count):
                agent_counter += 1
                phase_agents.append(f"agent_{agent_counter:03d}_{phase['type']}")

            # Intelligence agents
            if "intelligence_agents" in phase:
                for intel_agent in phase["intelligence_agents"]:
                    agent_counter += 1
                    phase_agents.append(f"agent_{agent_counter:03d}_{intel_agent}")

            # Additional agents for enhancements
            enhancement_count = len(phase.get("enhancements", []))
            if enhancement_count > 3:
                # Add extra agents for complex phases
                for i in range(min(2, enhancement_count // 3)):
                    agent_counter += 1
                    phase_agents.append(f"agent_{agent_counter:03d}_enhancement")

            assignments[phase["phase_id"]] = phase_agents

        return assignments

    def _get_base_agent_count(self, phase_type: str) -> int:
        """Get base number of agents for phase type"""
        agent_counts = {
            "requirements_discovery": 2,
            "architecture_design": 3,
            "frontend_implementation": 4,
            "backend_implementation": 4,
            "implementation": 5,
            "integration": 3,
            "testing": 3,
            "documentation": 2,
            "deployment": 2,
            "api_design": 2,
            "data_modeling": 2,
            "security": 2,
            "command_design": 1,
            "core_implementation": 3,
            "ui_implementation": 2,
            "packaging": 1,
            "innovation": 3,
        }

        return agent_counts.get(phase_type, 2)

    def _define_quality_gates(
        self, workflow_phases: List[Dict], enhancement_result: Dict
    ) -> List[Dict[str, Any]]:
        """Define quality gates for the workflow"""
        quality_gates = []

        for idx, phase in enumerate(workflow_phases):
            gate = {
                "gate_id": f"QG_{idx + 1}",
                "phase": phase["phase_id"],
                "name": f"{phase['name']} Quality Gate",
                "criteria": [],
                "automated_checks": [],
                "manual_reviews": [],
            }

            # Base criteria
            gate["criteria"].extend(
                [
                    "All deliverables completed",
                    "Code review passed",
                    "Unit tests passing",
                ]
            )

            # Phase-specific criteria
            if "implementation" in phase["type"]:
                gate["criteria"].extend(
                    [
                        "Code coverage > 80%",
                        "No critical security issues",
                        "Performance benchmarks met",
                    ]
                )
                gate["automated_checks"].extend(
                    [
                        "Unit test execution",
                        "Code coverage analysis",
                        "Security scanning",
                    ]
                )

            if "testing" in phase["type"]:
                gate["criteria"].extend(
                    [
                        "All test scenarios executed",
                        "No critical bugs",
                        "Performance tests passing",
                    ]
                )
                gate["automated_checks"].extend(
                    ["Integration test suite", "End-to-end tests", "Load testing"]
                )

            if "deployment" in phase["type"]:
                gate["criteria"].extend(
                    [
                        "Deployment checklist complete",
                        "Rollback plan tested",
                        "Monitoring configured",
                    ]
                )
                gate["manual_reviews"].append("Deployment readiness review")

            # Enhancement-specific criteria
            if phase.get("enhancements"):
                gate["criteria"].append(
                    f"All {len(phase['enhancements'])} enhancements implemented"
                )

            if phase.get("performance_optimizations"):
                gate["criteria"].append("Performance improvements verified")
                gate["automated_checks"].append("Performance benchmark suite")

            quality_gates.append(gate)

        # Add final gate
        final_gate = {
            "gate_id": "QG_FINAL",
            "phase": "completion",
            "name": "Final Release Gate",
            "criteria": [
                "All phases completed successfully",
                "Documentation complete",
                "User acceptance criteria met",
                "Production readiness verified",
            ],
            "automated_checks": [
                "Full regression test suite",
                "Security audit",
                "Performance validation",
            ],
            "manual_reviews": [
                "Architecture review",
                "Security review",
                "Business stakeholder approval",
            ],
        }
        quality_gates.append(final_gate)

        return quality_gates

    def _estimate_timeline(
        self, workflow_phases: List[Dict], constraints: Dict
    ) -> Dict[str, Any]:
        """Estimate project timeline"""
        timeline = {
            "phases": [],
            "total_duration": "",
            "critical_path": [],
            "milestones": [],
            "risk_buffer": "",
        }

        total_weeks = 0

        for phase in workflow_phases:
            duration_str = phase.get("estimated_duration", "1 week")

            # Parse duration
            if "week" in duration_str:
                weeks = self._parse_weeks(duration_str)
            else:
                weeks = 1

            # Adjust for constraints
            if constraints.get("timeline") == "aggressive":
                weeks = max(1, int(weeks * 0.8))
            elif constraints.get("timeline") == "relaxed":
                weeks = int(weeks * 1.2)

            phase_timeline = {
                "phase": phase["name"],
                "duration_weeks": weeks,
                "start_week": total_weeks + 1,
                "end_week": total_weeks + weeks,
            }

            timeline["phases"].append(phase_timeline)

            # Add milestone
            if phase.get("type") in ["deployment", "testing", "integration"]:
                timeline["milestones"].append(
                    {
                        "name": f"Complete {phase['name']}",
                        "week": total_weeks + weeks,
                        "deliverables": phase.get("deliverables", [])[:2],
                    }
                )

            total_weeks += weeks

        # Calculate totals
        timeline["total_duration"] = f"{total_weeks} weeks"

        # Add risk buffer
        risk_buffer = max(1, int(total_weeks * 0.15))
        timeline["risk_buffer"] = f"{risk_buffer} weeks"
        timeline["total_with_buffer"] = f"{total_weeks + risk_buffer} weeks"

        # Identify critical path (simplified)
        timeline["critical_path"] = [
            phase["name"]
            for phase in workflow_phases
            if phase.get("type")
            in ["architecture_design", "implementation", "testing", "deployment"]
        ]

        return timeline

    def _parse_weeks(self, duration_str: str) -> int:
        """Parse weeks from duration string"""
        import re

        # Try to extract number
        match = re.search(r"(\d+)", duration_str)
        if match:
            weeks = int(match.group(1))

            # Handle ranges
            if "-" in duration_str:
                match2 = re.search(r"-(\d+)", duration_str)
                if match2:
                    weeks = (weeks + int(match2.group(1))) // 2

            return weeks

        return 1

    def _save_workflow(self, workflow: EnhancedDPOWorkflow):
        """Save enhanced workflow to disk"""
        workflow_dir = self.output_dir / workflow.workflow_id
        workflow_dir.mkdir(exist_ok=True)

        # Save complete workflow JSON
        json_path = workflow_dir / "enhanced_workflow.json"
        with open(json_path, "w") as f:
            json.dump(workflow.to_dict(), f, indent=2, default=str)

        # Save workflow summary
        summary_path = workflow_dir / "workflow_summary.md"
        with open(summary_path, "w") as f:
            f.write(f"# Enhanced DPO Workflow\n\n")
            f.write(f"**Workflow ID**: {workflow.workflow_id}\n")
            f.write(f"**Request ID**: {workflow.original_request.request_id}\n")
            f.write(f"**Generated**: {workflow.metadata['timestamp']}\n\n")

            f.write(f"## Original Request\n")
            f.write(f"{workflow.original_request.user_request}\n\n")

            f.write(f"## Workflow Overview\n")
            f.write(f"- Total Phases: {workflow.metadata['total_phases']}\n")
            f.write(f"- Total Agents: {workflow.metadata['total_agents']}\n")
            f.write(
                f"- Enhancements Applied: {workflow.metadata['enhancement_count']}\n"
            )
            f.write(
                f"- Estimated Duration: {workflow.estimated_timeline['total_duration']}\n\n"
            )

            f.write(f"## Workflow Phases\n")
            for phase in workflow.workflow_phases:
                f.write(f"\n### {phase['name']}\n")
                f.write(f"- Duration: {phase['estimated_duration']}\n")
                f.write(
                    f"- Agents: {len(workflow.agent_assignments.get(phase['phase_id'], []))}\n"
                )

                if phase.get("enhancements"):
                    f.write(f"- Enhancements: {len(phase['enhancements'])}\n")

                if phase.get("deliverables"):
                    f.write("- Key Deliverables:\n")
                    for deliverable in phase["deliverables"][:3]:
                        f.write(f"  - {deliverable}\n")

            f.write(f"\n## Quality Gates\n")
            for gate in workflow.quality_gates[:3]:
                f.write(f"\n### {gate['name']}\n")
                f.write("Criteria:\n")
                for criterion in gate["criteria"][:3]:
                    f.write(f"- {criterion}\n")

        logger.info(f"Workflow saved to {workflow_dir}")


async def main():
    """Example usage of DPO Intelligence Integration"""
    # Create sample DPO request
    request = DPORequest(
        request_id="REQ_001",
        user_request="Build a real-time collaboration platform for remote teams with video chat, screen sharing, and document collaboration",
        project_type="web_app",
        complexity_level="complex",
        project_context={
            "target_users": "5000 concurrent users",
            "features": [
                "video_chat",
                "screen_sharing",
                "document_editing",
                "chat",
                "file_sharing",
            ],
            "platforms": ["web", "mobile"],
            "deployment": "AWS",
        },
        constraints={
            "timeline": "normal",
            "budget": "moderate",
            "team_size": 8,
            "max_enhancements": 20,
        },
        enhancement_preferences={
            "prioritize_innovation": True,
            "prioritize_performance": True,
        },
    )

    # Initialize integration
    integration = DPOIntelligenceIntegration(output_dir="output/dpo_enhanced")

    # Process request
    workflow = await integration.process_dpo_request(request)

    # Display results
    print("\n" + "=" * 80)
    print("ENHANCED DPO WORKFLOW GENERATED")
    print("=" * 80)
    print(f"\nWorkflow ID: {workflow.workflow_id}")
    print(f"Total Phases: {len(workflow.workflow_phases)}")
    print(f"Total Agents: {workflow.metadata['total_agents']}")
    print(f"Enhancements Applied: {workflow.metadata['enhancement_count']}")
    print(f"Estimated Timeline: {workflow.estimated_timeline['total_duration']}")

    print("\n" + "-" * 80)
    print("WORKFLOW PHASES:")
    print("-" * 80)
    for phase in workflow.workflow_phases:
        agents = len(workflow.agent_assignments.get(phase["phase_id"], []))
        enhancements = len(phase.get("enhancements", []))
        print(
            f"• {phase['name']}: {agents} agents, {enhancements} enhancements, {phase['estimated_duration']}"
        )

    print("\n" + "-" * 80)
    print("KEY MILESTONES:")
    print("-" * 80)
    for milestone in workflow.estimated_timeline["milestones"][:5]:
        print(f"• Week {milestone['week']}: {milestone['name']}")


if __name__ == "__main__":
    asyncio.run(main())
