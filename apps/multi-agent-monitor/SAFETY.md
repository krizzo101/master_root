# Multi-Agent Safety System

## Overview

The Multi-Agent Safety System provides comprehensive protection when unleashing AI agents on your codebase. It ensures all changes are tracked, validated, and reversible.

## Key Features

### 🛡️ Git Integration
- **Automatic Checkpoints**: Creates git branches before execution
- **Phase Commits**: Commits after each successful phase
- **Rollback Capability**: Instant rollback to any checkpoint
- **Branch Protection**: Never works directly on main/master

### 🔍 Change Validation
- **File Limits**: Configurable limits on files changed
- **Line Limits**: Maximum lines that can be modified
- **Protected Paths**: Prevents modification of sensitive files
- **Pattern Detection**: Identifies dangerous operations

### 📝 Review Workflow
- **Change Reports**: Detailed analysis of all modifications
- **Risk Assessment**: Automatic risk level calculation
- **Pull Requests**: Optional PR creation for review
- **Approval Gates**: Require human approval for risky changes

### 💾 Backup System
- **Pre-execution Backups**: Full backup before agents start
- **Phase Backups**: Optional backups between phases
- **Quick Recovery**: Restore from any backup point

## Quick Start

### 1. Basic Safe Execution

```bash
# Dry run first (preview only)
python safe_execute.py my_project --type web --dry-run

# Execute with default safety (medium)
python safe_execute.py my_project --type web --requirements "Build a todo app"

# High safety mode with review
python safe_execute.py my_project --type refactor --mode review --safety high
```

### 2. Safety Levels

| Level | Max Files | Max Lines | Use Case |
|-------|-----------|-----------|----------|
| LOW | 50 | 2000 | Documentation, comments |
| MEDIUM | 30 | 1000 | Features, bug fixes |
| HIGH | 10 | 500 | Core logic, APIs |
| CRITICAL | 5 | 100 | Production, security |

### 3. Execution Modes

#### Dry Run Mode
Preview what agents will do without making changes:
```bash
python safe_execute.py project --type web --dry-run
```

#### Safe Mode (Default)
Execute with all safety features:
```bash
python safe_execute.py project --type web --mode safe
```

#### Review Mode
Require manual review before merging:
```bash
python safe_execute.py project --type web --mode review
```

#### Emergency Mode
Bypass safety for urgent fixes (use with extreme caution!):
```bash
python safe_execute.py hotfix --type web --mode emergency
```

## Workflow

### Standard Safe Execution Flow

```
1. Pre-flight Checks
   ├── Git status clean?
   ├── Not on protected branch?
   ├── Tokens available?
   └── Disk space sufficient?

2. Create Safety Checkpoint
   ├── Create checkpoint branch
   ├── Initial commit
   └── Switch to working branch

3. Execute Phases
   ├── Run agents
   ├── Validate changes
   ├── Commit if valid
   └── Rollback if invalid

4. Post-execution Review
   ├── Generate report
   ├── Calculate risk
   ├── Create PR if needed
   └── Merge or request review
```

## Git Branch Structure

```
main/master
  │
  ├── checkpoint/project/20240115_120000  (safety checkpoint)
  │     │
  │     └── agents/project/20240115_120000  (working branch)
  │           │
  │           ├── commit: Discovery phase complete
  │           ├── commit: Design phase complete
  │           ├── commit: Development phase complete
  │           └── commit: Testing phase complete
  │
  └── [PR] Merge agents/project/20240115_120000
```

## Safety Commands

### Checkpoint Management

```bash
# Create manual checkpoint
python src/safety/git_safety_manager.py checkpoint my_checkpoint

# Rollback to checkpoint
python src/safety/git_safety_manager.py rollback

# Rollback to specific commit
python src/safety/git_safety_manager.py rollback abc123
```

### Review Process

```bash
# Generate review report
python src/safety/git_safety_manager.py review

# Approve and merge
python src/safety/git_safety_manager.py merge

# Check safety status
python src/safety/git_safety_manager.py status
```

## Configuration

### Safety Configuration File

Create `.agent_safety.json` in project root:

```json
{
  "auto_commit": true,
  "require_review": true,
  "max_file_changes": 50,
  "max_line_changes": 2000,
  "protected_paths": [
    ".env",
    "*.key",
    ".secrets/",
    "production/"
  ],
  "create_pr": true,
  "auto_rollback_on_error": true
}
```

### Protected Files

By default, the following are protected:
- `.git/` - Git directory
- `.env` - Environment variables
- `*.key`, `*.pem` - Keys and certificates
- `.secrets/` - Secrets directory
- `credentials` - Any credential files

Add custom patterns in configuration.

## Validation Rules

### File Change Validation

Agents cannot:
- Modify protected files
- Delete entire directories
- Change more files than limit
- Modify more lines than limit

### Content Validation

Detected and flagged:
- `rm -rf` commands
- `DROP TABLE` statements
- `DELETE FROM` without WHERE
- Force push operations
- Credential exposure

### Phase Validation

Each phase must:
- Complete successfully
- Pass validation checks
- Create expected deliverables
- Not exceed change limits

## Rollback Procedures

### Automatic Rollback

Triggered by:
- Agent execution failure
- Validation failure (HIGH/CRITICAL safety)
- User interrupt (Ctrl+C)
- Exceeding change limits

### Manual Rollback

```bash
# Rollback to last checkpoint
python src/safety/git_safety_manager.py rollback

# Rollback to specific phase
git log --oneline  # Find commit
git reset --hard <commit>

# Restore from backup
cp -r .agent_backups/backup_20240115_120000/* .
```

## Risk Assessment

### Risk Calculation

Risk level based on:
- Number of files changed
- Lines added/deleted
- Protected file modifications
- Dangerous patterns detected

### Risk Levels

| Level | Action |
|-------|--------|
| LOW | Auto-merge allowed |
| MEDIUM | Review recommended |
| HIGH | Review required |
| CRITICAL | Manual intervention required |

## Best Practices

### Before Execution

1. **Always dry run first**
   ```bash
   python safe_execute.py project --type web --dry-run
   ```

2. **Commit current work**
   ```bash
   git add -A && git commit -m "Pre-agent checkpoint"
   ```

3. **Use appropriate safety level**
   - Documentation → LOW
   - Features → MEDIUM
   - Core changes → HIGH
   - Production → CRITICAL

### During Execution

1. **Monitor output** - Watch for validation warnings
2. **Check progress** - Review phase commits
3. **Interrupt if needed** - Ctrl+C triggers rollback

### After Execution

1. **Review changes**
   ```bash
   git diff checkpoint/project...agents/project
   ```

2. **Test thoroughly** before merging
3. **Keep checkpoint** until verified

## Troubleshooting

### Common Issues

#### "Working directory not clean"
```bash
git stash  # Save changes
# or
git commit -am "Save work"
```

#### "On protected branch"
```bash
git checkout -b feature/my-feature
```

#### "Validation failed"
- Review the issues listed
- Adjust safety level if appropriate
- Manually fix problematic changes

#### "Rollback failed"
```bash
# Force rollback
git reset --hard checkpoint/project/timestamp

# Restore from backup
cp -r .agent_backups/latest/* .
```

### Emergency Recovery

If all else fails:

1. **Find last good commit**
   ```bash
   git log --oneline -20
   ```

2. **Hard reset**
   ```bash
   git reset --hard <good-commit>
   ```

3. **Restore from backup**
   ```bash
   ls -la .agent_backups/
   cp -r .agent_backups/<backup>/* .
   ```

## Advanced Usage

### Custom Safety Rules

```python
from src.safety import SafeOrchestrator, SafetyLevel

orchestrator = SafeOrchestrator()

# Custom file limits
orchestrator.safety_config["change_limits"][SafetyLevel.MEDIUM] = {
    "files": 20,
    "lines": 800
}

# Custom protected paths
orchestrator.safety_config["protected_paths"].extend([
    "production/",
    "*.prod.yml"
])
```

### Integration with CI/CD

```yaml
# .github/workflows/agent_review.yml
name: Agent Change Review

on:
  pull_request:
    branches: [main]
    paths:
      - 'agents/**'

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate Agent Changes
        run: |
          python src/safety/git_safety_manager.py review
```

### Monitoring Metrics

Track agent safety:
- Rollback frequency
- Validation failures
- Average risk levels
- Review approval rates

## Safety Guarantees

The system provides:

1. **No direct main branch modification** - Always works on feature branches
2. **Automatic rollback on failure** - Configurable auto-rollback
3. **Change validation** - All changes validated before commit
4. **Audit trail** - Complete git history of all changes
5. **Multiple recovery options** - Checkpoints, backups, and git history

## Summary

The Multi-Agent Safety System ensures that AI agents can work on your codebase with confidence. By combining git integration, validation rules, and review workflows, it provides multiple layers of protection against unwanted changes while maintaining the efficiency benefits of multi-agent orchestration.

**Remember**: Always start with a dry run, use appropriate safety levels, and review changes before merging to production!
