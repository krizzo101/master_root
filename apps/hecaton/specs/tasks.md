# HECATON Implementation Tasks

## Task Management System

All tasks follow this structure:
- **ID**: TASK-XXX
- **Requirement**: Links to REQ-XXX
- **Phase**: Phase 0-4
- **Priority**: Critical/High/Medium/Low
- **Effort**: Hours estimated
- **Dependencies**: Other tasks that must complete first
- **Assignee**: Self/Agent-1/Agent-2/etc

---

## Phase 0 Tasks (Manual Implementation)

### TASK-001: Environment Setup
**Requirement**: REQ-001, REQ-002, REQ-003
**Priority**: Critical
**Effort**: 0.5 hours
**Dependencies**: None
**Status**: 🔄 In Progress

**Steps**:
1. Copy .env.example to .env
2. Add CLAUDE_CODE_TOKEN values
3. Install dependencies with pip
4. Verify git worktree support
5. Create /tmp/hecaton_worktrees directory

**Validation**:
```bash
./scripts/run.sh setup
python -c "import langgraph; print('LangGraph OK')"
git worktree list
```

---

### TASK-002: Implement Minimal Token Pool
**Requirement**: REQ-002
**Priority**: Critical
**Effort**: 1 hour
**Dependencies**: TASK-001
**Status**: ⏳ Pending

**Implementation**:
```python
# src/hecaton/resources/token_pool.py
# Copy from: multi-agent-reference/multi-agent-monitor/orchestration/token_pool.py
# Simplify to 2 tokens only
# Must include threading.Lock()
```

**Tests Required**:
- test_loads_two_tokens()
- test_round_robin_rotation()
- test_thread_safety()

---

### TASK-003: Implement Worktree Manager
**Requirement**: REQ-003
**Priority**: Critical
**Effort**: 1 hour
**Dependencies**: TASK-001
**Status**: ⏳ Pending

**Implementation**:
```python
# src/hecaton/resources/worktree.py
# Copy from: multi-agent-reference/multi-agent-monitor/orchestration/worktree_manager.py
# Critical: Use 'git branch' not 'git checkout -b'
```

**Tests Required**:
- test_creates_unique_worktree()
- test_uses_git_branch_pattern()
- test_cleanup_removes_worktree()

---

### TASK-004: Implement Send API Orchestrator
**Requirement**: REQ-001, REQ-004
**Priority**: Critical
**Effort**: 2 hours
**Dependencies**: TASK-002, TASK-003
**Status**: ⏳ Pending

**Implementation**:
```python
# src/hecaton/orchestration/send_api.py
# Copy from: multi-agent-reference/oamat-sd/execution_engine.py
# MUST use add_conditional_edges
# MUST return List[Send]
```

**Tests Required**:
- test_uses_conditional_edges()
- test_returns_send_objects()
- test_parallel_execution()

---

### TASK-005: Create CLI Runner
**Requirement**: REQ-019
**Priority**: High
**Effort**: 0.5 hours
**Dependencies**: TASK-004
**Status**: ⏳ Pending

**Implementation**:
```python
# src/hecaton/cli/runner.py
# Simple CLI for testing
# Must call orchestrator.execute_parallel()
```

---

### TASK-006: Integration Testing
**Requirement**: REQ-001
**Priority**: Critical
**Effort**: 1 hour
**Dependencies**: TASK-005
**Status**: ⏳ Pending

**Test Case**:
```python
# tests/integration/test_parallel.py
# Verify 2 agents run simultaneously
# Measure execution time
# Assert time < sum of individual times
```

---

### TASK-007: Documentation Update
**Requirement**: All Phase 0
**Priority**: Medium
**Effort**: 0.5 hours
**Dependencies**: TASK-006
**Status**: ⏳ Pending

**Updates**:
- README.md with Phase 0 results
- PROJECT_STATUS.md with completion
- Git commit with working Phase 0

---

## Phase 1 Tasks (Bootstrap - System Builds Itself)

### TASK-008: Bootstrap Token Expansion
**Requirement**: REQ-005, REQ-006
**Priority**: Critical
**Effort**: N/A (Agent task)
**Dependencies**: Phase 0 Complete
**Assignee**: Agent-1
**Status**: ⏳ Pending

**Agent Prompt**:
```
Look at src/hecaton/resources/token_pool.py
Modify it to support 5 tokens instead of 2
Load CLAUDE_CODE_TOKEN_2, _3, and _4 from environment
Maintain thread safety with the lock
Update tests to verify 5 tokens
```

---

### TASK-009: Bootstrap Error Handling
**Requirement**: REQ-015
**Priority**: Critical
**Effort**: N/A (Agent task)
**Dependencies**: Phase 0 Complete
**Assignee**: Agent-2
**Status**: ⏳ Pending

**Agent Prompt**:
```
Look at src/hecaton/orchestration/send_api.py
Add error handling for agent failures
Implement retry logic (max 3 attempts)
Add exponential backoff
Create test for error recovery
```

---

### TASK-010: Test 5-Agent Execution
**Requirement**: REQ-005
**Priority**: High
**Effort**: 0.5 hours
**Dependencies**: TASK-008, TASK-009
**Status**: ⏳ Pending

**Manual Verification**:
- Run with 5 parallel tasks
- Verify all execute
- Check performance metrics

---

## Phase 2 Tasks (Feature Enhancement - Agents Build)

### TASK-011: Implement Agent Registry
**Requirement**: REQ-007
**Priority**: High
**Effort**: N/A (Agent task)
**Dependencies**: Phase 1 Complete
**Assignee**: Agent-1 to Agent-3
**Status**: ⏳ Planned

### TASK-012: Add Message Queue
**Requirement**: REQ-008
**Priority**: High
**Effort**: N/A (Agent task)
**Dependencies**: Phase 1 Complete
**Assignee**: Agent-4 to Agent-5
**Status**: ⏳ Planned

### TASK-013: Implement Phase Gates
**Requirement**: REQ-009
**Priority**: Medium
**Effort**: N/A (Agent task)
**Dependencies**: TASK-011
**Assignee**: Multi-agent collaboration
**Status**: ⏳ Planned

---

## Phase 3 Tasks (Autonomous - System Improves Itself)

### TASK-014: Add Performance Monitoring
**Requirement**: REQ-010
**Priority**: Medium
**Effort**: N/A (Agent task)
**Dependencies**: Phase 2 Complete
**Assignee**: System self-assigns
**Status**: ⏳ Planned

### TASK-015: Implement Self-Analysis
**Requirement**: REQ-010
**Priority**: Medium
**Effort**: N/A (Agent task)
**Dependencies**: TASK-014
**Assignee**: System self-assigns
**Status**: ⏳ Planned

### TASK-016: Create Improvement Tasks
**Requirement**: REQ-011
**Priority**: Medium
**Effort**: N/A (Agent task)
**Dependencies**: TASK-015
**Assignee**: System self-assigns
**Status**: ⏳ Planned

---

## Phase 4 Tasks (Optimization - Continuous Improvement)

### TASK-017: Optimization Loop
**Requirement**: REQ-012
**Priority**: Low
**Effort**: N/A (System task)
**Dependencies**: Phase 3 Complete
**Assignee**: Autonomous system
**Status**: ⏳ Future

---

## Task Tracking Dashboard

### Phase 0 Progress (Manual)
```
[█████░░░░░] 50% Complete
✅ Specifications (COMPLETE)
✅ Design (COMPLETE)
✅ Project Structure (COMPLETE)
🔄 Environment Setup (IN PROGRESS)
⏳ Token Pool (PENDING)
⏳ Worktree Manager (PENDING)
⏳ Send API (PENDING)
⏳ CLI Runner (PENDING)
⏳ Testing (PENDING)
```

### Overall Project Progress
```
Phase 0: [█████░░░░░] 50%
Phase 1: [░░░░░░░░░░] 0%
Phase 2: [░░░░░░░░░░] 0%
Phase 3: [░░░░░░░░░░] 0%
Phase 4: [░░░░░░░░░░] 0%
```

---

## Critical Path

The critical path for Phase 0:
1. TASK-001 (Environment) →
2. TASK-002 + TASK-003 (Token + Worktree) [Parallel] →
3. TASK-004 (Send API) →
4. TASK-005 (CLI) →
5. TASK-006 (Testing) →
6. TASK-007 (Documentation)

**Minimum time**: 6.5 hours of focused work

---

## Next Action

Start with TASK-001:
```bash
cd apps/hecaton
cp .env.example .env
nano .env  # Add your tokens
./scripts/run.sh setup
```

Then proceed to TASK-002 and TASK-003 in parallel if possible.
