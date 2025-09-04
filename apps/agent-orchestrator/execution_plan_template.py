"""
ExecutionPlan Template System
Provides ExecutionPlanBuilder and pre-built templates for common patterns
"""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from execution_plan_schema import (
        ExecutionMode,
        ExecutionPhase,
        ExecutionPlan,
        QualityGate,
        QualityGateType,
        ResourceRequirements,
        TaskContext,
        TaskDefinition,
        TaskPriority,
        TaskType,
        ValidationLevel,
        create_quality_gate,
        create_task_definition,
    )
except ImportError:
    from .execution_plan_schema import (
        ExecutionMode,
        ExecutionPhase,
        ExecutionPlan,
        QualityGate,
        QualityGateType,
        ResourceRequirements,
        TaskContext,
        TaskDefinition,
        TaskPriority,
        TaskType,
        ValidationLevel,
        create_quality_gate,
        create_task_definition,
    )


class ExecutionPlanBuilder:
    """Fluent API builder for ExecutionPlans"""

    def __init__(self, name: str, description: str = "", plan_id: str = None):
        self.plan_id = plan_id or f"plan_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.description = description or f"ExecutionPlan: {name}"

        # Collections
        self._tasks: List[TaskDefinition] = []
        self._quality_gates: List[QualityGate] = []
        self._phases: List[ExecutionPhase] = []

        # Configuration
        self._execution_mode = ExecutionMode.PARALLEL
        self._max_parallel = 5
        self._enable_quality_gates = True
        self._enable_monitoring = True
        self._use_optimizations = True
        self._output_directory = "./output"
        self._fallback_strategy = "continue"

        # Metadata
        self._tags: List[str] = []
        self._metadata: Dict[str, Any] = {}
        self._created_by = None

    def set_plan_id(self, plan_id: str) -> "ExecutionPlanBuilder":
        """Set custom plan ID"""
        self.plan_id = plan_id
        return self

    def set_execution_mode(
        self, mode: Union[ExecutionMode, str], max_parallel: int = 5
    ) -> "ExecutionPlanBuilder":
        """Set execution mode and parallel limit"""
        if isinstance(mode, str):
            mode = ExecutionMode(mode)
        self._execution_mode = mode
        self._max_parallel = max_parallel
        return self

    def set_quality_gates_enabled(self, enabled: bool) -> "ExecutionPlanBuilder":
        """Enable or disable quality gates"""
        self._enable_quality_gates = enabled
        return self

    def set_monitoring_enabled(self, enabled: bool) -> "ExecutionPlanBuilder":
        """Enable or disable monitoring"""
        self._enable_monitoring = enabled
        return self

    def set_optimizations_enabled(self, enabled: bool) -> "ExecutionPlanBuilder":
        """Enable or disable optimizations"""
        self._use_optimizations = enabled
        return self

    def set_output_directory(self, directory: str) -> "ExecutionPlanBuilder":
        """Set output directory for results"""
        self._output_directory = directory
        return self

    def set_fallback_strategy(self, strategy: str) -> "ExecutionPlanBuilder":
        """Set fallback strategy: continue, stop, retry"""
        if strategy not in ["continue", "stop", "retry"]:
            raise ValueError("Fallback strategy must be 'continue', 'stop', or 'retry'")
        self._fallback_strategy = strategy
        return self

    def add_tag(self, tag: str) -> "ExecutionPlanBuilder":
        """Add tag to plan"""
        if tag not in self._tags:
            self._tags.append(tag)
        return self

    def add_tags(self, tags: List[str]) -> "ExecutionPlanBuilder":
        """Add multiple tags"""
        for tag in tags:
            self.add_tag(tag)
        return self

    def set_metadata(self, key: str, value: Any) -> "ExecutionPlanBuilder":
        """Set metadata property"""
        self._metadata[key] = value
        return self

    def set_created_by(self, created_by: str) -> "ExecutionPlanBuilder":
        """Set creator information"""
        self._created_by = created_by
        return self

    def add_task(
        self,
        task_id: str,
        task_type: Union[TaskType, str],
        prompt: str,
        dependencies: List[str] = None,
        quality_gates: List[str] = None,
        phase_id: str = None,
        context: Union[TaskContext, Dict[str, Any]] = None,
        validation_level: Union[ValidationLevel, str] = ValidationLevel.STANDARD,
        priority: Union[TaskPriority, str, int] = TaskPriority.NORMAL,
        timeout_seconds: int = 1800,
        max_retries: int = 2,
        background_execution: bool = False,
        monitoring_enabled: bool = True,
        estimated_duration_minutes: int = None,
        **kwargs,
    ) -> "ExecutionPlanBuilder":
        """Add task to the plan"""

        # Check for duplicate task IDs
        existing_task_ids = {task.task_id for task in self._tasks}
        if task_id in existing_task_ids:
            raise ValueError(
                f"Duplicate task ID '{task_id}' - task IDs must be unique within a plan"
            )

        # Convert context dict to TaskContext if needed
        if isinstance(context, dict):
            context = TaskContext(
                working_directory=context.get("working_directory"),
                environment_variables=context.get("environment_variables", {}),
                files_to_read=context.get("files_to_read", []),
                output_directory=context.get("output_directory"),
                custom_properties=context.get("custom_properties", {}),
            )

        task = TaskDefinition(
            task_id=task_id,
            task_type=task_type,
            prompt=prompt,
            dependencies=dependencies or [],
            quality_gates=quality_gates or [],
            phase_id=phase_id,
            context=context,
            validation_level=validation_level,
            priority=priority,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            background_execution=background_execution,
            monitoring_enabled=monitoring_enabled,
            estimated_duration_minutes=estimated_duration_minutes,
            resource_requirements=kwargs,
        )

        self._tasks.append(task)
        return self

    def add_quality_gate(
        self,
        gate_id: str,
        name: str,
        description: str,
        gate_type: Union[QualityGateType, str],
        config: Dict[str, Any] = None,
        dependencies: List[str] = None,
        timeout_seconds: int = 300,
        enabled: bool = True,
        critical: bool = False,
    ) -> "ExecutionPlanBuilder":
        """Add quality gate to the plan"""

        gate = create_quality_gate(
            gate_id=gate_id,
            name=name,
            description=description,
            gate_type=gate_type,
            config=config or {},
            dependencies=dependencies or [],
            timeout_seconds=timeout_seconds,
            enabled=enabled,
            critical=critical,
        )

        self._quality_gates.append(gate)
        return self

    def add_phase(
        self,
        phase_id: str,
        name: str,
        description: str,
        gates: List[str] = None,
        parallel_execution: bool = True,
        max_parallel: int = 3,
        timeout_seconds: int = 3600,
        depends_on_phases: List[str] = None,
    ) -> "ExecutionPlanBuilder":
        """Add execution phase to the plan"""

        phase = ExecutionPhase(
            phase_id=phase_id,
            name=name,
            description=description,
            gates=gates or [],
            parallel_execution=parallel_execution,
            max_parallel=max_parallel,
            timeout_seconds=timeout_seconds,
            depends_on_phases=depends_on_phases or [],
        )

        self._phases.append(phase)
        return self

    def add_parallel_tasks(
        self,
        task_configs: List[Dict[str, Any]],
        shared_dependencies: List[str] = None,
        shared_phase: str = None,
    ) -> "ExecutionPlanBuilder":
        """Add multiple parallel tasks with shared configuration"""
        shared_dependencies = shared_dependencies or []

        for config in task_configs:
            # Merge shared dependencies
            task_deps = config.get("dependencies", [])
            config["dependencies"] = list(set(task_deps + shared_dependencies))

            # Set shared phase if provided
            if shared_phase and "phase_id" not in config:
                config["phase_id"] = shared_phase

            self.add_task(**config)

        return self

    def add_sequential_tasks(
        self,
        task_configs: List[Dict[str, Any]],
        shared_dependencies: List[str] = None,
        shared_phase: str = None,
    ) -> "ExecutionPlanBuilder":
        """Add sequential tasks where each depends on the previous"""
        shared_dependencies = shared_dependencies or []
        previous_task_id = None

        for config in task_configs:
            # Build dependency chain
            task_deps = config.get("dependencies", [])
            if previous_task_id:
                task_deps.append(previous_task_id)
            config["dependencies"] = list(set(task_deps + shared_dependencies))

            # Set shared phase if provided
            if shared_phase and "phase_id" not in config:
                config["phase_id"] = shared_phase

            self.add_task(**config)
            previous_task_id = config["task_id"]

        return self

    def build(self, validate: bool = True) -> ExecutionPlan:
        """Build the final ExecutionPlan with optional validation"""

        # Estimate resource requirements
        resource_requirements = ResourceRequirements(
            estimated_tokens=min(len(self._tasks), self._max_parallel),
            peak_parallel=self._max_parallel,
            memory_requirements_mb=512 * len(self._tasks),
            estimated_duration_minutes=sum(
                task.estimated_duration_minutes or 30 for task in self._tasks
            ),
        )

        plan = ExecutionPlan(
            plan_id=self.plan_id,
            name=self.name,
            description=self.description,
            tasks=self._tasks,
            execution_mode=self._execution_mode,
            max_parallel_tasks=self._max_parallel,
            enable_quality_gates=self._enable_quality_gates,
            enable_monitoring=self._enable_monitoring,
            use_optimizations=self._use_optimizations,
            quality_gates=self._quality_gates,
            phases=self._phases,
            resource_requirements=resource_requirements,
            output_directory=self._output_directory,
            fallback_strategy=self._fallback_strategy,
            created_by=self._created_by,
            created_at=datetime.now().isoformat(),
            tags=self._tags,
            metadata=self._metadata,
        )

        # Perform comprehensive validation if requested
        if validate:
            try:
                validation_result = plan.validate_comprehensive()
                if not validation_result.is_valid:
                    # Log warnings but don't fail for non-critical errors
                    import logging

                    logger = logging.getLogger(__name__)

                    critical_errors = [
                        e
                        for e in validation_result.errors
                        if e.error_type.value
                        in [
                            "circular_dependency",
                            "invalid_dependency_reference",
                            "empty_task_list",
                        ]
                    ]

                    if critical_errors:
                        error_messages = [str(e) for e in critical_errors]
                        raise ValueError(
                            f"Critical validation errors in ExecutionPlan:\n"
                            + "\n".join(error_messages)
                        )
                    else:
                        # Log non-critical errors as warnings
                        for error in validation_result.errors:
                            logger.warning(f"ExecutionPlan validation warning: {error}")

                    for warning in validation_result.warnings:
                        logger.info(f"ExecutionPlan optimization suggestion: {warning}")

            except ImportError:
                # Validation module not available, skip validation
                import logging

                logging.getLogger(__name__).warning(
                    "Advanced validation not available - skipping comprehensive validation"
                )

        return plan


# Pre-built template functions
def create_simple_parallel_plan(
    name: str, description: str, tasks: List[Dict[str, Any]], max_parallel: int = 3
) -> ExecutionPlan:
    """Create simple plan with parallel tasks"""
    builder = ExecutionPlanBuilder(name, description)
    builder.set_execution_mode(ExecutionMode.PARALLEL, max_parallel)

    for task_config in tasks:
        builder.add_task(**task_config)

    return builder.build()


def create_sdlc_pipeline_plan(
    project_name: str,
    requirements: str,
    tech_stack: Dict[str, str] = None,
    enable_deployment: bool = True,
) -> ExecutionPlan:
    """Create complete SDLC pipeline plan"""

    builder = ExecutionPlanBuilder(
        name=f"{project_name} SDLC Pipeline",
        description=f"Complete software development lifecycle for {project_name}",
        plan_id=f"sdlc_{project_name.lower().replace(' ', '_')}",
    )

    builder.set_execution_mode(ExecutionMode.MIXED, 5)
    builder.add_tags(["sdlc", "pipeline", "production"])

    tech_stack = tech_stack or {}
    tech_context = TaskContext(custom_properties={"tech_stack": tech_stack})

    # Discovery Phase
    builder.add_phase(
        "discovery", "Discovery & Planning", "Requirements analysis and system design"
    )

    builder.add_task(
        "requirements_analysis",
        TaskType.REQUIREMENTS_ANALYST,
        f"Analyze and document requirements for {project_name}: {requirements}",
        phase_id="discovery",
        context=tech_context,
        estimated_duration_minutes=45,
        priority=TaskPriority.HIGH,
    )

    builder.add_task(
        "system_architecture",
        TaskType.SOLUTION_ARCHITECT,
        f"Design system architecture for {project_name} based on requirements",
        dependencies=["requirements_analysis"],
        phase_id="discovery",
        context=tech_context,
        estimated_duration_minutes=60,
        priority=TaskPriority.HIGH,
    )

    # Design Phase
    builder.add_phase("design", "Design & Planning", "Detailed design and planning")

    builder.add_task(
        "api_design",
        TaskType.API_INTEGRATION_SPECIALIST,
        "Design API specifications and contracts",
        dependencies=["system_architecture"],
        phase_id="design",
        estimated_duration_minutes=45,
    )

    builder.add_task(
        "database_design",
        TaskType.DATABASE_SPECIALIST,
        "Design database schema and data models",
        dependencies=["system_architecture"],
        phase_id="design",
        estimated_duration_minutes=45,
    )

    # Development Phase - Parallel implementation
    builder.add_phase("development", "Implementation", "Core development work")

    dev_tasks = [
        {
            "task_id": "implement_backend",
            "task_type": TaskType.DEVELOPMENT_SPECIALIST,
            "prompt": "Implement backend services and API endpoints",
            "dependencies": ["api_design", "database_design"],
            "phase_id": "development",
            "estimated_duration_minutes": 120,
            "priority": TaskPriority.HIGH,
        },
        {
            "task_id": "implement_database",
            "task_type": TaskType.DATABASE_SPECIALIST,
            "prompt": "Implement database schema and migrations",
            "dependencies": ["database_design"],
            "phase_id": "development",
            "estimated_duration_minutes": 60,
        },
        {
            "task_id": "implement_frontend",
            "task_type": TaskType.DEVELOPMENT_SPECIALIST,
            "prompt": "Implement user interface and frontend components",
            "dependencies": ["api_design"],
            "phase_id": "development",
            "estimated_duration_minutes": 90,
        },
    ]

    builder.add_parallel_tasks(dev_tasks)

    # Testing Phase
    builder.add_phase("testing", "Quality Assurance", "Comprehensive testing")

    builder.add_quality_gate(
        "code_quality",
        "Code Quality Check",
        "Code passes quality standards",
        QualityGateType.CODE_QUALITY,
        {"min_score": 8.0},
    )

    builder.add_task(
        "unit_testing",
        TaskType.QA_TESTING_GURU,
        "Create and run comprehensive unit test suite",
        dependencies=["implement_backend", "implement_frontend"],
        phase_id="testing",
        quality_gates=["code_quality"],
        estimated_duration_minutes=90,
    )

    builder.add_task(
        "integration_testing",
        TaskType.QA_TESTING_GURU,
        "Perform integration testing across all components",
        dependencies=["unit_testing"],
        phase_id="testing",
        estimated_duration_minutes=60,
    )

    # Documentation Phase
    builder.add_task(
        "create_documentation",
        TaskType.TECHNICAL_WRITER,
        "Generate comprehensive project documentation",
        dependencies=["integration_testing"],
        estimated_duration_minutes=45,
    )

    # Deployment Phase (optional)
    if enable_deployment:
        builder.add_phase("deployment", "Deployment", "Production deployment")

        builder.add_quality_gate(
            "deployment_ready",
            "Deployment Ready",
            "All tests pass and documentation complete",
            QualityGateType.TEST_RESULTS,
            {"required_tests": ["unit_testing", "integration_testing"]},
        )

        builder.add_task(
            "deploy_to_production",
            TaskType.SDLC_DEPLOYMENT,
            "Deploy application to production environment",
            dependencies=["create_documentation"],
            phase_id="deployment",
            quality_gates=["deployment_ready"],
            estimated_duration_minutes=30,
            priority=TaskPriority.CRITICAL,
        )

    return builder.build()


def create_api_development_plan(
    api_name: str, endpoints: List[str], requirements: str, include_testing: bool = True
) -> ExecutionPlan:
    """Create API-focused development plan"""

    builder = ExecutionPlanBuilder(
        name=f"{api_name} Development",
        description=f"Complete API development plan for {api_name}",
        plan_id=f"api_{api_name.lower().replace(' ', '_')}",
    )

    builder.set_execution_mode(ExecutionMode.MIXED, 4)
    builder.add_tags(["api", "development", "rest"])

    # API Design
    builder.add_task(
        "api_specification",
        TaskType.API_INTEGRATION_SPECIALIST,
        f"Design comprehensive API specification for {api_name} with endpoints: {', '.join(endpoints)}. Requirements: {requirements}",
        estimated_duration_minutes=60,
        priority=TaskPriority.HIGH,
    )

    # Parallel endpoint implementation
    endpoint_tasks = []
    for i, endpoint in enumerate(endpoints):
        endpoint_tasks.append(
            {
                "task_id": f"implement_{endpoint.replace('/', '_').replace('{', '').replace('}', '').strip('_')}",
                "task_type": TaskType.DEVELOPMENT_SPECIALIST,
                "prompt": f"Implement {endpoint} endpoint according to API specification",
                "dependencies": ["api_specification"],
                "estimated_duration_minutes": 45,
            }
        )

    builder.add_parallel_tasks(endpoint_tasks)

    # Testing
    if include_testing:
        all_endpoint_tasks = [task["task_id"] for task in endpoint_tasks]

        builder.add_task(
            "api_testing",
            TaskType.QA_TESTING_GURU,
            "Create comprehensive API test suite covering all endpoints",
            dependencies=all_endpoint_tasks,
            estimated_duration_minutes=75,
        )

        builder.add_task(
            "performance_testing",
            TaskType.PERFORMANCE_OPTIMIZER,
            "Perform API performance testing and optimization",
            dependencies=["api_testing"],
            estimated_duration_minutes=45,
        )

    # Documentation
    final_deps = (
        ["api_testing"]
        if include_testing
        else [task["task_id"] for task in endpoint_tasks]
    )
    builder.add_task(
        "api_documentation",
        TaskType.TECHNICAL_WRITER,
        "Generate comprehensive API documentation with examples",
        dependencies=final_deps,
        estimated_duration_minutes=30,
    )

    return builder.build()


def create_database_optimization_plan(
    database_type: str,
    performance_issues: str,
    target_improvement: str = "50% performance improvement",
) -> ExecutionPlan:
    """Create database optimization plan"""

    builder = ExecutionPlanBuilder(
        name=f"{database_type} Optimization",
        description=f"Database optimization plan targeting {target_improvement}",
        plan_id=f"db_opt_{database_type.lower()}",
    )

    builder.set_execution_mode(ExecutionMode.MIXED, 3)
    builder.add_tags(["database", "optimization", "performance"])

    context = TaskContext(
        custom_properties={
            "database_type": database_type,
            "performance_issues": performance_issues,
            "target_improvement": target_improvement,
        }
    )

    # Analysis Phase - Parallel
    analysis_tasks = [
        {
            "task_id": "performance_analysis",
            "task_type": TaskType.PERFORMANCE_OPTIMIZER,
            "prompt": f"Analyze {database_type} performance issues: {performance_issues}",
            "context": context,
            "estimated_duration_minutes": 60,
        },
        {
            "task_id": "query_analysis",
            "task_type": TaskType.DATABASE_SPECIALIST,
            "prompt": f"Analyze slow queries and database usage patterns",
            "context": context,
            "estimated_duration_minutes": 45,
        },
        {
            "task_id": "schema_analysis",
            "task_type": TaskType.DATABASE_SPECIALIST,
            "prompt": f"Analyze database schema for optimization opportunities",
            "context": context,
            "estimated_duration_minutes": 30,
        },
    ]

    builder.add_parallel_tasks(analysis_tasks)

    # Implementation Phase
    builder.add_task(
        "implement_optimizations",
        TaskType.DATABASE_SPECIALIST,
        "Implement database optimizations based on analysis findings",
        dependencies=["performance_analysis", "query_analysis", "schema_analysis"],
        estimated_duration_minutes=90,
        priority=TaskPriority.HIGH,
    )

    # Validation Phase
    builder.add_task(
        "validate_improvements",
        TaskType.PERFORMANCE_OPTIMIZER,
        "Measure and validate performance improvements",
        dependencies=["implement_optimizations"],
        estimated_duration_minutes=45,
    )

    return builder.build()


def create_code_review_plan(
    codebase_path: str, focus_areas: List[str] = None, include_refactoring: bool = True
) -> ExecutionPlan:
    """Create comprehensive code review plan"""

    focus_areas = focus_areas or [
        "security",
        "performance",
        "maintainability",
        "best_practices",
    ]

    builder = ExecutionPlanBuilder(
        name="Comprehensive Code Review",
        description=f"Code review and analysis for {codebase_path}",
        plan_id="code_review_comprehensive",
    )

    builder.set_execution_mode(ExecutionMode.PARALLEL, 4)
    builder.add_tags(["code-review", "analysis", "quality"])

    context = TaskContext(
        working_directory=codebase_path, custom_properties={"focus_areas": focus_areas}
    )

    # Parallel analysis tasks
    review_tasks = [
        {
            "task_id": "security_review",
            "task_type": TaskType.SECURITY_ARCHITECT,
            "prompt": "Perform comprehensive security analysis of the codebase",
            "context": context,
            "estimated_duration_minutes": 60,
        },
        {
            "task_id": "performance_review",
            "task_type": TaskType.PERFORMANCE_OPTIMIZER,
            "prompt": "Analyze code for performance bottlenecks and optimization opportunities",
            "context": context,
            "estimated_duration_minutes": 45,
        },
        {
            "task_id": "quality_review",
            "task_type": TaskType.CODE_ANALYZER,
            "prompt": "Analyze code quality, maintainability, and adherence to best practices",
            "context": context,
            "estimated_duration_minutes": 50,
        },
        {
            "task_id": "architecture_review",
            "task_type": TaskType.SOLUTION_ARCHITECT,
            "prompt": "Review system architecture and design patterns",
            "context": context,
            "estimated_duration_minutes": 55,
        },
    ]

    builder.add_parallel_tasks(review_tasks)

    # Summary and recommendations
    all_reviews = [task["task_id"] for task in review_tasks]
    builder.add_task(
        "consolidate_findings",
        TaskType.REVIEWER_CRITIC,
        "Consolidate all review findings and provide prioritized recommendations",
        dependencies=all_reviews,
        estimated_duration_minutes=40,
        priority=TaskPriority.HIGH,
    )

    # Optional refactoring
    if include_refactoring:
        builder.add_task(
            "implement_improvements",
            TaskType.REFACTORING_MASTER,
            "Implement high-priority improvements and refactoring recommendations",
            dependencies=["consolidate_findings"],
            estimated_duration_minutes=120,
            background_execution=True,
        )

    return builder.build()


# Convenience function to load templates by name
def get_template(template_name: str, **kwargs) -> ExecutionPlan:
    """Get pre-built template by name"""
    templates = {
        "simple_parallel": lambda: create_simple_parallel_plan(**kwargs),
        "sdlc_pipeline": lambda: create_sdlc_pipeline_plan(**kwargs),
        "api_development": lambda: create_api_development_plan(**kwargs),
        "database_optimization": lambda: create_database_optimization_plan(**kwargs),
        "code_review": lambda: create_code_review_plan(**kwargs),
    }

    if template_name not in templates:
        available = ", ".join(templates.keys())
        raise ValueError(
            f"Unknown template '{template_name}'. Available templates: {available}"
        )

    return templates[template_name]()
