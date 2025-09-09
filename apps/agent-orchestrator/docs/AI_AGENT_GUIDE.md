# AI Agent's Guide to Agent Orchestrator

**Quick reference for AI agents working with the Agent Orchestrator system.**

---

## 🎯 What This System Does

Agent Orchestrator coordinates multiple AI agents to work together on complex tasks. Think of it as a smart project manager that distributes work, manages dependencies, handles failures, and tracks progress across up to 15 parallel agents.

## 🚀 Quick Start Commands

```bash
# Navigate to orchestrator directory
cd /home/opsvi/master_root/apps/agent-orchestrator

# Generate complete documentation for any project
python run_orchestrator_task.py \
  --task-type system-documentation \
  --app-name "project-name" \
  --app-root "/path/to/project"

# Run system analysis (comprehensive)
python run_system_analysis.py

# Custom workflow from JSON
python main.py --tasks-file my_tasks.json --max-parallel 5

# Resume interrupted work
python resume_orchestrator.py --list-checkpoints
python resume_orchestrator.py checkpoint_id_here

# Start monitoring dashboard
python production_dashboard.py
```

## 📋 Key Scripts & Their Uses

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `main.py` | Core orchestrator | Custom JSON workflows |
| `run_orchestrator_task.py` | Template workflows | Standard documentation, analysis |
| `run_system_analysis.py` | System self-analysis | Understand capabilities |
| `resume_orchestrator.py` | Checkpoint management | Resume interrupted work |
| `production_dashboard.py` | Monitoring dashboard | Real-time tracking |

## 🏗️ Task Definition Format

```json
{
  "tasks": [
    {
      "task_id": "analyze_code",
      "task_type": "analysis",
      "prompt": "Analyze the codebase for security issues",
      "context": {"target_dir": "/path/to/code"},
      "dependencies": ["setup_task"],
      "quality_gates": ["security_check"]
    }
  ]
}
```

## 🔧 Common Parameters

```bash
--max-parallel 10        # Max simultaneous agents (1-15)
--output-dir ./results   # Where to save outputs
--use-enhanced          # Enable quality gates
--enable-dashboard      # Real-time monitoring
--resume-checkpoint id  # Resume from checkpoint
--template comprehensive # Documentation template
```

## 📊 Built-in Workflows

### System Documentation (`system-documentation`)
**Generates:** README, ARCHITECTURE, API_REFERENCE, USER_GUIDE, DEVELOPER_GUIDE, DEPLOYMENT
```bash
python run_orchestrator_task.py \
  --task-type system-documentation \
  --app-name "my-app" \
  --app-root "/path/to/app"
```

### System Analysis
**Analyzes:** Architecture, performance, integration points, documentation gaps
```bash
python run_system_analysis.py
```

### Parallel Documentation Update
**Updates:** Multiple docs simultaneously with dependency management
```bash
python run_parallel_doc_update.py
```

## 💡 Key Concepts

**Dependencies:** Tasks can depend on others (e.g., "write docs" depends on "analyze code")

**Quality Gates:** Built-in validation (security_check, performance_review, completeness_check)

**Checkpoints:** Automatic save points - never lose progress on long workflows

**Token Pool:** Manages Claude API tokens across parallel agents automatically

**Dashboard:** Real-time monitoring at `http://localhost:8765` when enabled

## 🔍 Monitoring & Debugging

```bash
# Check logs
tail -f outputs/logs/orchestrator_*.log

# List checkpoints
python resume_orchestrator.py --list-checkpoints

# Monitor system
python agent_background_monitor.py

# Dashboard access
http://localhost:8765 (after starting production_dashboard.py)
```

## 📁 Output Structure

```
outputs/
├── analysis/           # System analysis results
├── doc_update_*/       # Documentation updates
├── workflow_*/         # Custom workflows
├── logs/              # Execution logs
├── checkpoints/       # Recovery points
└── tasks/            # Individual task results
```

## ⚡ Performance Tips

- **Start small:** 3-5 agents for testing, scale up based on results
- **Use templates:** Built-in workflows are optimized and tested
- **Enable checkpoints:** For any workflow > 30 minutes
- **Monitor resources:** Check system RAM/CPU with multiple agents
- **Quality gates:** Use `--use-enhanced` for production workflows

## 🚨 Common Issues & Fixes

**"No tokens available"**
- System auto-loads tokens from multiple sources
- Check: `python -c "from src.token_loader import load_tokens; print(f'Loaded {len(load_tokens())} tokens')"`

**"Task dependency failed"**
- Check logs: `tail -f outputs/logs/orchestrator_*.log`
- Resume from checkpoint: `python resume_orchestrator.py checkpoint_id`

**"Max parallel reached"**
- Reduce `--max-parallel` setting
- Monitor system resources

## 🎛️ Advanced Features

**Enhanced Orchestrator:** `--use-enhanced` enables quality gates, monitoring, optimizations

**Dashboard Integration:** `--enable-dashboard` provides real-time WebSocket updates

**Multi-Provider:** Supports Claude + OpenAI with automatic failover

**Collaboration:** Multi-agent coordination with conflict resolution

**Analytics:** Built-in session analysis and performance metrics

## 🔗 Integration Points

- **MCP Tools:** File ops, web scraping, databases
- **External APIs:** REST endpoints for status and control
- **WebSocket:** Real-time updates for dashboards
- **Checkpoints:** Resume from any point in complex workflows

## 📖 When to Read Full Docs

- **README.md:** Installation, architecture overview, Docker deployment
- **ARCHITECTURE.md:** Technical design, data flow, performance specs
- **API_REFERENCE.md:** Complete API docs, Python classes, error codes
- **USER_GUIDE.md:** Detailed examples, configuration, troubleshooting

## 🎯 Typical Agent Workflow

1. **Plan:** Define tasks with clear dependencies
2. **Configure:** Choose template or create custom JSON
3. **Execute:** Run with appropriate parallel limits
4. **Monitor:** Use dashboard or logs to track progress
5. **Recover:** Use checkpoints if interrupted
6. **Review:** Check outputs directory for results

---

**Key Insight:** This system excels at coordinating complex, multi-step workflows where different agents specialize in different aspects (analysis, documentation, implementation, testing) and need to work together efficiently.

**Production Ready:** Handles 15 parallel agents, automatic recovery, quality validation, and comprehensive monitoring out of the box.
