"""
ExecutionPlan Advanced Validation System
Production-grade validation with circular dependency detection and comprehensive edge case handling
"""
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ValidationErrorType(Enum):
    """Types of validation errors"""

    CIRCULAR_DEPENDENCY = "circular_dependency"
    DUPLICATE_TASK_ID = "duplicate_task_id"
    INVALID_DEPENDENCY_REFERENCE = "invalid_dependency_reference"
    SELF_DEPENDENCY = "self_dependency"
    EMPTY_TASK_ID = "empty_task_id"
    EMPTY_TASK_LIST = "empty_task_list"
    MAX_DEPENDENCY_DEPTH_EXCEEDED = "max_dependency_depth_exceeded"
    ORPHANED_TASK = "orphaned_task"
    INVALID_TASK_TYPE = "invalid_task_type"
    QUALITY_GATE_REFERENCE_ERROR = "quality_gate_reference_error"


@dataclass
class ValidationError:
    """Represents a validation error with detailed information"""

    error_type: ValidationErrorType
    message: str
    task_id: Optional[str] = None
    dependency_chain: Optional[List[str]] = None
    additional_info: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        base_msg = f"[{self.error_type.value}] {self.message}"
        if self.task_id:
            base_msg += f" (Task: {self.task_id})"
        if self.dependency_chain:
            base_msg += f" (Chain: {' -> '.join(self.dependency_chain)})"
        return base_msg


@dataclass
class ValidationResult:
    """Result of validation with success status and error details"""

    success: bool
    errors: List[ValidationError] = None
    warnings: List[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}

    @property
    def is_valid(self) -> bool:
        """Check if validation passed"""
        return self.success and len(self.errors) == 0

    @property
    def error_count(self) -> int:
        """Get total number of errors"""
        return len(self.errors)

    @property
    def critical_error_count(self) -> int:
        """Get count of critical errors that would prevent execution"""
        critical_types = {
            ValidationErrorType.CIRCULAR_DEPENDENCY,
            ValidationErrorType.INVALID_DEPENDENCY_REFERENCE,
            ValidationErrorType.EMPTY_TASK_LIST,
        }
        return len([e for e in self.errors if e.error_type in critical_types])

    def get_error_summary(self) -> str:
        """Get human-readable error summary"""
        if not self.errors:
            return "No errors found"

        error_counts = {}
        for error in self.errors:
            error_type = error.error_type.value
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

        summary_parts = []
        for error_type, count in error_counts.items():
            summary_parts.append(f"{error_type}: {count}")

        return f"Validation failed with {len(self.errors)} errors: {', '.join(summary_parts)}"


class CircularDependencyError(Exception):
    """Exception raised when circular dependencies are detected"""

    def __init__(self, cycle_path: List[str]):
        self.cycle_path = cycle_path
        super().__init__(f"Circular dependency detected: {' -> '.join(cycle_path)}")


class DuplicateTaskIdError(Exception):
    """Exception raised when duplicate task IDs are found"""

    def __init__(self, duplicate_ids: List[str]):
        self.duplicate_ids = duplicate_ids
        super().__init__(f"Duplicate task IDs found: {', '.join(duplicate_ids)}")


class InvalidDependencyError(Exception):
    """Exception raised when invalid dependency references are found"""

    def __init__(self, task_id: str, invalid_deps: List[str]):
        self.task_id = task_id
        self.invalid_deps = invalid_deps
        super().__init__(
            f"Task '{task_id}' references non-existent dependencies: {', '.join(invalid_deps)}"
        )


class ExecutionPlanValidator:
    """Production-grade validator for ExecutionPlan objects"""

    def __init__(self, max_dependency_depth: int = 20, enable_warnings: bool = True):
        """
        Initialize validator with configuration

        Args:
            max_dependency_depth: Maximum allowed depth in dependency chains
            enable_warnings: Whether to generate warnings for non-critical issues
        """
        self.max_dependency_depth = max_dependency_depth
        self.enable_warnings = enable_warnings

    def validate_execution_plan(self, plan) -> ValidationResult:
        """
        Comprehensive validation of an ExecutionPlan

        Args:
            plan: ExecutionPlan object to validate

        Returns:
            ValidationResult with success status and detailed error information
        """
        logger.info(f"Starting validation of ExecutionPlan: {plan.name}")

        errors = []
        warnings = []
        metadata = {"validation_timestamp": None, "plan_complexity": {}}

        try:
            # Extract tasks for validation
            tasks = plan.tasks if hasattr(plan, "tasks") else []

            # Phase 1: Basic structural validation
            basic_errors = self._validate_basic_structure(tasks)
            errors.extend(basic_errors)

            # Phase 2: Task ID validation
            id_errors = self._validate_task_ids(tasks)
            errors.extend(id_errors)

            # Phase 3: Dependency reference validation
            ref_errors = self._validate_dependency_references(tasks)
            errors.extend(ref_errors)

            # Phase 4: Circular dependency detection (most critical)
            cycle_errors = self._detect_circular_dependencies(tasks)
            errors.extend(cycle_errors)

            # Phase 5: Dependency depth validation
            depth_errors = self._validate_dependency_depth(tasks)
            errors.extend(depth_errors)

            # Phase 6: Quality gate validation
            qg_errors = self._validate_quality_gate_references(plan)
            errors.extend(qg_errors)

            # Phase 7: Generate warnings for optimization opportunities
            if self.enable_warnings:
                warnings = self._generate_optimization_warnings(tasks)

            # Calculate plan complexity metrics
            metadata["plan_complexity"] = self._calculate_complexity_metrics(tasks)

            success = (
                len(
                    [
                        e
                        for e in errors
                        if e.error_type
                        in {
                            ValidationErrorType.CIRCULAR_DEPENDENCY,
                            ValidationErrorType.INVALID_DEPENDENCY_REFERENCE,
                            ValidationErrorType.EMPTY_TASK_LIST,
                            ValidationErrorType.DUPLICATE_TASK_ID,
                        }
                    ]
                )
                == 0
            )

            result = ValidationResult(
                success=success, errors=errors, warnings=warnings, metadata=metadata
            )

            logger.info(
                f"Validation completed: {'SUCCESS' if result.is_valid else 'FAILED'} "
                f"({result.error_count} errors, {len(warnings)} warnings)"
            )

            return result

        except Exception as e:
            logger.error(f"Validation failed with exception: {e}")
            return ValidationResult(
                success=False,
                errors=[
                    ValidationError(
                        error_type=ValidationErrorType.INVALID_TASK_TYPE,
                        message=f"Validation failed with exception: {str(e)}",
                    )
                ],
            )

    def _validate_basic_structure(self, tasks: List) -> List[ValidationError]:
        """Validate basic structural requirements"""
        errors = []

        # Check for empty task list
        if not tasks:
            errors.append(
                ValidationError(
                    error_type=ValidationErrorType.EMPTY_TASK_LIST,
                    message="ExecutionPlan must contain at least one task",
                )
            )
            return errors

        # Check individual task structure
        for i, task in enumerate(tasks):
            if not hasattr(task, "task_id") or not task.task_id:
                errors.append(
                    ValidationError(
                        error_type=ValidationErrorType.EMPTY_TASK_ID,
                        message=f"Task at index {i} has empty or missing task_id",
                    )
                )

            if not hasattr(task, "dependencies"):
                # Set empty dependencies if missing
                task.dependencies = []

        return errors

    def _validate_task_ids(self, tasks: List) -> List[ValidationError]:
        """Validate task IDs for duplicates and validity"""
        errors = []
        task_ids = []

        for task in tasks:
            if hasattr(task, "task_id") and task.task_id:
                task_ids.append(task.task_id)

        # Check for duplicates
        seen = set()
        duplicates = []
        for task_id in task_ids:
            if task_id in seen and task_id not in duplicates:
                duplicates.append(task_id)
            seen.add(task_id)

        if duplicates:
            errors.append(
                ValidationError(
                    error_type=ValidationErrorType.DUPLICATE_TASK_ID,
                    message=f"Duplicate task IDs found: {', '.join(duplicates)}",
                    additional_info={"duplicate_ids": duplicates},
                )
            )

        return errors

    def _validate_dependency_references(self, tasks: List) -> List[ValidationError]:
        """Validate that all dependency references point to existing tasks"""
        errors = []

        # Get all valid task IDs
        valid_task_ids = {
            task.task_id for task in tasks if hasattr(task, "task_id") and task.task_id
        }

        for task in tasks:
            if not hasattr(task, "task_id") or not task.task_id:
                continue

            if not hasattr(task, "dependencies"):
                continue

            # Check for self-references
            if task.task_id in task.dependencies:
                errors.append(
                    ValidationError(
                        error_type=ValidationErrorType.SELF_DEPENDENCY,
                        message=f"Task cannot depend on itself",
                        task_id=task.task_id,
                    )
                )

            # Check for invalid references
            invalid_deps = [
                dep for dep in task.dependencies if dep not in valid_task_ids
            ]
            if invalid_deps:
                errors.append(
                    ValidationError(
                        error_type=ValidationErrorType.INVALID_DEPENDENCY_REFERENCE,
                        message=f"Task references non-existent dependencies: {', '.join(invalid_deps)}",
                        task_id=task.task_id,
                        additional_info={"invalid_dependencies": invalid_deps},
                    )
                )

        return errors

    def _detect_circular_dependencies(self, tasks: List) -> List[ValidationError]:
        """
        Detect circular dependencies using depth-first search algorithm
        This is the critical validation that was missing from the system
        """
        errors = []

        # Build adjacency list for dependency graph
        graph = {}
        task_ids = set()

        for task in tasks:
            if not hasattr(task, "task_id") or not task.task_id:
                continue

            task_id = task.task_id
            task_ids.add(task_id)

        # Second pass: build graph with all task_ids known
        for task in tasks:
            if not hasattr(task, "task_id") or not task.task_id:
                continue

            task_id = task.task_id
            dependencies = getattr(task, "dependencies", [])

            # Include all dependencies that exist in the task set (including self-references)
            graph[task_id] = [dep for dep in dependencies if dep in task_ids]

        # DFS-based cycle detection
        WHITE, GRAY, BLACK = 0, 1, 2
        colors = {task_id: WHITE for task_id in task_ids}

        def dfs_visit(node: str, path: List[str]) -> Optional[List[str]]:
            """
            DFS visit with cycle detection
            Returns cycle path if found, None otherwise
            """
            if colors[node] == GRAY:
                # Back edge found - cycle detected
                cycle_start_idx = path.index(node)
                cycle = path[cycle_start_idx:] + [node]
                return cycle

            if colors[node] == BLACK:
                return None

            colors[node] = GRAY
            current_path = path + [node]

            for neighbor in graph.get(node, []):
                if neighbor in task_ids:  # Only consider valid references
                    cycle = dfs_visit(neighbor, current_path)
                    if cycle:
                        return cycle

            colors[node] = BLACK
            return None

        # Check each unvisited node
        for task_id in task_ids:
            if colors[task_id] == WHITE:
                cycle = dfs_visit(task_id, [])
                if cycle:
                    errors.append(
                        ValidationError(
                            error_type=ValidationErrorType.CIRCULAR_DEPENDENCY,
                            message=f"Circular dependency detected in task chain",
                            dependency_chain=cycle,
                            additional_info={"cycle_length": len(cycle) - 1},
                        )
                    )
                    # Stop at first cycle for clarity (could find all cycles if needed)
                    break

        return errors

    def _validate_dependency_depth(self, tasks: List) -> List[ValidationError]:
        """Validate that dependency chains don't exceed maximum depth"""
        errors = []

        # Build dependency graph
        graph = {}
        for task in tasks:
            if hasattr(task, "task_id") and task.task_id:
                task_id = task.task_id
                dependencies = getattr(task, "dependencies", [])
                graph[task_id] = dependencies

        # Calculate maximum depth for each task
        def get_max_depth(task_id: str, visited: Set[str] = None) -> int:
            if visited is None:
                visited = set()

            if task_id in visited:
                return 0  # Circular dependency, handled elsewhere

            if task_id not in graph:
                return 0  # No dependencies

            visited.add(task_id)
            max_dep_depth = 0

            for dep in graph[task_id]:
                dep_depth = get_max_depth(dep, visited.copy())
                max_dep_depth = max(max_dep_depth, dep_depth + 1)

            return max_dep_depth

        for task_id in graph:
            depth = get_max_depth(task_id)
            if depth > self.max_dependency_depth:
                errors.append(
                    ValidationError(
                        error_type=ValidationErrorType.MAX_DEPENDENCY_DEPTH_EXCEEDED,
                        message=f"Dependency chain depth ({depth}) exceeds maximum ({self.max_dependency_depth})",
                        task_id=task_id,
                        additional_info={
                            "actual_depth": depth,
                            "max_depth": self.max_dependency_depth,
                        },
                    )
                )

        return errors

    def _validate_quality_gate_references(self, plan) -> List[ValidationError]:
        """Validate quality gate references in tasks"""
        errors = []

        # Get valid quality gate IDs
        valid_gate_ids = set()
        if hasattr(plan, "quality_gates") and plan.quality_gates:
            valid_gate_ids = {
                gate.gate_id for gate in plan.quality_gates if hasattr(gate, "gate_id")
            }

        # Check task quality gate references
        for task in getattr(plan, "tasks", []):
            if not hasattr(task, "quality_gates"):
                continue

            invalid_gates = [
                gate_id
                for gate_id in task.quality_gates
                if gate_id not in valid_gate_ids
            ]
            if invalid_gates:
                errors.append(
                    ValidationError(
                        error_type=ValidationErrorType.QUALITY_GATE_REFERENCE_ERROR,
                        message=f"Task references undefined quality gates: {', '.join(invalid_gates)}",
                        task_id=getattr(task, "task_id", "unknown"),
                        additional_info={"invalid_gates": invalid_gates},
                    )
                )

        return errors

    def _generate_optimization_warnings(self, tasks: List) -> List[str]:
        """Generate warnings for potential optimization opportunities"""
        warnings = []

        # Check for orphaned tasks (no dependencies, not depended upon)
        task_ids = {task.task_id for task in tasks if hasattr(task, "task_id")}
        depended_upon = set()

        for task in tasks:
            if hasattr(task, "dependencies"):
                depended_upon.update(task.dependencies)

        orphaned_tasks = []
        for task in tasks:
            if hasattr(task, "task_id") and hasattr(task, "dependencies"):
                task_id = task.task_id
                if (
                    not task.dependencies
                    and task_id not in depended_upon
                    and len(tasks) > 1
                ):
                    orphaned_tasks.append(task_id)

        if orphaned_tasks:
            warnings.append(
                f"Potentially orphaned tasks (no dependencies and not depended upon): {', '.join(orphaned_tasks)}"
            )

        # Check for tasks with many dependencies (possible bottlenecks)
        high_dependency_tasks = []
        for task in tasks:
            if hasattr(task, "dependencies") and len(task.dependencies) > 5:
                high_dependency_tasks.append((task.task_id, len(task.dependencies)))

        if high_dependency_tasks:
            task_list = [f"{tid}({count})" for tid, count in high_dependency_tasks]
            warnings.append(
                f"Tasks with high dependency count (potential bottlenecks): {', '.join(task_list)}"
            )

        return warnings

    def _calculate_complexity_metrics(self, tasks: List) -> Dict[str, Any]:
        """Calculate complexity metrics for the execution plan"""
        metrics = {
            "total_tasks": len(tasks),
            "total_dependencies": 0,
            "max_dependencies_per_task": 0,
            "avg_dependencies_per_task": 0.0,
            "dependency_depth": 0,
            "parallelization_potential": 0.0,
        }

        if not tasks:
            return metrics

        dependency_counts = []
        for task in tasks:
            if hasattr(task, "dependencies"):
                dep_count = len(task.dependencies)
                dependency_counts.append(dep_count)
                metrics["total_dependencies"] += dep_count
                metrics["max_dependencies_per_task"] = max(
                    metrics["max_dependencies_per_task"], dep_count
                )

        if dependency_counts:
            metrics["avg_dependencies_per_task"] = metrics["total_dependencies"] / len(
                dependency_counts
            )

        # Calculate parallelization potential (tasks with no dependencies / total tasks)
        no_dep_count = len(
            [task for task in tasks if not getattr(task, "dependencies", [])]
        )
        metrics["parallelization_potential"] = (
            no_dep_count / len(tasks) if tasks else 0.0
        )

        return metrics


# Factory function for creating validator
def create_execution_plan_validator(
    max_dependency_depth: int = 20, enable_warnings: bool = True
) -> ExecutionPlanValidator:
    """Create an ExecutionPlan validator with specified configuration"""
    return ExecutionPlanValidator(max_dependency_depth, enable_warnings)


# Helper function for quick validation
def validate_execution_plan(plan, strict: bool = True) -> ValidationResult:
    """
    Quick validation function for ExecutionPlan objects

    Args:
        plan: ExecutionPlan to validate
        strict: If True, uses strict validation settings

    Returns:
        ValidationResult with validation outcome
    """
    validator = create_execution_plan_validator(
        max_dependency_depth=15 if strict else 50, enable_warnings=True
    )
    return validator.validate_execution_plan(plan)


# Helper function to raise exceptions for critical errors
def validate_execution_plan_strict(plan) -> None:
    """
    Validate ExecutionPlan and raise exceptions for critical errors

    Args:
        plan: ExecutionPlan to validate

    Raises:
        CircularDependencyError: If circular dependencies detected
        DuplicateTaskIdError: If duplicate task IDs found
        InvalidDependencyError: If invalid dependency references found
    """
    result = validate_execution_plan(plan, strict=True)

    if not result.success:
        # Check for specific critical errors and raise appropriate exceptions
        for error in result.errors:
            if error.error_type == ValidationErrorType.CIRCULAR_DEPENDENCY:
                raise CircularDependencyError(error.dependency_chain or [])
            elif error.error_type == ValidationErrorType.DUPLICATE_TASK_ID:
                duplicate_ids = (
                    error.additional_info.get("duplicate_ids", [])
                    if error.additional_info
                    else []
                )
                raise DuplicateTaskIdError(duplicate_ids)
            elif error.error_type == ValidationErrorType.INVALID_DEPENDENCY_REFERENCE:
                invalid_deps = (
                    error.additional_info.get("invalid_dependencies", [])
                    if error.additional_info
                    else []
                )
                raise InvalidDependencyError(error.task_id or "unknown", invalid_deps)

        # If no specific exception type, raise general validation error
        raise ValueError(result.get_error_summary())


# Testing helper function
def test_circular_dependency_detection():
    """Test circular dependency detection with various scenarios"""
    print("🧪 Testing Circular Dependency Detection")

    # Mock task class for testing
    class MockTask:
        def __init__(self, task_id: str, dependencies: List[str] = None):
            self.task_id = task_id
            self.dependencies = dependencies or []

    # Mock plan class for testing
    class MockPlan:
        def __init__(self, name: str, tasks: List[MockTask]):
            self.name = name
            self.tasks = tasks
            self.quality_gates = []

    validator = create_execution_plan_validator()

    # Test 1: Simple circular dependency A -> B -> A
    print("\n1. Testing simple circular dependency (A -> B -> A)")
    tasks1 = [MockTask("A", ["B"]), MockTask("B", ["A"])]
    plan1 = MockPlan("Circular Test 1", tasks1)
    result1 = validator.validate_execution_plan(plan1)

    assert not result1.success, "Should detect circular dependency"
    assert any(
        e.error_type == ValidationErrorType.CIRCULAR_DEPENDENCY for e in result1.errors
    ), "Should have circular dependency error"
    print(f"   ✅ Detected: {result1.errors[0].message}")

    # Test 2: Complex circular dependency A -> B -> C -> A
    print("\n2. Testing complex circular dependency (A -> B -> C -> A)")
    tasks2 = [MockTask("A", ["B"]), MockTask("B", ["C"]), MockTask("C", ["A"])]
    plan2 = MockPlan("Circular Test 2", tasks2)
    result2 = validator.validate_execution_plan(plan2)

    assert not result2.success, "Should detect circular dependency"
    print(f"   ✅ Detected: {result2.errors[0].dependency_chain}")

    # Test 3: Valid dependency chain (no cycles)
    print("\n3. Testing valid dependency chain")
    tasks3 = [MockTask("A", ["B"]), MockTask("B", ["C"]), MockTask("C", [])]
    plan3 = MockPlan("Valid Test", tasks3)
    result3 = validator.validate_execution_plan(plan3)

    assert result3.success, f"Should be valid, but got: {result3.get_error_summary()}"
    print("   ✅ Valid dependency chain accepted")

    # Test 4: Self-dependency
    print("\n4. Testing self-dependency")
    tasks4 = [MockTask("A", ["A"])]
    plan4 = MockPlan("Self-Dep Test", tasks4)
    result4 = validator.validate_execution_plan(plan4)

    assert not result4.success, "Should reject self-dependency"
    print(f"   ✅ Self-dependency rejected")

    print("\n🎉 All circular dependency detection tests passed!")


if __name__ == "__main__":
    test_circular_dependency_detection()
