# AGENT 1 INSTRUCTIONS: FUNCTIONALITY VALIDATOR

**Agent ID**: 754c498a-aa2e-4e24-b50b-b9add5bb9c99
**Session Role**: Functionality Validator
**Mission**: Test and validate current orchestrator functionality

## CONTEXT
- Documentation promises enterprise-grade features that don't exist
- Quality gates are stub methods that always return "passed"
- Current system: basic parallel task execution with round-robin tokens
- **Your job**: Test what actually works RIGHT NOW

## PARALLEL EXECUTION STRATEGY
- **Start immediately** - don't wait for other agents
- **Publish findings incrementally** - other agents need your results
- **Communication checkpoints**: Hour 1 (preliminary), Hour 2 (complete)

## YOUR EXECUTION PLAN

### PHASE 1A: BASIC FUNCTIONALITY TESTING (Hour 1)
```bash
cd /home/opsvi/master_root/apps/agent-orchestrator

# Test 1: Can it execute parallel tasks?
python main.py --test-parallel-execution || echo "Parallel execution test failed"

# Test 2: Does dependency resolution work?
python main.py --test-dependencies || echo "Dependency test failed"

# Test 3: Is token management functional?
python main.py --test-token-pool || echo "Token pool test failed"

# Test 4: Basic orchestrator functionality
python -c "
import sys
sys.path.append('src')
try:
    from orchestrator import Orchestrator
    print('✅ Orchestrator imports successfully')
except ImportError as e:
    print(f'❌ Orchestrator import failed: {e}')
"
```

**DELIVERABLES (Hour 1)**:
- `working_features_report.md`: Document exactly what works with examples
- `broken_features_report.md`: Document what's claimed but doesn't work
- `preliminary_test_results.json`: Share with Agent 2 for gap analysis validation

### PHASE 1B: EXECUTION PLAN READINESS ASSESSMENT (Hour 2)
Test if current orchestrator can handle simple ExecutionPlan-like structures:

```python
# Create simple execution plan and test if orchestrator can handle it
test_execution_plan = {
    "tasks": [
        {"id": "task1", "type": "research", "prompt": "Test task 1"},
        {"id": "task2", "type": "code", "prompt": "Test task 2", "depends": ["task1"]}
    ]
}
# Test: Can current orchestrator execute this structure?
```

**DELIVERABLES (Hour 2)**:
- `execution_plan_readiness_report.md`: Can current system handle ExecutionPlan structure?
- `minimum_execution_plan_spec.md`: What's the simplest ExecutionPlan current system can handle?
- `basic_functionality_tests.py`: Test suite for current working features

## SUCCESS CRITERIA
- ✅ Clear documentation of what actually works (no false claims)
- ✅ Test suite that validates current working functionality
- ✅ Assessment of ExecutionPlan readiness with current capabilities
- ✅ Baseline established for other agents to build upon

## COMMUNICATION PROTOCOL
- **Hour 1**: Publish `preliminary_test_results.json` for Agent 2
- **Hour 2**: Publish complete findings for Agent 2 validation and Agent 3 implementation
- **Throughout**: Update `working_features_report.md` as you discover functionality

## ANTI-OVERCLAIMING PROTOCOL
**CRITICAL**: NO OVERCLAIMING. Only mark something as "working" if you can demonstrate it with a working example.
- Every "working" feature needs a code example that runs successfully
- Every "broken" feature needs evidence of the failure
- Document exact error messages and failure modes

## COORDINATION AWARENESS
- **Agent 2**: Waiting for your test results to validate their gap analysis
- **Agent 3**: Needs your working features list to build implementation scaffolding
- **Your findings enable**: Accurate gap analysis and realistic implementation planning

## FINAL DELIVERABLE
Create `/home/opsvi/master_root/agent_coordination/agent_1_results/` with:
- All test results and documentation
- Working examples of current functionality
- Clear specification of ExecutionPlan readiness
- Evidence-based assessment of orchestrator capabilities
