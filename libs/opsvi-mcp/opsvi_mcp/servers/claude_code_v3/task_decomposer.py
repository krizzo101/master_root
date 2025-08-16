"""Intelligent task decomposition for Claude Code V3"""

import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import hashlib


class TaskType(Enum):
    """Types of tasks for decomposition"""

    SERVER_CREATION = "server_creation"
    MULTI_FILE_OPERATION = "multi_file"
    REFACTORING = "refactoring"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    SIMPLE = "simple"
    UNKNOWN = "unknown"


class TaskPriority(Enum):
    """Task priority levels"""

    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass
class SubTask:
    """Represents a decomposed sub-task"""

    id: str
    type: str
    description: str
    priority: TaskPriority = TaskPriority.NORMAL
    estimated_time_ms: int = 60000
    can_parallel: bool = False
    can_decompose: bool = False
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    depth_hint: int = 1  # Suggested depth for execution

    def __post_init__(self):
        if not self.id:
            self.id = hashlib.md5(self.description.encode()).hexdigest()[:8]


class TaskDecomposer:
    """Intelligent task decomposition system"""

    def __init__(self, config):
        self.config = config
        self.patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[TaskType, re.Pattern]:
        """Compile regex patterns for task type detection"""
        return {
            TaskType.SERVER_CREATION: re.compile(
                r"(create|implement|build|develop).*(server|service|api|endpoint)",
                re.IGNORECASE,
            ),
            TaskType.MULTI_FILE_OPERATION: re.compile(
                r"(multiple|all|several|batch).*(file|component|module)", re.IGNORECASE
            ),
            TaskType.REFACTORING: re.compile(
                r"(refactor|restructure|reorganize|optimize|improve)", re.IGNORECASE
            ),
            TaskType.TESTING: re.compile(
                r"(test|testing|coverage|unittest|integration test)", re.IGNORECASE
            ),
            TaskType.DOCUMENTATION: re.compile(
                r"(document|documentation|readme|api doc|comment)", re.IGNORECASE
            ),
        }

    def analyze_task(self, task: str) -> TaskType:
        """Analyze task description to determine type"""
        for task_type, pattern in self.patterns.items():
            if pattern.search(task):
                return task_type

        # Simple heuristics for unmatched patterns
        if len(task.split()) < 10:
            return TaskType.SIMPLE

        return TaskType.UNKNOWN

    def estimate_complexity(self, task: str) -> str:
        """Estimate task complexity"""
        # Word count as a basic metric
        word_count = len(task.split())

        # Check for complexity indicators
        complex_keywords = ["implement", "create", "develop", "build", "integrate"]
        very_complex_keywords = [
            "server",
            "framework",
            "architecture",
            "system",
            "infrastructure",
        ]

        task_lower = task.lower()

        if any(kw in task_lower for kw in very_complex_keywords):
            return "very_complex"
        elif any(kw in task_lower for kw in complex_keywords):
            return "complex"
        elif word_count > 50:
            return "moderate"
        else:
            return "simple"

    def estimate_file_count(self, task: str) -> int:
        """Estimate number of files involved"""
        # Look for explicit file mentions
        file_patterns = [
            r"(\d+)\s*files?",
            r"multiple\s*files?",
            r"all\s*files?",
            r"several\s*files?",
        ]

        for pattern in file_patterns:
            match = re.search(pattern, task, re.IGNORECASE)
            if match:
                if match.group(1) if match.groups() else None:
                    return int(match.group(1))
                elif "multiple" in match.group(0) or "several" in match.group(0):
                    return 5
                elif "all" in match.group(0):
                    return 10

        # Estimate based on task type
        task_type = self.analyze_task(task)
        estimates = {
            TaskType.SERVER_CREATION: 8,
            TaskType.MULTI_FILE_OPERATION: 5,
            TaskType.REFACTORING: 3,
            TaskType.TESTING: 4,
            TaskType.DOCUMENTATION: 2,
            TaskType.SIMPLE: 1,
            TaskType.UNKNOWN: 2,
        }

        return estimates.get(task_type, 2)

    def decompose(self, task: str, context: Optional[Dict] = None) -> List[SubTask]:
        """Main decomposition method"""
        if not self.config.decomposition.enable_decomposition:
            return []

        task_type = self.analyze_task(task)

        # Route to specific decomposer
        decomposers = {
            TaskType.SERVER_CREATION: self._decompose_server_creation,
            TaskType.MULTI_FILE_OPERATION: self._decompose_multi_file,
            TaskType.REFACTORING: self._decompose_refactoring,
            TaskType.TESTING: self._decompose_testing,
            TaskType.DOCUMENTATION: self._decompose_documentation,
            TaskType.SIMPLE: self._decompose_simple,
            TaskType.UNKNOWN: self._decompose_unknown,
        }

        decomposer = decomposers.get(task_type, self._decompose_unknown)
        subtasks = decomposer(task, context or {})

        # Apply max subtasks limit
        if len(subtasks) > self.config.decomposition.max_subtasks:
            subtasks = self._consolidate_subtasks(subtasks)

        return subtasks

    def _decompose_server_creation(self, task: str, context: Dict) -> List[SubTask]:
        """Decompose server creation tasks"""
        subtasks = []

        # Extract server details from task
        server_name = self._extract_server_name(task)
        features = self._extract_features(task)

        # Phase 1: Structure and configuration (can parallel)
        subtasks.append(
            SubTask(
                id=f"{server_name}_structure",
                type="create_structure",
                description=f"Create directory structure for {server_name} server",
                priority=TaskPriority.HIGH,
                estimated_time_ms=60000,
                can_parallel=True,
                metadata={"phase": 1, "server": server_name},
            )
        )

        subtasks.append(
            SubTask(
                id=f"{server_name}_config",
                type="create_config",
                description=f"Create config.py with configuration classes for {server_name}",
                priority=TaskPriority.HIGH,
                estimated_time_ms=120000,
                can_parallel=True,
                metadata={"phase": 1, "server": server_name},
            )
        )

        subtasks.append(
            SubTask(
                id=f"{server_name}_models",
                type="create_models",
                description=f"Create models.py with Pydantic models for {server_name}",
                priority=TaskPriority.HIGH,
                estimated_time_ms=120000,
                can_parallel=True,
                metadata={"phase": 1, "server": server_name},
            )
        )

        # Phase 2: Core implementation (depends on phase 1)
        subtasks.append(
            SubTask(
                id=f"{server_name}_server",
                type="create_server",
                description=f"Implement main server.py with FastMCP for {server_name}",
                priority=TaskPriority.CRITICAL,
                estimated_time_ms=240000,
                can_parallel=False,
                dependencies=[
                    f"{server_name}_structure",
                    f"{server_name}_config",
                    f"{server_name}_models",
                ],
                metadata={"phase": 2, "server": server_name},
            )
        )

        # Phase 3: Tools implementation (can be further decomposed)
        if len(features) > 3:
            # Complex server with many tools - mark for further decomposition
            subtasks.append(
                SubTask(
                    id=f"{server_name}_tools",
                    type="create_tools",
                    description=f"Implement {len(features)} MCP tools: {', '.join(features[:3])}...",
                    priority=TaskPriority.CRITICAL,
                    estimated_time_ms=300000,
                    can_parallel=False,
                    can_decompose=True,  # Can be broken down further
                    dependencies=[f"{server_name}_server"],
                    metadata={"phase": 3, "server": server_name, "features": features},
                    depth_hint=2,  # Suggest executing at depth 2
                )
            )
        else:
            # Simple server - implement all tools together
            subtasks.append(
                SubTask(
                    id=f"{server_name}_tools",
                    type="create_tools",
                    description=f"Implement MCP tools for {server_name}",
                    priority=TaskPriority.CRITICAL,
                    estimated_time_ms=180000,
                    can_parallel=False,
                    dependencies=[f"{server_name}_server"],
                    metadata={"phase": 3, "server": server_name},
                )
            )

        # Phase 4: Supporting files (can parallel)
        subtasks.append(
            SubTask(
                id=f"{server_name}_init",
                type="create_init",
                description=f"Create __init__.py and __main__.py for {server_name}",
                priority=TaskPriority.NORMAL,
                estimated_time_ms=60000,
                can_parallel=True,
                dependencies=[f"{server_name}_server"],
                metadata={"phase": 4, "server": server_name},
            )
        )

        subtasks.append(
            SubTask(
                id=f"{server_name}_tests",
                type="create_tests",
                description=f"Create test files for {server_name}",
                priority=TaskPriority.LOW,
                estimated_time_ms=120000,
                can_parallel=True,
                dependencies=[f"{server_name}_tools"],
                metadata={"phase": 4, "server": server_name},
            )
        )

        return subtasks

    def _decompose_multi_file(self, task: str, context: Dict) -> List[SubTask]:
        """Decompose multi-file operations"""
        subtasks = []

        # Phase 1: Analysis
        subtasks.append(
            SubTask(
                id="analyze_files",
                type="analyze",
                description="Analyze target files and dependencies",
                priority=TaskPriority.HIGH,
                estimated_time_ms=60000,
                can_parallel=False,
            )
        )

        # Phase 2: Planning
        subtasks.append(
            SubTask(
                id="create_plan",
                type="plan",
                description="Create execution plan for file operations",
                priority=TaskPriority.HIGH,
                estimated_time_ms=60000,
                can_parallel=False,
                dependencies=["analyze_files"],
            )
        )

        # Phase 3: Parallel execution
        subtasks.append(
            SubTask(
                id="execute_operations",
                type="execute",
                description="Execute file operations in parallel where possible",
                priority=TaskPriority.CRITICAL,
                estimated_time_ms=180000,
                can_parallel=True,
                can_decompose=True,
                dependencies=["create_plan"],
                depth_hint=2,
            )
        )

        # Phase 4: Verification
        subtasks.append(
            SubTask(
                id="verify_results",
                type="verify",
                description="Verify all operations completed successfully",
                priority=TaskPriority.NORMAL,
                estimated_time_ms=60000,
                can_parallel=False,
                dependencies=["execute_operations"],
            )
        )

        return subtasks

    def _decompose_refactoring(self, task: str, context: Dict) -> List[SubTask]:
        """Decompose refactoring tasks"""
        return [
            SubTask(
                id="analyze_code",
                type="analyze",
                description="Analyze code structure and identify refactoring targets",
                priority=TaskPriority.HIGH,
                estimated_time_ms=90000,
            ),
            SubTask(
                id="create_backup",
                type="backup",
                description="Create backup of files to be refactored",
                priority=TaskPriority.HIGH,
                estimated_time_ms=30000,
                dependencies=["analyze_code"],
            ),
            SubTask(
                id="refactor_code",
                type="refactor",
                description="Apply refactoring changes",
                priority=TaskPriority.CRITICAL,
                estimated_time_ms=180000,
                dependencies=["create_backup"],
                can_decompose=True,
                depth_hint=2,
            ),
            SubTask(
                id="run_tests",
                type="test",
                description="Run tests to verify refactoring",
                priority=TaskPriority.HIGH,
                estimated_time_ms=120000,
                dependencies=["refactor_code"],
            ),
            SubTask(
                id="cleanup",
                type="cleanup",
                description="Clean up temporary files and finalize",
                priority=TaskPriority.LOW,
                estimated_time_ms=30000,
                dependencies=["run_tests"],
            ),
        ]

    def _decompose_testing(self, task: str, context: Dict) -> List[SubTask]:
        """Decompose testing tasks"""
        return [
            SubTask(
                id="analyze_coverage",
                type="analyze",
                description="Analyze current test coverage",
                priority=TaskPriority.HIGH,
                estimated_time_ms=60000,
                can_parallel=True,
            ),
            SubTask(
                id="generate_tests",
                type="generate",
                description="Generate test cases",
                priority=TaskPriority.CRITICAL,
                estimated_time_ms=180000,
                can_decompose=True,
                depth_hint=2,
            ),
            SubTask(
                id="run_tests",
                type="execute",
                description="Execute test suite",
                priority=TaskPriority.HIGH,
                estimated_time_ms=120000,
                dependencies=["generate_tests"],
            ),
            SubTask(
                id="generate_report",
                type="report",
                description="Generate test report",
                priority=TaskPriority.NORMAL,
                estimated_time_ms=60000,
                dependencies=["run_tests"],
            ),
        ]

    def _decompose_documentation(self, task: str, context: Dict) -> List[SubTask]:
        """Decompose documentation tasks"""
        return [
            SubTask(
                id="analyze_code",
                type="analyze",
                description="Analyze code for documentation needs",
                priority=TaskPriority.HIGH,
                estimated_time_ms=60000,
            ),
            SubTask(
                id="generate_docs",
                type="generate",
                description="Generate documentation",
                priority=TaskPriority.CRITICAL,
                estimated_time_ms=120000,
                dependencies=["analyze_code"],
                can_parallel=True,
            ),
            SubTask(
                id="format_docs",
                type="format",
                description="Format and organize documentation",
                priority=TaskPriority.NORMAL,
                estimated_time_ms=60000,
                dependencies=["generate_docs"],
            ),
        ]

    def _decompose_simple(self, task: str, context: Dict) -> List[SubTask]:
        """Handle simple tasks - no decomposition"""
        return []

    def _decompose_unknown(self, task: str, context: Dict) -> List[SubTask]:
        """Default decomposition for unknown tasks"""
        # Try to break into analyze-execute-verify pattern
        return [
            SubTask(
                id="analyze",
                type="analyze",
                description="Analyze requirements and context",
                priority=TaskPriority.HIGH,
                estimated_time_ms=60000,
            ),
            SubTask(
                id="execute",
                type="execute",
                description="Execute main task",
                priority=TaskPriority.CRITICAL,
                estimated_time_ms=180000,
                dependencies=["analyze"],
            ),
            SubTask(
                id="verify",
                type="verify",
                description="Verify results",
                priority=TaskPriority.NORMAL,
                estimated_time_ms=60000,
                dependencies=["execute"],
            ),
        ]

    def _extract_server_name(self, task: str) -> str:
        """Extract server name from task description"""
        # Look for patterns like "Database Integration Server" or "database server"
        patterns = [
            r"(\w+(?:\s+\w+)?)\s+(?:MCP\s+)?[Ss]erver",
            r"[Ss]erver(?:\s+for)?\s+(\w+(?:\s+\w+)?)",
            r"servers?/(\w+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, task)
            if match:
                return match.group(1).lower().replace(" ", "_")

        return "unknown"

    def _extract_features(self, task: str) -> List[str]:
        """Extract feature list from task description"""
        features = []

        # Look for numbered lists
        pattern = r"\d+\.\s+([^\n]+)"
        matches = re.findall(pattern, task)
        if matches:
            features.extend(matches)

        # Look for bullet points
        pattern = r"[-*]\s+([^\n]+)"
        matches = re.findall(pattern, task)
        if matches:
            features.extend(matches)

        # Clean up features
        features = [f.strip() for f in features]
        features = [f for f in features if len(f) > 5]  # Filter out short items

        return features[:10]  # Limit to 10 features

    def _consolidate_subtasks(self, subtasks: List[SubTask]) -> List[SubTask]:
        """Consolidate subtasks if exceeding max limit"""
        # Group by phase or type
        groups = {}
        for task in subtasks:
            key = task.metadata.get("phase", task.type)
            if key not in groups:
                groups[key] = []
            groups[key].append(task)

        # Consolidate each group if needed
        consolidated = []
        for key, group_tasks in groups.items():
            if len(group_tasks) > 2:
                # Merge into a single task
                descriptions = [t.description for t in group_tasks]
                total_time = sum(t.estimated_time_ms for t in group_tasks)
                all_deps = set()
                for t in group_tasks:
                    all_deps.update(t.dependencies)

                consolidated.append(
                    SubTask(
                        id=f"consolidated_{key}",
                        type=group_tasks[0].type,
                        description=f"Consolidated: {'; '.join(descriptions[:2])}...",
                        priority=min(t.priority for t in group_tasks),
                        estimated_time_ms=total_time,
                        can_parallel=any(t.can_parallel for t in group_tasks),
                        can_decompose=True,  # Can be re-decomposed later
                        dependencies=list(all_deps),
                        metadata={
                            "consolidated": True,
                            "original_count": len(group_tasks),
                        },
                    )
                )
            else:
                consolidated.extend(group_tasks)

        return consolidated[: self.config.decomposition.max_subtasks]
