# AGENT 3 INSTRUCTIONS: IMPLEMENTATION COORDINATOR

**Agent ID**: 93abe5ee-145c-4d5f-812f-fd36bc4f8b34
**Session Role**: Implementation Coordinator
**Mission**: Coordinated implementation using working orchestrator

## CRITICAL CONTEXT
- Agent 1 is testing what actually works now
- Agent 2 is identifying gaps and creating implementation plan
- You will use the current working orchestrator to coordinate implementing missing features
- **Goal**: Build ExecutionPlan capability on proven working foundation

## PARALLEL EXECUTION STRATEGY
- **Start immediately** with infrastructure preparation
- **Hour 2**: Receive Agent 2's implementation roadmap and begin priority features
- **Hour 3+**: Full coordinated implementation using working orchestrator

## YOUR EXECUTION PLAN

### PHASE 3A: INFRASTRUCTURE PREPARATION (Hour 0-2, Parallel Start)
Prepare implementation environment while waiting for other agents:

```bash
cd /home/opsvi/master_root/apps/agent-orchestrator

# Setup implementation workspace
mkdir -p implementation_workspace/{quality_gates,execution_plan,monitoring}
mkdir -p tests/integration
mkdir -p agent_coordination/agent_3_results

# Prepare testing framework skeleton
cat > tests/integration/test_framework.py << 'EOF'
"""
Integration testing framework for new features
"""
import pytest
import json
from pathlib import Path

class IntegrationTestFramework:
    def __init__(self):
        self.test_results = {}

    def test_feature_integration(self, feature_name, test_function):
        """Test that new feature integrates with current orchestrator"""
        try:
            result = test_function()
            self.test_results[feature_name] = {"status": "pass", "result": result}
            return True
        except Exception as e:
            self.test_results[feature_name] = {"status": "fail", "error": str(e)}
            return False

    def validate_execution_plan_integration(self, execution_plan):
        """Validate ExecutionPlan works with current orchestrator"""
        # Implementation pending Agent 1's findings
        pass
EOF
```

**DELIVERABLES (Hour 0-2)**:
- Implementation workspace prepared
- Testing framework skeleton created
- Integration scaffolding ready

### PHASE 3B: PRIORITY FEATURE IMPLEMENTATION (Hour 2-4)
**WAIT FOR**: Agent 2's `realistic_implementation_roadmap.md`

Use current working orchestrator to coordinate implementing priority features:

```python
# Example: Use current orchestrator to implement missing features
implementation_tasks = [
    {
        "task_id": "implement_quality_gates",
        "agent_type": "development-specialist",
        "prompt": "Implement working quality gates system based on gap analysis from Agent 2",
        "dependencies": [],
        "deliverable": "src/working_quality_gates.py",
        "integration_test": "Quality gates integrate with current orchestrator task validation"
    },
    {
        "task_id": "implement_execution_plan_parser",
        "agent_type": "development-specialist",
        "prompt": "Create ExecutionPlan parser that works with current orchestrator based on Agent 1's readiness assessment",
        "dependencies": ["implement_quality_gates"],
        "deliverable": "src/execution_plan_parser.py",
        "integration_test": "Parser converts ExecutionPlans to current orchestrator task format"
    },
    {
        "task_id": "implement_basic_monitoring",
        "agent_type": "development-specialist",
        "prompt": "Add real-time monitoring to current orchestrator without breaking existing functionality",
        "dependencies": [],
        "deliverable": "src/basic_monitoring.py",
        "integration_test": "Monitoring works with current parallel task execution"
    }
]

# Execute these using current working orchestrator
# orchestrator.execute_parallel_tasks(implementation_tasks)
```

**DELIVERABLES (Hour 2-4)**:
- `src/working_quality_gates.py`: Quality gates that actually validate
- `src/execution_plan_parser.py`: ExecutionPlan integration with current orchestrator
- `src/basic_monitoring.py`: Working monitoring system
- Integration tests proving each feature works with current orchestrator

### PHASE 3C: END-TO-END INTEGRATION AND VALIDATION (Hour 4-6)
Integrate all new features and create working ExecutionPlan system:

```python
# End-to-end integration test
end_to_end_test = {
    "execution_plan_input": {
        "id": "test_execution_plan",
        "tasks": [
            {"id": "task1", "type": "research", "prompt": "Test research task"},
            {"id": "task2", "type": "code", "prompt": "Test code task", "depends": ["task1"]}
        ]
    },
    "expected_flow": [
        "ExecutionPlan parsed by execution_plan_parser.py",
        "Tasks validated by working_quality_gates.py",
        "Tasks executed by current orchestrator parallel execution",
        "Progress monitored by basic_monitoring.py",
        "Results stored in current orchestrator format"
    ],
    "success_criteria": "Complete ExecutionPlan execution without breaking current functionality"
}
```

### PHASE 3D: SELF-IMPROVEMENT DEMONSTRATION (Hour 6)
Create ExecutionPlan that orchestrator uses to coordinate its own enhancement:

```python
self_improvement_plan = {
    "id": "orchestrator_self_enhancement",
    "description": "Orchestrator coordinating its own development",
    "tasks": [
        {
            "id": "enhance_quality_gates",
            "type": "development-specialist",
            "prompt": "Enhance quality gates based on usage feedback",
            "meta": "The orchestrator improving its own validation"
        },
        {
            "id": "optimize_execution_plan_parsing",
            "type": "performance-optimizer",
            "prompt": "Optimize ExecutionPlan parsing performance",
            "depends": ["enhance_quality_gates"],
            "meta": "Self-optimization of ExecutionPlan processing"
        }
    ],
    "self_reference": True  # The orchestrator improving itself using ExecutionPlans
}
```

## SUCCESS CRITERIA
- ✅ Missing features implemented using current working orchestrator
- ✅ ExecutionPlan integration functional with current capabilities
- ✅ Real quality gates and monitoring operational
- ✅ End-to-end ExecutionPlan execution working
- ✅ Self-improvement example: orchestrator coordinating its own enhancement

## COORDINATION METHOD
- **Build on Agent 1's validated working features only**
- **Implement Agent 2's prioritized gaps systematically**
- **Leverage current parallel task execution for coordination**
- **Validate each implementation step with working examples**

## COMMUNICATION PROTOCOL
- **Hour 0-2**: Prepare infrastructure, don't wait
- **Hour 2**: Receive Agent 2's roadmap and begin implementation
- **Hour 4**: Share integration results with other agents
- **Hour 6**: Demonstrate complete working ExecutionPlan system

## DELIVERABLE EVIDENCE REQUIREMENTS
Every implemented feature must include:
1. **Working code** that integrates with current orchestrator
2. **Integration test** that proves it actually works (not just claims)
3. **Example** showing ExecutionPlan functionality
4. **Documentation** of how it enhances ExecutionPlan capabilities

## COORDINATION AWARENESS
- **Agent 1**: Provides working feature baseline you must preserve
- **Agent 2**: Provides implementation roadmap and priority guidance
- **Your implementation enables**: Working ExecutionPlan system built on validated foundation

## FINAL DELIVERABLE
Create `/home/opsvi/master_root/agent_coordination/agent_3_results/` with:
- Working ExecutionPlan system integrated with current orchestrator
- Comprehensive integration tests and validation
- Self-improvement demonstration
- Documentation of complete ExecutionPlan capabilities

**FINAL GOAL**: Working ExecutionPlan system that can coordinate its own development, proving the self-orchestrating concept works.
