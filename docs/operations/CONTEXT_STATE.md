# Context State for Branch Integration

## Where We Are:
- Current branch: feature/chronological-integration-all
- Created from: main branch
- Status: Clean, ready to start merging

## What We've Done:
1. Analyzed all 16 unmerged branches
2. Determined they all diverged from same point (2025-08-03)
3. Created merge order based on commits/features
4. Created test branch feature/clean-integration-all with manual copy approach (abandoned for full merge)

## Key Discoveries:
- gemini branch has SDLC framework but would delete apps/ (because it has old .gitignore)
- hello-world branch has all apps tracked and fixed .gitignore
- Many branches move files to .archive/ (4000+ files, but directory is ignored)
- apps/ was previously ignored in .gitignore, now only apps/ACCF should be ignored

## Critical Issues Found:
- apps/README.md had wrong instructions (said to develop in intake/)
- intake/ should NEVER be used for development (only for external code evaluation)
- .archive/ and .reference/ should be ignored
- Multiple branches delete files they don't know about

## Files to Read After Compact:
- /home/opsvi/master_root/MERGE_PLAN.md - the merge strategy
- /home/opsvi/master_root/CONTEXT_STATE.md - this file
- /tmp/analyze_branches.py - script to analyze branch chronology

## Next Steps:
1. Execute merges in order from MERGE_PLAN.md
2. For each merge, handle conflicts by keeping files (never delete)
3. After all merges, validate everything is preserved

## Important Commands:
```bash
# Current branch
git branch --show-current  # should be feature/chronological-integration-all

# Start merging (example for first branch)
git merge AUTOSAVE

# If conflicts about deletions
git status  # see what's in conflict
git add <file>  # to keep a file that was "deleted"
git commit  # complete the merge

# Check what we have
ls apps/  # should show all apps
git ls-files apps/ | wc -l  # count tracked files
```
