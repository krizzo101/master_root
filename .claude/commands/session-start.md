# Start Development Session

Initialize a new development session with clear goals and tracking.

## Session Setup

1. **Create session file**:
   ```bash
   mkdir -p .claude/sessions
   SESSION_FILE=".claude/sessions/$(date +%Y%m%d-%H%M%S)-session.md"
   ```

2. **Record session metadata**:
   - Timestamp: $(date)
   - Branch: $(git branch --show-current)
   - Working directory: $(pwd)
   - Initial git status

3. **Define session goals** (ask if not provided):
   - Primary objective
   - Success criteria
   - Out of scope items
   - Time estimate

4. **Capture starting state**:
   - Current TODO items
   - Any failing tests
   - Open issues/PRs related to work
   - Dependencies or blockers

5. **Set up tracking**:
   - Create todo list for session tasks
   - Note files likely to be modified
   - Identify tests that need to pass

## Session Document Template

```markdown
# Development Session - [DATE]

## Goals
- [ ] Primary: [What we're building/fixing]
- [ ] Secondary: [Additional objectives]

## Context
- Branch: [branch-name]
- Related Issue: #[number]
- Dependencies: [list any]

## Progress Log
[Timestamps and updates will go here]

## Decisions Made
- [Key decisions and rationale]

## Problems & Solutions
- [Issues encountered and how they were resolved]

## Files Modified
- [List of changed files]

## Next Steps
- [What needs to be done next session]
```

Save session file path for updates throughout work.
