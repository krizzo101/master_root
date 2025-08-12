"""
OAMAT Task Decomposition Module
Breaks large agent tasks into smaller parallel sub-workflows
"""

from dataclasses import dataclass
from enum import Enum
import logging
from typing import Any, Dict, List

# Import the new file generation orchestrator
from src.applications.oamat.file_generation_orchestrator import (
    FileGenerationOrchestrator,
    FileSpec,
)


class TaskComplexity(Enum):
    SIMPLE = "simple"  # Single subtask
    MODERATE = "moderate"  # 2-3 subtasks
    COMPLEX = "complex"  # 4+ subtasks
    MASSIVE = "massive"  # Needs hierarchical breakdown


@dataclass
class SubTask:
    """Represents a decomposed subtask"""

    id: str
    description: str
    agent_role: str
    estimated_effort: int  # 1-10 scale
    dependencies: List[str]
    file_outputs: List[str]
    tools_needed: List[str]
    parallel_safe: bool = True

    # NEW: File-level parallel generation specs
    file_specs: List[FileSpec] = None
    enable_file_parallelization: bool = True


class TaskDecomposer:
    """Analyzes tasks and breaks them into parallel subtasks"""

    def __init__(self):
        self.logger = logging.getLogger("OAMAT.TaskDecomposer")

        # Define decomposition patterns for different roles
        self.decomposition_patterns = {
            "coder": self._decompose_coding_task,
            "tester": self._decompose_testing_task,
            "doc": self._decompose_documentation_task,
            "planner": self._decompose_planning_task,
            "reviewer": self._decompose_review_task,
        }

    def analyze_task_complexity(
        self, task_description: str, agent_role: str
    ) -> TaskComplexity:
        """Analyze if a task needs decomposition"""
        # Simple heuristics - can be enhanced with LLM analysis
        complexity_indicators = {
            "multiple": 2,
            "various": 2,
            "several": 2,
            "create and": 3,
            "implement and": 3,
            "build a": 2,
            "full": 3,
            "complete": 3,
            "comprehensive": 4,
            "entire": 4,
            "system": 3,
            "application": 3,
            "API": 2,
            "database": 2,
            "frontend": 2,
            "backend": 2,
            "microservice": 3,
        }

        score = 0
        task_lower = task_description.lower()

        for indicator, weight in complexity_indicators.items():
            if indicator in task_lower:
                score += weight

        # Role-specific complexity adjustments
        if agent_role == "coder":
            if any(
                word in task_lower for word in ["api", "web app", "system", "service"]
            ):
                score += 2

        if score <= 2:
            return TaskComplexity.SIMPLE
        elif score <= 5:
            return TaskComplexity.MODERATE
        elif score <= 8:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.MASSIVE

    def decompose_task(
        self, task_description: str, agent_role: str, user_request: str
    ) -> List[SubTask]:
        """Main method to decompose a task into subtasks"""
        complexity = self.analyze_task_complexity(task_description, agent_role)

        if complexity == TaskComplexity.SIMPLE:
            return []  # No decomposition needed

        print(f"🔧 DECOMPOSE: Breaking down {agent_role} task ({complexity.value})")

        if agent_role in self.decomposition_patterns:
            subtasks = self.decomposition_patterns[agent_role](
                task_description, user_request, complexity
            )
            print(f"🔧 DECOMPOSE: Created {len(subtasks)} subtasks for {agent_role}")
            return subtasks

        return []

    def _decompose_coding_task(
        self, task_description: str, user_request: str, complexity: TaskComplexity
    ) -> List[SubTask]:
        """Decompose coding tasks into parallel components"""
        subtasks = []
        task_lower = task_description.lower()

        # Web Application Pattern
        if any(
            word in task_lower
            for word in ["web app", "web application", "api", "service"]
        ):
            if "database" in task_lower or "data" in task_lower:
                # Create FileSpec objects for database-related files
                db_file_specs = [
                    FileSpec(
                        name="models.py",
                        path="models.py",
                        content_type="code",
                        dependencies=[],
                        agent_role="coder_db",
                        tools_needed=["write_file"],
                        success_criteria=[
                            "Complete database models",
                            "Proper relationships",
                            "Valid Python syntax",
                        ],
                        context_requirements=["database schema", "data models"],
                    ),
                    FileSpec(
                        name="schema.sql",
                        path="schema.sql",
                        content_type="code",
                        dependencies=[],
                        agent_role="coder_db",
                        tools_needed=["write_file"],
                        success_criteria=[
                            "Valid SQL syntax",
                            "Complete schema definition",
                        ],
                        context_requirements=["database requirements"],
                    ),
                    FileSpec(
                        name="migrations.py",
                        path="migrations/001_initial.py",
                        content_type="code",
                        dependencies=["models.py", "schema.sql"],
                        agent_role="coder_db",
                        tools_needed=["write_file", "create_directory"],
                        success_criteria=[
                            "Migration scripts work",
                            "Database setup automation",
                        ],
                        context_requirements=["database models", "schema changes"],
                    ),
                ]

                subtasks.append(
                    SubTask(
                        id="db_models",
                        description=f"Create database models and schema for: {user_request}",
                        agent_role="coder_db",
                        estimated_effort=6,
                        dependencies=[],
                        file_outputs=["models.py", "schema.sql", "migrations/"],
                        tools_needed=["write_file", "create_directory"],
                        parallel_safe=True,
                        file_specs=db_file_specs,
                        enable_file_parallelization=True,
                    )
                )

            if "api" in task_lower or "backend" in task_lower:
                # Create FileSpec objects for API-related files
                api_file_specs = [
                    FileSpec(
                        name="routes.py",
                        path="routes/main.py",
                        content_type="code",
                        dependencies=["models.py"] if "database" in task_lower else [],
                        agent_role="coder_api",
                        tools_needed=["write_file", "create_directory"],
                        success_criteria=[
                            "Complete API routes",
                            "Proper HTTP methods",
                            "Error handling",
                        ],
                        context_requirements=["API requirements", "data models"],
                    ),
                    FileSpec(
                        name="controllers.py",
                        path="controllers/main.py",
                        content_type="code",
                        dependencies=["models.py", "routes.py"]
                        if "database" in task_lower
                        else ["routes.py"],
                        agent_role="coder_api",
                        tools_needed=["write_file", "create_directory"],
                        success_criteria=[
                            "Business logic implementation",
                            "Input validation",
                            "Response formatting",
                        ],
                        context_requirements=["business requirements", "API design"],
                    ),
                    FileSpec(
                        name="app.py",
                        path="app.py",
                        content_type="code",
                        dependencies=["routes.py", "controllers.py"],
                        agent_role="coder_api",
                        tools_needed=["write_file"],
                        success_criteria=[
                            "Application startup",
                            "Route registration",
                            "Configuration setup",
                        ],
                        context_requirements=[
                            "application architecture",
                            "deployment requirements",
                        ],
                    ),
                ]

                subtasks.append(
                    SubTask(
                        id="api_endpoints",
                        description=f"Implement API endpoints for: {user_request}",
                        agent_role="coder_api",
                        estimated_effort=7,
                        dependencies=["db_models"] if "database" in task_lower else [],
                        file_outputs=["routes/", "controllers/", "app.py"],
                        tools_needed=["write_file", "create_directory"],
                        parallel_safe=False if "database" in task_lower else True,
                        file_specs=api_file_specs,
                        enable_file_parallelization=True,
                    )
                )

            if "frontend" in task_lower or "ui" in task_lower:
                # Create FileSpec objects for frontend files
                frontend_file_specs = [
                    FileSpec(
                        name="index.html",
                        path="frontend/index.html",
                        content_type="code",
                        dependencies=[],
                        agent_role="coder_frontend",
                        tools_needed=["write_file", "create_directory"],
                        success_criteria=[
                            "Valid HTML structure",
                            "Responsive design",
                            "Accessibility",
                        ],
                        context_requirements=["UI requirements", "user experience"],
                    ),
                    FileSpec(
                        name="styles.css",
                        path="frontend/styles.css",
                        content_type="code",
                        dependencies=[],
                        agent_role="coder_frontend",
                        tools_needed=["write_file"],
                        success_criteria=[
                            "Consistent styling",
                            "Responsive layout",
                            "Cross-browser compatibility",
                        ],
                        context_requirements=[
                            "design requirements",
                            "brand guidelines",
                        ],
                    ),
                    FileSpec(
                        name="script.js",
                        path="frontend/script.js",
                        content_type="code",
                        dependencies=["index.html"],
                        agent_role="coder_frontend",
                        tools_needed=["write_file"],
                        success_criteria=[
                            "Interactive functionality",
                            "API integration",
                            "Error handling",
                        ],
                        context_requirements=["API endpoints", "user interactions"],
                    ),
                ]

                subtasks.append(
                    SubTask(
                        id="frontend_ui",
                        description=f"Create frontend interface for: {user_request}",
                        agent_role="coder_frontend",
                        estimated_effort=6,
                        dependencies=[],
                        file_outputs=["frontend/"],
                        tools_needed=["write_file", "create_directory"],
                        parallel_safe=True,
                        file_specs=frontend_file_specs,
                        enable_file_parallelization=True,
                    )
                )

        # Generic Code Decomposition
        else:
            # Break into logical components
            if complexity in [TaskComplexity.MODERATE, TaskComplexity.COMPLEX]:
                # Core logic files
                core_file_specs = [
                    FileSpec(
                        name="main.py",
                        path="main.py",
                        content_type="code",
                        dependencies=[],
                        agent_role="coder_core",
                        tools_needed=["write_file"],
                        success_criteria=[
                            "Complete main logic",
                            "Proper entry point",
                            "Error handling",
                        ],
                        context_requirements=[
                            "business requirements",
                            "system architecture",
                        ],
                    ),
                    FileSpec(
                        name="core_logic.py",
                        path="core/logic.py",
                        content_type="code",
                        dependencies=[],
                        agent_role="coder_core",
                        tools_needed=["write_file", "create_directory"],
                        success_criteria=[
                            "Core business logic",
                            "Modular design",
                            "Unit testable",
                        ],
                        context_requirements=[
                            "business requirements",
                            "functional specifications",
                        ],
                    ),
                ]

                # Utility files
                util_file_specs = [
                    FileSpec(
                        name="utils.py",
                        path="utils/helpers.py",
                        content_type="code",
                        dependencies=[],
                        agent_role="coder_utils",
                        tools_needed=["write_file", "create_directory"],
                        success_criteria=[
                            "Reusable functions",
                            "Proper documentation",
                            "Type hints",
                        ],
                        context_requirements=["utility requirements", "code standards"],
                    ),
                    FileSpec(
                        name="constants.py",
                        path="utils/constants.py",
                        content_type="code",
                        dependencies=[],
                        agent_role="coder_utils",
                        tools_needed=["write_file"],
                        success_criteria=[
                            "Centralized constants",
                            "Clear naming",
                            "Proper organization",
                        ],
                        context_requirements=["configuration requirements"],
                    ),
                ]

                # Configuration files
                config_file_specs = [
                    FileSpec(
                        name="requirements.txt",
                        path="requirements.txt",
                        content_type="config",
                        dependencies=[],
                        agent_role="coder_config",
                        tools_needed=["write_file"],
                        success_criteria=[
                            "Complete dependencies",
                            "Version pinning",
                            "Security considerations",
                        ],
                        context_requirements=[
                            "dependency requirements",
                            "deployment environment",
                        ],
                    ),
                    FileSpec(
                        name="config.py",
                        path="config/settings.py",
                        content_type="code",
                        dependencies=[],
                        agent_role="coder_config",
                        tools_needed=["write_file", "create_directory"],
                        success_criteria=[
                            "Environment configuration",
                            "Security best practices",
                            "Flexibility",
                        ],
                        context_requirements=[
                            "deployment requirements",
                            "environment settings",
                        ],
                    ),
                    FileSpec(
                        name=".env.example",
                        path=".env.example",
                        content_type="config",
                        dependencies=["config.py"],
                        agent_role="coder_config",
                        tools_needed=["write_file"],
                        success_criteria=[
                            "Environment template",
                            "Security guidelines",
                            "Clear documentation",
                        ],
                        context_requirements=[
                            "configuration variables",
                            "deployment guide",
                        ],
                    ),
                ]

                subtasks.extend(
                    [
                        SubTask(
                            id="core_logic",
                            description=f"Implement core business logic for: {user_request}",
                            agent_role="coder_core",
                            estimated_effort=7,
                            dependencies=[],
                            file_outputs=["core/", "main.py"],
                            tools_needed=["write_file", "create_directory"],
                            parallel_safe=True,
                            file_specs=core_file_specs,
                            enable_file_parallelization=True,
                        ),
                        SubTask(
                            id="utilities",
                            description=f"Create utility functions and helpers for: {user_request}",
                            agent_role="coder_utils",
                            estimated_effort=4,
                            dependencies=[],
                            file_outputs=["utils/", "helpers/"],
                            tools_needed=["write_file", "create_directory"],
                            parallel_safe=True,
                            file_specs=util_file_specs,
                            enable_file_parallelization=True,
                        ),
                        SubTask(
                            id="config_setup",
                            description=f"Set up configuration and environment for: {user_request}",
                            agent_role="coder_config",
                            estimated_effort=3,
                            dependencies=[],
                            file_outputs=[
                                "config/",
                                "requirements.txt",
                                ".env.example",
                            ],
                            tools_needed=["write_file", "create_directory"],
                            parallel_safe=True,
                            file_specs=config_file_specs,
                            enable_file_parallelization=True,
                        ),
                    ]
                )

        return subtasks

    def _decompose_testing_task(
        self, task_description: str, user_request: str, complexity: TaskComplexity
    ) -> List[SubTask]:
        """Decompose testing tasks"""
        subtasks = []

        if complexity in [TaskComplexity.MODERATE, TaskComplexity.COMPLEX]:
            # Unit testing files
            unit_test_specs = [
                FileSpec(
                    name="test_models.py",
                    path="tests/unit/test_models.py",
                    content_type="code",
                    dependencies=[],
                    agent_role="tester_unit",
                    tools_needed=["write_file", "create_directory"],
                    success_criteria=[
                        "Complete model tests",
                        "High coverage",
                        "Clear assertions",
                    ],
                    context_requirements=["models code", "testing standards"],
                ),
                FileSpec(
                    name="test_api.py",
                    path="tests/unit/test_api.py",
                    content_type="code",
                    dependencies=[],
                    agent_role="tester_unit",
                    tools_needed=["write_file"],
                    success_criteria=[
                        "API endpoint tests",
                        "Input validation tests",
                        "Error handling tests",
                    ],
                    context_requirements=["API code", "endpoints"],
                ),
                FileSpec(
                    name="test_utils.py",
                    path="tests/unit/test_utils.py",
                    content_type="code",
                    dependencies=[],
                    agent_role="tester_unit",
                    tools_needed=["write_file"],
                    success_criteria=[
                        "Utility function tests",
                        "Edge case coverage",
                        "Type validation",
                    ],
                    context_requirements=["utility functions", "helper methods"],
                ),
            ]

            # Integration testing files
            integration_test_specs = [
                FileSpec(
                    name="test_integration.py",
                    path="tests/integration/test_integration.py",
                    content_type="code",
                    dependencies=["test_models.py", "test_api.py"],
                    agent_role="tester_integration",
                    tools_needed=["write_file", "create_directory"],
                    success_criteria=[
                        "End-to-end tests",
                        "Component integration",
                        "Database interactions",
                    ],
                    context_requirements=["system architecture", "data flow"],
                ),
                FileSpec(
                    name="test_workflow.py",
                    path="tests/integration/test_workflow.py",
                    content_type="code",
                    dependencies=["test_integration.py"],
                    agent_role="tester_integration",
                    tools_needed=["write_file"],
                    success_criteria=[
                        "Complete user workflows",
                        "Business process validation",
                        "Real scenarios",
                    ],
                    context_requirements=["user requirements", "business logic"],
                ),
            ]

            # Test configuration files
            test_config_specs = [
                FileSpec(
                    name="conftest.py",
                    path="tests/conftest.py",
                    content_type="code",
                    dependencies=[],
                    agent_role="tester_config",
                    tools_needed=["write_file"],
                    success_criteria=[
                        "Test fixtures",
                        "Shared utilities",
                        "Test configuration",
                    ],
                    context_requirements=["testing framework", "test data"],
                ),
                FileSpec(
                    name="pytest.ini",
                    path="pytest.ini",
                    content_type="config",
                    dependencies=[],
                    agent_role="tester_config",
                    tools_needed=["write_file"],
                    success_criteria=[
                        "Test configuration",
                        "Coverage settings",
                        "Plugin configuration",
                    ],
                    context_requirements=["testing requirements", "CI/CD setup"],
                ),
            ]

            subtasks.extend(
                [
                    SubTask(
                        id="unit_tests",
                        description=f"Create unit tests for: {user_request}",
                        agent_role="tester_unit",
                        estimated_effort=5,
                        dependencies=[],
                        file_outputs=["tests/unit/", "test_*.py"],
                        tools_needed=["write_file", "create_directory"],
                        parallel_safe=True,
                        file_specs=unit_test_specs,
                        enable_file_parallelization=True,
                    ),
                    SubTask(
                        id="integration_tests",
                        description=f"Create integration tests for: {user_request}",
                        agent_role="tester_integration",
                        estimated_effort=6,
                        dependencies=["unit_tests"],
                        file_outputs=["tests/integration/"],
                        tools_needed=["write_file", "create_directory"],
                        parallel_safe=False,
                        file_specs=integration_test_specs,
                        enable_file_parallelization=True,
                    ),
                    SubTask(
                        id="test_config",
                        description=f"Set up test configuration and fixtures for: {user_request}",
                        agent_role="tester_config",
                        estimated_effort=3,
                        dependencies=[],
                        file_outputs=["tests/conftest.py", "pytest.ini"],
                        tools_needed=["write_file"],
                        parallel_safe=True,
                        file_specs=test_config_specs,
                        enable_file_parallelization=True,
                    ),
                ]
            )

        return subtasks

    def _decompose_documentation_task(
        self, task_description: str, user_request: str, complexity: TaskComplexity
    ) -> List[SubTask]:
        """Decompose documentation tasks"""
        subtasks = []

        if complexity in [TaskComplexity.MODERATE, TaskComplexity.COMPLEX]:
            # API documentation files
            api_doc_specs = [
                FileSpec(
                    name="api.md",
                    path="docs/api.md",
                    content_type="documentation",
                    dependencies=[],
                    agent_role="doc_api",
                    tools_needed=["write_file", "create_directory"],
                    success_criteria=[
                        "Complete API reference",
                        "Example requests",
                        "Response schemas",
                    ],
                    context_requirements=["API endpoints", "data models"],
                ),
                FileSpec(
                    name="openapi.yaml",
                    path="docs/openapi.yaml",
                    content_type="documentation",
                    dependencies=[],
                    agent_role="doc_api",
                    tools_needed=["write_file"],
                    success_criteria=[
                        "OpenAPI specification",
                        "Valid YAML",
                        "Complete schemas",
                    ],
                    context_requirements=["API structure", "request/response formats"],
                ),
            ]

            # User documentation files
            user_doc_specs = [
                FileSpec(
                    name="user-guide.md",
                    path="docs/user-guide.md",
                    content_type="documentation",
                    dependencies=[],
                    agent_role="doc_user",
                    tools_needed=["write_file"],
                    success_criteria=[
                        "Clear instructions",
                        "Screenshots/examples",
                        "Troubleshooting",
                    ],
                    context_requirements=["user workflows", "feature list"],
                ),
                FileSpec(
                    name="quickstart.md",
                    path="docs/quickstart.md",
                    content_type="documentation",
                    dependencies=[],
                    agent_role="doc_user",
                    tools_needed=["write_file"],
                    success_criteria=[
                        "Quick setup guide",
                        "Basic examples",
                        "Getting started",
                    ],
                    context_requirements=["installation process", "basic usage"],
                ),
                FileSpec(
                    name="FAQ.md",
                    path="docs/FAQ.md",
                    content_type="documentation",
                    dependencies=["user-guide.md"],
                    agent_role="doc_user",
                    tools_needed=["write_file"],
                    success_criteria=[
                        "Common questions",
                        "Problem solutions",
                        "Helpful answers",
                    ],
                    context_requirements=["user guide", "common issues"],
                ),
            ]

            # Developer documentation files
            dev_doc_specs = [
                FileSpec(
                    name="development.md",
                    path="docs/development.md",
                    content_type="documentation",
                    dependencies=[],
                    agent_role="doc_dev",
                    tools_needed=["write_file"],
                    success_criteria=[
                        "Setup instructions",
                        "Architecture overview",
                        "Contribution guide",
                    ],
                    context_requirements=[
                        "system architecture",
                        "development workflow",
                    ],
                ),
                FileSpec(
                    name="CONTRIBUTING.md",
                    path="CONTRIBUTING.md",
                    content_type="documentation",
                    dependencies=[],
                    agent_role="doc_dev",
                    tools_needed=["write_file"],
                    success_criteria=[
                        "Contribution guidelines",
                        "Code standards",
                        "PR process",
                    ],
                    context_requirements=["development standards", "team workflow"],
                ),
                FileSpec(
                    name="architecture.md",
                    path="docs/architecture.md",
                    content_type="documentation",
                    dependencies=["development.md"],
                    agent_role="doc_dev",
                    tools_needed=["write_file"],
                    success_criteria=[
                        "System design",
                        "Component diagrams",
                        "Technical decisions",
                    ],
                    context_requirements=["system design", "technical architecture"],
                ),
            ]

            subtasks.extend(
                [
                    SubTask(
                        id="api_docs",
                        description=f"Create API documentation for: {user_request}",
                        agent_role="doc_api",
                        estimated_effort=4,
                        dependencies=[],
                        file_outputs=["docs/api.md", "openapi.yaml"],
                        tools_needed=["write_file"],
                        parallel_safe=True,
                        file_specs=api_doc_specs,
                        enable_file_parallelization=True,
                    ),
                    SubTask(
                        id="user_guide",
                        description=f"Write user guide for: {user_request}",
                        agent_role="doc_user",
                        estimated_effort=5,
                        dependencies=[],
                        file_outputs=["docs/user-guide.md", "docs/quickstart.md"],
                        tools_needed=["write_file"],
                        parallel_safe=True,
                        file_specs=user_doc_specs,
                        enable_file_parallelization=True,
                    ),
                    SubTask(
                        id="dev_docs",
                        description=f"Create developer documentation for: {user_request}",
                        agent_role="doc_dev",
                        estimated_effort=4,
                        dependencies=[],
                        file_outputs=["docs/development.md", "CONTRIBUTING.md"],
                        tools_needed=["write_file"],
                        parallel_safe=True,
                        file_specs=dev_doc_specs,
                        enable_file_parallelization=True,
                    ),
                ]
            )

        return subtasks

    def _decompose_planning_task(
        self, task_description: str, user_request: str, complexity: TaskComplexity
    ) -> List[SubTask]:
        """Decompose planning tasks"""
        return []  # Planning typically shouldn't be decomposed

    def _decompose_review_task(
        self, task_description: str, user_request: str, complexity: TaskComplexity
    ) -> List[SubTask]:
        """Decompose review tasks"""
        subtasks = []

        if complexity in [TaskComplexity.COMPLEX, TaskComplexity.MASSIVE]:
            subtasks.extend(
                [
                    SubTask(
                        id="code_review",
                        description=f"Review code quality and best practices for: {user_request}",
                        agent_role="reviewer_code",
                        estimated_effort=5,
                        dependencies=[],
                        file_outputs=["reviews/code-review.md"],
                        tools_needed=["write_file", "read_file"],
                        parallel_safe=True,
                    ),
                    SubTask(
                        id="security_review",
                        description=f"Review security aspects for: {user_request}",
                        agent_role="reviewer_security",
                        estimated_effort=4,
                        dependencies=[],
                        file_outputs=["reviews/security-review.md"],
                        tools_needed=["write_file", "read_file"],
                        parallel_safe=True,
                    ),
                    SubTask(
                        id="performance_review",
                        description=f"Review performance aspects for: {user_request}",
                        agent_role="reviewer_performance",
                        estimated_effort=4,
                        dependencies=[],
                        file_outputs=["reviews/performance-review.md"],
                        tools_needed=["write_file", "read_file"],
                        parallel_safe=True,
                    ),
                ]
            )

        return subtasks


class SubWorkflowOrchestrator:
    """Orchestrates parallel execution of subtasks"""

    def __init__(self, main_oamat_instance):
        self.oamat = main_oamat_instance
        self.logger = logging.getLogger("OAMAT.SubWorkflow")
        # Initialize file generation orchestrator for file-level parallelization
        self.file_orchestrator = FileGenerationOrchestrator(main_oamat_instance)

    async def execute_subtasks(self, subtasks: List[SubTask], base_state: Dict) -> Dict:
        """Execute subtasks with dependency management"""
        if not subtasks:
            return {"success": False, "error": "No subtasks provided"}

        print(f"🔧 SUBWORKFLOW: Executing {len(subtasks)} subtasks")

        # Group subtasks by dependency levels
        execution_levels = self._organize_by_dependencies(subtasks)

        all_results = {}
        consolidated_context = base_state.copy()

        # Execute each level in sequence, but tasks within level in parallel
        for level, level_tasks in execution_levels.items():
            print(f"🔧 SUBWORKFLOW: Level {level} - {len(level_tasks)} parallel tasks")

            # Execute subtasks in this level in parallel
            level_results = await self._execute_level_parallel(
                level_tasks, consolidated_context
            )

            # Consolidate results and update context for next level
            for subtask_id, result in level_results.items():
                all_results[subtask_id] = result

                # Add subtask results to consolidated context for dependent tasks
                if result.get("success") and "consolidated_context" in result:
                    # Merge file generation results into the main context
                    file_results = result["consolidated_context"]
                    consolidated_context.update(file_results)

                    # Specifically track subtask outputs for dependency resolution
                    if "subtask_outputs" not in consolidated_context:
                        consolidated_context["subtask_outputs"] = {}
                    consolidated_context["subtask_outputs"][subtask_id] = result

        return {
            "success": True,
            "subtask_results": all_results,
            "completed_subtasks": list(all_results.keys()),
            "consolidated_context": consolidated_context,
        }

    def _organize_by_dependencies(
        self, subtasks: List[SubTask]
    ) -> Dict[int, List[SubTask]]:
        """Organize subtasks by dependency levels for parallel execution"""
        levels = {}
        subtask_map = {task.id: task for task in subtasks}
        completed = set()
        level = 0

        while len(completed) < len(subtasks):
            ready_tasks = []

            for task in subtasks:
                if task.id in completed:
                    continue

                # Check if all dependencies are completed
                deps_met = all(dep in completed for dep in task.dependencies)

                if deps_met:
                    ready_tasks.append(task)

            if not ready_tasks:
                # Handle circular dependencies or other issues
                remaining = [task for task in subtasks if task.id not in completed]
                if remaining:
                    self.logger.warning(
                        f"Potential circular dependency in subtasks, adding {len(remaining)} to final level"
                    )
                    ready_tasks = remaining

            if ready_tasks:
                levels[level] = ready_tasks
                for task in ready_tasks:
                    completed.add(task.id)
                level += 1

        return levels

    async def _execute_level_parallel(
        self, tasks: List[SubTask], base_state: Dict
    ) -> Dict:
        """Execute all tasks in a level in parallel"""
        import asyncio

        if len(tasks) == 1:
            # Single task - execute directly
            task = tasks[0]
            result = await self._execute_single_subtask(task, base_state)
            return {task.id: result}

        # Create tasks for parallel execution
        async_tasks = []
        for task in tasks:
            async_task = self._execute_single_subtask(task, base_state)
            async_tasks.append(async_task)

        # Execute all subtasks concurrently
        try:
            results = await asyncio.gather(*async_tasks, return_exceptions=True)

            # Process results
            level_results = {}
            for i, result in enumerate(results):
                task = tasks[i]
                if isinstance(result, Exception):
                    level_results[task.id] = {
                        "success": False,
                        "error": str(result),
                        "subtask_id": task.id,
                    }
                else:
                    level_results[task.id] = result

            return level_results

        except Exception as e:
            self.logger.error(f"Level parallel execution failed: {e}")
            return {task.id: {"success": False, "error": str(e)} for task in tasks}

    async def _execute_single_subtask(self, subtask: SubTask, base_state: Dict) -> Dict:
        """Execute a single subtask, with file-level parallelization if enabled"""

        try:
            # Prepare subtask context
            subtask_context = self._prepare_subtask_context(subtask, base_state)

            # Check if this subtask should use file-level parallelization
            if (
                subtask.enable_file_parallelization
                and subtask.file_specs
                and len(subtask.file_specs) > 1
            ):
                self.logger.info(
                    f"🔧 FILE-PARALLEL: Subtask {subtask.id} using file-level parallelization with {len(subtask.file_specs)} files"
                )

                # Use FileGenerationOrchestrator for parallel file generation
                file_result = await self.file_orchestrator.generate_files_parallel(
                    subtask.file_specs, subtask_context
                )

                if file_result["success"]:
                    return {
                        "success": True,
                        "subtask_id": subtask.id,
                        "execution_type": "file_parallel",
                        "files_generated": len(subtask.file_specs),
                        "consolidated_context": file_result["consolidated_context"],
                        "file_results": file_result["results"],
                    }
                else:
                    return {
                        "success": False,
                        "subtask_id": subtask.id,
                        "execution_type": "file_parallel",
                        "error": "File generation failed",
                        "file_results": file_result.get("results", []),
                    }

            else:
                # Use traditional single-agent execution for subtasks with single files or disabled parallelization
                self.logger.info(
                    f"🔧 SEQUENTIAL: Subtask {subtask.id} using sequential execution"
                )

                agent_result = await self._execute_traditional_subtask(
                    subtask, subtask_context
                )

                return {
                    "success": agent_result.get("success", False),
                    "subtask_id": subtask.id,
                    "execution_type": "sequential",
                    "consolidated_context": subtask_context,
                    "agent_result": agent_result,
                }

        except Exception as e:
            self.logger.error(f"Subtask {subtask.id} execution failed: {e}")
            return {"success": False, "subtask_id": subtask.id, "error": str(e)}

    def _prepare_subtask_context(
        self, subtask: SubTask, base_state: Dict
    ) -> Dict[str, Any]:
        """Prepare context for subtask execution"""

        subtask_context = base_state.copy()

        # Add subtask-specific information
        subtask_context.update(
            {
                "current_subtask": {
                    "id": subtask.id,
                    "description": subtask.description,
                    "agent_role": subtask.agent_role,
                    "estimated_effort": subtask.estimated_effort,
                    "dependencies": subtask.dependencies,
                    "file_outputs": subtask.file_outputs,
                    "tools_needed": subtask.tools_needed,
                },
                # Context from completed dependency subtasks
                "dependency_context": self._get_dependency_context(subtask, base_state),
                # File-level context if applicable
                "file_generation_enabled": subtask.enable_file_parallelization,
                "expected_files": subtask.file_outputs,
            }
        )

        return subtask_context

    def _get_dependency_context(
        self, subtask: SubTask, base_state: Dict
    ) -> Dict[str, Any]:
        """Get context from completed dependency subtasks"""
        dependency_context = {}

        subtask_outputs = base_state.get("subtask_outputs", {})

        for dep_id in subtask.dependencies:
            if dep_id in subtask_outputs:
                dep_result = subtask_outputs[dep_id]
                dependency_context[dep_id] = {
                    "success": dep_result.get("success", False),
                    "execution_type": dep_result.get("execution_type", "unknown"),
                    "files_generated": dep_result.get("files_generated", 0),
                    # Include file artifacts if available
                    "file_artifacts": dep_result.get("consolidated_context", {}).get(
                        "file_artifacts", []
                    ),
                }

        return dependency_context

    async def _execute_traditional_subtask(
        self, subtask: SubTask, subtask_context: Dict
    ) -> Dict:
        """Execute subtask using traditional single-agent approach"""

        try:
            # Convert SubTask to agent candidate format for existing parallel executor
            candidate = {
                "node_id": subtask.id,
                "agent_role": subtask.agent_role,
                "description": subtask.description,
                "dependencies": subtask.dependencies,
                "subtask_context": {
                    "estimated_effort": subtask.estimated_effort,
                    "file_outputs": subtask.file_outputs,
                    "tools_needed": subtask.tools_needed,
                },
            }

            # Use existing parallel executor for single subtask
            from src.applications.oamat.parallel_executor import ParallelAgentExecutor

            executor = ParallelAgentExecutor(self.oamat)

            # Execute single agent
            results = await executor.execute_agents_parallel(
                [candidate], subtask_context.get("user_request", ""), subtask_context
            )

            agent_results = results.get("agent_results", {})
            if subtask.id in agent_results:
                return agent_results[subtask.id]
            else:
                return {"success": False, "error": "No agent result received"}

        except Exception as e:
            return {"success": False, "error": f"Traditional execution failed: {e}"}
