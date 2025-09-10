# ORCHESTRATOR USAGE STANDARD - MANDATORY

## THE ONLY WAY TO USE ORCHESTRATOR

### 1. SIMPLE TASK EXECUTION
```bash
python main.py --tasks-file workflow.json --max-parallel 10
```

### 2. RESUME FROM CHECKPOINT
```bash
python standardized_resume.py output/workflow_dir
```

### THAT'S IT. NO OTHER WAYS.

## FORBIDDEN PRACTICES
❌ Creating new orchestrator wrapper scripts
❌ Making "improved" orchestrator versions
❌ Building custom runners or launchers
❌ Inventing new workflow formats
❌ Adding unnecessary complexity

## WORKFLOW FILE FORMAT (ONLY THIS)
```json
{
  "workflow_name": "descriptive_name",
  "tasks": [
    {
      "task_id": "001_task_name",
      "task_type": "agent-type",
      "prompt": "Clear instruction",
      "dependencies": []
    }
  ]
}
```

## AVAILABLE TASK TYPES (USE ONLY THESE)
- development-specialist
- qa-testing-guru
- solution-architect
- devops-automation
- technical-writer
- security-architect
- performance-optimizer

## RULES
1. **ONE TASK = ONE AGENT** - Never split tasks
2. **DEPENDENCIES ONLY** - No manual sequencing
3. **NO MEGA-WORKFLOWS** - Max 15 tasks per workflow
4. **USE EXISTING FEATURES** - Don't reinvent
5. **SIMPLE PROMPTS** - Clear, direct instructions

## MONITORING (ONLY WAY)
```bash
python orchestrator_monitor.py --output-dir output/workflow_dir
```

## NO EXCEPTIONS. NO CREATIVITY. JUST USE IT AS DESIGNED.

---
*This is the standard. Follow it.*
