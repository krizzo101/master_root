---
description: Quick onboarding for the Agent Orchestrator system
allowed-tools: Read, Bash, Grep
---

## 🚀 Agent Orchestrator Quick Start

You're working with the **Agent Orchestrator** - a system that coordinates up to 15 parallel AI agents for complex tasks. Here's what you need to know:

### 📍 Location & Navigation
```bash
cd /home/opsvi/master_root/apps/agent-orchestrator
```

### 🎯 Core Purpose
- **Smart project manager** for AI agents
- Handles task distribution, dependencies, failures, and progress tracking
- Production-ready with checkpoints, monitoring, and quality gates

### ⚡ Essential Commands

**1. Generate Complete Documentation**
```bash
python run_orchestrator_task.py \
  --task-type system-documentation \
  --app-name "project-name" \
  --app-root "/path/to/project"
```
Creates: README, ARCHITECTURE, API_REFERENCE, USER_GUIDE, DEVELOPER_GUIDE, DEPLOYMENT

**2. Run System Analysis**
```bash
python run_system_analysis.py
```

**3. Custom Workflow**
```bash
python main.py --tasks-file my_tasks.json --max-parallel 5
```

**4. Resume Interrupted Work**
```bash
python resume_orchestrator.py --list-checkpoints
python resume_orchestrator.py checkpoint_id_here
```

**5. Monitor in Real-time**
```bash
python production_dashboard.py
# Access at http://localhost:8765
```

### 📋 Task JSON Format
```json
{
  "tasks": [{
    "task_id": "analyze_code",
    "task_type": "analysis",
    "prompt": "Analyze the codebase for security issues",
    "context": {"target_dir": "/path/to/code"},
    "dependencies": ["setup_task"],
    "quality_gates": ["security_check"]
  }]
}
```

### 🔧 Key Parameters
- `--max-parallel 10` → Max simultaneous agents (1-15)
- `--use-enhanced` → Enable quality gates
- `--enable-dashboard` → Real-time monitoring
- `--resume-checkpoint id` → Resume from checkpoint

### 💡 Key Features
- **Dependencies**: Tasks can depend on others
- **Quality Gates**: Built-in validation (security_check, performance_review)
- **Checkpoints**: Auto-save points for long workflows
- **Token Pool**: Automatic Claude API token management
- **Dashboard**: Real-time monitoring at localhost:8765

### 📁 Output Structure
```
outputs/
├── analysis/        # System analysis results
├── workflow_*/      # Custom workflows
├── logs/           # Execution logs
├── checkpoints/    # Recovery points
└── tasks/          # Individual task results
```

### 🚨 Quick Fixes
- **"No tokens available"**: Check `python -c "from src.token_loader import load_tokens; print(f'Loaded {len(load_tokens())} tokens')"`
- **"Task dependency failed"**: Check logs: `tail -f outputs/logs/orchestrator_*.log`
- **Resume after failure**: `python resume_orchestrator.py checkpoint_id`

### 🎯 Your Next Steps
Based on "$ARGUMENTS", here's what to do:

1. If documenting: Use `run_orchestrator_task.py --task-type system-documentation`
2. If analyzing: Use `run_system_analysis.py`
3. If custom workflow: Create JSON task definition and use `main.py`
4. If monitoring: Start `production_dashboard.py`

### 📊 Project Intelligence Integration
If `.proj-intel/` exists, use:
```bash
python /home/opsvi/master_root/scripts/proj_intel_reader.py --action file-elements --format summary
```

**Remember**: This system excels at coordinating complex, multi-step workflows where different agents specialize in different aspects. It's production-ready with 15 parallel agents, automatic recovery, and comprehensive monitoring.
