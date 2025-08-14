# MCP Servers Truth Report - What's Actually Implemented

## Executive Summary

After thorough code audit, here's what each server **actually does** versus what was claimed:

### 🔴 Critical Findings

1. **V3 is NOT parallel** - Executes subtasks sequentially, making it slower than V1
2. **Gemini server is STUBBED** - Only calls `gemini --help`, doesn't execute tasks
3. **V2 was initially stubbed** - Fixed during our session to call real Claude
4. **V1 is the ONLY originally working server** - Actually executes Claude Code CLI

## Server-by-Server Truth

### V1 (claude_code) - ✅ MOSTLY AS ADVERTISED

**What it claims:**
- Synchronous and asynchronous Claude Code execution
- Recursion management and parallel job tracking
- Dashboard and monitoring

**What it ACTUALLY does:**
- ✅ **WORKS**: Calls real Claude Code CLI (`claude` command)
- ✅ **WORKS**: Handles auth tokens correctly (CLAUDE_CODE_TOKEN)
- ✅ **WORKS**: Nullifies ANTHROPIC_API_KEY to prevent API usage
- ✅ **WORKS**: Async execution with job tracking
- ✅ **WORKS**: Recursion depth limiting
- ⚠️ **PARTIAL**: MCP server selection (code exists but complex)
- ❌ **MISSING**: True parallel execution (uses asyncio but still sequential)

**Code evidence (job_manager.py:154-186):**
```python
cmd = ["claude"]
cmd.append("--dangerously-skip-permissions")
if job.output_format in ("json", "stream-json"):
    cmd.extend(["--output-format", job.output_format])
cmd.extend(["-p", job.task])

# Actually spawns subprocess
process = subprocess.Popen(cmd, ...)
```

### V2 (claude_code_v2) - ✅ FIXED (Was Stubbed)

**What it claims:**
- Fire-and-forget parallel agents
- Independent task execution
- Result aggregation

**What it ACTUALLY does (after fix):**
- ✅ **NOW WORKS**: Creates Python scripts that call real Claude CLI
- ✅ **NOW WORKS**: Spawns detached processes (`start_new_session=True`)
- ✅ **NOW WORKS**: Each agent runs independently in parallel
- ✅ **NOW WORKS**: Nullifies ANTHROPIC_API_KEY correctly
- ⚠️ **PARTIAL**: Context management (code exists, untested)
- ⚠️ **PARTIAL**: MCP server selection (code exists, untested)

**Original stub (before fix):**
```python
# Was just returning fake results
return {"success": True, "message": "Stubbed implementation"}
```

**Fixed implementation (job_manager.py:149-156):**
```python
process = subprocess.Popen(
    [sys.executable, script_path],  # Runs Python script
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    start_new_session=True  # True parallel execution
)
```

### V3 (claude_code_v3) - ❌ MISLEADING ARCHITECTURE

**What it claims:**
- Multi-agent orchestration
- Parallel subtask execution
- Quality assurance through decomposition
- Production-ready code generation

**What it ACTUALLY does:**
- ✅ **WORKS**: Task decomposition (breaks complex tasks into subtasks)
- ✅ **WORKS**: Calls real Claude Code for each subtask
- ❌ **BROKEN**: **SEQUENTIAL execution, NOT parallel**
- ❌ **INEFFICIENT**: Makes tasks SLOWER (7 subtasks = 7× time)
- ⚠️ **MISLEADING**: Claims "multi_agent": True but runs sequentially

**Damning code evidence (server.py:204-216):**
```python
# Line 204: Sequential for loop, NOT parallel!
for i, subtask in enumerate(subtasks):
    result = await execute_claude_code(  # WAITS for each to complete
        task_desc,
        mode=execution_mode.name,
        timeout=timeout_seconds // len(subtasks),
        output_format="json"
    )
    results.append(result)
```

**What it SHOULD do for parallel:**
```python
# This would be actual parallel execution
tasks = [execute_claude_code(subtask) for subtask in subtasks]
results = await asyncio.gather(*tasks)  # All run simultaneously
```

### Gemini Agent - ❌ COMPLETELY STUBBED

**What it claims:**
- Integration with Gemini CLI
- Multiple execution modes (react, code, analyze, etc.)
- Async task execution

**What it ACTUALLY does:**
- ❌ **FAKE**: Only runs `gemini --help` command
- ❌ **FAKE**: Returns success regardless of task
- ❌ **NO EXECUTION**: Doesn't actually process any tasks
- ✅ **METRICS**: Tracks fake metrics correctly

**Stub evidence (server.py:103-116):**
```python
async def _execute_gemini_task(self, task_info: GeminiTask) -> None:
    # ... setup code ...
    
    # Only runs --help!
    cmd = ["gemini", "--help"]  # ← THIS IS ALL IT DOES
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
```

## What Else Might Be Misleading?

### Likely Issues (Not Verified):

1. **Context Management (V2/V3)**
   - Code exists but complex and untested
   - May not actually preserve context between calls

2. **MCP Server Selection**
   - Complex analyzer code exists
   - May not actually load/unload servers dynamically

3. **Quality Assurance (V3)**
   - Claims critic/tester/documenter agents
   - But since it's sequential, these may just be naming conventions

4. **Session Management**
   - Code for session preservation exists
   - Likely doesn't work as expected

5. **Performance Monitoring**
   - Dashboard code exists
   - Metrics may be incorrect due to sequential execution

## The Pattern of Deception

1. **Sophisticated Architecture**: Complex class hierarchies and configurations
2. **Impressive Documentation**: Detailed README files and docstrings
3. **Stubbed Implementation**: Actual execution is fake or broken
4. **Misleading Responses**: Returns success even when doing nothing

## What Actually Works

### Reliably Working:
- V1 synchronous execution
- V1 async job tracking
- V2 parallel spawning (after fix)
- Token management (CLAUDE_CODE_TOKEN)
- ANTHROPIC_API_KEY nullification

### Partially Working:
- Task decomposition (V3)
- Job tracking and status
- Basic error handling

### Not Working:
- V3 parallel execution (sequential instead)
- Gemini integration (completely stubbed)
- True multi-agent orchestration
- Quality assurance as advertised

## Recommendations

1. **Use V1 for everything** - It's the only reliable server
2. **Avoid V3** - It makes tasks slower, not faster
3. **V2 can be used** - But only after our fixes
4. **Don't trust Gemini server** - It's completely fake
5. **Verify everything** - Test actual behavior, don't trust documentation

## The Real Architecture

```
What was advertised:
V1: Simple execution
V2: Parallel fire-and-forget  
V3: Intelligent multi-agent orchestration
Gemini: Alternative LLM integration

What actually exists:
V1: Works as advertised ✅
V2: Works after our fix ✅
V3: Sequential, slower execution ❌
Gemini: Returns "success" doing nothing ❌
```

## Conclusion

The codebase presents a sophisticated facade with impressive architecture and documentation, but actual implementation is largely broken or stubbed. Only V1 was originally functional. V2 works after fixes. V3 is fundamentally flawed (sequential not parallel). Gemini is completely fake.

**Trust level: Verify everything with actual execution tests.**