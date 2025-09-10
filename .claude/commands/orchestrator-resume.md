---
description: Resume interrupted orchestrator workflows from checkpoints
allowed-tools: Bash, Read
---

## 🔄 Resume Orchestrator Workflow

Managing and resuming interrupted orchestrator workflows.

### List Available Checkpoints

```bash
cd /home/opsvi/master_root/apps/agent-orchestrator

# List all checkpoints
python resume_orchestrator.py --list-checkpoints

# Show checkpoint details
ls -la outputs/checkpoints/
```

### Resume from Checkpoint

If checkpoint ID provided: $ARGUMENTS

```bash
# Resume specific checkpoint
python resume_orchestrator.py ${ARGUMENTS:-$(ls -t outputs/checkpoints/*.json | head -1 | xargs basename | sed 's/.json//')}

# With enhanced features
python resume_orchestrator.py ${ARGUMENTS} --use-enhanced --enable-dashboard
```

### Checkpoint Information:
Each checkpoint contains:
- Task states and progress
- Completed outputs
- Dependencies resolved
- Token pool state
- Quality gate results

### Recovery Options:
- **--retry-failed** - Retry failed tasks
- **--skip-completed** - Skip already completed tasks
- **--max-parallel N** - Adjust parallelism
- **--enable-dashboard** - Monitor recovery progress
