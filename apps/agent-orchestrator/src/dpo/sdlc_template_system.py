#!/usr/bin/env python3
"""
SDLC Template System - Core workflow generation component for DPO
Generates comprehensive development workflows based on project type and specifications
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class WorkflowPhase:
    """Represents a phase in the SDLC workflow"""

    phase_id: str
    phase_name: str
    phase_type: str  # discovery, design, implementation, qa, documentation, deployment
    agents: List[Dict[str, Any]]
    dependencies: List[str] = field(default_factory=list)
    parallel_execution: bool = True
    quality_gates: List[str] = field(default_factory=list)
    expected_outputs: List[str] = field(default_factory=list)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    max_iterations: int = 1
    context_requirements: List[str] = field(default_factory=list)


class BaseTemplate(ABC):
    """Abstract base class for all SDLC templates"""

    def __init__(self, project_name: str, complexity: str = "medium"):
        self.project_name = project_name
        self.complexity = complexity
        self.phases: List[WorkflowPhase] = []
        self.metadata = {
            "template_type": self.__class__.__name__,
            "created_at": datetime.now().isoformat(),
            "project_name": project_name,
            "complexity": complexity,
        }

    @abstractmethod
    def build_workflow(self) -> List[WorkflowPhase]:
        """Build the complete workflow for this template"""
        pass

    def get_agent_count(self, base_count: int) -> int:
        """Scale agent count based on complexity"""
        scaling = {"low": 0.7, "medium": 1.0, "high": 1.5, "enterprise": 2.0}
        return max(1, int(base_count * scaling.get(self.complexity, 1.0)))

    def add_discovery_phase(self) -> WorkflowPhase:
        """Standard discovery phase for all templates"""
        return WorkflowPhase(
            phase_id="discovery",
            phase_name="Requirements Discovery & Analysis",
            phase_type="discovery",
            agents=[
                {"type": "requirements-analyst", "count": self.get_agent_count(2)},
                {"type": "business-analyst", "count": self.get_agent_count(1)},
                {"type": "research-specialist", "count": 1},
            ],
            quality_gates=["requirements_completeness", "feasibility_check"],
            expected_outputs=[
                "requirements.md",
                "user_stories.md",
                "research_findings.md",
            ],
            validation_rules={
                "min_requirements": 10,
                "must_have_acceptance_criteria": True,
            },
        )

    def add_design_phase(self, focus_areas: List[str] = None) -> WorkflowPhase:
        """Standard design phase with customizable focus"""
        agents = [{"type": "solution-architect", "count": self.get_agent_count(2)}]

        if focus_areas:
            if "database" in focus_areas:
                agents.append({"type": "database-specialist", "count": 1})
            if "security" in focus_areas:
                agents.append({"type": "security-architect", "count": 1})
            if "api" in focus_areas:
                agents.append({"type": "api-designer", "count": 1})
            if "ui" in focus_areas:
                agents.append({"type": "ui-ux-designer", "count": 1})

        return WorkflowPhase(
            phase_id="design",
            phase_name="Architecture & Design",
            phase_type="design",
            agents=agents,
            dependencies=["discovery"],
            quality_gates=["architecture_review", "design_consistency"],
            expected_outputs=["architecture.md", "design_specs.md", "api_design.yaml"],
            validation_rules={
                "must_have_diagrams": True,
                "scalability_addressed": True,
            },
        )

    def add_implementation_phase(self, streams: List[str]) -> List[WorkflowPhase]:
        """Create parallel implementation streams"""
        phases = []

        for stream in streams:
            phase = WorkflowPhase(
                phase_id=f"implementation_{stream}",
                phase_name=f"Implementation - {stream.title()}",
                phase_type="implementation",
                agents=[
                    {
                        "type": "development-specialist",
                        "count": self.get_agent_count(3),
                    },
                    {"type": "code-analyzer", "count": 1},
                ],
                dependencies=["design"],
                parallel_execution=True,
                quality_gates=["code_review", "unit_tests"],
                expected_outputs=[f"src/{stream}/", f"tests/{stream}/"],
                validation_rules={"test_coverage": 80, "no_critical_issues": True},
            )
            phases.append(phase)

        return phases

    def add_qa_phase(self) -> WorkflowPhase:
        """Standard QA phase"""
        return WorkflowPhase(
            phase_id="qa",
            phase_name="Quality Assurance & Testing",
            phase_type="qa",
            agents=[
                {"type": "qa-testing-guru", "count": self.get_agent_count(2)},
                {"type": "performance-optimizer", "count": 1},
                {"type": "security-tester", "count": 1},
            ],
            dependencies=["implementation_*"],
            quality_gates=["all_tests_pass", "security_scan", "performance_benchmarks"],
            expected_outputs=[
                "test_reports/",
                "security_audit.md",
                "performance_report.md",
            ],
            validation_rules={
                "all_tests_passing": True,
                "no_security_vulnerabilities": True,
                "performance_targets_met": True,
            },
        )

    def add_documentation_phase(self) -> WorkflowPhase:
        """Standard documentation phase"""
        return WorkflowPhase(
            phase_id="documentation",
            phase_name="Documentation & Knowledge Transfer",
            phase_type="documentation",
            agents=[
                {"type": "technical-writer", "count": self.get_agent_count(2)},
                {"type": "api-documenter", "count": 1},
            ],
            dependencies=["qa"],
            quality_gates=["documentation_completeness", "examples_provided"],
            expected_outputs=[
                "README.md",
                "API_DOCS.md",
                "USER_GUIDE.md",
                "DEVELOPER_GUIDE.md",
            ],
            validation_rules={
                "all_endpoints_documented": True,
                "setup_instructions_complete": True,
            },
        )

    def add_deployment_phase(self) -> WorkflowPhase:
        """Standard deployment preparation phase"""
        return WorkflowPhase(
            phase_id="deployment",
            phase_name="Deployment Preparation",
            phase_type="deployment",
            agents=[
                {"type": "sdlc-deployment", "count": 1},
                {"type": "infrastructure-specialist", "count": 1},
            ],
            dependencies=["documentation"],
            quality_gates=["deployment_readiness", "rollback_plan"],
            expected_outputs=["deployment/", "docker-compose.yml", "DEPLOYMENT.md"],
            validation_rules={"containers_build": True, "health_checks_defined": True},
        )

    def add_review_cycle(self, after_phase: str) -> WorkflowPhase:
        """Add a review cycle after a specific phase"""
        return WorkflowPhase(
            phase_id=f"review_{after_phase}",
            phase_name=f"Review Cycle - {after_phase.title()}",
            phase_type="review",
            agents=[
                {"type": "reviewer-critic", "count": 2},
                {"type": "quality-analyst", "count": 1},
            ],
            dependencies=[after_phase],
            quality_gates=["review_approval", "no_blockers"],
            expected_outputs=[f"review_{after_phase}.md"],
            max_iterations=2,
        )

    def to_orchestrator_format(self) -> Dict[str, Any]:
        """Convert workflow to orchestrator-compatible JSON format"""
        tasks = []

        for phase in self.phases:
            for i, agent_config in enumerate(phase.agents):
                for agent_num in range(agent_config["count"]):
                    task = {
                        "task_id": f"{phase.phase_id}_{agent_config['type']}_{agent_num}",
                        "task_type": agent_config["type"],
                        "phase": phase.phase_id,
                        "prompt": self._generate_agent_prompt(
                            phase, agent_config["type"]
                        ),
                        "context": {
                            "project_name": self.project_name,
                            "phase_name": phase.phase_name,
                            "expected_outputs": phase.expected_outputs,
                            "quality_gates": phase.quality_gates,
                        },
                        "dependencies": [
                            f"{dep}_complete" for dep in phase.dependencies
                        ],
                        "parallel_execution": phase.parallel_execution,
                        "validation_rules": phase.validation_rules,
                    }
                    tasks.append(task)

        return {
            "workflow_id": f"{self.project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "metadata": self.metadata,
            "phases": [p.__dict__ for p in self.phases],
            "tasks": tasks,
            "execution_config": {
                "max_parallel_agents": 10,
                "checkpoint_interval": 300,
                "failure_threshold": 0.2,
            },
        }

    def _generate_agent_prompt(self, phase: WorkflowPhase, agent_type: str) -> str:
        """Generate specific prompt for agent based on phase and type"""
        base_prompt = f"""
You are a {agent_type} working on the {phase.phase_name} phase of {self.project_name}.

Phase Objectives:
- Type: {phase.phase_type}
- Expected Outputs: {', '.join(phase.expected_outputs)}
- Quality Gates: {', '.join(phase.quality_gates)}

Your specific responsibilities as a {agent_type}:
"""

        # Add agent-specific instructions
        agent_prompts = {
            "requirements-analyst": "Analyze and document detailed requirements, user stories, and acceptance criteria.",
            "solution-architect": "Design the system architecture, define components, and create technical specifications.",
            "development-specialist": "Implement the solution according to specifications with clean, maintainable code.",
            "qa-testing-guru": "Create and execute comprehensive test plans, ensure quality standards are met.",
            "technical-writer": "Create clear, comprehensive documentation for all stakeholders.",
            "reviewer-critic": "Review deliverables critically, identify issues, and suggest improvements.",
            "security-architect": "Design and validate security measures, identify vulnerabilities.",
            "performance-optimizer": "Analyze and optimize system performance, identify bottlenecks.",
        }

        return base_prompt + agent_prompts.get(
            agent_type, "Complete your assigned tasks with excellence."
        )


class BackendAPITemplate(BaseTemplate):
    """Template for backend API development projects"""

    def build_workflow(self) -> List[WorkflowPhase]:
        """Build complete backend API workflow"""
        self.phases = []

        # Discovery phase
        self.phases.append(self.add_discovery_phase())

        # Design phase with API and database focus
        self.phases.append(self.add_design_phase(["database", "security", "api"]))

        # Implementation streams
        self.phases.extend(
            self.add_implementation_phase(["api", "database", "auth", "services"])
        )

        # Add review after implementation
        self.phases.append(self.add_review_cycle("implementation_api"))

        # QA phase
        self.phases.append(self.add_qa_phase())

        # Documentation
        self.phases.append(self.add_documentation_phase())

        # Deployment
        self.phases.append(self.add_deployment_phase())

        return self.phases


class FrontendApplicationTemplate(BaseTemplate):
    """Template for frontend application development"""

    def build_workflow(self) -> List[WorkflowPhase]:
        """Build complete frontend application workflow"""
        self.phases = []

        # Discovery phase
        self.phases.append(self.add_discovery_phase())

        # Design phase with UI/UX focus
        self.phases.append(self.add_design_phase(["ui", "security"]))

        # Implementation streams
        self.phases.extend(
            self.add_implementation_phase(["components", "state", "routing", "styles"])
        )

        # Add review after implementation
        self.phases.append(self.add_review_cycle("implementation_components"))

        # QA phase
        self.phases.append(self.add_qa_phase())

        # Documentation
        self.phases.append(self.add_documentation_phase())

        # Deployment
        self.phases.append(self.add_deployment_phase())

        return self.phases


class FullStackApplicationTemplate(BaseTemplate):
    """Template for full-stack application development"""

    def build_workflow(self) -> List[WorkflowPhase]:
        """Build complete full-stack workflow"""
        self.phases = []

        # Discovery phase
        self.phases.append(self.add_discovery_phase())

        # Design phase with comprehensive focus
        self.phases.append(self.add_design_phase(["database", "security", "api", "ui"]))

        # Backend implementation
        self.phases.extend(
            self.add_implementation_phase(
                ["backend_api", "backend_services", "database"]
            )
        )

        # Frontend implementation (depends on backend)
        frontend_phases = self.add_implementation_phase(
            ["frontend_components", "frontend_state", "frontend_integration"]
        )
        for phase in frontend_phases:
            phase.dependencies = ["implementation_backend_api"]
        self.phases.extend(frontend_phases)

        # Integration phase
        self.phases.append(
            WorkflowPhase(
                phase_id="integration",
                phase_name="Full-Stack Integration",
                phase_type="implementation",
                agents=[
                    {"type": "integration-specialist", "count": 2},
                    {"type": "development-specialist", "count": 2},
                ],
                dependencies=["implementation_frontend_integration"],
                quality_gates=["end_to_end_tests", "integration_tests"],
                expected_outputs=["integration_tests/", "e2e_tests/"],
            )
        )

        # QA phase
        self.phases.append(self.add_qa_phase())

        # Documentation
        self.phases.append(self.add_documentation_phase())

        # Deployment
        self.phases.append(self.add_deployment_phase())

        return self.phases


class CLIToolTemplate(BaseTemplate):
    """Template for CLI tool development"""

    def build_workflow(self) -> List[WorkflowPhase]:
        """Build complete CLI tool workflow"""
        self.phases = []

        # Discovery phase
        self.phases.append(self.add_discovery_phase())

        # Design phase
        self.phases.append(self.add_design_phase(["security"]))

        # CLI-specific design phase
        self.phases.append(
            WorkflowPhase(
                phase_id="cli_design",
                phase_name="CLI Interface Design",
                phase_type="design",
                agents=[
                    {"type": "cli-specialist", "count": 1},
                    {"type": "ux-designer", "count": 1},
                ],
                dependencies=["design"],
                quality_gates=["command_structure", "help_system"],
                expected_outputs=["cli_spec.md", "command_reference.md"],
            )
        )

        # Implementation
        self.phases.extend(self.add_implementation_phase(["core", "commands", "utils"]))

        # QA with CLI-specific testing
        qa_phase = self.add_qa_phase()
        qa_phase.agents.append({"type": "cli-tester", "count": 1})
        self.phases.append(qa_phase)

        # Documentation with CLI examples
        doc_phase = self.add_documentation_phase()
        doc_phase.expected_outputs.append("EXAMPLES.md")
        self.phases.append(doc_phase)

        # Package distribution phase
        self.phases.append(
            WorkflowPhase(
                phase_id="packaging",
                phase_name="Package Distribution",
                phase_type="deployment",
                agents=[{"type": "package-specialist", "count": 1}],
                dependencies=["documentation"],
                quality_gates=["package_build", "installation_test"],
                expected_outputs=["setup.py", "requirements.txt", "dist/"],
            )
        )

        return self.phases


class LibraryPackageTemplate(BaseTemplate):
    """Template for library/package development"""

    def build_workflow(self) -> List[WorkflowPhase]:
        """Build complete library development workflow"""
        self.phases = []

        # Discovery phase
        self.phases.append(self.add_discovery_phase())

        # API design phase
        self.phases.append(
            WorkflowPhase(
                phase_id="api_design",
                phase_name="Library API Design",
                phase_type="design",
                agents=[
                    {"type": "api-designer", "count": 2},
                    {"type": "solution-architect", "count": 1},
                ],
                dependencies=["discovery"],
                quality_gates=["api_consistency", "backward_compatibility"],
                expected_outputs=["api_spec.md", "interface_design.md"],
            )
        )

        # Implementation
        self.phases.extend(
            self.add_implementation_phase(["core", "extensions", "adapters"])
        )

        # Testing with emphasis on unit tests
        self.phases.append(
            WorkflowPhase(
                phase_id="testing",
                phase_name="Comprehensive Testing",
                phase_type="qa",
                agents=[
                    {"type": "test-engineer", "count": 3},
                    {"type": "qa-testing-guru", "count": 1},
                ],
                dependencies=["implementation_core"],
                quality_gates=["unit_tests", "integration_tests", "coverage_threshold"],
                expected_outputs=["tests/", "coverage_report.html"],
                validation_rules={"test_coverage": 90},
            )
        )

        # Documentation with API focus
        self.phases.append(
            WorkflowPhase(
                phase_id="documentation",
                phase_name="Library Documentation",
                phase_type="documentation",
                agents=[
                    {"type": "api-documenter", "count": 2},
                    {"type": "technical-writer", "count": 1},
                ],
                dependencies=["testing"],
                quality_gates=["api_docs_complete", "examples_provided"],
                expected_outputs=["API.md", "EXAMPLES.md", "CONTRIBUTING.md"],
            )
        )

        # Publishing phase
        self.phases.append(
            WorkflowPhase(
                phase_id="publishing",
                phase_name="Package Publishing",
                phase_type="deployment",
                agents=[{"type": "package-specialist", "count": 1}],
                dependencies=["documentation"],
                quality_gates=["version_tagged", "changelog_updated"],
                expected_outputs=["CHANGELOG.md", "setup.py", "pyproject.toml"],
            )
        )

        return self.phases


class IntegrationConnectorTemplate(BaseTemplate):
    """Template for integration/connector development"""

    def build_workflow(self) -> List[WorkflowPhase]:
        """Build complete integration connector workflow"""
        self.phases = []

        # Discovery with focus on external systems
        discovery = self.add_discovery_phase()
        discovery.agents.append({"type": "integration-analyst", "count": 2})
        self.phases.append(discovery)

        # Design phase with integration focus
        self.phases.append(self.add_design_phase(["api", "security"]))

        # Connector design phase
        self.phases.append(
            WorkflowPhase(
                phase_id="connector_design",
                phase_name="Connector Architecture",
                phase_type="design",
                agents=[
                    {"type": "integration-architect", "count": 2},
                    {"type": "api-designer", "count": 1},
                ],
                dependencies=["design"],
                quality_gates=["protocol_compatibility", "error_handling"],
                expected_outputs=["connector_spec.md", "protocol_mapping.md"],
            )
        )

        # Implementation with retry logic and error handling
        self.phases.extend(
            self.add_implementation_phase(["connector", "transformers", "handlers"])
        )

        # Integration testing phase
        self.phases.append(
            WorkflowPhase(
                phase_id="integration_testing",
                phase_name="Integration Testing",
                phase_type="qa",
                agents=[
                    {"type": "integration-tester", "count": 2},
                    {"type": "qa-testing-guru", "count": 1},
                ],
                dependencies=["implementation_connector"],
                quality_gates=[
                    "connection_tests",
                    "data_validation",
                    "error_scenarios",
                ],
                expected_outputs=["integration_tests/", "test_scenarios.md"],
            )
        )

        # Documentation
        self.phases.append(self.add_documentation_phase())

        # Monitoring setup
        self.phases.append(
            WorkflowPhase(
                phase_id="monitoring",
                phase_name="Monitoring & Observability",
                phase_type="deployment",
                agents=[
                    {"type": "monitoring-specialist", "count": 1},
                    {"type": "sdlc-deployment", "count": 1},
                ],
                dependencies=["documentation"],
                quality_gates=["metrics_defined", "alerts_configured"],
                expected_outputs=["monitoring/", "alerts.yaml"],
            )
        )

        return self.phases


class DataPipelineTemplate(BaseTemplate):
    """Template for data processing pipeline development"""

    def build_workflow(self) -> List[WorkflowPhase]:
        """Build complete data pipeline workflow"""
        self.phases = []

        # Discovery with data focus
        discovery = self.add_discovery_phase()
        discovery.agents.append({"type": "data-analyst", "count": 2})
        self.phases.append(discovery)

        # Design phase with data architecture
        self.phases.append(self.add_design_phase(["database", "security"]))

        # Data pipeline design
        self.phases.append(
            WorkflowPhase(
                phase_id="pipeline_design",
                phase_name="Pipeline Architecture",
                phase_type="design",
                agents=[
                    {"type": "data-architect", "count": 2},
                    {"type": "etl-specialist", "count": 1},
                ],
                dependencies=["design"],
                quality_gates=["data_flow", "scalability", "fault_tolerance"],
                expected_outputs=["pipeline_design.md", "data_flow_diagram.md"],
            )
        )

        # Implementation of pipeline stages
        self.phases.extend(
            self.add_implementation_phase(
                ["ingestion", "transformation", "storage", "orchestration"]
            )
        )

        # Data quality phase
        self.phases.append(
            WorkflowPhase(
                phase_id="data_quality",
                phase_name="Data Quality & Validation",
                phase_type="qa",
                agents=[
                    {"type": "data-quality-analyst", "count": 2},
                    {"type": "qa-testing-guru", "count": 1},
                ],
                dependencies=["implementation_transformation"],
                quality_gates=[
                    "data_validation",
                    "quality_metrics",
                    "performance_benchmarks",
                ],
                expected_outputs=["data_quality_report.md", "validation_rules.yaml"],
            )
        )

        # Performance optimization
        self.phases.append(
            WorkflowPhase(
                phase_id="optimization",
                phase_name="Performance Optimization",
                phase_type="implementation",
                agents=[
                    {"type": "performance-optimizer", "count": 2},
                    {"type": "data-engineer", "count": 1},
                ],
                dependencies=["data_quality"],
                quality_gates=["throughput_targets", "latency_requirements"],
                expected_outputs=["performance_report.md", "optimization_config.yaml"],
            )
        )

        # Documentation
        self.phases.append(self.add_documentation_phase())

        # Deployment with scheduling
        deployment = self.add_deployment_phase()
        deployment.expected_outputs.extend(["airflow_dags/", "schedule_config.yaml"])
        self.phases.append(deployment)

        return self.phases


class SDLCTemplateSystem:
    """Main template system for generating SDLC workflows"""

    def __init__(self):
        self.templates = {
            "backend_api": BackendAPITemplate,
            "frontend_app": FrontendApplicationTemplate,
            "fullstack_app": FullStackApplicationTemplate,
            "cli_tool": CLIToolTemplate,
            "library_package": LibraryPackageTemplate,
            "integration_connector": IntegrationConnectorTemplate,
            "data_pipeline": DataPipelineTemplate,
        }
        self.custom_templates = {}

    def register_custom_template(self, name: str, template_class: type):
        """Register a custom template"""
        if not issubclass(template_class, BaseTemplate):
            raise ValueError("Custom template must inherit from BaseTemplate")
        self.custom_templates[name] = template_class

    def get_available_templates(self) -> List[str]:
        """Get list of all available templates"""
        return list(self.templates.keys()) + list(self.custom_templates.keys())

    def select_template(self, project_type: str, project_specs: Dict[str, Any]) -> str:
        """Select appropriate template based on project specifications"""
        # Direct match
        if project_type in self.templates or project_type in self.custom_templates:
            return project_type

        # Intelligent selection based on specs
        indicators = {
            "backend_api": ["api", "rest", "graphql", "microservice", "backend"],
            "frontend_app": ["ui", "frontend", "react", "vue", "angular", "spa"],
            "fullstack_app": ["fullstack", "webapp", "application"],
            "cli_tool": ["cli", "command", "terminal", "console"],
            "library_package": ["library", "package", "sdk", "framework"],
            "integration_connector": ["integration", "connector", "adapter", "bridge"],
            "data_pipeline": ["etl", "pipeline", "data", "streaming", "batch"],
        }

        project_desc = str(project_specs.get("description", "")).lower()
        project_tech = str(project_specs.get("technology_stack", "")).lower()

        scores = {}
        for template, keywords in indicators.items():
            score = sum(
                1 for kw in keywords if kw in project_desc or kw in project_tech
            )
            if score > 0:
                scores[template] = score

        if scores:
            return max(scores, key=scores.get)

        # Default to backend API for unknown types
        return "backend_api"

    def generate_workflow(
        self,
        project_name: str,
        project_type: str,
        complexity: str = "medium",
        specifications: Dict[str, Any] = None,
        customizations: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Generate a complete SDLC workflow"""

        # Select template
        template_type = self.select_template(project_type, specifications or {})

        # Get template class
        if template_type in self.templates:
            template_class = self.templates[template_type]
        elif template_type in self.custom_templates:
            template_class = self.custom_templates[template_type]
        else:
            raise ValueError(f"Unknown template type: {template_type}")

        # Create template instance
        template = template_class(project_name, complexity)

        # Build workflow
        template.build_workflow()

        # Apply customizations
        if customizations:
            self._apply_customizations(template, customizations)

        # Inject context from specifications
        if specifications:
            self._inject_context(template, specifications)

        # Convert to orchestrator format
        workflow = template.to_orchestrator_format()

        # Add metadata
        workflow["metadata"].update(
            {
                "template_type": template_type,
                "specifications": specifications,
                "customizations": customizations,
            }
        )

        return workflow

    def _apply_customizations(
        self, template: BaseTemplate, customizations: Dict[str, Any]
    ):
        """Apply customizations to template"""
        # Add custom phases
        if "additional_phases" in customizations:
            for phase_config in customizations["additional_phases"]:
                phase = WorkflowPhase(**phase_config)
                template.phases.append(phase)

        # Modify existing phases
        if "phase_modifications" in customizations:
            for phase_id, modifications in customizations[
                "phase_modifications"
            ].items():
                for phase in template.phases:
                    if phase.phase_id == phase_id:
                        for key, value in modifications.items():
                            setattr(phase, key, value)

        # Add quality gates
        if "additional_quality_gates" in customizations:
            for phase in template.phases:
                phase.quality_gates.extend(customizations["additional_quality_gates"])

        # Scale agents
        if "agent_scaling_factor" in customizations:
            factor = customizations["agent_scaling_factor"]
            for phase in template.phases:
                for agent in phase.agents:
                    agent["count"] = max(1, int(agent["count"] * factor))

    def _inject_context(self, template: BaseTemplate, specifications: Dict[str, Any]):
        """Inject context from specifications into workflow"""
        # Add technology-specific context
        if "technology_stack" in specifications:
            tech_stack = specifications["technology_stack"]
            for phase in template.phases:
                phase.context_requirements.append(f"technology_stack: {tech_stack}")

        # Add requirements context
        if "requirements" in specifications:
            for phase in template.phases:
                if phase.phase_type in ["design", "implementation"]:
                    phase.context_requirements.append("project_requirements")

        # Add integration points
        if "integrations" in specifications:
            for phase in template.phases:
                if phase.phase_type == "implementation":
                    phase.context_requirements.append("integration_specifications")

    def validate_workflow(self, workflow: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate generated workflow"""
        issues = []

        # Check for required fields
        required_fields = ["workflow_id", "metadata", "phases", "tasks"]
        for field in required_fields:
            if field not in workflow:
                issues.append(f"Missing required field: {field}")

        # Validate phases
        if "phases" in workflow:
            phase_ids = set()
            for phase in workflow["phases"]:
                if phase["phase_id"] in phase_ids:
                    issues.append(f"Duplicate phase ID: {phase['phase_id']}")
                phase_ids.add(phase["phase_id"])

                # Check dependencies exist
                for dep in phase.get("dependencies", []):
                    if dep not in phase_ids and not dep.endswith("*"):
                        issues.append(
                            f"Unknown dependency: {dep} in phase {phase['phase_id']}"
                        )

        # Validate tasks
        if "tasks" in workflow:
            task_ids = set()
            for task in workflow["tasks"]:
                if task["task_id"] in task_ids:
                    issues.append(f"Duplicate task ID: {task['task_id']}")
                task_ids.add(task["task_id"])

        # Check execution config
        if "execution_config" in workflow:
            config = workflow["execution_config"]
            if config.get("max_parallel_agents", 0) < 1:
                issues.append("max_parallel_agents must be at least 1")

        return len(issues) == 0, issues

    def export_workflow(self, workflow: Dict[str, Any], output_path: Path) -> Path:
        """Export workflow to JSON file"""
        output_file = output_path / f"{workflow['workflow_id']}.json"

        with open(output_file, "w") as f:
            json.dump(workflow, f, indent=2, default=str)

        logger.info(f"Workflow exported to: {output_file}")
        return output_file


def main():
    """Example usage of SDLC Template System"""
    system = SDLCTemplateSystem()

    # Example 1: Generate backend API workflow
    workflow = system.generate_workflow(
        project_name="user-service",
        project_type="backend_api",
        complexity="high",
        specifications={
            "technology_stack": "Python FastAPI PostgreSQL Redis",
            "requirements": ["authentication", "authorization", "crud operations"],
            "integrations": ["payment_gateway", "email_service"],
        },
        customizations={
            "agent_scaling_factor": 1.2,
            "additional_quality_gates": ["code_coverage_90", "zero_security_issues"],
        },
    )

    # Validate workflow
    is_valid, issues = system.validate_workflow(workflow)
    if is_valid:
        print(
            f"✅ Generated valid workflow with {len(workflow['tasks'])} tasks across {len(workflow['phases'])} phases"
        )
    else:
        print(f"❌ Workflow validation failed: {issues}")

    # Export workflow
    output_path = Path("./workflows")
    output_path.mkdir(exist_ok=True)
    exported_file = system.export_workflow(workflow, output_path)
    print(f"📁 Workflow exported to: {exported_file}")

    # Show available templates
    print(f"\n📋 Available templates: {', '.join(system.get_available_templates())}")


if __name__ == "__main__":
    main()
