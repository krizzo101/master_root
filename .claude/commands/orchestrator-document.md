---
description: Generate complete documentation for a project using Agent Orchestrator
argument-hint: [project-path or leave blank for current]
allowed-tools: Bash, Read
---

## 📚 Generate Complete Project Documentation

Using Agent Orchestrator to create comprehensive documentation for: ${ARGUMENTS:-current directory}

### Executing Documentation Generation

```bash
cd /home/opsvi/master_root/apps/agent-orchestrator

# Determine project path
PROJECT_PATH="${ARGUMENTS:-$(pwd)}"
PROJECT_NAME=$(basename "$PROJECT_PATH")

python run_orchestrator_task.py \
  --task-type system-documentation \
  --app-name "$PROJECT_NAME" \
  --app-root "$PROJECT_PATH" \
  --template comprehensive \
  --use-enhanced \
  --max-parallel 5
```

### What This Creates:
- **README.md** - Overview, installation, quick start
- **ARCHITECTURE.md** - System design, components, data flow
- **API_REFERENCE.md** - Complete API documentation
- **USER_GUIDE.md** - End-user documentation
- **DEVELOPER_GUIDE.md** - Development setup, workflows
- **DEPLOYMENT.md** - Deployment and operations guide

### Output Location:
Documentation will be saved to: `$PROJECT_PATH/docs/`

### Monitor Progress:
- Check logs: `tail -f outputs/logs/orchestrator_*.log`
- Or start dashboard: `python production_dashboard.py`
