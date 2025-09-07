# Error Capture Fix Specification

**Issue ID:** ORCH-002  
**Component:** Task Execution Engine  
**Severity:** HIGH  
**Estimated Time:** 1 hour  
**Files to Modify:** 1  

## Problem Statement

Task execution can produce empty error strings when processes fail silently (non-zero exit code with no stderr/stdout). This makes debugging impossible and violates error handling contracts.

## Current Behavior

**Location:** `/home/opsvi/master_root/apps/agent-orchestrator/src/generic_orchestrator.py`  
**Lines:** 630-649

When a subprocess fails:
1. Error parts are built from stderr/stdout (lines 635-648)
2. Parts are joined with " | " separator (line 649)
3. **BUG:** If all parts are informational (e.g., "No stderr output"), the error string can be empty or unhelpful

## Root Cause

The error string construction at line 649 doesn't guarantee a non-empty, meaningful error message. When a process fails silently, we get:
- stderr: empty → "No stderr output"
- stdout: empty → not added
- Exit code: added
- Task ID: added

Result: `"No stderr output | Exit code: 1 | Task: task_id"` which sometimes gets stripped to empty.

## Implementation Details

### File: `/home/opsvi/master_root/apps/agent-orchestrator/src/generic_orchestrator.py`

#### Modification 1: Add Final Error Validation (Line 649)

**Current Code (lines 649-650):**
```python
task.error = " | ".join(error_parts)
task.raw_output = stdout.decode() if stdout else None  # Preserve for debugging
```

**New Code:**
```python
task.error = " | ".join(error_parts)

# CRITICAL: Ensure error is never empty
if not task.error or task.error.strip() == "":
    task.error = f"Task {task.task_id} failed with exit code {process.returncode} but no error details were captured"
elif task.error.strip() in ["No stderr output", "No stderr output | ", "| No stderr output"]:
    # Handle edge case where only boilerplate text exists
    task.error = f"Task {task.task_id} failed silently with exit code {process.returncode} (no stderr/stdout)"

task.raw_output = stdout.decode() if stdout else None  # Preserve for debugging
```

#### Modification 2: Improve Error Building Logic (Lines 635-638)

**Current Code:**
```python
if stderr and stderr.strip():
    error_parts.append(f"Stderr: {stderr.decode().strip()}")
else:
    error_parts.append("No stderr output")
```

**New Code:**
```python
if stderr and stderr.strip():
    error_parts.append(f"Stderr: {stderr.decode().strip()}")
# Remove the else clause - don't add "No stderr output" as it's not helpful
```

#### Modification 3: Add Command Information (After line 634)

**Add after line 634:**
```python
# Include the command that failed for better debugging
if hasattr(task, 'agent_type'):
    error_parts.append(f"Command: {task.agent_type}")
```

## Complete Fixed Code Block

```python
# Lines 630-655 after fix
else:
    task.status = "failed"
    # Build comprehensive error from available information
    error_parts = []
    
    # Include the command that failed for better debugging
    if hasattr(task, 'agent_type'):
        error_parts.append(f"Command: {task.agent_type}")
    
    if stderr and stderr.strip():
        error_parts.append(f"Stderr: {stderr.decode().strip()}")
    
    if stdout and stdout.strip():
        # Include stdout in error for debugging
        stdout_str = stdout.decode()
        preview = stdout_str[:500] if len(stdout_str) > 500 else stdout_str
        error_parts.append(f"Stdout: {preview}")
    
    error_parts.append(f"Exit code: {process.returncode}")
    error_parts.append(f"Task: {task.task_id}")
    
    task.error = " | ".join(error_parts)
    
    # CRITICAL: Ensure error is never empty
    if not task.error or task.error.strip() == "":
        task.error = f"Task {task.task_id} failed with exit code {process.returncode} but no error details were captured"
    elif task.error.strip() in ["No stderr output", "No stderr output | ", "| No stderr output"]:
        # Handle edge case where only boilerplate text exists
        task.error = f"Task {task.task_id} failed silently with exit code {process.returncode} (no stderr/stdout)"
    
    task.raw_output = stdout.decode() if stdout else None  # Preserve for debugging
    
    await self.dep_manager.mark_failed(task.task_id)
    self.metrics["failed"] += 1

    logger.error(f"✗ {task.task_id} failed: {task.error}")
```

## Testing Requirements

### Unit Tests to Add

1. **Test Silent Failure:**
```python
async def test_silent_process_failure():
    """Test that silent failures produce meaningful error messages"""
    task = AgentTask(
        task_id="silent_fail",
        agent_type="exit-1-silent",
        prompt="Exit with code 1 without output"
    )
    # Mock subprocess to return exit_code=1, stderr=b"", stdout=b""
    # Verify task.error is not empty and contains meaningful message
```

2. **Test Whitespace-Only Output:**
```python
async def test_whitespace_only_stderr():
    """Test that whitespace-only stderr produces meaningful errors"""
    task = AgentTask(
        task_id="whitespace_fail",
        agent_type="whitespace-error",
        prompt="Fail with whitespace stderr"
    )
    # Mock subprocess to return exit_code=1, stderr=b"   \n  ", stdout=b""
    # Verify task.error is not empty
```

3. **Test Error String Edge Cases:**
```python
async def test_error_string_edge_cases():
    """Test various edge cases in error string construction"""
    test_cases = [
        (b"", b"", 1),  # Empty stderr/stdout
        (b"   ", b"   ", 1),  # Whitespace only
        (b"\n\n", b"\n\n", 1),  # Newlines only
        (None, None, 1),  # None values
    ]
    # For each case, verify non-empty error message
```

## Validation Criteria

### Success Metrics
1. No task execution can produce an empty error string
2. All failed tasks have meaningful error messages
3. Error messages include relevant debugging information
4. Silent failures are clearly identified

### Validation Commands
```bash
# Run specific error handling tests
python -m pytest tests/test_error_handling.py -v

# Run validation suite error scenarios
python orchestrator_validation_suite.py --test error_handling

# Check for empty errors in logs
grep -E '"error":\s*""' unified_orchestrator_validation_*/logs/*.json | wc -l
# Expected: 0
```

## Implementation Notes

1. **Preserve Existing Behavior:** The fix maintains backward compatibility while ensuring non-empty errors
2. **Minimal Changes:** Only 3 small modifications to guarantee error quality
3. **No Dependencies:** This fix is independent and can be applied immediately
4. **Performance:** No performance impact - only adds simple string checks

## Rollback Plan

If issues occur, revert changes to lines 635-655 in `generic_orchestrator.py`.

## Agent Instructions

**For: error_capture_specialist**

1. Navigate to `/home/opsvi/master_root/apps/agent-orchestrator/src/generic_orchestrator.py`
2. Locate lines 630-655 (the error handling section in execute_task method)
3. Apply the three modifications described above
4. Add unit tests as specified
5. Run validation suite to confirm fix
6. Document any edge cases discovered

**Success Criteria:**
- Zero empty error strings in all test scenarios
- All failed tasks have actionable error messages
- Validation suite error_handling tests pass