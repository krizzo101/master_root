# Orchestrator Resume Guide

## Standardized Checkpoint Resume System

### Quick Start
```bash
# Resume from any checkpoint or output directory
python standardized_resume.py <checkpoint_or_output_dir>

# With options
python standardized_resume.py output/self_improvement_continued --max-parallel 15
```

### Resume Methods

#### 1. Standardized Resume (RECOMMENDED)
**Script:** `standardized_resume.py`
**Features:**
- Auto-detects orchestrator type (Unified/Generic)
- Finds latest checkpoint automatically
- Filters completed tasks
- Adjusts dependencies
- Supports all orchestrator features

**Usage:**
```bash
# From checkpoint file
python standardized_resume.py output/workflow_*/checkpoints/latest_checkpoint.json

# From output directory (auto-finds checkpoint)
python standardized_resume.py output/self_improvement_continued

# After WSL restart with more RAM
./resume_after_restart.sh
```

#### 2. Simple Resume (Legacy)
**Script:** `simple_resume.py`
**Use Case:** Basic task-based resumption
**Limitation:** Doesn't handle UnifiedOrchestrator features

```bash
python simple_resume.py outputs/analysis/system_analysis_*
```

#### 3. Resume Orchestrator (Original)
**Script:** `resume_orchestrator.py`
**Use Case:** Interactive checkpoint selection
**Limitation:** No unified orchestrator parameters

```bash
python resume_orchestrator.py --list-checkpoints
python resume_orchestrator.py checkpoint_id
```

### When to Use Each Method

| Scenario | Recommended Script | Command |
|----------|-------------------|---------|
| After crash/restart | `standardized_resume.py` | `python standardized_resume.py output/dir` |
| Self-improvement workflow | `standardized_resume.py` | `./resume_after_restart.sh` |
| Simple workflows | `simple_resume.py` | `python simple_resume.py output/dir` |
| Interactive selection | `resume_orchestrator.py` | `python resume_orchestrator.py --list` |

### Checkpoint Locations

Checkpoints are saved in:
```
output/
└── workflow_name_timestamp/
    └── checkpoints/
        ├── checkpoint_20250910_*.json    # Timestamped checkpoints
        └── latest_checkpoint.json        # Most recent checkpoint
```

### Resume Process Flow

1. **Analyze Checkpoint**
   - Load checkpoint file
   - Identify completed/failed/running tasks
   - Determine orchestrator type

2. **Filter Tasks**
   - Remove completed tasks from workflow
   - Adjust dependencies (remove refs to completed tasks)
   - Create resume workflow file

3. **Configure Orchestrator**
   - UnifiedOrchestrator: All features enabled
   - GenericOrchestrator: Basic execution
   - Set appropriate parallelism

4. **Execute Resume**
   - Start from first incomplete task
   - Skip already completed work
   - Continue until workflow complete

### Troubleshooting

**"No checkpoint found"**
- Check output directory exists
- Verify checkpoint file present
- Use `--list-checkpoints` to see available

**"Task already completed"**
- Normal - orchestrator skips completed tasks
- Check task output files in `output/*/tasks/`

**Memory issues during resume**
- Reduce `--max-parallel` setting
- Check system resources with `free -h`
- Consider restarting with more RAM

**Token exhaustion**
- Wait for 5-hour window reset
- Resume will continue from last checkpoint
- Consider reducing context size

### Best Practices

1. **Always use standardized_resume.py** for consistency
2. **Monitor with orchestrator_monitor.py** during execution
3. **Check memory before resuming** large workflows
4. **Save checkpoint path** before system changes
5. **Use appropriate parallelism** for available RAM:
   - 8GB RAM: max-parallel 5-8
   - 16GB RAM: max-parallel 10-12
   - 28GB RAM: max-parallel 15-20

### Example: Self-Improvement Workflow

```bash
# After token exhaustion or crash
cd /home/opsvi/master_root/apps/agent-orchestrator

# Check status
python orchestrator_monitor.py --once

# Resume from checkpoint
python standardized_resume.py output/self_improvement_continued

# Monitor progress
python orchestrator_monitor.py --interval 10
```

---

*Last Updated: 2025-09-10*
*Version: 1.0*
