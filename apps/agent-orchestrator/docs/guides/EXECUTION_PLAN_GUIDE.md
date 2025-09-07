# Agent Orchestrator Execution Plan Guide

This guide explains how agents can generate execution plans for the agent orchestrator system to control parallel task execution with dependencies, quality gates, and monitoring.

## Overview

The agent orchestrator uses **Execution Plans** to define:
- **Tasks**: Individual agent operations with dependencies
- **Quality Gates**: Validation checkpoints that tasks must satisfy
- **Execution Phases**: Logical groupings of related tasks
- **Validation System**: Advanced validation with circular dependency detection
- **Monitoring**: Real-time tracking of agent progress
- **Resource Management**: Token allocation and parallel execution limits

## 🛡️ Validation & Error Handling (NEW)

**ExecutionPlan now includes comprehensive validation to prevent common errors and ensure reliable execution.**

### Automatic Validation

All ExecutionPlans are validated by default when created:

```python
from execution_plan_template import ExecutionPlanBuilder
from execution_plan_schema import TaskType

builder = ExecutionPlanBuilder("My Project")
builder.add_task("task1", TaskType.RESEARCH_GENIUS, "Research task")
plan = builder.build()  # ✅ Validates automatically
```

### Circular Dependency Detection

**Prevents infinite loops by detecting dependency cycles:**

```python
# This will raise CircularDependencyError
builder = ExecutionPlanBuilder("Circular Test")
builder.add_task("A", TaskType.GENERAL_PURPOSE, "Task A", dependencies=["B"])
builder.add_task("B", TaskType.GENERAL_PURPOSE, "Task B", dependencies=["A"])  # Creates cycle

try:
    plan = builder.build()
except CircularDependencyError as e:
    print(f"Circular dependency detected: {e.dependency_chain}")
    # Output: ['A', 'B', 'A']
```

### Validation Error Types

The system detects these validation errors:

| Error Type | Description | Example |
|------------|-------------|---------|
| `circular_dependency` | Tasks form dependency cycles | A→B→C→A |
| `duplicate_task_id` | Multiple tasks with same ID | Two tasks named "test" |
| `invalid_dependency_reference` | Task depends on non-existent task | Task A depends on "missing_task" |
| `self_dependency` | Task depends on itself | Task A depends on "A" |
| `empty_task_id` | Task has no identifier | task_id="" |
| `empty_task_list` | ExecutionPlan has no tasks | tasks=[] |
| `max_dependency_depth_exceeded` | Dependency chain too deep | 20+ levels |
| `orphaned_task` | Task unreachable due to missing dependencies | Isolated task |

### Error Handling Best Practices

```python
from execution_plan_validation import CircularDependencyError, ValidationError

try:
    plan = builder.build()
    print("✅ Plan validated successfully")
except CircularDependencyError as e:
    print(f"❌ Circular dependency: {e.dependency_chain}")
except ValidationError as e:
    print(f"❌ Validation failed: {e}")
    print(f"   Error type: {e.error_type}")
    print(f"   Task involved: {e.task_id}")
```

### Testing Mode (Validation Disabled)

For testing scenarios, you can disable validation:

```python
# Skip validation for testing
plan = builder.build(validate=False)

# Manual validation later
from execution_plan_validation import validate_execution_plan
result = validate_execution_plan(plan)
if not result.success:
    print(f"Validation errors found: {result.errors}")
```

## Quick Start

### 1. Simple Parallel Execution

```python
from execution_plan_template import create_simple_parallel_plan

# Create plan for independent parallel tasks
plan = create_simple_parallel_plan(
    name="Data Processing Pipeline",
    description="Process multiple data sources in parallel",
    tasks=[
        {
            "task_id": "extract_users",
            "task_type": "general-purpose",
            "prompt": "Extract user data from database and validate schema"
        },
        {
            "task_id": "extract_orders",
            "task_type": "general-purpose",
            "prompt": "Extract order data and calculate metrics"
        },
        {
            "task_id": "generate_report",
            "task_type": "general-purpose",
            "prompt": "Generate summary report from extracted data"
        }
    ]
)

# Execute with orchestrator
orchestrator = EnhancedOrchestrator(output_dir=Path("/tmp/results"))
results = await orchestrator.execute_batch(plan.tasks)
```

### 2. Sequential Dependencies

```python
from execution_plan_template import ExecutionPlanBuilder
from execution_plan_schema import TaskType

# Build plan with task dependencies
builder = ExecutionPlanBuilder(
    name="Build and Deploy Pipeline",
    description="Sequential build, test, and deployment"
)

builder.add_task("build_app", TaskType.DEVELOPMENT_SPECIALIST,
                "Build the application with all dependencies")

builder.add_task("run_tests", TaskType.QA_TESTING_GURU,
                "Execute comprehensive test suite",
                dependencies=["build_app"])  # Runs after build

builder.add_task("deploy_app", TaskType.SDLC_DEPLOYMENT,
                "Deploy application to production environment",
                dependencies=["run_tests"])  # Runs after tests pass

plan = builder.build()
```

### 3. Complete SDLC Pipeline

```python
from execution_plan_template import create_sdlc_pipeline_plan

# Full software development lifecycle
plan = create_sdlc_pipeline_plan(
    project_name="User Management System",
    requirements="""
    Build a REST API for user management with:
    - User registration and authentication
    - Profile management
    - Role-based access control
    - Integration with external OAuth providers
    """
)

# This creates a complete pipeline with phases:
# Discovery → Design → Development → Testing → Deployment
```

## Schema Components

### TaskDefinition

Core task structure that agents generate:

```python
TaskDefinition(
    task_id="unique_task_id",           # Unique identifier
    task_type=TaskType.QA_TESTING_GURU, # Agent type to use
    prompt="Detailed task description",  # Instructions for agent

    # Dependencies and execution
    dependencies=["prereq_task_1"],     # Must complete before this runs
    quality_gates=["tests_passing"],    # Quality checks required
    phase_id="testing",                 # Logical phase grouping

    # Configuration
    context={"database_url": "..."},    # Additional context
    working_directory="/path/to/work",   # Where agent operates
    validation_level=ValidationLevel.STRICT, # How strictly to validate

    # Monitoring and control
    monitoring_enabled=True,            # Enable real-time tracking
    timeout_seconds=1800,               # Max execution time
    max_retries=2,                      # Retry failed attempts
    priority=10                         # Higher = runs first
)
```

### Quality Gates

Validation checkpoints that control task execution:

```python
QualityGate(
    gate_id="database_ready",
    name="Database Accessible",
    description="Database connection is working",
    gate_type=QualityGateType.DATABASE,
    config={
        "connection_string": "postgresql://localhost/myapp",
        "timeout_seconds": 30
    },
    dependencies=["infrastructure_ready"]  # Other gates required first
)
```

Available gate types:
- `DATABASE`: Check database connectivity/queries
- `HTTP`: Validate API endpoints are responding
- `FILE_EXISTS`: Ensure required files are present
- `CODE_QUALITY`: Run linting/code analysis
- `TEST_RESULTS`: Validate test suite results
- `CUSTOM`: Custom validation logic

### Execution Phases

Group related tasks for better organization:

```python
ExecutionPhase(
    phase_id="development",
    name="Development Phase",
    description="Implement core functionality",
    gates=["design_approved"],          # Gates required for phase
    parallel_execution=True,            # Allow parallel tasks in phase
    max_parallel=3,                     # Limit concurrent tasks
    timeout_seconds=3600                # Phase timeout
)
```

## Advanced Patterns

### Mixed Execution Modes

```python
# Some tasks parallel, others sequential based on dependencies
builder = ExecutionPlanBuilder(name="Complex Pipeline")
builder.set_execution_mode(ExecutionMode.MIXED, max_parallel=5)

# These can run in parallel (no dependencies)
builder.add_task("analyze_frontend", TaskType.GENERAL_PURPOSE, "Analyze React frontend")
builder.add_task("analyze_backend", TaskType.GENERAL_PURPOSE, "Analyze Node.js backend")
builder.add_task("analyze_database", TaskType.DATABASE_SPECIALIST, "Analyze database schema")

# This runs after all analysis tasks complete
builder.add_task("create_integration_plan", TaskType.SOLUTION_ARCHITECT,
                "Create integration strategy based on analysis",
                dependencies=["analyze_frontend", "analyze_backend", "analyze_database"])
```

### Background Execution

```python
# Long-running tasks that can execute in background
task = TaskDefinition(
    task_id="large_data_migration",
    task_type=TaskType.DATABASE_SPECIALIST,
    prompt="Migrate 10M records to new schema",
    background_execution=True,          # Runs in background
    monitoring_enabled=True,            # Still track progress
    estimated_duration_minutes=240      # 4 hours estimated
)
```

### Quality Gate Dependencies

```python
builder = ExecutionPlanBuilder(name="Production Deployment")

# Infrastructure gates
builder.add_quality_gate("infrastructure_ready", "Infrastructure Ready",
                        "Cloud infrastructure is provisioned",
                        QualityGateType.HTTP, {"url": "https://api.myapp.com/health"})

builder.add_quality_gate("database_migrated", "Database Migrated",
                        "Database schema is up to date",
                        QualityGateType.DATABASE, {"migration_check": True},
                        dependencies=["infrastructure_ready"])

# Tasks that depend on gates
builder.add_task("deploy_application", TaskType.SDLC_DEPLOYMENT,
                "Deploy application to production",
                quality_gates=["infrastructure_ready", "database_migrated"])
```

## Pre-built Templates

### Database Optimization

```python
from execution_plan_template import create_database_optimization_plan

plan = create_database_optimization_plan(
    database_type="PostgreSQL",
    performance_issues="Slow queries on user table, high CPU usage during reports"
)

# Creates plan with:
# 1. Performance analysis (parallel)
# 2. Query analysis (parallel)
# 3. Implement optimizations (depends on analysis)
# 4. Validate improvements (depends on implementation)
```

### API Development

```python
from execution_plan_template import create_api_development_plan

plan = create_api_development_plan(
    api_name="User Management API",
    endpoints=["/users", "/auth/login", "/auth/register", "/profiles", "/roles"],
    requirements="RESTful API with JWT authentication and role-based access"
)

# Creates plan with:
# 1. API design
# 2. Parallel endpoint implementation (grouped)
# 3. Comprehensive testing
# 4. Documentation generation
```

## Integration with Orchestrator

### Basic Execution

```python
from src.enhanced_orchestrator import EnhancedOrchestrator

# Create orchestrator with features enabled
orchestrator = EnhancedOrchestrator(
    output_dir=Path("/tmp/execution_results"),
    max_parallel=10,
    enable_quality_gates=True,
    enable_monitoring=True,
    use_optimizations=True
)

# Execute plan
results = await orchestrator.execute_batch(plan.tasks)

# Process results
for result in results:
    print(f"Task {result['task_id']}: {result['status']}")
    if result['status'] == 'failed':
        print(f"  Error: {result['error']}")
```

### With Quality Gates

```python
# Initialize quality gates from plan
if plan.quality_gates:
    for gate in plan.quality_gates:
        await orchestrator.define_quality_gate(
            gate.gate_id, gate.name, gate.description,
            gate.gate_type.value, gate.config, gate.dependencies
        )

# Define phases
if plan.phases:
    for phase in plan.phases:
        await orchestrator.define_phase(
            phase.phase_id, phase.name, phase.description, phase.gates
        )

# Execute with quality gate validation
results = await orchestrator.execute_batch(plan.tasks)
```

### Background Execution

```python
# Launch long-running tasks in background
background_tasks = [task for task in plan.tasks if task.background_execution]
if background_tasks:
    job_id = await orchestrator.launch_background_team(background_tasks, "bg-team-1")

    # Monitor progress
    while True:
        status = await orchestrator.get_background_job_status(job_id)
        if status['status'] != 'running':
            break
        await asyncio.sleep(30)  # Check every 30 seconds
```

## Plan Validation

Always validate plans before execution:

```python
# Validate plan structure
errors = plan.validate()
if errors:
    print("Plan validation errors:")
    for error in errors:
        print(f"  - {error}")
    return

# Check execution order
try:
    execution_order = plan.get_execution_order()
    print("Execution order:")
    for i, batch in enumerate(execution_order):
        print(f"  Batch {i+1}: {', '.join(batch)}")
except ValueError as e:
    print(f"Execution order error: {e}")
```

## Best Practices

### 1. Task Design
- Use descriptive task IDs that indicate purpose
- Write detailed prompts with specific requirements
- Include context for complex tasks
- Set realistic timeouts and retry limits

### 2. Dependency Management
- Keep dependency chains as short as possible
- Group independent tasks to run in parallel
- Use phases to logically organize related tasks
- Avoid circular dependencies

### 3. Quality Gates
- Use quality gates for critical validation points
- Don't over-gate simple tasks
- Set reasonable timeouts for gate validation
- Test gate validation logic before deployment

### 4. Resource Management
- Set `max_parallel` based on available tokens
- Use background execution for long-running tasks
- Estimate task durations for better scheduling
- Monitor resource usage during execution

### 5. Error Handling
- Set appropriate retry limits for flaky operations
- Use validation levels matching task criticality
- Plan for partial failures in complex pipelines
- Include cleanup tasks for failed operations

## Troubleshooting

### Common Issues

**Circular Dependencies**
```python
# Wrong: A depends on B, B depends on A
builder.add_task("task_a", TaskType.GENERAL_PURPOSE, "Do A", dependencies=["task_b"])
builder.add_task("task_b", TaskType.GENERAL_PURPOSE, "Do B", dependencies=["task_a"])

# Validation will catch this and provide error
```

**Quality Gate Failures**
```python
# Check quality gate status
status = await orchestrator.get_quality_status()
for gate_id, gate_status in status.items():
    if gate_status['status'] != 'passed':
        print(f"Gate {gate_id} failed: {gate_status['message']}")
```

**Task Timeouts**
```python
# Increase timeout for slow tasks
TaskDefinition(
    task_id="slow_analysis",
    task_type=TaskType.GENERAL_PURPOSE,
    prompt="Deep analysis of large codebase",
    timeout_seconds=3600,  # 1 hour
    max_retries=1
)
```

For more examples, see the `examples/` directory in the agent-orchestrator application.
