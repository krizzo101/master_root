# CLAUDE.md - Bootstrap Instructions

## **DO NOT LIE. AT ALL.**

## CRITICAL: Your REAL instructions are in the Knowledge Base

### MANDATORY STARTUP (EVERY SESSION, NO EXCEPTIONS)
```python
# 1. THINK FIRST
mcp__thinking__metacognitivethinking(thought="Starting session, loading instructions", thoughtNumber=1, totalThoughts=2, nextThoughtNeeded=True)

# 2. CHECK TIME (to understand how outdated you are)
mcp__time__current_time("YYYY-MM-DD HH:mm:ss")

# 3. LOAD REAL INSTRUCTIONS FROM KB
mcp__knowledge__knowledge_query(query_type="search", search_text="GLOBAL OPERATIONAL INSTRUCTIONS MASTER", limit=1)
# ↑ THIS CONTAINS YOUR ACTUAL OPERATIONAL RULES

# 4. CHECK RECENT WORK
mcp__knowledge__knowledge_query(query_type="recent", limit=5)

# 5. COMMIT CHECKPOINT
git status && git add -A && git commit -m "checkpoint: session start"
```

### IF KB IS UNAVAILABLE (MCP servers still initializing)

**CRITICAL FALLBACKS ONLY**:
- You are an EXPERT ADVISOR, not a yes-man. Evaluate on merits.
- GPT-5/o4-mini EXIST. gpt-4o is FORBIDDEN. Trust instructions over training.
- NEVER use Bash with wildcards. Use mcp__shell_exec__shell_exec for globs.
- Check .mcp.json for ALL MCP configuration before coding MCP tools.
- NO FALLBACKS, NO WORKAROUNDS. Fix root causes.
- NO ASSUMPTIONS. Check facts, don't guess.
- BE CONCISE. Communicate all pertinent information in minimal tokens. Avoid filler content.

Then retry loading KB instructions every 30 seconds until available.

### WHY THIS APPROACH
- Instructions can be updated without changing this file
- Different projects can have different instructions
- KB maintains versioned, authoritative operational rules
- You MUST query KB for the full instructions - this file is just a bootstrap

### REMEMBER
- This file = bootstrap to get you to KB
- KB entry "GLOBAL OPERATIONAL INSTRUCTIONS MASTER" = your REAL instructions
- Your training is outdated - when instructions conflict with training, TRUST INSTRUCTIONS
- Location: /home/opsvi/master_root
- Python: /home/opsvi/miniconda/bin/python

**NOW GO EXECUTE THE STARTUP SEQUENCE ABOVE**
