---
description: Run comprehensive system analysis using Agent Orchestrator
allowed-tools: Bash, Read
---

## 🔍 System Analysis with Agent Orchestrator

Running comprehensive analysis of the orchestrator system and optionally analyzing: $ARGUMENTS

### Starting Analysis

```bash
cd /home/opsvi/master_root/apps/agent-orchestrator

# Run comprehensive system analysis
python run_system_analysis.py

# If specific target provided
if [ -n "$ARGUMENTS" ]; then
    python main.py --tasks-file <(cat <<EOF
{
  "tasks": [
    {
      "task_id": "analyze_target",
      "task_type": "analysis",
      "prompt": "Perform comprehensive analysis of $ARGUMENTS including architecture, performance, security, and documentation gaps",
      "context": {
        "target": "$ARGUMENTS",
        "analysis_depth": "comprehensive"
      },
      "quality_gates": ["completeness_check"]
    }
  ]
}
EOF
) --use-enhanced --max-parallel 3
fi
```

### Analysis Components:
- **Architecture Review** - Component relationships, design patterns
- **Performance Analysis** - Bottlenecks, optimization opportunities
- **Integration Points** - External dependencies, APIs
- **Documentation Gaps** - Missing or outdated docs
- **Security Assessment** - Potential vulnerabilities
- **Code Quality** - Complexity, maintainability

### Results Location:
- System analysis: `outputs/analysis/`
- Custom analysis: `outputs/workflow_*/`
- Detailed logs: `outputs/logs/`
