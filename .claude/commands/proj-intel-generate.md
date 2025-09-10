---
description: Generate project intelligence for a codebase
argument-hint: [project-path or leave blank for current]
allowed-tools: Bash, Read
---

## =( Generate Project Intelligence

Creating project intelligence for: ${ARGUMENTS:-current directory}

### Generating Intelligence
```bash
PROJECT_PATH="${ARGUMENTS:-$(pwd)}"
cd "$PROJECT_PATH"

# Run generation (auto-overwrites existing data)
project-intelligence full-package

# With options:
# project-intelligence full-package --verbose     # See progress
# project-intelligence full-package --enhanced    # Enhanced analysis
```

### Output:
Creates `.proj-intel/` directory with indexed data for O(1) lookups.

### Note:
Regenerate after code changes (not automated yet).
