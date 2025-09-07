# ExecutionPlan Validation Quick Reference

**Current Implementation Status**: The validation system is **fully functional** and raises detailed `ValueError` exceptions with validation information.

## ✅ Working Validation Examples

### Basic Validation Success
```python
from execution_plan_template import ExecutionPlanBuilder
from execution_plan_schema import TaskType

# This works - valid plan
builder = ExecutionPlanBuilder("Valid Plan")
builder.add_task("research", TaskType.RESEARCH_GENIUS, "Research task")
builder.add_task("design", TaskType.SOLUTION_ARCHITECT, "Design task",
                dependencies=["research"])
plan = builder.build()  # ✅ Validates successfully
print(f"Created plan with {len(plan.tasks)} tasks")
```

### Circular Dependency Detection
```python
# This will raise ValueError with validation details
builder = ExecutionPlanBuilder("Circular Test")
builder.add_task("A", TaskType.GENERAL_PURPOSE, "Task A", dependencies=["B"])
builder.add_task("B", TaskType.GENERAL_PURPOSE, "Task B", dependencies=["A"])

try:
    plan = builder.build()
except ValueError as e:
    if "circular_dependency" in str(e):
        print("✅ Circular dependency correctly detected")
        print(f"Details: {e}")
        # Output: Critical validation errors in ExecutionPlan:
        # [circular_dependency] Circular dependency detected in task chain (Chain: A -> B -> A)
```

### Duplicate Task ID Detection
```python
# This will raise ValueError at add_task time
builder = ExecutionPlanBuilder("Duplicate Test")
builder.add_task("analysis", TaskType.RESEARCH_GENIUS, "Research analysis")

try:
    builder.add_task("analysis", TaskType.SOLUTION_ARCHITECT, "Design analysis")  # Duplicate
except ValueError as e:
    print("✅ Duplicate task ID correctly detected")
    print(f"Details: {e}")
    # Output: Duplicate task ID 'analysis' - task IDs must be unique within a plan
```

### Invalid Dependency Reference
```python
# This will raise ValueError with validation details
builder = ExecutionPlanBuilder("Invalid Reference Test")
builder.add_task("deploy", TaskType.SDLC_DEPLOYMENT, "Deploy application",
                dependencies=["nonexistent_task"])

try:
    plan = builder.build()
except ValueError as e:
    if "invalid_dependency_reference" in str(e):
        print("✅ Invalid dependency reference correctly detected")
        print(f"Details: {e}")
        # Output: Critical validation errors in ExecutionPlan:
        # [invalid_dependency_reference] Task references non-existent dependencies: nonexistent_task (Task: deploy)
```

### Testing Mode (Validation Disabled)
```python
# Skip validation for testing scenarios
builder = ExecutionPlanBuilder("Test Plan")
builder.add_task("A", TaskType.GENERAL_PURPOSE, "Task A", dependencies=["B"])
builder.add_task("B", TaskType.GENERAL_PURPOSE, "Task B", dependencies=["A"])

plan = builder.build(validate=False)  # ✅ No validation error
print(f"Created test plan with {len(plan.tasks)} tasks")

# Manual validation later if needed
from execution_plan_validation import validate_execution_plan
result = validate_execution_plan(plan)
if not result.success:
    print(f"Found {len(result.errors)} validation errors")
```

## 🛠️ Error Handling Patterns

### Recommended Approach
```python
def create_execution_plan_safely(name, task_configs):
    """Create ExecutionPlan with proper error handling"""
    try:
        builder = ExecutionPlanBuilder(name)
        for config in task_configs:
            builder.add_task(**config)

        return builder.build()  # May raise ValueError

    except ValueError as e:
        error_msg = str(e)

        if "circular_dependency" in error_msg:
            print(f"❌ Circular dependency detected in '{name}'")
        elif "invalid_dependency_reference" in error_msg:
            print(f"❌ Invalid task references in '{name}'")
        elif "Duplicate task ID" in error_msg:
            print(f"❌ Duplicate task IDs in '{name}'")
        else:
            print(f"❌ Validation error in '{name}': {e}")

        return None

# Usage
plan = create_execution_plan_safely("My Plan", task_configurations)
if plan:
    print("✅ Plan created successfully")
else:
    print("❌ Plan creation failed")
```

## 📊 Validation Types Currently Supported

| Validation Type | Detection Time | Exception | Status |
|-----------------|----------------|-----------|--------|
| Circular Dependencies | `build()` | `ValueError` | ✅ Working |
| Invalid References | `build()` | `ValueError` | ✅ Working |
| Duplicate Task IDs | `add_task()` | `ValueError` | ✅ Working |
| Self Dependencies | `build()` | `ValueError` | ✅ Working |
| Empty Task Lists | `build()` | `ValueError` | ✅ Working |
| Deep Dependency Chains | `build()` | Warning | ✅ Working |

## 🎯 Key Points

1. **All validation is functional** - The system successfully detects and prevents problematic plans
2. **ValueError exceptions** - Current implementation uses `ValueError` with detailed messages
3. **Early detection** - Duplicate IDs caught at `add_task()`, others at `build()`
4. **Flexible modes** - Can disable validation with `validate=False` for testing
5. **Clear messages** - Error messages include specific details about the problem

## 🚀 Production Usage

```python
# Production pattern - always validate
def create_production_plan():
    builder = ExecutionPlanBuilder("Production Pipeline")
    builder.add_task("research", TaskType.RESEARCH_GENIUS, "Research task")
    builder.add_task("develop", TaskType.DEVELOPMENT_SPECIALIST, "Build solution",
                    dependencies=["research"])

    try:
        return builder.build()  # Validates automatically
    except ValueError as e:
        logger.error(f"ExecutionPlan validation failed: {e}")
        raise  # Re-raise for proper error handling

# Test pattern - flexible validation
def create_test_plan():
    builder = ExecutionPlanBuilder("Test Pipeline")
    # ... add test tasks that might have temporary issues
    return builder.build(validate=False)  # Skip for testing
```

**The ExecutionPlan validation system is production-ready and provides comprehensive error detection to ensure reliable agent orchestration.**
