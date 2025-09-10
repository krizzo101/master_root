# HECATON Development Guide

## For AI Agents and Human Developers

### Quick Start: Where to Find What You Need

```markdown
Current State → docs/CURRENT_STATE_AND_ARCHITECTURE.md
Design Specs → docs/design/MULTI_AGENT_TECHNICAL_SPEC_V2.md
Implementation Map → docs/IMPLEMENTATION_CROSS_REFERENCE.md
Reference Code → multi-agent-reference/
Phase Status → docs/PHASE_[0-3]_COMPLETE.md
Next Steps → docs/PHASE_4_OPTIMIZATION_PLAN.md
```

---

## 🎯 Current Mission: Phase 4 Performance Optimization

**Goal**: 10x speed improvement (30-60s → 3-5s per agent)

### Immediate Tasks:

1. **Integrate Optimized Executor**
   ```python
   # Replace in src/hecaton/agents/real_claude_executor.py
   # Line 341: Fix command structure
   cmd = ["claude", "-p", "--strict-mcp-config", ...]  # Not "claude code"
   ```

2. **Deploy Minimal Environments**
   ```python
   # Use src/hecaton/config/agent_environment_optimizer.py
   optimizer = AgentEnvironmentOptimizer()
   config = optimizer.create_agent_environment(agent_type="code")
   ```

3. **Test Performance**
   ```bash
   python examples/optimized_parallel_demo.py
   ```

---

## 📚 Essential Reference Patterns

### From `multi-agent-reference/CRITICAL_PATTERNS_ANALYSIS.md`:

#### Rule 997: Git Worktree
```python
# ALWAYS
subprocess.run(["git", "branch", branch_name])
# NEVER
subprocess.run(["git", "checkout", "-b", branch_name])
```

#### Send API for Parallelism
```python
# MUST USE
workflow.add_conditional_edges("node", func, ["target"])
# NOT
workflow.add_edge("node", "target")  # Sequential!
```

#### Thread-Safe Token Pool
```python
with self._lock:  # REQUIRED
    token = self._tokens[self._token_index]
    self._token_index = (self._token_index + 1) % len(self._tokens)
```

---

## 🗺️ Navigation Guide

### By Task:

#### "I need to implement a new agent type"
1. Template: `src/hecaton/agents/specialized/base_agent.py`
2. Example: `src/hecaton/agents/specialized/code_agent.py`
3. Reference: `multi-agent-reference/metagpt/`

#### "I need to improve performance"
1. Guide: `docs/AGENT_ENVIRONMENT_OPTIMIZATION.md`
2. Code: `src/hecaton/execution/optimized_headless_executor.py`
3. Reference: `multi-agent-reference/claude_headless_agents/`

#### "I need to add parallel execution"
1. Current: `src/hecaton/agents/real_claude_executor.py`
2. Pattern: `multi-agent-reference/oamat-sd/execution_engine.py`
3. Headless: `multi-agent-reference/claude_headless_agents/claude_agent_orchestrator.py`

#### "I need to understand the architecture"
1. Overview: `docs/CURRENT_STATE_AND_ARCHITECTURE.md`
2. Design: `docs/design/MULTI_AGENT_ARCHITECTURE_V2.md`
3. Implementation: `docs/IMPLEMENTATION_CROSS_REFERENCE.md`

---

## 🔧 Development Workflow

### 1. Before Starting Any Task:

```python
# Check if it already exists
grep -r "component_name" docs/IMPLEMENTATION_CROSS_REFERENCE.md
find src/hecaton -name "*.py" | xargs grep "component_name"
find multi-agent-reference -name "*.py" | xargs grep "pattern"
```

### 2. Follow Existing Patterns:

```python
# Don't recreate - reuse from multi-agent-reference/
# Example: Token Pool
cp multi-agent-reference/multi-agent-monitor/orchestration/token_pool.py \
   src/hecaton/resources/token_pool_v2.py
# Then modify for your needs
```

### 3. Test Your Changes:

```bash
# Unit tests
pytest tests/unit/test_component.py -v

# Integration test
python test_phase3_integration.py

# Performance benchmark
python examples/optimized_parallel_demo.py
```

### 4. Document Your Work:

```python
"""
Component description
Based on: multi-agent-reference/path/to/reference.py
See: docs/IMPLEMENTATION_CROSS_REFERENCE.md → Section X
Performance: 3-5s execution time
"""
```

---

## 📊 Performance Targets

### Current (Phase 3)
- Single agent: 30-60s
- 5 parallel: 40-80s
- Memory: 500MB/agent
- **Bottleneck**: MCP servers, generic configs

### Target (Phase 4)
- Single agent: 3-5s ✨
- 5 parallel: 5-10s ✨
- Memory: 100MB/agent ✨
- **Solution**: Minimal configs, no MCP

---

## 🚀 Key Files to Know

### Core System:
```
src/hecaton/
├── agents/
│   ├── real_claude_executor.py      # Current executor (needs optimization)
│   └── specialized/*.py             # Agent types
├── resources/
│   ├── token_pool.py                # Token management (complete)
│   └── worktree.py                  # Git isolation (complete)
├── orchestration/
│   └── self_improving_orchestrator.py # Autonomous improvement (complete)
└── execution/
    └── optimized_headless_executor.py # 10x faster (ready to integrate)
```

### Reference Code:
```
multi-agent-reference/
├── CRITICAL_PATTERNS_ANALYSIS.md    # MUST READ
├── claude_headless_agents/          # Performance optimization patterns
├── multi-agent-monitor/             # Token pool, worktree patterns
└── oamat-sd/execution_engine.py    # Send API pattern
```

---

## ⚠️ Common Pitfalls to Avoid

### 1. Wrong Git Command
```python
# WRONG
subprocess.run(["git", "checkout", "-b", branch])  # ❌

# RIGHT
subprocess.run(["git", "branch", branch])  # ✅
```

### 2. Wrong Claude Command
```python
# WRONG (current issue in real_claude_executor.py)
cmd = ["claude", "code", task]  # ❌ Slow, wrong

# RIGHT
cmd = ["claude", "-p", "--strict-mcp-config", ...]  # ✅ Fast
```

### 3. Sequential Instead of Parallel
```python
# WRONG
workflow.add_edge("node1", "node2")  # ❌ Sequential

# RIGHT
workflow.add_conditional_edges("node", func, ["target"])  # ✅ Parallel
```

### 4. Loading All MCP Servers
```python
# WRONG
mcp_config = load_all_servers()  # ❌ 15-20s overhead

# RIGHT
mcp_config = {"mcpServers": {}}  # ✅ 0s for most agents
```

---

## 📈 Success Metrics

You're on track if:
- ✅ Single agent executes in <5 seconds
- ✅ Parallel agents show true concurrency
- ✅ Memory usage <100MB per agent
- ✅ No MCP servers for code/test agents
- ✅ Git worktrees isolate properly

---

## 🆘 Getting Help

1. **Check Documentation**:
   - This guide
   - IMPLEMENTATION_CROSS_REFERENCE.md
   - CRITICAL_PATTERNS_ANALYSIS.md

2. **Find Examples**:
   ```bash
   # Find reference implementations
   find multi-agent-reference -name "*.py" -exec grep -l "pattern" {} \;

   # Find current usage
   grep -r "component" src/hecaton/
   ```

3. **Test in Isolation**:
   ```python
   # Create minimal test
   python -c "from hecaton.resources.token_pool import TokenPool; tp = TokenPool(); print(tp.get_token())"
   ```

---

## 🎯 Next Actions for Phase 4

1. [ ] Fix claude command in `real_claude_executor.py` line 341
2. [ ] Integrate `optimized_headless_executor.py`
3. [ ] Create minimal MCP configs in `config/minimal_profiles/`
4. [ ] Test with `examples/optimized_parallel_demo.py`
5. [ ] Benchmark and validate <5s execution

---

**Remember**: Don't recreate what exists. The patterns in `multi-agent-reference/` are proven and tested. Use them!

**Current Phase**: 3 Complete ✅
**Next Phase**: 4 (Performance Optimization) 🚧
**Expected Completion**: 2 weeks
