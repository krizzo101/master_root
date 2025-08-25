# /compact - Enhanced Compact with Auto-Export

## Description
This overrides the built-in `/compact` command to add auto-export functionality.

## Behavior
1. Automatically exports the full session to `~/.claude/session-exports/pre-compact/`
2. Creates metadata file with session info
3. Maintains symlink to latest export
4. Then triggers the actual compact operation

## Implementation Details

The built-in `/compact` command in Claude Code:
- Compresses the conversation context
- Removes older messages while preserving important context
- Creates a summary stored at the path specified (e.g., `.claude/compact_context.txt`)
- **Implementation is closed-source within Claude Code**

Our enhancement:
- Intercepts the command via this markdown definition
- Triggers our Python export script first
- Then allows the built-in compact to proceed

## Usage
```
/compact
```
or
```
/compact @.claude/compact_context.txt
```

## Auto-Export Location
Sessions are automatically saved to:
- `~/.claude/session-exports/pre-compact/{project}_{timestamp}.jsonl`
- Metadata: `~/.claude/session-exports/pre-compact/{project}_{timestamp}_metadata.json`
- Latest symlink: `~/.claude/session-exports/pre-compact/latest.jsonl`

## Recovery
If you need to recover a pre-compact session:
```bash
# List all exported sessions
ls -la ~/.claude/session-exports/pre-compact/

# View the latest
python /home/opsvi/master_root/scripts/view-claude-session.py ~/.claude/session-exports/pre-compact/latest.jsonl
```

## Technical Notes

The `/compact` command visibility is limited because:
1. It's a **built-in Claude Code command** (not user-defined)
2. Implementation is within Claude Code's core (not accessible)
3. We can only hook into it via:
   - Command override (this file)
   - Pre/post hooks (if Claude Code supports them)
   - Shell aliases or wrappers

## Customization

To customize the export behavior, edit:
```
/home/opsvi/master_root/.claude/hooks/auto-export-on-compact.py
```

## Implementation

```python
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Auto-export before compact
exec(open('/home/opsvi/master_root/.claude/hooks/auto-export-on-compact.py').read())

# Then trigger the actual compact
# This passes through to the built-in command
print("Proceeding with compaction...")
```

---

**Note**: This command definition overrides the built-in `/compact` to add our export functionality. The actual compaction mechanism remains opaque as it's part of Claude Code's core implementation.
