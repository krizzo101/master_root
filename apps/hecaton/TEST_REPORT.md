# HECATON Comprehensive Test Report

Generated: 2025-09-02 07:56:17

## Summary

- **Total Tests**: 10
- **Passed**: 0 (0.0%)
- **Failed**: 10 (100.0%)
- **Unique Error Types**: 0

## Test Results by Mode

### Simple Mode

### Simple Mode
- Tests: 5
- Passed: 0
- Failed: 5
- Avg Duration: 3.15s

| Test | Agents | Success | Duration | Errors |
|------|--------|---------|----------|--------|
| simple_1agents | 1 | ❌ | 2.75s | 0 |
| simple_2agents | 2 | ❌ | 3.44s | 0 |
| simple_1agents_verbose | 1 | ❌ | 1.99s | 0 |
| simple_2agents | 2 | ❌ | 3.04s | 0 |
| simple_3agents | 3 | ❌ | 4.55s | 0 |

### Send-Api Mode
- Tests: 2
- Passed: 0
- Failed: 2
- Avg Duration: 3.49s

| Test | Agents | Success | Duration | Errors |
|------|--------|---------|----------|--------|
| send-api_1agents | 1 | ❌ | 3.04s | 0 |
| send-api_2agents | 2 | ❌ | 3.95s | 0 |

### Enhanced Mode
- Tests: 3
- Passed: 0
- Failed: 3
- Avg Duration: 0.17s

| Test | Agents | Success | Duration | Errors |
|------|--------|---------|----------|--------|
| enhanced_1agents | 1 | ❌ | 0.18s | 0 |
| enhanced_2agents | 2 | ❌ | 0.16s | 0 |
| enhanced_2agents | 2 | ❌ | 0.18s | 0 |


## Error Analysis

### Error Types Distribution


## Identified Issues and Patches

### 1. Missing 'metrics' field (FIXED)
**Issue**: Enhanced orchestrator's `_execute_complex_task` doesn't return metrics
**Solution**: Added metrics calculation to return structure
**Status**: ✅ Patched

### 2. Timeout Issues
**Issue**: Send-api and Enhanced modes timeout frequently
**Possible Causes**:
- Deadlock in async execution
- Infinite loop in task decomposition
- Token pool exhaustion
**Status**: ⚠️ Needs investigation

## Recommendations

1. **Critical**: Fix timeout issues in send-api and enhanced modes
2. **Important**: Add proper error handling for missing fields
3. **Nice-to-have**: Improve verbose output formatting
4. **Testing**: Add unit tests for each mode

## Detailed Error Log
