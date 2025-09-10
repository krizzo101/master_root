# Agent Orchestrator - Issues & Remediation Plan

## Issues Found

### 1. ❌ Invalid Session ID Format
**Problem**: Session ID is `task_id_hexstring` instead of valid UUID
**Line**: `session_id = f"{task.task_id}_{uuid.uuid4().hex[:8]}"`
**Fix**: Use proper UUID: `session_id = str(uuid.uuid4())`

### 2. ❌ Missing Token Check
**Problem**: No CLAUDE_CODE_TOKEN environment variable set
**Fix**: Need to check for token before running

### 3. ❌ Output Directory Not Created
**Problem**: `output` directory may not exist
**Fix**: Ensure directory creation in `__init__`

### 4. ❌ Wrong Prompt Format
**Problem**: Sending raw prompt string instead of using `--` separator
**Fix**: Update command construction

### 5. ⚠️ Missing Error Details
**Problem**: stderr not showing full error details
**Fix**: Better error logging

## Testing Gaps

### Missing:
1. Token validation before execution
2. Claude CLI availability check
3. Minimal config validation
4. Proper command line argument handling
5. JSON parsing error handling

## Dependencies Not Documented

### Required but not mentioned:
1. `CLAUDE_CODE_TOKEN` environment variable
2. `claude` CLI installed and in PATH
3. Valid `.claude_minimal.json` config

## Remediation Plan

### Step 1: Fix Critical Bugs
- [ ] Fix session ID generation
- [ ] Add token validation
- [ ] Fix command construction
- [ ] Ensure output directory exists

### Step 2: Add Validation
- [ ] Check for claude CLI
- [ ] Validate token exists
- [ ] Verify minimal config

### Step 3: Improve Error Handling
- [ ] Better error messages
- [ ] Graceful degradation
- [ ] Setup instructions on failure

### Step 4: Add Tests
- [ ] Unit tests for orchestrator
- [ ] Integration test with mock claude
- [ ] End-to-end test with real claude
