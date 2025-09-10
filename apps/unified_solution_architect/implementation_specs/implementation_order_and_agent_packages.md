# UnifiedOrchestrator Fix Implementation Order & Agent Work Packages

## Implementation Strategy Overview

**Total Estimated Time:** 41 hours (3-5 days)  
**Parallel Execution Possible:** Yes (Phase 1 & 2)  
**Risk Mitigation:** Feature flags and incremental deployment

## Implementation Phases

### Phase 1: Quick Wins (Day 1 Morning) - PARALLEL EXECUTION
**Time:** 5 hours total (can be done in parallel)  
**Risk:** LOW  
**Dependencies:** None

#### Agent Package 1A: Subprocess Working Directory Fix
**Time:** 2 hours  
**Files:** `src/generic_orchestrator.py`, `src/models.py`  
**Specification:** `subprocess_cwd_fix_spec.md`

#### Agent Package 1B: Task Type Validation Fix  
**Time:** 3 hours  
**Files:** `src/generic_orchestrator.py`, `src/task_validator.py` (new)  
**Specification:** `task_validation_fix_spec.md`

These can run simultaneously as they touch different parts of the codebase.

---

### Phase 2: Core Stability (Day 1 Afternoon - Day 2 Morning)
**Time:** 8 hours  
**Risk:** MEDIUM  
**Dependencies:** None (but blocks testing of other fixes)

#### Agent Package 2: Error Handling System Fix
**Time:** 8 hours  
**Files:** `src/generic_orchestrator.py`, `src/models.py`  
**Specification:** `error_capture_fix_spec.md`  
**Critical:** Must complete before Phase 3/4 testing

---

### Phase 3: Architecture Enhancement (Day 2 Afternoon - Day 3)
**Time:** 12 hours  
**Risk:** HIGH  
**Dependencies:** Phase 1A (working directories)

#### Agent Package 3: Agent Context Isolation
**Time:** 12 hours  
**Files:** `src/generic_orchestrator.py`, `src/isolation_manager.py` (new), `src/models.py`  
**Specification:** `context_isolation_fix_spec.md`  
**Note:** Complex architectural change, requires careful testing

---

### Phase 4: Feature Implementation (Day 3 - Day 5)
**Time:** 16 hours  
**Risk:** HIGH  
**Dependencies:** Phase 2 (error handling), Phase 3 (isolation)

#### Agent Package 4: Enhanced Module Implementation
**Time:** 16 hours  
**Files:** 
- `src/unified/modules/quality_gates_module.py` (new)
- `src/unified/modules/monitoring_module.py` (new)  
- `src/unified/modules/execution_plan_module.py` (new)
- `src/unified/modules/base_module.py` (new if missing)
- `src/unified/unified_orchestrator.py` (import fixes)
**Specification:** `module_loading_fix_spec.md`  
**Note:** Can be partially implemented (stub modules first)

---

## Detailed Agent Work Packages

### Package 1A: Subprocess Working Directory Fix Agent

**AGENT PROMPT:**
```
You are implementing a critical fix for the UnifiedOrchestrator subprocess working directory issue.

SPECIFICATION: Read implementation_specs/subprocess_cwd_fix_spec.md

YOUR TASK:
1. Fix the conditional working directory setting in generic_orchestrator.py (line 570)
2. Add fallback directory creation when dynamic configs are disabled
3. Update AgentTask model to track working_directory
4. Ensure directories are created with proper structure (input/output/logs)
5. Test both with enable_dynamic_configs=True and False

SUCCESS CRITERIA:
- Working directory is NEVER None
- Fallback directories created properly
- Relative paths work correctly
- All tests in the spec pass

DELIVERABLES:
- Modified generic_orchestrator.py
- Updated models.py
- Test results showing fix works
```

---

### Package 1B: Task Type Validation Fix Agent

**AGENT PROMPT:**
```
You are implementing task type validation fixes for the UnifiedOrchestrator.

SPECIFICATION: Read implementation_specs/task_validation_fix_spec.md

YOUR TASK:
1. Expand system_prompts dictionary with all required task types
2. Create get_system_prompt() function with fallback support
3. Create new task_validator.py with TaskTypeRegistry
4. Update all prompt retrieval to use validation
5. Test with "test-remediation-specialist" and other validation types

SUCCESS CRITERIA:
- All validation task types recognized
- Unknown types get generic fallback
- No task execution failures from missing types
- Task type aliases work correctly

DELIVERABLES:
- Updated generic_orchestrator.py with expanded prompts
- New task_validator.py file
- Test results showing all types work
```

---

### Package 2: Error Handling System Fix Agent

**AGENT PROMPT:**
```
You are implementing comprehensive error handling fixes for the UnifiedOrchestrator.

SPECIFICATION: Read implementation_specs/error_capture_fix_spec.md

YOUR TASK:
1. Fix empty error string problem in generic_orchestrator.py (lines 619-623)
2. Add comprehensive error capture with context
3. Implement JSON parsing error handling with output preview
4. Add error_details field to AgentTask model
5. Ensure stderr is properly captured and included

SUCCESS CRITERIA:
- NO empty error strings in any failure scenario
- All errors include sufficient debugging context
- JSON parsing failures show output preview
- Error details structure available for analysis

DELIVERABLES:
- Modified generic_orchestrator.py with enhanced error handling
- Updated models.py with error tracking fields
- Test demonstrating no empty errors
- Validation suite showing improved error capture
```

---

### Package 3: Agent Context Isolation Implementation Agent

**AGENT PROMPT:**
```
You are implementing agent context isolation for the UnifiedOrchestrator.

SPECIFICATION: Read implementation_specs/context_isolation_fix_spec.md

YOUR TASK:
1. Create IsolationManager class in new isolation_manager.py
2. Remove conditional isolation - make it mandatory
3. Implement deep configuration copying
4. Create isolated environment variables for each agent
5. Integrate IsolationManager with orchestrator
6. Add cleanup that preserves outputs

SUCCESS CRITERIA:
- Every agent gets isolated workspace (regardless of config)
- No configuration contamination between agents
- Environment variables properly isolated
- Resources properly namespaced
- Cleanup preserves important outputs

DELIVERABLES:
- New isolation_manager.py implementation
- Modified generic_orchestrator.py with integration
- Updated models.py with IsolatedAgentTask
- Tests showing complete isolation
```

---

### Package 4: Enhanced Module Implementation Agent

**AGENT PROMPT:**
```
You are implementing the missing enhanced feature modules for UnifiedOrchestrator.

SPECIFICATION: Read implementation_specs/module_loading_fix_spec.md

YOUR TASK:
1. Create quality_gates_module.py with validation gates
2. Create monitoring_module.py with metrics tracking
3. Create execution_plan_module.py with optimization logic
4. Create base_module.py if it doesn't exist
5. Fix ALL import paths from src.modules to src.unified.modules
6. Test that all modules load and initialize

SUCCESS CRITERIA:
- All three modules created and functional
- Import errors completely resolved
- Modules initialize without errors
- Module hooks execute during task processing
- Quality gates validate tasks
- Monitoring collects metrics
- Execution plans optimize task order

DELIVERABLES:
- Three new module files (quality_gates, monitoring, execution_plan)
- base_module.py if needed
- Fixed import statements in unified_orchestrator.py
- Integration test showing all modules work
```

---

## Validation After Each Phase

### Phase 1 Validation:
```bash
python orchestrator_validation_suite.py --component basic_orchestration
# Should show improved task type handling and working directories
```

### Phase 2 Validation:
```bash
python orchestrator_validation_suite.py --component error_handling
# Should show NO empty error strings
```

### Phase 3 Validation:
```bash
python orchestrator_validation_suite.py --component resource_management
# Should show proper isolation
```

### Phase 4 Validation:
```bash
python orchestrator_validation_suite.py --component enhanced_features
# Should show modules loading and working
```

## Risk Mitigation Strategies

1. **Feature Flags:** Add config options to disable new features if issues arise
2. **Incremental Testing:** Test each fix independently before integration
3. **Rollback Points:** Git commits after each successful phase
4. **Parallel Development:** Phase 1 fixes can be done simultaneously
5. **Stub Implementation:** For modules, start with stubs then add functionality

## Success Metrics

After all fixes:
- Production Readiness Score should increase from 6.2/10 to >8/10
- Basic Orchestration score should improve from 3.8/10 to >8/10
- Enhanced Features should move from 0/10 to functional (>5/10)
- Zero empty error strings in any scenario
- All validation tests passing

## Final Integration Testing

After all phases complete:
```bash
# Run full validation suite
python orchestrator_validation_suite.py --full

# Run specific problem scenarios
python test_error_handling_fix.py
python test_module_loading.py
python test_isolation.py
python test_working_directory.py

# Run performance benchmark
python orchestrator_validation_suite.py --component performance
```

## Notes for Orchestration

- Phases 1A and 1B can run in parallel (different files)
- Phase 2 should complete before heavy testing of Phases 3-4
- Phase 4 can use stub implementations initially
- Each agent should commit their changes separately
- Maintain a fix tracking document with status updates