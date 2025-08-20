# App Migration Guide

## Overview

This guide documents the proven process for migrating applications into the master_root project ecosystem, based on the successful migration of proj-mapper.

## Migration Principles

1. **Error-First Development**: Stop and fix errors immediately, don't proceed past them
2. **Incremental Changes**: Small, testable changes with validation at each step
3. **Backup Everything**: Always create backups before modifications
4. **Test Continuously**: Verify each change works before proceeding
5. **Document Issues**: Record all errors and solutions for future reference

## Pre-Migration Checklist

- [ ] App is no longer a symlink (actual directory in `apps/`)
- [ ] Identify all external dependencies
- [ ] List all custom agents/analyzers to be replaced
- [ ] Determine which shared libs are needed
- [ ] Create backup of original code

## Migration Steps

### Step 1: Initial Analysis

```bash
# Analyze app structure
find apps/APP_NAME -name "*.py" -type f | wc -l  # Count Python files
find apps/APP_NAME -name "requirements*.txt"      # Find dependencies
ls -la apps/APP_NAME/                            # Check for .venv
```

### Step 2: Create Backup

```bash
# Always backup before changes
cp -r apps/APP_NAME .archive/APP_NAME-backup-$(date +%Y%m%d_%H%M%S)
```

### Step 3: Dependency Analysis

Map current components to shared libraries:

| Current Component | Master Root Library | Notes |
|------------------|-------------------|-------|
| custom/storage/* | libs/opsvi-data | File and data storage |
| custom/models/* | libs/opsvi-models | Data models |
| custom/agents/* | libs/opsvi-agents + claude-code | Use claude-code profiles |
| custom/pipeline/* | libs/opsvi-pipeline | Pipeline orchestration |
| custom/cli/* | libs/opsvi-interfaces | CLI interfaces |

### Step 4: Create Missing Libraries

If needed libraries don't exist, create them:

```python
# Example: Creating opsvi-visualization
libs/opsvi-NEWLIB/
├── __init__.py
├── opsvi_newlib/
│   ├── __init__.py
│   └── core.py
├── tests/
│   └── test_core.py
└── setup.py
```

### Step 5: Create Claude-Code Adapter

Replace custom agents/analyzers with claude-code adapter:

```python
# apps/APP_NAME/claude_code_adapter.py
from typing import Dict, Any
from pathlib import Path

class ClaudeCodeAdapter:
    """Adapter to use claude-code agent for all operations"""

    def __init__(self):
        self.profiles = {
            "analyze": {"mode": "analyze", "temperature": 0.1},
            "generate": {"mode": "code", "temperature": 0.2},
            "test": {"mode": "test", "temperature": 0.1}
        }

    def execute(self, task: str, data: Any) -> Dict[str, Any]:
        # Placeholder - will connect to real claude-code
        return {"status": "success", "result": data}

# Export as replacements for old classes
OldAnalyzer = ClaudeCodeAdapter
OldGenerator = ClaudeCodeAdapter
OldTester = ClaudeCodeAdapter
```

### Step 6: Fix Imports

Create import fixer script:

```python
import_mappings = {
    "from APP_NAME.core": "from opsvi_core",
    "from APP_NAME.models": "from opsvi_models",
    "from APP_NAME.storage": "from opsvi_data.storage",
    # Add more mappings
}

for py_file in python_files:
    content = py_file.read_text()
    for old, new in import_mappings.items():
        content = content.replace(old, new)
    py_file.write_text(content)
```

### Step 7: Environment Setup

Remove app-specific virtual environments:

```bash
rm -rf apps/APP_NAME/.venv
rm -rf apps/APP_NAME/venv
```

Create wrapper script:

```bash
#!/bin/bash
# scripts/APP_NAME
export PYTHONPATH="/home/opsvi/master_root/libs:apps/APP_NAME/src"
exec /home/opsvi/miniconda/bin/python apps/APP_NAME/main.py "$@"
```

### Step 8: Testing

Test incrementally:

```bash
# Test imports
python -c "import sys; sys.path.insert(0, 'libs'); from APP_NAME import __version__"

# Test CLI
scripts/APP_NAME --help

# Test core functionality
scripts/APP_NAME test-command
```

## Common Errors and Solutions

### Error: ModuleNotFoundError

**Symptom**: `ModuleNotFoundError: No module named 'some_module'`

**Solutions**:
1. Check Python environment: `which python`
2. Install in correct environment: `/home/opsvi/miniconda/bin/pip install module`
3. Check PYTHONPATH includes all needed directories

### Error: ImportError for Missing Classes

**Symptom**: `ImportError: cannot import name 'SomeClass' from 'module'`

**Solution**: Add missing exports to adapter:
```python
# In claude_code_adapter.py
SomeClass = ClaudeCodeAdapter  # Add this line
```

### Error: AttributeError for Missing Methods

**Symptom**: `AttributeError: 'Factory' object has no attribute 'some_method'`

**Solution**: Add missing method to adapter class:
```python
def some_method(self, *args, **kwargs):
    return self.default_implementation()
```

### Error: SyntaxError in Modified Files

**Symptom**: `SyntaxError: unterminated string literal`

**Solution**:
1. Check for unclosed quotes or docstrings
2. Verify automated replacements didn't break syntax
3. Use `python -m py_compile file.py` to validate

### Error: Package vs Module Execution

**Symptom**: `No module named APP.__main__; 'APP' is a package`

**Solution**: Run the main module directly:
```bash
python apps/APP_NAME/src/main.py  # Instead of python -m APP
```

## Migration Patterns

### Pattern 1: Agent Consolidation

Replace multiple specialized agents with claude-code profiles:

```python
# Before: 10+ custom agents
class PlannerAgent: ...
class CoderAgent: ...
class TesterAgent: ...

# After: One claude-code with profiles
profiles = {
    "planner": {"mode": "plan", "temperature": 0.1},
    "coder": {"mode": "code", "temperature": 0.2},
    "tester": {"mode": "test", "temperature": 0.1}
}
```

### Pattern 2: Infrastructure Simplification

Replace external dependencies with master_root components:

| External | Master Root Alternative |
|----------|------------------------|
| Redis | libs/opsvi-memory or Neo4j |
| PostgreSQL | libs/opsvi-data + Neo4j |
| Custom Cache | libs/opsvi-memory |
| Custom Logger | libs/opsvi-monitoring |

### Pattern 3: Gradual Migration

Use compatibility layers for incremental migration:

```python
# compatibility.py
class StorageAdapter:
    def __init__(self):
        try:
            from opsvi_data import Storage
            self.storage = Storage()
        except ImportError:
            from APP_NAME.storage import Storage
            self.storage = Storage()
```

## Testing Strategy

1. **Unit Tests**: Test individual components after migration
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Verify complete functionality
4. **Regression Tests**: Ensure nothing broke

```bash
# Run tests after each major change
pytest apps/APP_NAME/tests/ -v
```

## Rollback Procedure

If migration fails:

1. Restore from backup:
```bash
rm -rf apps/APP_NAME
cp -r .archive/APP_NAME-backup-TIMESTAMP apps/APP_NAME
```

2. Document what failed for next attempt

3. Create smaller incremental changes

## Success Metrics

Migration is complete when:

- [ ] All tests pass
- [ ] No custom virtual environment needed
- [ ] Using shared libraries from libs/
- [ ] Custom agents replaced with claude-code
- [ ] Wrapper script works
- [ ] Core functionality verified

## Example: proj-mapper Migration

**Stats**:
- Files modified: 119
- Libraries created: 1 (opsvi-visualization)
- Agents replaced: 5+ analyzers → 1 claude-code adapter
- Time taken: ~2 hours with error fixes

**Key Learnings**:
1. Python environment matters (venv vs miniconda)
2. Must fix errors immediately, not continue past them
3. Test after every change
4. Create adapters for gradual migration

## Next Apps to Migrate

Priority order based on complexity:

1. **auto-forge-factory** (Complex - 10+ agents)
   - High value: Demonstrates complete agent consolidation
   - Challenge: Redis/PostgreSQL replacement

2. **hello-cli** (Simple)
   - Good practice app
   - Minimal dependencies

3. **knowledge_system** (Medium)
   - Already uses some shared components
   - Good Neo4j integration example

## Automation Opportunities

Future tool to automate migration:

```python
class AppMigrator:
    def __init__(self, app_name):
        self.app_name = app_name
        self.error_handler = ErrorHandler()

    def migrate(self):
        self.backup()
        self.analyze_dependencies()
        self.create_adapters()
        self.fix_imports()
        self.test()
        self.create_wrapper()
```

## Support

For migration issues:
1. Check this guide's Common Errors section
2. Review proj-mapper migration in git history
3. Test incrementally with verbose logging
4. Document new issues and solutions
