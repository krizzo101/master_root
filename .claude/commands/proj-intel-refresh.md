---
description: Refresh project intelligence after code changes
allowed-tools: Bash, Read
---

## = Refresh Project Intelligence

### Check Current State
```bash
if [ -d ".proj-intel" ]; then
    echo "Last generated: $(stat -c %y .proj-intel/proj_intel_manifest.json 2>/dev/null)"
fi
```

### Regenerate
```bash
# Auto-overwrites existing data
project-intelligence full-package --verbose

echo " Intelligence refreshed!"
```

### When to Refresh:
- After code changes
- After adding/removing files
- Before architectural reviews
- Note: Not automated yet - must run manually
