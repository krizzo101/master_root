# Claude Code Self-Analysis

## Executive Summary

This document analyzes the capabilities and behavior of Claude Code in headless mode for orchestration purposes.

**Last Updated:** 2025-01-13
**Environment:** Claude Code CLI

---

## 1. Core Execution Modes

### 1.1 Interactive Mode (Default)
```bash
claude  # Starts interactive session
```
- Starts interactive session requiring human input
- **Orchestration Use:** Not suitable for automation

### 1.2 Headless/Print Mode
```bash
claude --print -p "prompt"  # Single execution and exit
```
- Executes and exits immediately
- **Orchestration Use:** Primary mode for automation

### 1.3 Continuation Modes
```bash
claude --continue           # Continue most recent conversation
claude --resume <session>   # Resume specific session
```
- **Behavior:**
  - `--continue`: Continues recent conversation ✓
  - `--resume`: Creates NEW session ID (branches) ✓
  - Cannot combine `--session-id` with `--resume` ✓

---

## 2. Output Formats

### 2.1 Text Format
```bash
claude --print --output-format text -p "prompt"
```
**Result:** Returns plain text

### 2.2 JSON Format
```bash
claude --print --output-format json -p "prompt"
```
**Verified Structure:**
```json
{
  "type": "result",
  "subtype": "success",
  "is_error": false,
  "duration_ms": 2267,
  "duration_api_ms": 3022,
  "num_turns": 1,
  "result": "response text",
  "session_id": "uuid-format",
  "total_cost_usd": 0.027365,
  "usage": {
    "input_tokens": 3,
    "cache_creation_input_tokens": 285,
    "cache_read_input_tokens": 14301,
    "output_tokens": 7
  }
}
```
**Result:** Valid JSON with cost and token tracking

### 2.3 Stream-JSON Format
```bash
--output-format stream-json
```
**Status:** NOT TESTED

---

## 3. Permission Modes

### 3.1 Plan Mode
```bash
--permission-mode plan
```
**Test:** Create file command
**Result:** File NOT created, only described plan ✓

### 3.2 BypassPermissions Mode
```bash
--permission-mode bypassPermissions
```
**Test:** Create file command
**Result:** File created without prompting ✓

### 3.3 Default Mode
```bash
--permission-mode default
```
**Observed:** Behavior varies by environment

### 3.4 AcceptEdits Mode
```bash
--permission-mode acceptEdits
```
**Status:** NOT TESTED

---

## 4. Model Selection

### 4.1 Opus Model
```bash
--model opus
```
**Response:** "I'm Claude, powered by the Opus 4.1 model (claude-opus-4-1-20250805)" ✓

### 4.2 Sonnet Model
```bash
--model sonnet
```
**Response:** "I'm Claude Sonnet 4 (model ID: claude-sonnet-4-20250514)" ✓

### 4.3 Fallback Model
```bash
--fallback-model <model>
```
**Status:** NOT TESTED

---

## 5. Session Management

### 5.1 Session ID Requirements
- - Must be valid UUID format
- **Error for invalid ID:** "Error: Invalid session ID. Must be a valid UUID."

### 5.2 Resume Creates New Sessions
**Test Results:**
```
Original session: c8bcc2dd-18c1-4004-8bbd-73e409766004
After --resume:   d53009f5-c5d7-4f93-b223-4b303523a290
```
**Result:** Resume creates new session (branches conversation)

### 5.3 Multiple Agents Can Resume Same Session
```
Original: c8bcc2dd-18c1-4004-8bbd-73e409766004
Agent A:  c131c27c-1739-4213-ba50-01b2d484a013  
Agent B:  2dab3a79-296f-4f5d-9f8e-2f0c1a91de74
```
**Result:** Each creates independent branch

### 5.4 Flag Incompatibility
- Cannot use `--session-id` with `--resume`
**Error:** "Error: --session-id cannot be used with --continue or --resume."

---

## 6. System Prompt Customization

```bash
--append-system-prompt "Additional instructions"
```
**Test:** Added "Always respond with exactly 'MODIFIED'"
**Result:** Response included "MODIFIED" ✓
**Result:** System prompt modification works

---

## 7. Tool Access Control

### 7.1 Tool Restriction Flags
```bash
--allowedTools "Read,Write"
--disallowedTools "Bash"
```
**Observed:** In test environment, restrictions appeared ineffective
**Status:** INCONCLUSIVE - may depend on environment configuration

---

## 8. Directory Access

### 8.1 Add Directory
```bash
--add-dir /path/one --add-dir /path/two
```
- Flag exists and is accepted

### 8.2 Remove Directory
- No `--remove-dir` flag exists

---

## 9. Performance Metrics

### 9.1 Measured Execution Times
```
With empty MCP config: 3487ms
With default config:   3633ms
```
**Note:** No significant difference observed with/without MCP configuration

### 9.2 JSON Metrics
**Verified Fields:**
- `duration_ms`: Total execution time
- `duration_api_ms`: API call time  
- `total_cost_usd`: Cost per execution
- `usage`: Detailed token breakdown

---

## 10. Environment Variables

**Present in environment:**
```bash
CLAUDE_CODE_TOKEN: sk-ant-oat01-...
CLAUDE_CODE_MAX_OUTPUT_TOKENS: 8192
CLAUDE_CODE_SSE_PORT: 33023
CLAUDE_CODE_ENTRYPOINT: cli
CLAUDECODE: 1
ANTHROPIC_API_KEY: [empty in test environment]
```

---

## 11. MCP Configuration

### 11.1 MCP Flags
```bash
--mcp-config <file>
--strict-mcp-config
```
- Flags accepted by CLI
**Note:** No MCP tools (mcp__ prefix) detected in test environment

---

## 12. Conversation Branching

### Test Scenario
```
Parent session: Knows [42]
├─ Agent A resumes → New session, knows [42, "Sky is blue"]  
└─ Agent B resumes → New session, knows [42, "Grass is green"]

Parent still knows: [42] only
```

**Behaviors:**
1. Each resume creates independent branch
2. Parent conversation unchanged
3. No automatic merging
4. Full history inherited to branches

---

## 13. Command-Line Flags (from --help)

**Available flags:**
- `-p, --print` - Non-interactive output
- `--output-format` - text, json, stream-json
- `--permission-mode` - acceptEdits, bypassPermissions, default, plan
- `--model` - Model selection
- `--session-id` - Specific session UUID
- `--resume` - Resume conversation (creates branch)
- `--continue` - Continue most recent
- `--append-system-prompt` - Add to system prompt
- `--add-dir` - Additional directories
- `--allowedTools` - Tool whitelist
- `--disallowedTools` - Tool blacklist
- `--mcp-config` - MCP configuration file
- `--strict-mcp-config` - Only use specified MCP
- `--dangerously-skip-permissions` - Bypass all permissions
- `--verbose` - Verbose output
- `--debug` - Debug mode

---

## 14. Key Findings for Orchestration

### Capabilities
1. **Session branching** - Parallel exploration possible
2. **JSON output** - Reliable structure with metadata
3. **Cost tracking** - Every response includes cost
4. **Token metrics** - Detailed usage statistics
5. **Permission control** - Plan vs bypass modes work
6. **Model selection** - Can specify different models
7. **System prompt customization** - Can specialize behavior

### Limitations
1. **No session merging** - Branches remain separate
2. **No --remove-dir** - Can only add directories
3. **UUID requirement** - Session IDs must be valid UUIDs
4. **Flag incompatibility** - Some flags cannot be combined

### Not Tested
1. **MCP server behavior** - No MCP tools found in environment
2. **Tool restrictions** - Appeared ineffective in tests
3. **Stream-JSON details** - Not fully tested
4. **Fallback model** - Not tested

---

## 15. Optimal Orchestration Pattern

Based on tested components:
```bash
claude --print \
  --output-format json \                    # ✓ Machine parseable
  --permission-mode bypassPermissions \     # ✓ No prompts
  --model opus \                            # ✓ Model selection
  --append-system-prompt "Role: analyst" \  # ✓ Specialization
  --resume $PARENT_SESSION \                # ✓ Branch from parent
  -p "Task description"
```

---

## Testing Methodology

Testing methodology:
1. Direct execution of `claude` binary
2. Output observation and parsing
3. File system verification
4. Error message capture
5. Timing measurements

**Not Included:**
- Assumptions
- Untested features  
- Extrapolated behaviors
- Claims from documentation without verification