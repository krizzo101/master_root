# ExecutionPlan Validation System Guide

**Production-grade validation with circular dependency detection and comprehensive error handling**

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Validation Types](#validation-types)
- [Error Handling](#error-handling)
- [Advanced Usage](#advanced-usage)
- [Performance](#performance)
- [Testing](#testing)
- [API Reference](#api-reference)

## 🎯 Overview

The ExecutionPlan validation system provides production-ready validation to ensure reliable agent orchestration:

### Key Features

- **Circular Dependency Detection**: Prevents infinite loops in task execution
- **Data Integrity Validation**: Ensures all task references are valid
- **Performance Optimized**: Validates complex plans in milliseconds
- **Flexible Modes**: Strict validation for production, relaxed for testing
- **Comprehensive Error Reporting**: Detailed error messages with dependency chains
- **Backward Compatible**: All existing code continues to work unchanged

### Production Benefits

- **Reliability**: Catch errors before execution starts
- **Developer Experience**: Clear, actionable error messages
- **System Stability**: Prevent orchestrator hangs and failures
- **Quality Assurance**: Ensure plan correctness at build time

## 🚀 Quick Start

### Basic Validation

```python
from execution_plan_template import ExecutionPlanBuilder
from execution_plan_schema import TaskType

# Create a validated ExecutionPlan
builder = ExecutionPlanBuilder("My Project")
builder.add_task("research", TaskType.RESEARCH_GENIUS, "Research the problem")
builder.add_task("solution", TaskType.SOLUTION_ARCHITECT, "Design solution",
                dependencies=["research"])

plan = builder.build()  # ✅ Automatically validates
print(f"Created plan with {len(plan.tasks)} tasks")
```

### Error Detection Example

```python
# This will catch circular dependency
try:
    builder = ExecutionPlanBuilder("Circular Test")
    builder.add_task("A", TaskType.GENERAL_PURPOSE, "Task A", dependencies=["B"])
    builder.add_task("B", TaskType.GENERAL_PURPOSE, "Task B", dependencies=["A"])
    plan = builder.build()  # Will raise CircularDependencyError
except CircularDependencyError as e:
    print(f"Circular dependency detected: {e.dependency_chain}")
    # Output: Circular dependency detected: ['A', 'B', 'A']
```

## 🔍 Validation Types

### 1. Circular Dependency Detection

**Purpose**: Prevent infinite loops in task execution

**Detection Algorithm**: Uses Depth-First Search (DFS) to detect cycles in the task dependency graph

```python
# ❌ Simple circular dependency
A → B → A

# ❌ Complex circular dependency
A → B → C → D → B

# ❌ Self-dependency
A → A

# ✅ Valid dependency chain
A → B → C → D
```

**Example**:
```python
from execution_plan_validation import CircularDependencyError

builder = ExecutionPlanBuilder("Complex Pipeline")
builder.add_task("analyze", TaskType.RESEARCH_GENIUS, "Analyze requirements")
builder.add_task("design", TaskType.SOLUTION_ARCHITECT, "Create design",
                dependencies=["analyze", "prototype"])  # Will cause circular dependency
builder.add_task("prototype", TaskType.DEVELOPMENT_SPECIALIST, "Build prototype",
                dependencies=["design"])

try:
    plan = builder.build()
except CircularDependencyError as e:
    print(f"Cycle detected: {' -> '.join(e.dependency_chain)}")
    # Output: design -> prototype -> design
```

### 2. Data Integrity Validation

#### Duplicate Task ID Detection

```python
# ❌ This will raise DuplicateTaskIdError
builder.add_task("analysis", TaskType.RESEARCH_GENIUS, "Research analysis")
builder.add_task("analysis", TaskType.SOLUTION_ARCHITECT, "Design analysis")  # Duplicate ID
```

#### Invalid Dependency References

```python
# ❌ This will raise InvalidDependencyError
builder.add_task("deploy", TaskType.SDLC_DEPLOYMENT, "Deploy application",
                dependencies=["nonexistent_task"])  # References missing task
```

#### Self-Dependency Detection

```python
# ❌ This will raise SelfDependencyError
builder.add_task("recursive", TaskType.GENERAL_PURPOSE, "Recursive task",
                dependencies=["recursive"])  # Task depends on itself
```

### 3. Structure Validation

#### Empty Task Validation

```python
# ❌ Empty task ID
builder.add_task("", TaskType.GENERAL_PURPOSE, "Task with no ID")

# ❌ Empty task list
builder = ExecutionPlanBuilder("Empty Plan")
plan = builder.build()  # No tasks added
```

#### Dependency Depth Limits

```python
# ❌ Will raise MaxDependencyDepthExceededError if chain > 20 levels
# A → B → C → ... → Z (26 levels)
```

## 🛠️ Error Handling

### Exception Hierarchy

```python
ValidationError                    # Base validation exception
├── CircularDependencyError        # Circular dependencies detected
├── DuplicateTaskIdError          # Duplicate task IDs found
├── InvalidDependencyError        # Invalid task references
├── SelfDependencyError           # Task depends on itself
├── EmptyTaskIdError              # Task has empty identifier
├── EmptyTaskListError            # Plan has no tasks
├── MaxDependencyDepthError       # Dependency chain too deep
└── OrphanedTaskError             # Unreachable task
```

### Comprehensive Error Handling

```python
from execution_plan_validation import (
    ValidationError, CircularDependencyError,
    DuplicateTaskIdError, InvalidDependencyError
)

try:
    plan = builder.build()
    print("✅ Plan validation successful")

except CircularDependencyError as e:
    print(f"❌ Circular dependency: {' -> '.join(e.dependency_chain)}")
    print(f"   Tasks involved: {e.task_id}")

except DuplicateTaskIdError as e:
    print(f"❌ Duplicate task IDs found: {e.duplicate_ids}")

except InvalidDependencyError as e:
    print(f"❌ Task '{e.task_id}' depends on missing task: {e.invalid_references}")

except ValidationError as e:
    print(f"❌ Validation failed: {e}")
    print(f"   Error type: {e.error_type.value}")
    print(f"   Task: {e.task_id}")

except Exception as e:
    print(f"❌ Unexpected error: {e}")
```

### Validation Results

For non-exception based validation:

```python
from execution_plan_validation import validate_execution_plan

# Manual validation (returns result object)
result = validate_execution_plan(plan)

if result.success:
    print("✅ Validation passed")
    if result.warnings:
        print(f"⚠️ Warnings: {len(result.warnings)}")
        for warning in result.warnings:
            print(f"   - {warning}")
else:
    print(f"❌ Validation failed with {len(result.errors)} errors:")
    for error in result.errors:
        print(f"   - {error.error_type.value}: {error.message}")
        if error.dependency_chain:
            print(f"     Chain: {' -> '.join(error.dependency_chain)}")
```

## ⚙️ Advanced Usage

### Flexible Validation Modes

```python
# Production mode (default) - strict validation
plan = builder.build(validate=True)   # Default behavior
plan = builder.build()                # Same as above

# Testing mode - skip validation for complex test scenarios
plan = builder.build(validate=False)  # Skip validation

# Custom validation - validate specific aspects
validator = ExecutionPlanValidator()
result = validator.validate_dependencies_only(plan)
```

### Manual Validation Control

```python
from execution_plan_validation import ExecutionPlanValidator

# Create validator with custom settings
validator = ExecutionPlanValidator(
    max_dependency_depth=50,          # Allow deeper dependency chains
    allow_empty_plans=True,           # Allow plans with no tasks
    strict_mode=False                 # More lenient validation
)

# Validate specific aspects
result = validator.validate_circular_dependencies(plan.tasks)
if not result.success:
    print(f"Circular dependencies found: {result.errors}")

result = validator.validate_task_references(plan.tasks)
if not result.success:
    print(f"Invalid references found: {result.errors}")
```

### Integration with ExecutionPlan Schema

```python
from execution_plan_schema import ExecutionPlan, ValidationLevel

# Create plan with validation level
plan = ExecutionPlan(
    name="Custom Plan",
    validation_level=ValidationLevel.STRICT,  # STRICT | STANDARD | MINIMAL
    tasks=[...],
    quality_gates=[...]
)

# Validate existing plan
result = plan.validate_comprehensive()
if not result.is_valid:
    for error in result.errors:
        print(f"Error: {error}")
```

## 📊 Performance

### Validation Performance Characteristics

| Plan Size | Tasks | Validation Time | Memory Usage |
|-----------|-------|-----------------|--------------|
| Small     | 1-10  | <0.1ms         | <1KB         |
| Medium    | 11-50 | <1ms           | <5KB         |
| Large     | 51-100| <5ms           | <10KB        |
| Very Large| 100+  | <10ms          | <20KB        |

### Performance Best Practices

```python
# ✅ Good: Validate once after building complete plan
builder = ExecutionPlanBuilder("Efficient Plan")
# ... add many tasks ...
plan = builder.build()  # Single validation

# ❌ Avoid: Multiple validations during building
builder = ExecutionPlanBuilder("Inefficient Plan")
builder.add_task(...)
plan1 = builder.build()  # First validation
builder.add_task(...)
plan2 = builder.build()  # Second validation (unnecessary)
```

### Monitoring Validation Performance

```python
import time
from execution_plan_validation import ExecutionPlanValidator

start_time = time.time()
result = validate_execution_plan(large_plan)
validation_time = time.time() - start_time

print(f"Validated {len(large_plan.tasks)} tasks in {validation_time:.3f}s")
print(f"Performance: {len(large_plan.tasks) / validation_time:.0f} tasks/sec")
```

## 🧪 Testing

### Testing with Validation Disabled

```python
import pytest
from execution_plan_template import ExecutionPlanBuilder
from execution_plan_schema import TaskType

def test_complex_plan_structure():
    """Test complex plan logic without validation overhead"""
    builder = ExecutionPlanBuilder("Test Plan")

    # Add complex test structure that might have temporary circular deps
    builder.add_task("A", TaskType.GENERAL_PURPOSE, "Task A", dependencies=["B"])
    builder.add_task("B", TaskType.GENERAL_PURPOSE, "Task B", dependencies=["C"])
    builder.add_task("C", TaskType.GENERAL_PURPOSE, "Task C", dependencies=["A"])

    # Skip validation for testing intermediate state
    plan = builder.build(validate=False)

    assert len(plan.tasks) == 3
    # ... test plan structure without validation blocking the test
```

### Testing Validation Behavior

```python
def test_circular_dependency_detection():
    """Test that circular dependencies are properly detected"""
    builder = ExecutionPlanBuilder("Circular Test")
    builder.add_task("A", TaskType.GENERAL_PURPOSE, "Task A", dependencies=["B"])
    builder.add_task("B", TaskType.GENERAL_PURPOSE, "Task B", dependencies=["A"])

    with pytest.raises(CircularDependencyError) as exc_info:
        plan = builder.build()

    assert "A" in exc_info.value.dependency_chain
    assert "B" in exc_info.value.dependency_chain

def test_duplicate_task_detection():
    """Test duplicate task ID detection"""
    builder = ExecutionPlanBuilder("Duplicate Test")
    builder.add_task("duplicate", TaskType.GENERAL_PURPOSE, "First task")

    with pytest.raises(DuplicateTaskIdError):
        builder.add_task("duplicate", TaskType.RESEARCH_GENIUS, "Second task")
```

### Mock Validation for Unit Tests

```python
from unittest.mock import patch

def test_plan_execution_logic():
    """Test plan execution without validation side effects"""
    with patch('execution_plan_template.ExecutionPlanBuilder.build') as mock_build:
        # Mock successful validation
        mock_build.return_value = create_mock_plan()

        builder = ExecutionPlanBuilder("Mock Test")
        builder.add_task("test", TaskType.GENERAL_PURPOSE, "Test task")
        plan = builder.build()

        # Test the actual logic without validation interfering
        assert plan.name == "Mock Test"
```

## 📚 API Reference

### Core Classes

#### `ExecutionPlanValidator`

Main validation engine for ExecutionPlan objects.

```python
class ExecutionPlanValidator:
    def __init__(self, max_dependency_depth: int = 20, strict_mode: bool = True):
        """Initialize validator with configuration"""

    def validate_execution_plan(self, plan: ExecutionPlan) -> ValidationResult:
        """Comprehensive validation of ExecutionPlan"""

    def detect_circular_dependencies(self, tasks: List[TaskDefinition]) -> Optional[List[str]]:
        """Detect circular dependencies in task list"""

    def validate_task_references(self, tasks: List[TaskDefinition]) -> ValidationResult:
        """Validate all task dependency references are valid"""

    def validate_duplicate_task_ids(self, tasks: List[TaskDefinition]) -> ValidationResult:
        """Check for duplicate task identifiers"""
```

#### `ValidationResult`

Result object containing validation outcome and details.

```python
@dataclass
class ValidationResult:
    success: bool                    # True if validation passed
    errors: List[ValidationError]    # List of validation errors found
    warnings: List[ValidationError]  # List of warnings (non-fatal)
    execution_time: float           # Time taken for validation (seconds)

    @property
    def is_valid(self) -> bool:
        """True if no errors (warnings allowed)"""

    def get_error_summary(self) -> str:
        """Human-readable summary of errors"""
```

#### `ValidationError`

Detailed error information for validation failures.

```python
@dataclass
class ValidationError:
    error_type: ValidationErrorType   # Type of validation error
    message: str                     # Human-readable error message
    task_id: Optional[str]           # Task involved in error (if applicable)
    dependency_chain: Optional[List[str]]  # Dependency chain causing error
    additional_info: Optional[Dict[str, Any]]  # Extra error context

    def __str__(self) -> str:
        """Formatted error message with context"""
```

#### `ValidationErrorType`

Enumeration of all validation error types.

```python
class ValidationErrorType(Enum):
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
```

### Exception Classes

#### `CircularDependencyError`

Raised when circular dependencies are detected.

```python
class CircularDependencyError(ValidationError):
    def __init__(self, dependency_chain: List[str], task_id: str = None):
        self.dependency_chain = dependency_chain  # Chain showing the cycle
        self.task_id = task_id                   # Task where cycle was detected
```

#### `DuplicateTaskIdError`

Raised when duplicate task IDs are found.

```python
class DuplicateTaskIdError(ValidationError):
    def __init__(self, duplicate_ids: List[str], task_id: str = None):
        self.duplicate_ids = duplicate_ids  # List of duplicate IDs found
```

#### `InvalidDependencyError`

Raised when tasks reference non-existent dependencies.

```python
class InvalidDependencyError(ValidationError):
    def __init__(self, invalid_references: List[str], task_id: str = None):
        self.invalid_references = invalid_references  # Missing dependency IDs
```

### Utility Functions

#### `validate_execution_plan(plan: ExecutionPlan) -> ValidationResult`

Convenient function for one-off validation:

```python
from execution_plan_validation import validate_execution_plan

result = validate_execution_plan(my_plan)
if result.success:
    print("Validation passed!")
else:
    print(f"Found {len(result.errors)} errors")
```

#### `get_dependency_graph(tasks: List[TaskDefinition]) -> Dict[str, List[str]]`

Utility to visualize task dependencies:

```python
from execution_plan_validation import get_dependency_graph

graph = get_dependency_graph(plan.tasks)
for task_id, dependencies in graph.items():
    print(f"{task_id} depends on: {dependencies}")
```

## 🎯 Best Practices

### 1. Validation Strategy

```python
# ✅ Always validate in production
def create_production_plan():
    builder = ExecutionPlanBuilder("Production Pipeline")
    # ... add tasks ...
    return builder.build()  # Auto-validates

# ✅ Use flexible validation in tests
def create_test_plan():
    builder = ExecutionPlanBuilder("Test Pipeline")
    # ... add tasks ...
    return builder.build(validate=False)  # Skip for testing
```

### 2. Error Handling Patterns

```python
# ✅ Specific error handling for different scenarios
try:
    plan = builder.build()
except CircularDependencyError:
    # Handle circular dependency specifically
    return create_alternative_plan()
except ValidationError as e:
    # Handle other validation errors
    log_validation_error(e)
    raise
```

### 3. Performance Optimization

```python
# ✅ Validate once after complete plan construction
builder = ExecutionPlanBuilder("Optimized Plan")
for task_config in task_configurations:
    builder.add_task(**task_config)  # Build entire plan
plan = builder.build()  # Single validation

# ❌ Avoid multiple validations
for task_config in task_configurations:
    builder.add_task(**task_config)
    partial_plan = builder.build()  # Validates each time
```

### 4. Clear Error Messages

```python
# ✅ Provide context in error handling
try:
    plan = builder.build()
except ValidationError as e:
    error_message = f"""
    ExecutionPlan validation failed for '{builder.name}':
    - Error: {e.error_type.value}
    - Message: {e.message}
    - Task: {e.task_id or 'N/A'}
    """
    logger.error(error_message)
    raise RuntimeError(f"Cannot create plan: {e.message}") from e
```

---

## 🚀 Migration Guide

### From Previous Versions

**No Breaking Changes**: All existing ExecutionPlan code continues to work unchanged.

**New Features Available**:
- Automatic validation (can be disabled with `validate=False`)
- Enhanced error messages with detailed information
- Circular dependency detection
- Comprehensive validation API

### Adopting New Features

```python
# Before: Basic plan creation (still works)
plan = builder.build()

# After: Explicit validation control
plan = builder.build(validate=True)   # Production mode
plan = builder.build(validate=False)  # Testing mode

# After: Manual validation with detailed results
result = validate_execution_plan(plan)
```

---

**The ExecutionPlan validation system provides production-ready reliability while maintaining full backward compatibility and excellent performance.**
