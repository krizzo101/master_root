# CLAUDE.md - Bootstrap Instructions

## **DO NOT LIE. AT ALL.**

## CRITICAL: Your REAL instructions are in the Knowledge Base

### MANDATORY STARTUP (EVERY SESSION, NO EXCEPTIONS)
```python
# 1. CHECK TIME (to understand how outdated you are)
mcp__time__current_time("YYYY-MM-DD HH:mm:ss")

# 2. STATE KNOWLEDGE CUTOFF AWARENESS
# Tell the agent to state:
# "Today is ____________ (today's date). It has been XXXX days since my knowledge cutoff occurred.
# That means what I think I know about the latest versions, capabilities, discoveries, best practices,
# and other time sensitive topics is ________ and I need to _________." (Fill in the blanks)

# 3. LOAD REAL INSTRUCTIONS FROM KB
mcp__knowledge__knowledge_query(query_type="search", search_text="GLOBAL OPERATIONAL INSTRUCTIONS MASTER", limit=1)
# ↑ THIS CONTAINS YOUR ACTUAL OPERATIONAL RULES

# 4. CHECK RECENT WORK
mcp__knowledge__knowledge_query(query_type="recent", limit=5)

# 5. UNDERSTAND PROJECT CONTEXT
# Read .claude/knowledge/docs/COMPREHENSIVE_PROJECT_CONTEXT.md - WHY you're working on this
# Read .claude/knowledge/docs/CRITICAL_FILE_ORGANIZATION_SAFEGUARDS.md - FILE RULES (NON-NEGOTIABLE)
# Read .claude/knowledge/docs/session_reference.md - WHAT works right now

# 6. OPTIONAL: Update workspace intelligence (only if needed)
# python3 .claude/knowledge/scripts/env_profiler.py
```

### IF KB IS UNAVAILABLE (MCP servers still initializing)

**CRITICAL FALLBACKS ONLY**:
- You are an EXPERT ADVISOR, not a yes-man. Evaluate on merits.
- 🚨 NEVER WRITE FILES TO PROJECT ROOT - Use `.claude/knowledge/` for agent files
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

# CLAUDE KNOWLEDGE WORKSPACE

## What It Is
`.claude/knowledge/` is YOUR personal workspace - separate from project deliverables. It contains your operational intelligence, reference materials, and tools for maintaining context across sessions.

**Key Distinction:**
- `.claude/knowledge/` = YOUR private workspace (not for humans)
- Project docs = Human-facing deliverables (goes WITH the project)

## How to Use It

### Daily Startup
The startup sequence automatically:
1. Runs `env_profiler.py` to capture current environment state
2. Updates `session_reference.md` with what actually works
3. Loads recent knowledge from KB for context

### During Work
- Store learnings and patterns in appropriate subdirectories
- Reference `session_reference.md` when unsure what works
- Use KB tools to persist insights across sessions

### Key Files Created
- `docs/environment_profile.json` - Current system state (auto-generated)
- `docs/session_reference.md` - Daily workflow guidance
- `scripts/env_profiler.py` - Environment data collection tool

# FILE ORGANIZATION RULES

## Claude Knowledge Space Structure
**MANDATORY**: All Claude-generated documentation, guides, and analysis files MUST go in `.claude/knowledge/` subdirectories.

### Directory Structure:
- `.claude/knowledge/docs/` - Project documentation and state files
- `.claude/knowledge/guides/` - How-to guides and comprehensive documentation
- `.claude/knowledge/architecture/` - System design, architecture docs
- `.claude/knowledge/workflows/` - Process documentation and workflows
- `.claude/knowledge/templates/` - Reusable templates and patterns
- `.claude/knowledge/analysis/` - Analysis reports and findings

### Rules:
1. **NEVER create documentation files in project root** - Always use `.claude/knowledge/`
2. **Choose appropriate subdirectory** based on content type
3. **Use descriptive filenames** with prefixes: `claude_`, `analysis_`, `guide_`, etc.
4. **Store KB entries** for persistent knowledge using `mcp__knowledge__knowledge_store`
5. **Reference location** in KB entries for easy retrieval
