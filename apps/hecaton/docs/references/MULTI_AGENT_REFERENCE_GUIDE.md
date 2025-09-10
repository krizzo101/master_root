# Multi-Agent Reference Integration Guide
## How to Leverage Existing Patterns from multi-agent-reference

---

## 🎯 Purpose
This guide maps Hecaton components to existing implementations in `/home/opsvi/master_root/multi-agent-reference/` that should be reviewed and considered for each functional area.

---

## 📍 Critical Code to Review by Component

### 1. Agent Implementation Patterns

#### For Code Agents (`src/hecaton/agents/specialized/code_agent.py`)
**MUST REVIEW:**
```bash
# Existing implementation to study:
/home/opsvi/master_root/multi-agent-reference/claude_headless_agents/performance_tests/claude_agent_orchestrator.py
# Lines 45-89: Specialized agent creation patterns

/home/opsvi/master_root/multi-agent-reference/claude_headless_agents/archive/opus_bst.py
# Complete code generation example with error handling
```

**Key Patterns to Adopt:**
- Token rotation from lines 156-178 in `claude_agent_orchestrator.py`
- Error recovery patterns from `opus_bst.py`
- Response parsing from headless agent implementations

#### For Research Agents (`src/hecaton/agents/specialized/research_agent.py`)
**MUST REVIEW:**
```bash
/home/opsvi/master_root/multi-agent-reference/claude_headless_agents/claude_headless_guide.md
# Research task patterns and optimization strategies

/home/opsvi/master_root/multi-agent-reference/claude_headless_agents/performance_tests/model_quality_comparison.sh
# Quality benchmarking approaches for research tasks
```

### 2. Orchestration Patterns

#### For LangGraph Orchestrator (`src/hecaton/orchestration/langgraph_orchestrator.py`)
**MUST REVIEW:**
```bash
/home/opsvi/master_root/multi-agent-reference/claude_headless_agents/performance_tests/claude_agent_orchestrator.py
# Lines 195-236: Orchestration and coordination patterns
# Parallel execution strategies

/home/opsvi/master_root/multi-agent-reference/claude_headless_agents/PROJECT_STRUCTURE.md
# Architectural patterns for multi-agent coordination
```

**Critical Implementation Details:**
- Batch processing approach (lines 195-210)
- Result aggregation patterns (lines 220-236)
- Error handling in orchestration

#### For Self-Improving Orchestrator (`src/hecaton/orchestration/self_improving_orchestrator.py`)
**MUST REVIEW:**
```bash
/home/opsvi/master_root/multi-agent-reference/claude_headless_agents/archive/agent_optimization_summary.md
# Optimization strategies and performance improvements

/home/opsvi/master_root/multi-agent-reference/claude_headless_agents/archive/final_optimization_strategy.md
# Final optimization patterns with metrics
```

### 3. Performance Testing & Optimization

#### Before Implementing Any Performance Features
**MUST REVIEW:**
```bash
/home/opsvi/master_root/multi-agent-reference/claude_headless_agents/performance_tests/
├── test_haiku.sh          # Lightweight model testing
├── test_sonnet.sh         # Balanced model testing
├── test_opus.sh           # Heavy model testing
├── test_optimization_combos.sh  # Combined optimization strategies
└── run_empirical_tests.sh      # Comprehensive benchmark suite
```

**Key Metrics to Track (from existing tests):**
- Response time percentiles
- Token usage per task
- Error rates by model type
- Cost per operation

### 4. Real Claude Executor Integration

#### For Claude Executor (`src/hecaton/agents/real_claude_executor.py`)
**MUST REVIEW:**
```bash
/home/opsvi/master_root/multi-agent-reference/claude_headless_agents/claude_testing_report.md
# Real-world testing results and gotchas

/home/opsvi/master_root/multi-agent-reference/claude_headless_agents/archive/claude_conversation_capture.sh
# Conversation capture and logging patterns
```

**Implementation Patterns:**
- Rate limit handling strategies
- Token counting and management
- Conversation context preservation
- Error recovery mechanisms

### 5. Documentation Patterns

#### For Creating Agent Documentation
**MUST REVIEW:**
```bash
/home/opsvi/master_root/multi-agent-reference/claude_headless_agents/claude_headless_complete_guide.md
# Comprehensive documentation structure

/home/opsvi/master_root/multi-agent-reference/claude_headless_agents/readme.md
# Clear explanation patterns
```

---

## 🔧 Specific Files to Import/Adapt

### High-Priority Imports

1. **Performance Testing Framework**
   ```python
   # FROM: multi-agent-reference/claude_headless_agents/performance_tests/claude_agent_orchestrator.py
   # TO: apps/hecaton/tests/performance/
   # WHY: Proven testing framework with metrics collection
   ```

2. **Optimization Strategies**
   ```python
   # FROM: multi-agent-reference/claude_headless_agents/archive/final_optimization_strategy.md
   # TO: apps/hecaton/docs/patterns/optimization_patterns.md
   # WHY: Documented optimization approaches with proven results
   ```

3. **Model Selection Logic**
   ```python
   # FROM: multi-agent-reference/claude_headless_agents/performance_tests/model_quality_comparison.sh
   # TO: apps/hecaton/src/hecaton/agents/model_selector.py
   # WHY: Empirical model selection based on task complexity
   ```

---

## 📊 Performance Benchmarks to Match

From multi-agent-reference testing results:

| Metric | Baseline | Optimized | File Reference |
|--------|----------|-----------|----------------|
| Response Time (p50) | 3.2s | 1.8s | `performance_tests/run_empirical_tests.sh` |
| Token Usage | 100% | 77% | `archive/performance_analysis.md` |
| Error Rate | 5.2% | 0.3% | `claude_testing_report.md` |
| Parallel Throughput | 1x | 3.5x | `performance_tests/claude_agent_orchestrator.py` |

---

## 🚨 Critical Patterns Not Yet Implemented

Based on multi-agent-reference review, Hecaton is missing:

1. **Token Pool Rotation** (see `claude_agent_orchestrator.py:156-178`)
2. **Batch Processing** (see `run_parallel_tests.sh`)
3. **Quality Scoring** (see `model_quality_comparison.sh`)
4. **Conversation Capture** (see `claude_conversation_capture.sh`)
5. **Empirical Testing Suite** (see entire `performance_tests/` directory)

---

## 📝 Implementation Checklist

When implementing new features in Hecaton, review these files:

- [ ] **Before creating any agent**: Review `claude_headless_agents/performance_tests/claude_agent_orchestrator.py`
- [ ] **Before implementing orchestration**: Study `PROJECT_STRUCTURE.md` patterns
- [ ] **Before adding error handling**: Check `archive/opus_bst.py` error patterns
- [ ] **Before performance optimization**: Run `performance_tests/run_empirical_tests.sh`
- [ ] **Before deployment**: Review `claude_testing_report.md` for production gotchas

---

## 🔗 Quick Reference Commands

```bash
# Compare Hecaton agent with reference implementation
diff apps/hecaton/src/hecaton/agents/specialized/code_agent.py \
     multi-agent-reference/claude_headless_agents/archive/opus_bst.py

# Check optimization strategies
grep -n "optimization" multi-agent-reference/claude_headless_agents/archive/*.md

# Find error handling patterns
grep -n "try\|except\|error" multi-agent-reference/claude_headless_agents/performance_tests/*.py

# Locate token management
grep -n "token" multi-agent-reference/claude_headless_agents/performance_tests/claude_agent_orchestrator.py
```

---

*This guide ensures Hecaton developers review and leverage existing multi-agent-reference implementations rather than reinventing patterns.*
