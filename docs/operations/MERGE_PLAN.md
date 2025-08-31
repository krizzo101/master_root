# Chronological Branch Merge Plan

## Current Situation
- We're on branch: feature/chronological-integration-all (created from main)
- Goal: Merge ALL 16 feature branches chronologically to preserve all work
- Critical: Don't lose any files or changes from any branch

## Merge Order (MUST follow this sequence):
1. **AUTOSAVE** (11 commits)
2. **fix/storage-api** (18 commits)
3. **feature/libs-foundation** (36 commits)
4. **feature/gpt5-agent** (50 commits)
5. **feat/workspace-optimization** (17 commits)
6. **feature/yaml-templates-modernization** (88 commits)
7. **feature/ai-populator-helper** (104 commits)
8. **feat/research-reliability** (105 commits)
9. **feature/proj-mapper-visualize-reliability** (107 commits)
10. **feature/w1-data-extraction** (107 commits)
11. **feature/w1-opsvi-data-copy** (108 commits)
12. **feature/fix-uv-workspace** (124 commits)
13. **feature/auto-forge-production-factory** (125 commits)
14. **feature/migrate-misplaced-packages** (137 commits)
15. **feature/gemini-cli-2_5-pro-and-cli-invoke** (189 commits)
16. **feature/hello-world-app** (4 commits)

## Critical Rules for Merging:
- **NEVER delete files** - always keep files when there's a deletion conflict
- **For .gitignore conflicts**: Keep apps/ tracked (not ignored), only ignore apps/ACCF
- **For file moves to .archive/**: Accept them (directory is ignored anyway)
- **When in doubt**: Keep everything, we'll clean up later

## Key Files to Preserve:
- CLAUDE.md (from gemini branch)
- .claude/agents/*.md (agent profiles)
- apps/proj-mapper/ (429 files)
- apps/auto-forge-factory/ (21 files)
- apps/knowledge_system/ (22 files)
- apps/hello-world/ (docs by another agent)
- libs/opsvi-mcp/opsvi_mcp/tools/mcp_resource_discovery.py
- .claude/commands/sdlc.md (our fixed version)

## Branches Already Partially Integrated:
- feature/clean-integration-all - manually copied SDLC files from gemini and hello-world
- This was our test approach but we decided to do chronological merge instead

## What NOT to Merge:
- test-integration-merge (test branch)
- backup/pre-merge-20250815-194708 (backup)
- feature/clean-integration-all (our manual attempt)

## After All Merges:
1. Verify all apps/* are present
2. Verify CLAUDE.md exists in root
3. Verify .gitignore only ignores apps/ACCF (not all of apps/)
4. Run git status to check for issues
5. Commit the final integrated state

## User's Backup:
User has full backup of master_root directory, so we can recover if needed.
