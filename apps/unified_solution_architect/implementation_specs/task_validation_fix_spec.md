# Task Type Validation Fix Specification

**Issue ID:** ORCH-005  
**Component:** Task Type Validation  
**Severity:** MEDIUM  
**Estimated Time:** 30 minutes  
**Files to Modify:** 2  

## Problem Statement

The invalid task type `test-remediation-specialist` appears in multiple files but is not in the approved task type list. This causes validation failures when tasks are executed with this deprecated type.

## Current Behavior

**Invalid Task Type:** `test-remediation-specialist`  
**Occurrences:** 
- `/home/opsvi/master_root/apps/agent-orchestrator/examples/unified_orchestrator_demo.py` - Lines 126, 383, 578, 616
- `/home/opsvi/master_root/apps/agent-orchestrator/archive/execution_plan_schema.py` - Line 53

## Valid Task Types

Based on validation test `test_task_type_validation.py`, the valid types are:

### Architecture & Design
- `security-architect`
- `solution-architect`
- `requirements-analyst`

### Development & Testing
- `development-specialist`
- `qa-testing-guru`
- `performance-optimizer`

### Integration & Data
- `api-integration-specialist`
- `database-specialist`

### Analysis & Documentation
- `business-analyst`

## Implementation Details

### File 1: `/home/opsvi/master_root/apps/agent-orchestrator/examples/unified_orchestrator_demo.py`

#### Line 126 - Test Remediation Task
**Current:**
```python
task_type="test-remediation-specialist",
```

**Replace with:**
```python
task_type="qa-testing-guru",
```

#### Line 383 - Automated Test Suite
**Current:**
```python
task_type="test-remediation-specialist",
```

**Replace with:**
```python
task_type="qa-testing-guru",
```

#### Line 578 - Complex Test Scenario
**Current:**
```python
task_type="test-remediation-specialist",
```

**Replace with:**
```python
task_type="qa-testing-guru",
```

#### Line 616 - Test Verification
**Current:**
```python
task_type="test-remediation-specialist",
```

**Replace with:**
```python
task_type="qa-testing-guru",
```

### File 2: `/home/opsvi/master_root/apps/agent-orchestrator/archive/execution_plan_schema.py`

#### Line 53 - Task Type Enum Definition
**Current:**
```python
"test-remediation-specialist",  # In enum list
```

**Replace with:**
```python
"qa-testing-guru",  # Updated task type
```

## Validation Criteria

### Success Metrics
1. All task types in codebase are in approved list
2. No validation failures for task type checking
3. Demo scripts run without task type errors

### Validation Commands
```bash
# Check for any remaining invalid task types
grep -r "test-remediation-specialist" /home/opsvi/master_root/apps/agent-orchestrator/
# Expected: No results

# Verify all task types are valid
python -m pytest tests/test_task_type_validation.py -v
# Expected: All tests pass

# Run demo to ensure no runtime errors
python examples/unified_orchestrator_demo.py --validate-only
# Expected: No task type validation errors
```

## Testing Requirements

### Pre-change Testing
```bash
# Capture current failures
grep "test-remediation-specialist" examples/unified_orchestrator_demo.py | wc -l
# Expected: 4 occurrences
```

### Post-change Testing
```bash
# Verify replacements
grep "qa-testing-guru" examples/unified_orchestrator_demo.py | wc -l
# Expected: 4 occurrences (where test-remediation-specialist was)

# Ensure no invalid types remain
grep "test-remediation-specialist" examples/unified_orchestrator_demo.py | wc -l
# Expected: 0 occurrences
```

## Implementation Notes

1. **Simple Find/Replace:** This is a straightforward string replacement
2. **Context Preservation:** The replacement `qa-testing-guru` maintains the testing context
3. **No Logic Changes:** Only string literals are changed, no logic modifications
4. **Archive File:** The schema file in `archive/` should also be updated for consistency

## Rollback Plan

If issues occur, revert the changes:
```bash
# Revert changes in demo file
git checkout -- examples/unified_orchestrator_demo.py

# Revert changes in schema file
git checkout -- archive/execution_plan_schema.py
```

## Agent Instructions

**For: task_validation_specialist**

1. Open `/home/opsvi/master_root/apps/agent-orchestrator/examples/unified_orchestrator_demo.py`
2. Replace all 4 occurrences of `test-remediation-specialist` with `qa-testing-guru`
   - Line 126
   - Line 383
   - Line 578
   - Line 616
3. Open `/home/opsvi/master_root/apps/agent-orchestrator/archive/execution_plan_schema.py`
4. Replace the occurrence on line 53
5. Run validation commands to confirm fix
6. Search for any other occurrences of invalid task types

**Success Criteria:**
- Zero occurrences of `test-remediation-specialist` in codebase
- All task type validation tests pass
- Demo scripts execute without task type errors

## Additional Considerations

### Future Prevention
1. Add pre-commit hook to validate task types
2. Create central task type registry
3. Add runtime validation against approved list

### Related Files to Check
After fixing the main files, verify no other files use invalid task types:
```bash
# Search for other potential invalid types
grep -r "remediation" --include="*.py" /home/opsvi/master_root/apps/agent-orchestrator/
```