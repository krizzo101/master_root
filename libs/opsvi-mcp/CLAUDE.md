# CLAUDE.md - Project Guidelines and Server Selection

## File Management Rules (ALL FILES - Code, Docs, Config, Scripts)

### MANDATORY for ALL file types
1. **UPDATE existing files** - Never create duplicate versions
2. **NO versioning in filenames** - No "v2", "verified", "final", "updated", "new", "fixed" suffixes
3. **Single source of truth** - One authoritative file per purpose
4. **Direct updates only** - Fix errors in place, don't create new files
5. **No parallel implementations** - Don't create alternate versions of same functionality

### Quality Standards
- Only include tested and observed behavior
- Mark untested features as "NOT TESTED"
- No assumptions or guesses presented as facts
- No meta-commentary about verification processes or corrections
- Content should stand on its own merit

## Claude Code Server Selection Reference

## 🚀 Quick Start: Which Server Should I Use?

### 🆕 Context-Aware Execution (V2/V3 Enhanced)
All V2 and V3 servers now support:
- **Dynamic context accumulation** between execution phases
- **Intelligent agent specialization** based on task analysis
- **Custom system prompts** for role-specific behavior
- **Session management** for conversation continuity
- **Selective MCP loading** for 3-5x faster startup

## Original Server Selection Guide

### Use V1 (`mcp__claude-code-wrapper`) when:
- 🔍 **Debugging** or investigating issues
- 💬 **Interactive** development needed
- 📝 **Simple** single-task operations
- ⏱️ **Immediate** response required
- 🔗 Tasks have **dependencies** on each other

### Use V2 (`mcp__claude-code-v2`) when:
- 📊 **Analyzing** multiple files/repos
- 🔄 **Parallel** independent tasks
- 📦 **Batch** processing needed
- ⚡ **Speed** is critical for many tasks
- 🔥 **Fire-and-forget** pattern preferred

### Use V3 (`mcp__claude-code-v3`) when:
- 🏭 **Production-ready** code needed
- ✅ **Quality assurance** required
- 🎯 **Complex** multi-component systems
- 📚 Need **tests and documentation**
- 🤖 **Multi-agent** orchestration beneficial

---

## 📊 Server Selection Cheat Sheet

```python
# Quick selection logic
def select_claude_server(prompt: str) -> str:
    prompt_lower = prompt.lower()
    
    # V1 Triggers
    if any(word in prompt_lower for word in ['debug', 'fix', 'error', 'why', 'help me']):
        return 'mcp__claude-code-wrapper__claude_run'
    
    # V2 Triggers  
    if any(word in prompt_lower for word in ['all files', 'every', 'analyze all', 'parallel']):
        return 'mcp__claude-code-v2__spawn_parallel_agents'
    
    # V3 Triggers
    if any(word in prompt_lower for word in ['production', 'robust', 'comprehensive', 'enterprise']):
        return 'mcp__claude-code-v3__claude_run_v3'
    
    # Default
    return 'mcp__claude-code-wrapper__claude_run'  # Safe default
```

---

## 🎯 Tool Usage Examples

### V1 Examples
```python
# Synchronous debugging
await mcp__claude-code-wrapper__claude_run(
    task="Debug the authentication error in login.py",
    outputFormat="json"
)

# Async long-running task
job_id = await mcp__claude-code-wrapper__claude_run_async(
    task="Refactor the entire user module",
    permissionMode="default"
)
```

### V2 Examples
```python
# Parallel analysis
await mcp__claude-code-v2__spawn_parallel_agents(
    tasks=[
        "Analyze security in auth.py",
        "Check performance in db.py",
        "Review code style in api.py"
    ],
    timeout=300
)

# Fire-and-forget batch
await mcp__claude-code-v2__spawn_parallel_agents(
    tasks=[f"Generate tests for {module}" for module in modules],
    output_dir="/tmp/test_results"
)
```

### V3 Examples
```python
# Auto-detect mode
await mcp__claude-code-v3__claude_run_v3(
    task="Create a production-ready REST API with authentication",
    auto_detect=True
)

# Force quality mode
await mcp__claude-code-v3__claude_run_v3(
    task="Refactor payment processing with comprehensive tests",
    mode="QUALITY",
    quality_level="high"
)
```

---

## 🎭 Common Scenarios

### Scenario: "Fix all the bugs in my code"
**Server:** V2 (parallel bug fixing)
```python
# First identify bugs with V1
bugs = await mcp__claude-code-wrapper__claude_run(
    task="Identify all bugs in the codebase"
)

# Then fix in parallel with V2
await mcp__claude-code-v2__spawn_parallel_agents(
    tasks=[f"Fix bug: {bug}" for bug in bugs['bugs']]
)
```

### Scenario: "Create a new feature with tests"
**Server:** V3 (comprehensive development)
```python
await mcp__claude-code-v3__claude_run_v3(
    task="Create user profile feature with tests and documentation",
    mode="FULL_CYCLE"
)
```

### Scenario: "Why is my function returning None?"
**Server:** V1 (interactive debugging)
```python
await mcp__claude-code-wrapper__claude_run(
    task="Debug why get_user() returns None instead of user object",
    outputFormat="json",
    permissionMode="readonly"
)
```

---

## ⚡ Performance Guidelines

| Server | Response Time | Best For | Avoid For |
|--------|--------------|----------|-----------|
| **V1** | 5-30s | Debugging, simple tasks | Large-scale analysis |
| **V2** | Instant spawn | Parallel work | Dependent tasks |
| **V3** | 30s-5min | Production code | Simple queries |

---

## 🔄 Fallback Strategy

```python
async def execute_with_smart_fallback(task):
    """Smart fallback between servers"""
    
    # Assess task
    if 'production' in task.lower():
        try:
            return await mcp__claude-code-v3__claude_run_v3(task=task)
        except:
            pass  # Fallback to V1
    
    if 'all' in task.lower() or 'every' in task.lower():
        try:
            return await mcp__claude-code-v2__spawn_parallel_agents(tasks=[task])
        except:
            pass  # Fallback to V1
    
    # V1 as ultimate fallback
    return await mcp__claude-code-wrapper__claude_run(task=task)
```

---

## 🎮 Mode Selection for V3

### V3 Modes Quick Reference
- **RAPID**: Quick prototypes, no validation
- **CODE**: Standard development with basic checks
- **QUALITY**: Code + Review + Basic Tests
- **FULL_CYCLE**: Everything including comprehensive docs
- **TESTING**: Focus on test generation
- **DOCUMENTATION**: Focus on documentation
- **DEBUG**: Fix issues with validation
- **ANALYSIS**: Code understanding and analysis
- **REVIEW**: Comprehensive code critique

### Mode Selection Logic
```python
def select_v3_mode(task: str) -> str:
    task_lower = task.lower()
    
    if 'test' in task_lower:
        return 'TESTING'
    elif 'document' in task_lower or 'docs' in task_lower:
        return 'DOCUMENTATION'
    elif 'production' in task_lower or 'robust' in task_lower:
        return 'FULL_CYCLE'
    elif 'review' in task_lower or 'critique' in task_lower:
        return 'REVIEW'
    elif 'fix' in task_lower or 'debug' in task_lower:
        return 'DEBUG'
    elif 'analyze' in task_lower or 'understand' in task_lower:
        return 'ANALYSIS'
    elif 'quick' in task_lower or 'prototype' in task_lower:
        return 'RAPID'
    else:
        return 'CODE'  # Default standard mode
```

---

## 📋 Task Complexity Assessment

### Simple (Use V1)
- Single file changes
- Quick lookups
- Debugging one issue
- Learning queries
- < 5 minute tasks

### Medium (Use V1 Async or V2)
- Multiple files
- Parallel analysis
- Batch operations
- 5-30 minute tasks
- Independent subtasks

### Complex (Use V3)
- System design
- Multi-component features
- Production requirements
- > 30 minute tasks
- Quality critical

---

## 🛠️ Environment Variables

```bash
# Required for all servers
export CLAUDE_CODE_TOKEN="your_token"

# V1 specific
export CLAUDE_TIMEOUT_SECONDS=600
export CLAUDE_MAX_RECURSION=3

# V2 specific
export CLAUDE_RESULTS_DIR="/tmp/claude_results"
export CLAUDE_MAX_CONCURRENT=10

# V3 specific
export CLAUDE_V3_MODE="auto"
export CLAUDE_V3_QUALITY="normal"
```

---

## 🚨 Common Pitfalls to Avoid

### ❌ Don't Use V3 for Simple Tasks
```python
# BAD: Overkill for simple query
await mcp__claude-code-v3__claude_run_v3(
    task="What does this function do?"  # Too simple for V3
)

# GOOD: Use V1 for simple queries
await mcp__claude-code-wrapper__claude_run(
    task="What does this function do?"
)
```

### ❌ Don't Use V2 for Dependent Tasks
```python
# BAD: Tasks depend on each other
await mcp__claude-code-v2__spawn_parallel_agents(
    tasks=["Create user model", "Use user model in API"]  # Second depends on first
)

# GOOD: Use V1 with sequential execution
await mcp__claude-code-wrapper__claude_run(
    task="Create user model, then use it in API"
)
```

### ❌ Don't Use V1 for Massive Parallel Work
```python
# BAD: V1 will be very slow
for file in hundred_files:
    await mcp__claude-code-wrapper__claude_run(f"Analyze {file}")

# GOOD: Use V2 for parallelism
await mcp__claude-code-v2__spawn_parallel_agents(
    tasks=[f"Analyze {file}" for file in hundred_files]
)
```

---

## 📈 Success Metrics

Track these to ensure optimal server selection:

1. **Task Completion Rate**: Should be > 95%
2. **Average Response Time**: V1 < 30s, V2 instant, V3 < 5min
3. **Quality Score**: V3 > 90%, V1/V2 > 80%
4. **Fallback Rate**: < 5% (low fallback = good selection)

---

## 🔮 Future-Proofing

As new versions are released:
1. V4 might focus on: Real-time collaboration
2. V5 might focus on: Distributed processing
3. Always check latest capabilities with `get_v3_status()`

---

## Quick Decision Flowchart

```
User prompt received
    ↓
Is it debugging/investigation?
    Yes → V1 Sync
    No ↓
Are there multiple independent tasks?
    Yes → V2 Parallel
    No ↓
Does it need production quality?
    Yes → V3 FULL_CYCLE
    No ↓
Is it complex with multiple aspects?
    Yes → V3 Auto-detect
    No ↓
Default → V1 Async
```

---

## Remember

1. **V1** = Interactive & Sequential
2. **V2** = Parallel & Independent  
3. **V3** = Intelligent & Quality-Assured

When in doubt, V1 is the safe default that works for everything, just might not be optimal for performance or quality assurance.