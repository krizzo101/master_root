# Logging Usage Report

Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

## Python Hook Scripts in .claude/hooks/

### 1. answer_review.py (274 lines)
**Current State:** Uses try/except blocks, returns JSON responses, no logging
**Key Functions to Instrument:**
- `call_review()` - Makes OpenAI API calls
- `read_last_items()` - Reads transcript file
- `get_output_text()` - Extracts text from API response
- `main()` - Main entry point with exception handling

**Suggested Debug Points:**
```python
# Line 141: Before API call
if os.getenv('DEBUG'): print(f"DEBUG: answer_review.py:call_review() -- calling model={model} with {len(prev5)} previous prompts", file=sys.stderr)

# Line 155: After API response
if os.getenv('DEBUG'): print(f"DEBUG: answer_review.py:call_review() -- response status={resp.status if hasattr(resp, 'status') else 'unknown'}", file=sys.stderr)

# Line 195: Main entry
if os.getenv('DEBUG'): print(f"DEBUG: answer_review.py:main() -- session_id={session_id}, stop_hook_active={stop_hook_active}", file=sys.stderr)

# Line 262: Exception handler
if os.getenv('DEBUG'): print(f"DEBUG: answer_review.py:main() -- exception={e}", file=sys.stderr)
```

### 2. prompt_opt.py (231 lines)
**Current State:** Uses try/except blocks, returns JSON responses, no logging
**Key Functions to Instrument:**
- `main()` - Main entry point
- `get_output_text()` - Extracts text from API response
- `last_user_prompts()` - Reads transcript

**Suggested Debug Points:**
```python
# Line 112: Main entry
if os.getenv('DEBUG'): print(f"DEBUG: prompt_opt.py:main() -- user_prompt='{user_prompt[:50]}...'", file=sys.stderr)

# Line 162: Before API call
if os.getenv('DEBUG'): print(f"DEBUG: prompt_opt.py:main() -- calling model={MODEL} with max_tokens={MAX_TOK}", file=sys.stderr)

# Line 182: After response processing
if os.getenv('DEBUG'): print(f"DEBUG: prompt_opt.py:main() -- optimized={bool(optimized)}, research_flag={research_flag}", file=sys.stderr)

# Line 219: Exception handler
if os.getenv('DEBUG'): print(f"DEBUG: prompt_opt.py:main() -- exception={e}", file=sys.stderr)
```

### 3. safety_gate.py (48 lines)
**Current State:** Uses sys.stderr.write for errors
**Key Functions to Instrument:**
- `main()` - Main entry point
- `fail()` - Error handler

**Suggested Debug Points:**
```python
# Line 13: Main entry
if os.getenv('DEBUG'): print(f"DEBUG: safety_gate.py:main() -- tool={tool}, path={path}", file=sys.stderr)

# Line 37: Block decision
if os.getenv('DEBUG'): print(f"DEBUG: safety_gate.py:main() -- blocking edit to {path}", file=sys.stderr)

# Line 39: Block decision
if os.getenv('DEBUG'): print(f"DEBUG: safety_gate.py:main() -- blocking command: {cmd[:50]}...", file=sys.stderr)

# Line 43: Exception handler
if os.getenv('DEBUG'): print(f"DEBUG: safety_gate.py:main() -- exception={e}", file=sys.stderr)
```

### 4. auto-export-on-compact.py (103 lines)
**Current State:** Already uses print to stderr for status messages
**Key Functions to Instrument:**
- `export_session()` - Main export logic
- `main()` - Entry point

**Suggested Debug Points:**
```python
# Line 25: Function entry
if os.getenv('DEBUG'): print(f"DEBUG: auto-export-on-compact.py:export_session() -- transcript_path={transcript_path}", file=sys.stderr)

# Line 82: Before export
if os.getenv('DEBUG'): print(f"DEBUG: auto-export-on-compact.py:export_session() -- exporting to {export_path}", file=sys.stderr)
```

### 5. test_acceptance.py (0 lines - file might be empty or not exist)
**Current State:** File not found or empty
**Action:** Skip

## Shell Scripts in .claude/hooks/

### 1. export-session.sh
**Current State:** Uses echo for logging to hook.log file
**Suggested Debug Points:**
```bash
# Add at script start
[ "$DEBUG" = "1" ] && echo "DEBUG: export-session.sh -- starting with args: $*" >&2

# Before key operations
[ "$DEBUG" = "1" ] && echo "DEBUG: export-session.sh -- exporting to $EXPORT_PATH" >&2
```

### 2. pre-edit.sh
**Current State:** Uses echo for warnings
**Suggested Debug Points:**
```bash
# Add at script start
[ "$DEBUG" = "1" ] && echo "DEBUG: pre-edit.sh -- checking file: $1" >&2
```

## Summary

**Total Files to Modify:** 5 Python scripts, 2 Shell scripts
**Debug Environment Variable:** `DEBUG` (set to "1" to enable)
**Output Target:** stderr (to avoid interfering with JSON responses)
**Guard Pattern:** `if os.getenv('DEBUG'):` for Python, `[ "$DEBUG" = "1" ] &&` for Shell

## Implementation Priority
1. answer_review.py - Critical for debugging review logic
2. prompt_opt.py - Critical for debugging prompt optimization
3. safety_gate.py - Important for security debugging
4. Shell scripts - Lower priority
5. auto-export-on-compact.py - Already has some debug output
