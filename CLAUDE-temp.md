# CLAUDE AGENT DIRECTIVES

## 🕐 MANDATORY FIRST ACTION: CHECK CURRENT TIME

### CRITICAL REQUIREMENT - ALWAYS EXECUTE FIRST
**BEFORE ANY OTHER ACTION**: You MUST check the current date and time using the MCP time tool when starting ANY new conversation or task.

```python
# MANDATORY FIRST ACTION - NO EXCEPTIONS
from mcp__time__current_time import current_time
current_datetime = current_time(format="YYYY-MM-DD HH:mm:ss")
# Now proceed with user's request with accurate time context
```

### Why This Matters
- **Knowledge Gap Awareness**: Understand the time elapsed since the model's knowledge cutoff date - this period represents the gap in knowledge regarding available tools, software versions, syntax changes, access methods, and related details. It also means you lack knowledge of the latest concepts, techniques, or discoveries regarding how to best implement, leverage, or use various technologies and tools.
- **Technology Evolution**: Be aware that you lack current knowledge of best practices, new APIs, framework updates, and security patches
- **API Version Awareness**: Know which APIs and models are current vs deprecated
- **File Dating**: Accurate timestamps for logs, reports, and analysis
- **Audit Compliance**: Proper temporal tracking for all operations

### MANDATORY: USE MCP TOOLS TO BRIDGE KNOWLEDGE GAPS
**When you identify a knowledge gap, you MUST use the available MCP tools to get current information:**

#### Research & Information Gathering
- **`mcp_web_search`** (Brave Search): Search for current API versions, documentation, best practices
- **`tech_docs`** (Context7): Get up-to-date technical documentation for libraries and frameworks
- **`research_papers`** (ArXiv): Find latest research papers on technologies and methodologies
- **`firecrawl`**: Extract current content from specific websites, documentation sites, GitHub repos

#### When to Use These Tools
```python
# BEFORE making any technical decisions, research current state:

# 1. Check API versions and syntax changes
mcp_web_search(query="OpenAI API latest version 2025 changes")
mcp_tech_docs(context7CompatibleLibraryID="/openai/openai-python")

# 2. Research best practices for frameworks
mcp_web_search(query="FastAPI latest best practices 2025 security")
mcp_firecrawl_scrape(url="https://fastapi.tiangolo.com/")

# 3. Find current solutions to common problems
mcp_web_search(query="Python async database connection pooling 2025")
mcp_research_papers(query="microservices architecture patterns")

# 4. Verify library compatibility and versions
mcp_web_search(query="pydantic v2 vs v1 migration guide 2025")
```

#### Available MCP Tools for Knowledge Updates

| Tool | Purpose | When to Use | Example Queries |
|------|---------|-------------|-----------------|
| **`mcp_web_search`** | Brave Search API | Current versions, breaking changes, new features | "Python 3.12 new features", "Docker latest security best practices 2025" |
| **`tech_docs`** | Context7 docs | Library documentation, API references | "/fastapi/fastapi", "/openai/openai-python" |
| **`research_papers`** | ArXiv papers | Latest research, methodologies, algorithms | "transformer architecture improvements", "microservices patterns" |
| **`firecrawl`** | Web scraping | Official docs, changelogs, GitHub releases | "https://docs.python.org/3/whatsnew/", "https://github.com/openai/openai-python/releases" |
| **`consult_suite_enhanced`** | Expert AI agents | Complex architecture decisions, code reviews | Complex system design, production-ready implementations |

#### MANDATORY Research Protocol
**BEFORE making technical decisions, you MUST:**
1. **Search for current information** using `mcp_web_search`
2. **Verify with official documentation** using `tech_docs` or `firecrawl`
3. **Check for recent changes** in APIs, libraries, best practices
4. **Research latest methodologies** if implementing new patterns
5. **Only THEN proceed** with informed implementation

### Enforcement
- ❌ **VIOLATION**: Starting work without checking time
- ❌ **VIOLATION**: Making technical decisions without researching current state
- ❌ **VIOLATION**: Using outdated information from training data
- ✅ **COMPLIANT**: First action is always `mcp__time__current_time`
- ✅ **COMPLIANT**: Research current information before implementation

## 🔄 MANDATORY: GIT COMMITS (DEFAULT BEHAVIOR - CANNOT BE IGNORED)

### CRITICAL: FREQUENT COMMITTING IS MANDATORY
Git commits are NOT optional - they are fundamental requirements for all development work. This is default behavior that cannot be skipped, ignored, or postponed.

### MANDATORY COMMIT TRIGGERS (NO EXCEPTIONS)
**You MUST commit after:**
- **EVERY functional change** - Any code that adds, fixes, or modifies functionality
- **EVERY logical unit of work** - Complete a feature, fix a bug, then commit
- **EVERY 2-3 file modifications** - Never let more than 3 files go uncommitted
- **BEFORE switching tasks** - Never leave uncommitted work when changing focus
- **AFTER any significant refactoring** - Code improvements that enhance performance/functionality

### GIT COMMIT PROTOCOL (MANDATORY EXECUTION)
```bash
# MANDATORY COMMIT SEQUENCE - EXECUTE AFTER EVERY LOGICAL UNIT OF WORK
git add -A
git diff --cached --quiet --ignore-submodules -- || git commit --no-verify -m "chore: autosave commit of all changes ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
git status | cat
```

### ENFORCEMENT RULES
- ❌ **VIOLATION**: Making changes without committing
- ❌ **VIOLATION**: Switching tasks with uncommitted work
- ✅ **COMPLIANT**: Committing after every logical unit of work

## 📊 PROJECT INTELLIGENCE (USE BY DEFAULT)

### MANDATORY: READ AGENT_ONBOARDING.md FIRST
**BEFORE attempting to use project intelligence data, you MUST:**
1. **READ and UNDERSTAND** the `.proj-intel/AGENT_ONBOARDING.md` file
2. **COMPREHEND** what data is available, how to access it, and why you should use it
3. **ONLY THEN** proceed to review or use the intelligence data

### MANDATORY DATA REFRESH PROTOCOL
**ALWAYS refresh project intelligence data before major tasks:**
1. **CHECK TIMESTAMP**: Compare `.proj-intel/proj_intel_manifest.json` timestamp with current time
2. **EXECUTE REFRESH**: Run `project-intelligence full-package` from project root (recommended every time since it's fast and ensures current data)
3. **VERIFY SUCCESS**: Confirm new timestamp is current

### What's Available
- **Comprehensive indexed data** about every file, class, function, and import (size varies as project evolves)
- **Agent/class definitions** in `agent_architecture.jsonl` (count varies as architecture changes)
- **O(1) lookups** via reverse_index.json and symbol_index.json
- **File statistics** in file_elements.min.jsonl (lines, functions, classes)
- **Gatekeeper tools** in apps/ACCF/src/accf/tools/ for smart context selection

**Note**: All statistics and counts are snapshots in time and change as the project evolves. Always check current data rather than relying on hardcoded numbers.

### Usage Pattern
1. **THINK**: What am I trying to accomplish?
2. **CHECK**: What does project intelligence tell me about this?
3. **ACT**: Proceed with intelligence-informed action

### Quick Access Commands
```bash
# Find files by pattern
jq -r '.path' .proj-intel/file_elements.min.jsonl | grep -i "pattern"

# Check file statistics
jq 'select(.path | contains("filename"))' .proj-intel/file_elements.min.jsonl

# Get freshness info
jq -r .generated_at .proj-intel/proj_intel_manifest.json
```

## 📝 FILE OPERATIONS (CRITICAL ERROR PREVENTION)

### MANDATORY: CHECK FILE EXISTENCE BEFORE WRITING
**ALWAYS check if file exists before writing to prevent errors:**
- **Edit**: For modifying existing files (PREFERRED)
- **Write**: ONLY for creating new files or complete rewrites
- **ERROR PREVENTION**: If you get errors trying to write to a file, check for existence first and switch to edit if it exists
- **DEFAULT BEHAVIOR**: Always check file existence before writing - this prevents wasted tokens and time from failed write operations

### File Management Rules
1. **UPDATE existing files** - Do not create duplicate versions
2. **NO versioning in filenames** - No "v2", "verified", "final", "updated", "new", "fixed" suffixes
3. **Single source of truth** - One file per purpose
4. **USE GIT FOR VERSIONING** - Commit changes regularly with descriptive messages

## ⚡ BATCH & PARALLEL BY DEFAULT (MANDATORY)

### BATCH OPERATIONS ARE DEFAULT BEHAVIOR
**Batch operations are the DEFAULT behavior for all work:**
- **ALWAYS batch independent operations** - Never run sequential when parallel is possible
- **BATCH file operations** - Process multiple files in single operations
- **BATCH analysis tasks** - Use parallel processing for multiple analyses
- **BATCH test execution** - Run test suites simultaneously
- **BATCH git operations** - Status, diff, log in parallel

### PARALLEL OPERATIONS (MANDATORY DEFAULT)
**Parallel execution is the DEFAULT behavior:**
- **Read multiple files**: Use single tool call with multiple file paths
- **Search operations**: Use project intelligence methods FIRST, then grep/find as secondary behavior
- **Status checks**: Run git status, diff, log in parallel
- **DEFAULT BEHAVIOR**: Always use parallel execution when possible - this is mandatory, not optional

### Tool Selection Priority
```
For file changes:
1st choice: MultiEdit (for multiple edits)
2nd choice: Edit (for single edit)
Last resort: Write (only for new files)

For searching:
1st choice: Project intelligence indices
2nd choice: Grep with specific paths
Last resort: Find with full scan
```

## 📋 OUTPUT MANAGEMENT & TOKEN LIMITS

### CHUNKED OUTPUT STRATEGY (MANDATORY)
**Batch sizes based on file complexity:**
- **SMALL files (<100 lines)**: Process 10-15 files per batch
- **MEDIUM files (100-300 lines)**: Process 5-8 files per batch
- **LARGE files (300-1000 lines)**: Process 2-4 files per batch
- **VERY LARGE files (1000+ lines)**: Process 1-2 files maximum

### TOKEN LIMIT AWARENESS
- **Maximum output**: 32,000 tokens (~24,000 words)
- **Safe target**: 20,000 tokens per response
- **If approaching limit**: STOP and continue in next response

### SAFE OUTPUT PATTERNS
- Show summaries and confirmations, not full file contents
- Use MultiEdit for coordinated changes across multiple files
- Display only relevant excerpts (10-20 lines) when showing code
- Write large generated content directly to files

## 🗂️ ORGANIZATION RULES (ZERO TOLERANCE FOR CHAOS)

### FILE CREATION DECISION TREE
```
BEFORE CREATING ANY FILE:
1. Does similar file exist? → YES: UPDATE IT (never create duplicate)
2. Is it documentation? → YES: Goes in docs/* (NEVER in root)
3. Is it temporary? → YES: Use /tmp/ with auto-cleanup
4. Must go in appropriate subdirectory
```

### PROHIBITED ACTIONS
- **NEVER create files with version suffixes**: No V1, V2, _v2, _final, _updated, _new
- **NEVER place documentation in root**: Maximum 5 .md files allowed in root
- **NEVER create "just temporary" files in root**: Use /tmp/ or .tmp/

### MANDATORY FILE LOCATIONS
```
master_root/
├── docs/                    # ALL documentation except README, CLAUDE.md, QUICK_START
│   ├── architecture/        # System design, architecture decisions
│   ├── guides/             # How-to guides, tutorials, API docs
│   └── analysis/           # Reports with YYYY-MM-DD prefix, archive after 30 days
├── apps/                   # Applications only
├── scripts/                # Utility scripts, tools
└── .tmp/                   # Temporary files (auto-cleaned daily)
```

## 📊 QUICK REFERENCE

### Essential Commands
```bash
# Time check (FIRST ACTION)
mcp__time__current_time(format="YYYY-MM-DD HH:mm:ss")

# Research current information (BEFORE TECHNICAL DECISIONS)
mcp_web_search(query="technology latest version 2025")
mcp_tech_docs(context7CompatibleLibraryID="/library/name")

# Commit workflow (AFTER EVERY CHANGE)
git add -A && git commit --no-verify -m "chore: autosave ($(date -u +%Y-%m-%dT%H:%M:%SZ))"

# Intelligence refresh (BEFORE MAJOR TASKS)
project-intelligence full-package

# File existence check (BEFORE WRITING)
ls -la target_file.ext || echo "File does not exist, safe to write"
```

### Tool Priority
1. **Time Check** → MANDATORY first action every session
2. **Research Tools** → MANDATORY before technical decisions (web_search, tech_docs, firecrawl)
3. **Project Intelligence** → Fast, indexed, accurate for existing codebase
4. **MultiEdit** → Efficient for multiple changes
5. **Parallel Operations** → Always when possible
6. **Batch Processing** → Default behavior for all work

---

**REMEMBER**: These are not suggestions - they are mandatory requirements. Compliance is not optional.

**Detailed documentation moved to:**
- Error patterns: `docs/architecture/error_patterns.md`
- Agent collaboration: `docs/architecture/agent_collaboration.md`
- Performance monitoring: `docs/architecture/performance_tracking.md`
- Advanced behaviors: `docs/guides/agent_behavior.md`
