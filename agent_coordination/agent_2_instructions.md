# AGENT 2 INSTRUCTIONS: GAP ANALYSIS ENGINEER

**Agent ID**: 73e9afda-d056-40b8-917f-9c1845706830
**Session Role**: Gap Analysis Engineer
**Mission**: Gap analysis and implementation planning

## CRITICAL CONTEXT
- **Your previous "ExecutionPlan complete" claims were overclaimed**
- Agent 1 is testing what actually works right now
- You can start immediately with existing documentation analysis
- **Your job**: Honest gap analysis and realistic implementation planning

## PARALLEL EXECUTION STRATEGY
- **Start immediately** with documentation-based gap analysis
- **Hour 1**: Receive Agent 1's preliminary findings and validate your analysis
- **Hour 2**: Publish validated roadmap for Agent 3's implementation

## YOUR EXECUTION PLAN

### PHASE 2A: INITIAL GAP ANALYSIS (Hour 0-1, Parallel Start)
Begin immediately using existing documentation analysis:

```python
# Based on documentation review findings, start gap analysis
initial_gaps_analysis = {
    "documented_features": [
        "Quality gates system",
        "Agent team manager",
        "Dynamic token pools",
        "Escalation manager",
        "Real-time monitoring",
        "ExecutionPlan integration"
    ],
    "likely_missing": "Most advanced features based on doc vs implementation analysis",
    "execution_plan_requirements": [
        "Task validation and quality gates",
        "Execution plan parsing and validation",
        "Dynamic task coordination",
        "Real-time monitoring and status updates",
        "Error handling and recovery"
    ]
}
```

**DELIVERABLES (Hour 1)**:
- `preliminary_gap_analysis.md`: Based on documentation review
- `execution_plan_requirements.md`: What ExecutionPlans need to work

### PHASE 2B: VALIDATION AGAINST REALITY (Hour 1-2)
**WAIT FOR**: Agent 1's `preliminary_test_results.json`

Validate your preliminary analysis against Agent 1's actual test results:

```python
# Compare your assumptions to Agent 1's findings
reality_check = {
    "your_predictions_vs_agent_1_findings": comparison,
    "accurate_predictions": [],
    "incorrect_assumptions": [],
    "updated_gap_analysis": revised_based_on_evidence
}
```

**DELIVERABLES (Hour 1-2)**:
- `validated_gap_analysis.md`: Updated based on Agent 1's findings
- `reality_vs_assumptions_report.md`: What you got right/wrong in initial analysis

### PHASE 2C: IMPLEMENTATION PRIORITIZATION (Hour 2-3)
Create implementation plan for Agent 3:

```python
implementation_roadmap = {
    "priority_1_features": {
        "quality_gates": {
            "description": "Working quality gates that actually validate tasks",
            "effort": "Medium",
            "blocks": "ExecutionPlan validation",
            "implementation_method": "Use current orchestrator to coordinate development"
        },
        "execution_plan_parser": {
            "description": "Parse ExecutionPlans into current orchestrator task format",
            "effort": "High",
            "blocks": "ExecutionPlan execution",
            "dependencies": ["quality_gates"]
        }
    },
    "coordination_method": "How Agent 3 uses current working orchestrator"
}
```

**DELIVERABLES (Hour 2-3)**:
- `implementation_priority_matrix.md`: Features ranked by impact vs effort
- `realistic_implementation_roadmap.md`: Step-by-step plan for Agent 3
- `coordination_execution_plans.md`: How to use current orchestrator for implementation

## SUCCESS CRITERIA
- ✅ Honest assessment of gaps (no overclaiming)
- ✅ Realistic implementation plan based on actual capabilities
- ✅ Clear roadmap that Agent 3 can execute
- ✅ Implementation plan uses current working orchestrator for coordination

## ANTI-OVERCLAIMING PROTOCOL
**BREAK THE CYCLE**: Your previous claims about ExecutionPlan completion were inaccurate
- Every gap must be verified against Agent 1's test results
- Every implementation estimate must be realistic and evidence-based
- No feature marked as "easy" unless you can justify the assessment
- Implementation plan must use current working orchestrator capabilities only

## COMMUNICATION PROTOCOL
- **Hour 0**: Start with preliminary analysis, don't wait
- **Hour 1**: Receive and validate against Agent 1's findings
- **Hour 2**: Publish implementation roadmap for Agent 3

## COORDINATION AWARENESS
- **Agent 1**: Provides reality check for your gap analysis
- **Agent 3**: Waiting for your implementation roadmap and coordination strategy
- **Your analysis enables**: Realistic, evidence-based implementation planning

## FINAL DELIVERABLE
Create `/home/opsvi/master_root/agent_coordination/agent_2_results/` with:
- Validated gap analysis based on real testing
- Prioritized implementation roadmap
- Coordination strategy for using current orchestrator
- Honest assessment of implementation complexity and timeline
