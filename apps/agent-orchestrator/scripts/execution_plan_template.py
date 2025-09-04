#!/usr/bin/env python3
"""
Execution Plan Template and Utilities

Provides templates and utility functions for agents to generate execution plans
for the orchestrator system. Includes common patterns and examples.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from execution_plan_schema import (
    ExecutionMode,
    ExecutionPhase,
    ExecutionPlan,
    QualityGate,
    QualityGateType,
    TaskDefinition,
    TaskType,
    ValidationLevel,
)


class ExecutionPlanBuilder:
    """Builder class for creating execution plans"""

    def __init__(self, plan_id: str = None, name: str = "", description: str = ""):
        self.plan_id = plan_id or f"plan-{str(uuid.uuid4())[:8]}"
        self.plan = ExecutionPlan(
            plan_id=self.plan_id,
            name=name,
            description=description,
            created_at=datetime.now().isoformat(),
        )

    def set_execution_mode(
        self, mode: ExecutionMode, max_parallel: int = 10
    ) -> "ExecutionPlanBuilder":
        """Set execution mode and parallel limits"""
        self.plan.execution_mode = mode
        self.plan.max_parallel_tasks = max_parallel
        return self

    def enable_features(
        self,
        quality_gates: bool = True,
        monitoring: bool = True,
        optimizations: bool = True,
    ) -> "ExecutionPlanBuilder":
        """Enable/disable orchestrator features"""
        self.plan.enable_quality_gates = quality_gates
        self.plan.enable_monitoring = monitoring
        self.plan.use_optimizations = optimizations
        return self

    def add_task(
        self,
        task_id: str,
        task_type: TaskType,
        prompt: str,
        dependencies: List[str] = None,
        **kwargs,
    ) -> "ExecutionPlanBuilder":
        """Add a task to the execution plan"""
        task = TaskDefinition(
            task_id=task_id,
            task_type=task_type,
            prompt=prompt,
            dependencies=dependencies or [],
            **kwargs,
        )
        self.plan.tasks.append(task)
        return self

    def add_phase(
        self,
        phase_id: str,
        name: str,
        description: str,
        gates: List[str] = None,
        **kwargs,
    ) -> "ExecutionPlanBuilder":
        """Add an execution phase"""
        phase = ExecutionPhase(
            phase_id=phase_id,
            name=name,
            description=description,
            gates=gates or [],
            **kwargs,
        )
        self.plan.phases.append(phase)
        return self

    def add_quality_gate(
        self,
        gate_id: str,
        name: str,
        description: str,
        gate_type: QualityGateType,
        config: Dict[str, Any],
        **kwargs,
    ) -> "ExecutionPlanBuilder":
        """Add a quality gate"""
        gate = QualityGate(
            gate_id=gate_id,
            name=name,
            description=description,
            gate_type=gate_type,
            config=config,
            **kwargs,
        )
        self.plan.quality_gates.append(gate)
        return self

    def set_output_directory(self, directory: str) -> "ExecutionPlanBuilder":
        """Set output directory for results"""
        self.plan.output_directory = directory
        return self

    def build(self) -> ExecutionPlan:
        """Build and validate the execution plan"""
        errors = self.plan.validate()
        if errors:
            raise ValueError(f"Invalid execution plan: {', '.join(errors)}")
        return self.plan


def create_simple_parallel_plan(
    name: str, tasks: List[Dict[str, Any]], description: str = ""
) -> ExecutionPlan:
    """
    Create a simple parallel execution plan

    Args:
        name: Plan name
        tasks: List of task dictionaries with task_id, task_type, and prompt
        description: Plan description
    """
    builder = ExecutionPlanBuilder(name=name, description=description)
    builder.set_execution_mode(ExecutionMode.PARALLEL, max_parallel=len(tasks))

    for task_data in tasks:
        builder.add_task(
            task_id=task_data["task_id"],
            task_type=TaskType(task_data["task_type"]),
            prompt=task_data["prompt"],
            dependencies=task_data.get("dependencies", []),
            context=task_data.get("context", {}),
            validation_level=ValidationLevel(
                task_data.get("validation_level", "standard")
            ),
        )

    return builder.build()


def create_sdlc_pipeline_plan(project_name: str, requirements: str) -> ExecutionPlan:
    """
    Create a complete SDLC pipeline execution plan

    Args:
        project_name: Name of the project
        requirements: Project requirements description
    """
    builder = ExecutionPlanBuilder(
        name=f"{project_name} SDLC Pipeline",
        description=f"Complete software development lifecycle for {project_name}",
    )

    # Configure for SDLC phases
    builder.set_execution_mode(ExecutionMode.MIXED, max_parallel=3)
    builder.enable_features(quality_gates=True, monitoring=True)

    # Add quality gates for each phase
    phases = [
        ("discovery", "Discovery Complete", "Requirements and research completed"),
        ("design", "Design Complete", "Architecture and design approved"),
        ("development", "Development Complete", "Code implementation finished"),
        ("testing", "Testing Complete", "All tests passing"),
        ("deployment", "Deployment Ready", "Application deployed successfully"),
    ]

    for phase_id, gate_name, gate_desc in phases:
        builder.add_quality_gate(
            gate_id=f"{phase_id}_complete",
            name=gate_name,
            description=gate_desc,
            gate_type=QualityGateType.CUSTOM,
            config={"validation_type": "phase_completion"},
        )

        builder.add_phase(
            phase_id=phase_id,
            name=gate_name.replace(" Complete", ""),
            description=f"{phase_id.title()} phase",
            gates=[f"{phase_id}_complete"],
        )

    # Discovery phase tasks
    builder.add_task(
        task_id="requirements_analysis",
        task_type=TaskType.REQUIREMENTS_ANALYST,
        prompt=f"Analyze and document detailed requirements for: {requirements}",
        phase_id="discovery",
        quality_gates=["discovery_complete"],
    )

    builder.add_task(
        task_id="research_existing_solutions",
        task_type=TaskType.SDLC_DISCOVERY,
        prompt=f"Research existing solutions and technologies for: {requirements}",
        phase_id="discovery",
        quality_gates=["discovery_complete"],
    )

    # Design phase tasks (depends on discovery)
    builder.add_task(
        task_id="system_architecture",
        task_type=TaskType.SOLUTION_ARCHITECT,
        prompt="Design system architecture based on requirements analysis",
        dependencies=["requirements_analysis", "research_existing_solutions"],
        phase_id="design",
        quality_gates=["design_complete"],
    )

    builder.add_task(
        task_id="technical_design",
        task_type=TaskType.SDLC_DESIGN,
        prompt="Create detailed technical design and specifications",
        dependencies=["system_architecture"],
        phase_id="design",
        quality_gates=["design_complete"],
    )

    # Development phase (depends on design)
    builder.add_task(
        task_id="core_development",
        task_type=TaskType.SDLC_DEVELOPMENT,
        prompt="Implement core application functionality based on technical design",
        dependencies=["technical_design"],
        phase_id="development",
        quality_gates=["development_complete"],
        estimated_duration_minutes=120,
    )

    builder.add_task(
        task_id="api_implementation",
        task_type=TaskType.API_INTEGRATION_SPECIALIST,
        prompt="Implement API endpoints and integrations",
        dependencies=["technical_design"],
        phase_id="development",
        quality_gates=["development_complete"],
        estimated_duration_minutes=90,
    )

    # Testing phase (depends on development)
    builder.add_task(
        task_id="comprehensive_testing",
        task_type=TaskType.QA_TESTING_GURU,
        prompt="Create and execute comprehensive test suite",
        dependencies=["core_development", "api_implementation"],
        phase_id="testing",
        quality_gates=["testing_complete"],
        estimated_duration_minutes=60,
    )

    builder.add_task(
        task_id="security_testing",
        task_type=TaskType.SECURITY_ARCHITECT,
        prompt="Perform security analysis and testing",
        dependencies=["core_development", "api_implementation"],
        phase_id="testing",
        quality_gates=["testing_complete"],
    )

    # Deployment phase (depends on testing)
    builder.add_task(
        task_id="deployment_setup",
        task_type=TaskType.SDLC_DEPLOYMENT,
        prompt="Set up deployment pipeline and infrastructure",
        dependencies=["comprehensive_testing", "security_testing"],
        phase_id="deployment",
        quality_gates=["deployment_complete"],
    )

    builder.add_task(
        task_id="documentation",
        task_type=TaskType.TECHNICAL_WRITER,
        prompt="Create comprehensive project documentation",
        dependencies=["comprehensive_testing"],
        phase_id="deployment",
        quality_gates=["deployment_complete"],
    )

    return builder.build()


def create_database_optimization_plan(
    database_type: str, performance_issues: str
) -> ExecutionPlan:
    """
    Create execution plan for database optimization tasks

    Args:
        database_type: Type of database (PostgreSQL, MongoDB, etc.)
        performance_issues: Description of performance issues
    """
    builder = ExecutionPlanBuilder(
        name=f"{database_type} Performance Optimization",
        description=f"Optimize {database_type} database performance: {performance_issues}",
    )

    builder.set_execution_mode(ExecutionMode.MIXED, max_parallel=2)

    # Add database readiness quality gate
    builder.add_quality_gate(
        gate_id="database_accessible",
        name="Database Accessible",
        description="Database is accessible and responding",
        gate_type=QualityGateType.DATABASE,
        config={"connection_check": True, "timeout_seconds": 30},
    )

    # Analysis tasks (parallel)
    builder.add_task(
        task_id="performance_analysis",
        task_type=TaskType.PERFORMANCE_OPTIMIZER,
        prompt=f"Analyze {database_type} performance issues: {performance_issues}",
        quality_gates=["database_accessible"],
    )

    builder.add_task(
        task_id="query_analysis",
        task_type=TaskType.DATABASE_SPECIALIST,
        prompt=f"Analyze slow queries and identify optimization opportunities in {database_type}",
        quality_gates=["database_accessible"],
    )

    # Optimization implementation (depends on analysis)
    builder.add_task(
        task_id="implement_optimizations",
        task_type=TaskType.DATABASE_SPECIALIST,
        prompt="Implement database optimizations based on analysis results",
        dependencies=["performance_analysis", "query_analysis"],
        validation_level=ValidationLevel.STRICT,
    )

    # Validation (depends on implementation)
    builder.add_task(
        task_id="performance_validation",
        task_type=TaskType.PERFORMANCE_OPTIMIZER,
        prompt="Validate performance improvements and create benchmark report",
        dependencies=["implement_optimizations"],
        validation_level=ValidationLevel.STRICT,
    )

    return builder.build()


def create_api_development_plan(
    api_name: str, endpoints: List[str], requirements: str
) -> ExecutionPlan:
    """
    Create execution plan for API development

    Args:
        api_name: Name of the API
        endpoints: List of endpoint paths to implement
        requirements: API requirements and specifications
    """
    builder = ExecutionPlanBuilder(
        name=f"{api_name} API Development",
        description=f"Develop {api_name} API with endpoints: {', '.join(endpoints)}",
    )

    builder.set_execution_mode(ExecutionMode.PARALLEL, max_parallel=3)

    # Design phase
    builder.add_task(
        task_id="api_design",
        task_type=TaskType.SOLUTION_ARCHITECT,
        prompt=f"Design {api_name} API architecture and specifications: {requirements}",
        validation_level=ValidationLevel.STANDARD,
    )

    # Parallel implementation of endpoint groups
    endpoint_groups = [endpoints[i : i + 3] for i in range(0, len(endpoints), 3)]

    for i, group in enumerate(endpoint_groups):
        builder.add_task(
            task_id=f"implement_endpoints_group_{i+1}",
            task_type=TaskType.API_INTEGRATION_SPECIALIST,
            prompt=f"Implement API endpoints: {', '.join(group)}",
            dependencies=["api_design"],
            context={"endpoint_group": group},
            estimated_duration_minutes=60,
        )

    # Integration testing
    group_deps = [
        f"implement_endpoints_group_{i+1}" for i in range(len(endpoint_groups))
    ]
    builder.add_task(
        task_id="api_testing",
        task_type=TaskType.QA_TESTING_GURU,
        prompt=f"Create comprehensive API tests for {api_name}",
        dependencies=group_deps,
        validation_level=ValidationLevel.STRICT,
    )

    # Documentation
    builder.add_task(
        task_id="api_documentation",
        task_type=TaskType.TECHNICAL_WRITER,
        prompt=f"Create API documentation for {api_name}",
        dependencies=group_deps,
        output_files=["api_docs.md", "openapi.yaml"],
    )

    return builder.build()


# Template examples for common patterns
TEMPLATE_EXAMPLES = {
    "simple_parallel": {
        "description": "Simple parallel task execution",
        "example": """
# Simple parallel execution of independent tasks
plan = create_simple_parallel_plan(
    name="Data Processing Pipeline",
    tasks=[
        {
            "task_id": "extract_data",
            "task_type": "general-purpose",
            "prompt": "Extract data from source systems"
        },
        {
            "task_id": "transform_data",
            "task_type": "general-purpose",
            "prompt": "Transform and clean extracted data"
        },
        {
            "task_id": "validate_data",
            "task_type": "qa-testing-guru",
            "prompt": "Validate data quality and completeness"
        }
    ]
)
        """,
    },
    "dependency_chain": {
        "description": "Sequential tasks with dependencies",
        "example": """
# Sequential dependency chain
builder = ExecutionPlanBuilder(name="Build and Deploy")
builder.add_task("build", TaskType.DEVELOPMENT_SPECIALIST, "Build application")
builder.add_task("test", TaskType.QA_TESTING_GURU, "Run test suite", dependencies=["build"])
builder.add_task("deploy", TaskType.SDLC_DEPLOYMENT, "Deploy to production", dependencies=["test"])
plan = builder.build()
        """,
    },
    "quality_gates": {
        "description": "Using quality gates for validation",
        "example": """
# Quality gate validation example
builder = ExecutionPlanBuilder(name="Database Migration")
builder.add_quality_gate(
    "database_ready", "Database Ready", "Database is accessible",
    QualityGateType.DATABASE, {"connection_string": "postgresql://..."}
)
builder.add_task("migration", TaskType.DATABASE_SPECIALIST,
                "Run database migrations", quality_gates=["database_ready"])
plan = builder.build()
        """,
    },
}


def get_template_example(template_name: str) -> str:
    """Get code example for a template pattern"""
    template = TEMPLATE_EXAMPLES.get(template_name)
    if not template:
        available = ", ".join(TEMPLATE_EXAMPLES.keys())
        raise ValueError(f"Unknown template: {template_name}. Available: {available}")

    return template["example"].strip()


def list_template_patterns() -> Dict[str, str]:
    """List available template patterns with descriptions"""
    return {name: info["description"] for name, info in TEMPLATE_EXAMPLES.items()}
