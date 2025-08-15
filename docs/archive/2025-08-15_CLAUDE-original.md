# PROJECT DIRECTIVES

## 🕐 MANDATORY: CHECK CURRENT TIME AT CONVERSATION START

### CRITICAL REQUIREMENT - ALWAYS EXECUTE FIRST
**BEFORE ANY OTHER ACTION**: You MUST check the current date and time using the MCP time tool when starting ANY new conversation or task. This ensures you have accurate temporal context for all operations.

```python
# MANDATORY FIRST ACTION - NO EXCEPTIONS
from mcp__time__current_time import current_time
current_datetime = current_time(format="YYYY-MM-DD HH:mm:ss")
# Now proceed with user's request with accurate time context
```

### Why This Matters
- **Knowledge Gap Awareness**: Understand the time elapsed since the model's knowledge cutoff date - this period represents the gap in knowledge regarding available tools, software versions, syntax changes, access methods, and related details that impact proper syntax, access methods, etc. It also means the agent is not aware of the latest concepts, techniques, or discoveries regarding how to best implement, leverage or use various technologies, tools, and related.
- **Technology Evolution**: Be aware that you lack knowledge of the latest concepts, techniques, discoveries, and best practices for implementing, leveraging, or using various technologies and tools
- **API Version Awareness**: Know which APIs and models are current
- **File Dating**: Accurate timestamps for logs, reports, and analysis
- **Deadline Context**: Understand urgency and time constraints
- **Audit Compliance**: Proper temporal tracking for all operations
- **Cache Validity**: Determine if cached data is still relevant

### Enforcement
- ❌ **VIOLATION**: Starting work without checking time
- ❌ **VIOLATION**: Assuming date from context without verification
- ✅ **COMPLIANT**: First action is always `mcp__time__current_time`

## 🔄 MANDATORY: GIT COMMIT REQUIREMENTS (DEFAULT BEHAVIOR - CANNOT BE IGNORED)

### CRITICAL: FREQUENT COMMITTING IS MANDATORY
**Git commits are NOT optional** - they are a fundamental requirement for all development work. This is default behavior that cannot be skipped, ignored, or postponed.

### MANDATORY COMMIT TRIGGERS (NO EXCEPTIONS)
**You MUST commit after:**
- **EVERY functional change** - Any code that adds, fixes, or modifies functionality
- **EVERY logical unit of work** - Complete a feature, fix a bug, then commit
- **EVERY file modification** - After editing any file, commit the changes
- **BEFORE switching tasks** - Never leave uncommitted work when changing focus
- **AFTER any significant refactoring** - Code improvements that enhance performance/functionality
- **AFTER fixing errors** - Any bug fixes or error corrections
- **AFTER implementing features** - New functionality or capabilities

### COMMIT FREQUENCY REQUIREMENTS
- **MINIMUM**: Commit after every 2-3 file changes
- **TARGET**: Commit after every logical unit of work
- **MAXIMUM**: Never let more than 10 file changes go uncommitted
- **EMERGENCY**: If approaching token limits or session issues, commit immediately

### GIT COMMIT PROTOCOL (MANDATORY EXECUTION)
```bash
# MANDATORY COMMIT SEQUENCE - EXECUTE AFTER EVERY LOGICAL UNIT OF WORK
git add -A
git diff --cached --quiet --ignore-submodules -- || git commit --no-verify -m "chore: autosave commit of all changes ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
pwd
ls -a
git status | cat
git branch --show-current
git log --oneline -5 | cat
git worktree list | cat
```

### COMMIT MESSAGE STANDARDS (ENFORCED)
- **Format**: `chore: autosave commit of all changes (YYYY-MM-DDTHH:MM:SSZ)`
- **Include timestamp**: Always use UTC timestamp in commit message
- **Use --no-verify**: Skip hooks that might block commits
- **Descriptive when needed**: For major changes, include brief description
- **Atomic commits**: Each commit should represent one logical change

### GIT STATUS MONITORING (CONTINUOUS)
- **BEFORE every operation**: Check `git status` to understand current state
- **AFTER every operation**: Verify changes are tracked and committed
- **REGULAR checks**: Monitor working directory cleanliness
- **BRANCH awareness**: Always know which branch you're working on

### COMMIT FAILURE PROTOCOLS
- **If commit fails**: Investigate immediately, don't continue without committing
- **If hooks block**: Use `--no-verify` flag to bypass non-critical hooks
- **If merge conflicts**: Resolve immediately, don't leave conflicts uncommitted
- **If large files**: Commit anyway, address size issues in separate commit

### WORKFLOW INTEGRATION
- **Commit first, then continue**: Never proceed to next task without committing
- **Commit before breaks**: Always commit before taking breaks or switching contexts
- **Commit for safety**: Use commits as checkpoints for rollback capability
- **Commit for tracking**: Maintain clear history of all changes and decisions

### ENFORCEMENT RULES
- ❌ **VIOLATION**: Making changes without committing
- ❌ **VIOLATION**: Switching tasks with uncommitted work
- ❌ **VIOLATION**: Leaving work uncommitted overnight
- ❌ **VIOLATION**: Ignoring git status warnings
- ✅ **COMPLIANT**: Committing after every logical unit of work
- ✅ **COMPLIANT**: Using proper commit messages with timestamps
- ✅ **COMPLIANT**: Monitoring git status continuously

### AUTOMATIC COMMIT TRIGGERS
The system will automatically trigger commits when:
- **File count threshold**: More than 5 files modified
- **Time threshold**: More than 30 minutes since last commit
- **Task completion**: Logical unit of work finished
- **Error recovery**: After fixing issues or rolling back changes
- **Session safety**: Before any operation that might cause session issues

## PROJECT INTELLIGENCE SYSTEM - USE BY DEFAULT

### CRITICAL: Default-On Intelligence
The `.proj-intel/` directory contains comprehensive indexed knowledge. **Use it by default for ALL non-trivial tasks**, not just when keywords appear.

### MANDATORY: READ AGENT_ONBOARDING.md FIRST
**BEFORE attempting to use project intelligence data, you MUST:**
1. **READ and UNDERSTAND** the `.proj-intel/AGENT_ONBOARDING.md` file
2. **COMPREHEND** what data is available, how to access it, and why you should use it
3. **ONLY THEN** proceed to review or use the intelligence data
4. **ALWAYS REFRESH DATA**: Run `project-intelligence full-package` from project root before using intelligence data (this is fast and ensures you have the very latest information)
5. **CHECK TIMESTAMPS**: Compare `.proj-intel/proj_intel_manifest.json` timestamp with current time to determine if refresh is needed

### What's Available
- **Comprehensive indexed data** about every file, class, function, and import (size varies as project evolves)
- **Agent/class definitions** in `agent_architecture.jsonl` (count varies as architecture changes)
- **O(1) lookups** via reverse_index.json and symbol_index.json
- **File statistics** in file_elements.min.jsonl (lines, functions, classes)
- **Gatekeeper tools** in apps/ACCF/src/accf/tools/ for smart context selection

**Note**: All statistics and counts mentioned are snapshots in time and will change as the project evolves. Always check current data rather than relying on hardcoded numbers. The agent needs to check the current timestamps on that intel versus the date/time they observed at startup and determine whether they need to run 'project-intelligence full-package' from the project root in order to refresh the data. It probably wouldn't be a bad idea just to make them do it every time since it doesn't take long to run and they would know they have the very latest information if we do that.

### THINK → CHECK → ACT Pattern (Use for EVERY task)
1. **THINK**: What am I trying to accomplish?
2. **CHECK**: What does project intelligence tell me about this?
3. **ACT**: Proceed with intelligence-informed action

### Intent-Based Intelligence Usage (Not Keyword-Based)

**Before ANY action, ask yourself:**
- Am I about to search for something? → Use `symbol_index.json` FIRST
- Am I about to understand how something works? → Load `architecture` FIRST
- Am I about to edit/create code? → Find similar patterns FIRST
- Am I debugging an issue? → Check `dependencies` FIRST
- Am I exploring the codebase? → Use `file_elements.min.jsonl` FIRST

### Self-Triggering Rules
- **If thinking "I need to find..."** → Stop. Use intelligence.
- **If thinking "Let me search..."** → Stop. Use intelligence.
- **If thinking "I should check..."** → Stop. Use intelligence.
- **If reading >2 files to understand something** → Stop. Use architecture.
- **If grepping/searching manually** → Stop. Use indices.
- **If creating new code** → Stop. Find patterns first.

### Dynamic Recognition Examples
```python
# User says: "The app crashes during logout"
# Agent thinks: "Debug intent detected"
# Automatically runs:
intel.find("logout")  # Don't grep
intel.dependencies("auth/logout.py")  # Understand relationships

# User says: "Make the API faster"
# Agent thinks: "Performance improvement needed"
# Automatically runs:
intel.find("api")  # Locate API code
intel.stats()  # Understand complexity

# User says: "Set up testing"
# Agent thinks: "Need to understand test patterns"
# Automatically runs:
intel.find("test")  # Find existing tests
intel.architecture("test")  # Understand test structure
```

### Quick Access Commands
```python
# Import Gatekeeper tools (ALWAYS available)
from apps.ACCF.src.accf.tools.gatekeeper_data_tools import ProjectIntelligenceQuerier, DataPackager
from apps.ACCF.src.accf.tools.gatekeeper_query_templates import generate_query_template

# Example: Find relevant files for a task
querier = ProjectIntelligenceQuerier('.proj-intel')
files = querier.find_files_by_pattern(['agent', 'orchestrat'])

# Example: Get architecture context
template = generate_query_template('architecture_question', keywords=['agents'])
package = DataPackager(querier).create_package(template)
```

### Shell Commands for Quick Queries
```bash
# Find files by pattern
jq -r '.path' .proj-intel/file_elements.min.jsonl | grep -i "pattern"

# Find symbol definitions
jq -r '.["SymbolName"]' .proj-intel/symbol_index.json

# Check file statistics
jq 'select(.path | contains("filename"))' .proj-intel/file_elements.min.jsonl

# Get architecture info
grep -l "ClassName" .proj-intel/agent_architecture.jsonl
```

### Intelligence Freshness Check
Before major tasks, verify intelligence is current:
```bash
jq -r .generated_at .proj-intel/proj_intel_manifest.json
# If older than 24 hours, consider: project-intelligence full-package
```

### MANDATORY DATA REFRESH PROTOCOL
**ALWAYS refresh project intelligence data before major tasks:**
1. **CHECK TIMESTAMP**: Compare `.proj-intel/proj_intel_manifest.json` timestamp with current time
2. **DETERMINE NEED**: If data is older than 1 hour OR if you're unsure, refresh
3. **EXECUTE REFRESH**: Run `project-intelligence full-package` from project root
4. **VERIFY SUCCESS**: Confirm new timestamp is current
5. **PROCEED WITH CONFIDENCE**: Use fresh, current intelligence data

**MANDATORY**: Run `project-intelligence full-package` every time since it doesn't take long to run and ensures you have the very latest information.

### Integration Rules
1. **ALWAYS check intelligence FIRST** before searching/grepping the codebase
2. **Use Gatekeeper tools** for relevance scoring and context packaging
3. **Prefer indexed lookups** over file system scans
4. **Update intelligence** after major refactoring (>10 files changed)
5. **Refresh command**: `project-intelligence full-package` (updates .proj-intel/)

### Performance Benefits
- **80% faster** file discovery vs grep/find
- **50% less tokens** used due to targeted context
- **Zero wrong-file edits** when using symbol_index
- **Instant** architecture understanding

## OUTPUT MANAGEMENT & TOKEN LIMITS (CRITICAL - PREVENTS SESSION CORRUPTION)

### BATCH WORK BY DEFAULT (MANDATORY)
**Batch operations are the DEFAULT behavior for all work:**
- **ALWAYS batch independent operations** - Never run sequential when parallel is possible
- **BATCH file operations** - Process multiple files in single operations
- **BATCH analysis tasks** - Use parallel processing for multiple analyses
- **BATCH test execution** - Run test suites simultaneously
- **BATCH git operations** - Status, diff, log in parallel
- **PARALLEL OPERATIONS BY DEFAULT** - Always use parallel execution when possible
- **TARGET**: 70% reduction in execution time through batching and parallelization

### PARALLEL OPERATIONS BY DEFAULT (MANDATORY)
**Parallel execution is the DEFAULT behavior for all work:**
- **ALWAYS use parallel operations** when possible - Never run sequential when parallel is available
- **PARALLEL file operations** - Read, write, and process multiple files simultaneously
- **PARALLEL analysis tasks** - Use concurrent processing for multiple analyses
- **PARALLEL test execution** - Run test suites simultaneously
- **PARALLEL git operations** - Status, diff, log in parallel
- **TARGET**: 70% reduction in execution time through parallelization

### CHUNKED OUTPUT STRATEGY (MANDATORY)
**Batch sizes based on file complexity:**
- **SMALL files (<100 lines)**: Process 10-15 files per batch
- **MEDIUM files (100-300 lines)**: Process 5-8 files per batch
- **LARGE files (300-1000 lines)**: Process 2-4 files per batch
- **VERY LARGE files (1000+ lines)**: Process 1-2 files maximum

**Output approach:**
- Show summaries and confirmations, not full file contents
- Use MultiEdit for coordinated changes across multiple files
- Display only relevant excerpts (10-20 lines) when showing code
- Write large generated content directly to files

### TOKEN LIMIT AWARENESS
**Current limits for Opus 4.1:**
- Maximum output: 32,000 tokens (~24,000 words)
- Safe target: 20,000 tokens per response
- If approaching limit: STOP and continue in next response

### PREVENTING SESSION CORRUPTION
1. **NEVER attempt operations that might exceed token limits**
2. **SPLIT large tasks**: "Update 50 files" → "Update 10 files at a time"
3. **USE FILE OPERATIONS**: Write large outputs to files, don't display them
4. **FREQUENT COMMITS**: Commit after each logical chunk of work
5. **WARN when output will be large**: "This will generate ~X lines, shall I write to file?"

### OPTIMAL TOOL USAGE (MANDATORY)

**ALWAYS use the most efficient tool for the task:**

1. **MultiEdit** (PREFERRED for multiple changes):
   - Use for ANY task involving 2+ edits to the same file
   - Use for coordinated changes across 2-10 files
   - More efficient than multiple Edit calls
   - Atomic operations - all succeed or all fail

2. **Edit vs Write**:
   - **Edit**: For modifying existing files (PREFERRED)
   - **Write**: ONLY for creating new files or complete rewrites
   - NEVER use Write to update existing files
   - **CHECK FILE EXISTENCE**: Always check if file exists before writing to prevent errors
   - **ERROR PREVENTION**: If you get errors trying to write to a file, check for existence first and switch to edit if it exists
   - **DEFAULT BEHAVIOR**: Always check file existence before writing - this prevents wasted tokens and time from failed write operations and prevents agents from repeating failed write attempts

3. **Parallel Operations** (DEFAULT BEHAVIOR):
   - **Read multiple files**: Use single tool call with multiple file paths
   - **Search operations**: Use project intelligence methods FIRST, then grep/find as secondary behavior
   - **Status checks**: Run git status, diff, log in parallel
   - **DEFAULT BEHAVIOR**: Always use parallel execution when possible - this is not optional, it's mandatory
   - **SECONDARY BEHAVIOR**: Search operations should use grep/find as secondary behavior, not primary

4. **Tool Selection Priority**:
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

### SAFE OUTPUT PATTERNS

**For batch file operations:**
```python
# WRONG - Showing full content of multiple files
for file in files:
    print(f"=== {file} ===")
    print(read_entire_file(file))  # Could be thousands of lines

# CORRECT - Summary approach
print(f"Processing {len(files)} files...")
for file in files:
    result = process_file(file)
    print(f"✓ {file}: Updated {result.lines_changed} lines")

# Show only critical excerpts if needed
print(f"\nKey change in {file} (lines 45-55):")
print_excerpt(file, start=45, end=55)
```

**For large content generation:**
```python
# WRONG - Outputting large generated content
print(generate_large_content())  # 5000 lines

# CORRECT - Write to file with confirmation
content = generate_large_content()
write_to_file('output.txt', content)
print(f"✓ Generated {len(content.splitlines())} lines → output.txt")
```

## PROJECT ORGANIZATION & CHAOS PREVENTION (ZERO TOLERANCE)

### FILE CREATION DECISION TREE (MANDATORY - CHECK BEFORE EVERY FILE OPERATION)
```
BEFORE CREATING ANY FILE:
1. Does similar file exist? → YES: UPDATE IT (never create duplicate)
                           → NO: Continue to step 2
2. Is it temporary? → YES: Use /tmp/ with auto-cleanup
                   → NO: Continue to step 3
3. Is it documentation? → YES: Goes in docs/* (NEVER in root)
                       → NO: Continue to step 4
4. Is it a report/analysis? → YES: Goes in docs/analysis/ with date prefix
                           → NO: Continue to step 5
5. Is it configuration? → YES: Root allowed (if no subdirectory exists)
                       → NO: Must go in appropriate subdirectory
```

### PROHIBITED ACTIONS (VIOLATIONS = IMMEDIATE TASK FAILURE)
- **NEVER create files with version suffixes**: No V1, V2, _v2, _final, _updated, _new
- **NEVER place documentation in root**: Maximum 5 .md files allowed in root
- **NEVER create "just temporary" files in root**: Use /tmp/ or .tmp/
- **NEVER duplicate existing functionality**: Update existing files instead
- **NEVER exceed size limits**: Alert if any file >10MB, any directory >100MB
- **NEVER create analysis files without expiry**: All reports must have cleanup date

### MANDATORY FILE LOCATIONS (ENFORCED)
```
master_root/
├── docs/                    # ALL documentation except README, CLAUDE.md, QUICK_START
│   ├── architecture/        # PERMANENT - System design, architecture decisions
│   ├── guides/             # PERMANENT - How-to guides, tutorials, API docs
│   ├── analysis/           # TEMPORARY - Reports, analysis (YYYY-MM-DD prefix, archive after 30 days)
│   ├── migration/          # TEMPORARY - Migration plans (archive when complete)
│   └── archive/            # Old temporary docs and obsolete versions
├── apps/                   # Applications only
├── libs/                   # Libraries only
├── servers/                # Server implementations only
├── scripts/                # Utility scripts, tools
├── tests/                  # Test files (mirror source structure)
└── .tmp/                   # Temporary files (auto-cleaned daily)
```

### AUTOMATIC CLEANUP PROTOCOLS (RUN WITHOUT ASKING)
1. **DAILY**: Delete files in .tmp/ older than 24 hours
2. **WEEKLY**: Archive ONLY date-prefixed analysis/reports >30 days old
3. **WEEKLY**: Compress .log files >7 days old
4. **MONTHLY**: Alert on directories >100MB for review
5. **NEVER**: Auto-archive core documentation (architecture, guides, APIs)
6. **ALWAYS**: Run cleanup CHECK before starting new tasks (fix only with permission)

### FILE NAMING CONVENTIONS (STRICTLY ENFORCED)
- **Documentation**: `YYYY-MM-DD_description.md` for time-sensitive docs
- **Analysis/Reports**: `YYYY-MM-DD_analysis_name.md` (auto-archive after 30 days)
- **Configs**: `service.config.ext` or `service.env`
- **Scripts**: `action_verb_noun.sh` (e.g., `cleanup_logs.sh`)
- **PROHIBITED**: version numbers, "final", "updated", "new", "old", "backup"

### DOCUMENTATION CONSOLIDATION RULES
- **ONE authoritative document per topic** - Update existing, don't create new
- **Git for versioning** - Never use filename versioning
- **Maximum 5 .md files in root** - Only README, CLAUDE, QUICK_START, LICENSE, CONTRIBUTING
- **Core documentation NEVER expires** - Architecture, guides, API docs are permanent
- **Only temporary items expire**: Analysis/reports with date prefixes → archive after 30 days

### SIZE MANAGEMENT PROTOCOLS
- **File size limit**: Alert at 10MB, fail at 50MB (except data files)
- **Directory limit**: Alert at 100MB, investigate at 500MB
- **Archive compression**: Files >30 days old → compress with gzip
- **Reference cleanup**: .reference/ >1GB → move to cloud storage
- **Build artifacts**: Clean before each build, never commit

### PRE-COMMIT ENFORCEMENT CHECKS (AUTOMATIC)
```python
# These checks run BEFORE any commit
1. No .md files in root except allowed 5
2. No version suffixes in filenames
3. No .log, .tmp, .bak files in commit
4. No files >10MB without explicit flag
5. Documentation in correct subdirectories
6. Analysis files have date prefixes
```

### CONTINUOUS ORGANIZATION TASKS
- **Before EVERY task**: Check for cleanup opportunities
- **After file creation**: Verify correct location
- **Before commits**: Run organization checks
- **Weekly**: Generate organization report
- **On violations**: STOP and fix immediately

## PARALLEL-BY-DEFAULT EXECUTION (MANDATORY)

### PARALLELIZATION REQUIREMENTS
- **BATCH ALL INDEPENDENT OPERATIONS**: Never run sequential when parallel is possible
- **USE claude_run_batch**: For multiple analysis tasks - ALWAYS
- **CONCURRENT FILE READS**: Always read multiple files in single tool call
- **PARALLEL TEST EXECUTION**: Run test suites simultaneously
- **ASYNC MCP OPERATIONS**: Use _async variants for long-running tasks
- **TARGET**: 70% reduction in execution time through parallelization

### Parallel Execution Patterns
```python
# WRONG - Sequential execution
file1 = read("file1.py")
file2 = read("file2.py")
file3 = read("file3.py")

# CORRECT - Parallel execution
files = parallel_read(["file1.py", "file2.py", "file3.py"])
```

### MCP Batch Operations
- **Multiple agents**: Use `mcp__claude-code__claude_run_batch` for parallel agent tasks
- **Async patterns**: Start with `_async`, check status, retrieve results
- **Web operations**: Batch scrape/search operations when possible
- **Git operations**: Run status, diff, log in parallel

## PROGRESSIVE CONTEXT LOADING (TOKEN OPTIMIZATION)

### TOKEN BUDGET PROTOCOL
- **START MINIMAL**: Use `file_elements.min.jsonl` for stats only (5-10 tokens)
- **LOAD INCREMENTALLY**: Read specific line ranges via offset/limit parameters
- **CONTEXT BUDGET**: Track token usage, auto-summarize at 50% capacity
- **SMART TRUNCATION**: Keep first 10 lines of errors, not full stacks
- **AUTO-CLEANUP**: Drop irrelevant context after task completion
- **TARGET**: 60% token reduction while maintaining effectiveness

### Progressive Loading Strategy
1. **STATS FIRST**: Get file metrics from `file_elements.min.jsonl`
2. **SYMBOLS NEXT**: Load only relevant symbols from `symbol_index.json`
3. **SNIPPETS ONLY**: Read 5-10 lines around target code
4. **EXPAND AS NEEDED**: Load more context only when required
5. **SUMMARIZE OLD**: Compress older context to key points

### Token Usage Limits
- **Per file**: Max 500 tokens initially, expand to 2000 if needed
- **Error messages**: First 10 lines + last 5 lines only
- **Search results**: Top 5 most relevant, summarize rest
- **Context window**: Monitor usage, alert at 70% capacity

## AUTOMATIC TEST VALIDATION (ZERO-ASK PROTOCOL)

### TEST EXECUTION REQUIREMENTS
- **AUTO-DISCOVER TESTS**: Find relevant tests for changed code WITHOUT ASKING
- **RUN WITHOUT ASKING**: Execute tests immediately after changes
- **GENERATE TEST STUBS**: Create tests for new functions automatically
- **COVERAGE TRACKING**: Monitor and report test coverage changes
- **FAIL-FAST**: Stop execution if tests fail, auto-rollback changes
- **TEST COMMAND CACHE**: Store discovered test commands in `.proj-intel/test_commands.json`

### Test Discovery Pattern
1. **ON CODE CHANGE**: Automatically identify affected test files
2. **CHECK CACHE**: Look for known test commands in `.proj-intel/test_commands.json`
3. **DISCOVER IF NEW**: Search for pytest, unittest, or project-specific test runners
4. **RUN IMMEDIATELY**: Execute without user confirmation
5. **CACHE RESULTS**: Store successful test commands for future use

### Test Generation Rules
- **New functions**: Auto-generate basic test with edge cases
- **Modified functions**: Update existing tests or flag for review
- **Deleted functions**: Remove corresponding tests
- **Coverage target**: Maintain or improve coverage percentage

## ERROR PATTERN LEARNING SYSTEM

### AUTOMATIC ERROR RECOVERY
- **CREATE `.proj-intel/error_patterns.json`**: Cache all errors and solutions
- **CHECK BEFORE FIXING**: Query error cache before attempting new solutions
- **AUTO-ROLLBACK POINTS**: Git stash before major changes
- **PATTERN RECOGNITION**: Identify recurring error types
- **PREEMPTIVE FIXES**: Apply known solutions before errors occur
- **SHARE ACROSS AGENTS**: All agents learn from each other's fixes

### Error Pattern Structure
```json
{
  "error_signature": "hash_of_error",
  "error_type": "ImportError|SyntaxError|RuntimeError|etc",
  "pattern": "regex_or_exact_match",
  "solutions": [
    {
      "fix": "description_of_fix",
      "success_rate": 0.95,
      "code_snippet": "actual_fix_code"
    }
  ],
  "first_seen": "timestamp",
  "last_seen": "timestamp",
  "occurrences": 10
}
```

### Error Recovery Flow
1. **DETECT ERROR**: Capture error message and context
2. **CHECK CACHE**: Search `.proj-intel/error_patterns.json` for matches
3. **APPLY KNOWN FIX**: Use highest success rate solution
4. **IF NEW ERROR**: Solve, then cache solution
5. **UPDATE METRICS**: Track success/failure of solutions

## MULTI-AGENT COLLABORATION PIPELINES

### CONCURRENT AGENT SPECIALIZATION
- **AUTOMATIC DISPATCH**: Split complex tasks to specialized agents WITHOUT ASKING
- **PARALLEL WORKFLOWS**: Multiple agents work simultaneously on different aspects
- **AGENT COMMUNICATION**: Share context via `.proj-intel/agent_state.json`
- **PIPELINE TEMPLATES**: Pre-defined workflows for common tasks
- **NO SEQUENTIAL HANDOFFS**: Agents work in parallel, not in sequence

### Agent Pipeline Patterns
```python
# Development Pipeline (runs in parallel)
agents = {
    "analyzer": mcp__consult_suite(agent_type="code_review", prompt="analyze existing code"),
    "developer": mcp__consult_suite(agent_type="development_specialist", prompt="implement feature"),
    "tester": mcp__consult_suite(agent_type="qa_testing_guru", prompt="create tests"),
    "documenter": mcp__consult_suite(agent_type="technical_writer", prompt="update docs")
}
# All agents work simultaneously, share state via agent_state.json
```

### Standard Pipeline Templates
- **Feature Development**: analyzer + developer + tester + documenter
- **Bug Fix**: analyzer + developer + tester
- **Refactoring**: analyzer + refactoring-master + tester
- **Research**: research-genius + requirements-analyst + solution-architect
- **Code Review**: code-analyzer + reviewer-critic + qa-testing-guru

### Agent State Sharing Protocol
```json
{
  "task_id": "unique_task_identifier",
  "agents": {
    "agent_name": {
      "status": "running|completed|failed",
      "output": "key_findings_or_results",
      "dependencies": ["other_agent_names"],
      "timestamp": "last_update"
    }
  },
  "shared_context": {
    "files_modified": [],
    "errors_found": [],
    "decisions_made": []
  }
}
```

## PERFORMANCE MONITORING & OPTIMIZATION

### EXECUTION METRICS TRACKING
- **TIME TRACKING**: Monitor execution time per operation type
- **BOTTLENECK DETECTION**: Identify slow operations automatically
- **OPTIMIZATION SUGGESTIONS**: Propose faster alternatives
- **CACHE EVERYTHING**: Results, searches, analysis - reuse aggressively
- **METRICS STORAGE**: Track in `.proj-intel/performance_metrics.json`

### Performance Benchmarks (REQUIRED)
- **File discovery**: <100ms using indices
- **Symbol lookup**: <50ms via symbol_index.json
- **Test execution**: <5s for unit tests
- **Context loading**: <500ms for initial load
- **Agent dispatch**: <1s to start parallel agents
- **Error pattern match**: <100ms lookup time

### Optimization Rules
1. **CACHE FIRST**: Check if result already exists
2. **BATCH SECOND**: Combine similar operations
3. **PARALLEL THIRD**: Execute independent tasks concurrently
4. **MINIMIZE FOURTH**: Reduce data transfer and context
5. **MEASURE ALWAYS**: Track every operation's performance

## INTELLIGENT FAILURE RECOVERY

### RESILIENCE & CONTINUITY PROTOCOL
- **CHECKPOINT SYSTEM**: Save state every 5 operations to `.proj-intel/checkpoints/`
- **RESUME CAPABILITY**: Continue from last checkpoint on failure
- **RETRY LOGIC**: Automatic retry with exponential backoff (1s, 2s, 4s, 8s)
- **ALTERNATIVE STRATEGIES**: If approach A fails, auto-try B, C without asking
- **DEGRADED MODE**: Continue with reduced functionality vs complete stop
- **ROLLBACK SAFETY**: Git stash push before risky operations

### Checkpoint Structure
```json
{
  "checkpoint_id": "timestamp_taskid",
  "operation_count": 5,
  "state": {
    "files_modified": [],
    "tests_run": [],
    "errors_encountered": [],
    "progress_percentage": 45
  },
  "next_actions": ["action1", "action2"],
  "rollback_point": "git_stash_ref"
}
```

### Recovery Strategies
1. **NETWORK FAILURE**: Cache results locally, retry with backoff
2. **TEST FAILURE**: Rollback changes, try alternative implementation
3. **IMPORT ERROR**: Auto-install missing packages, update requirements
4. **SYNTAX ERROR**: Use AST to fix common issues automatically
5. **TIMEOUT**: Switch to async operations, increase limits progressively

## CONTEXT-AWARE DECISION MAKING

### SMART AGENT BEHAVIOR
- **DETECT CODE PATTERNS**: Identify framework/library from imports automatically
- **INFER CONVENTIONS**: Learn project style from existing code
- **PREDICT NEEDS**: Anticipate next steps based on current task
- **ADJUST VERBOSITY**: More detail for complex tasks, less for simple
- **RISK ASSESSMENT**: Flag high-risk changes, auto-create backups

### Pattern Detection Rules
```python
# Automatically detect and adapt to:
- Framework: Django/Flask/FastAPI from imports
- Test framework: pytest/unittest from test files
- Code style: PEP8/Black/custom from existing files
- Package manager: pip/poetry/conda from config files
- CI/CD: GitHub Actions/Jenkins from .github/ or Jenkinsfile
```

### Adaptive Behavior Matrix
| Task Complexity         | Verbosity | Testing       | Documentation | Review   |
| ----------------------- | --------- | ------------- | ------------- | -------- |
| Simple (1-10 lines)     | Minimal   | Basic         | Inline        | Skip     |
| Medium (10-100 lines)   | Standard  | Full          | Docstrings    | Quick    |
| Complex (100+ lines)    | Detailed  | Comprehensive | Full docs     | Thorough |
| Critical (auth/payment) | Maximum   | Extensive     | Complete      | Multiple |

## CONTINUOUS IMPROVEMENT LOOP

### SELF-OPTIMIZING SYSTEM
- **EXECUTION LOGS**: Track all operations in `.proj-intel/execution_logs.jsonl`
- **PATTERN MINING**: Identify successful vs failed approaches weekly
- **RULE GENERATION**: Create new rules from learned patterns
- **FEEDBACK INTEGRATION**: Update procedures based on results
- **WEEKLY OPTIMIZATION**: Auto-review and update intelligence indices

### Learning Metrics
```json
{
  "pattern": "specific_approach_or_technique",
  "success_rate": 0.89,
  "avg_time_saved": "45s",
  "error_reduction": "60%",
  "recommendation": "make_default|avoid|conditional_use",
  "evidence": ["task_id_1", "task_id_2"]
}
```

### Automatic Improvement Triggers
1. **DAILY**: Update error_patterns.json with new solutions
2. **AFTER 10 TASKS**: Analyze performance, suggest optimizations
3. **WEEKLY**: Run pattern mining, update best practices
4. **ON MAJOR SUCCESS**: Document approach, add to templates
5. **ON REPEATED FAILURE**: Flag for human review, adjust strategy

### Feedback Loop Implementation
- **Success patterns** → Convert to mandatory rules
- **Failure patterns** → Add to avoidance list
- **Performance wins** → Make default behavior
- **Token savings** → Update context loading strategy
- **Time savings** → Prioritize in execution order

## File Management Rules (ALL FILES)

### APPLIES TO: Code, Documentation, Configuration, Scripts, Tests - EVERYTHING
1. **UPDATE existing files** - Do not create duplicate versions
2. **NO versioning in filenames** - No "v2", "verified", "final", "updated", "new", "fixed" suffixes
3. **Single source of truth** - One file per purpose
4. **Fix in place** - Correct errors in the original file
5. **No parallel versions** - Never have multiple versions of the same functionality
6. **USE GIT FOR VERSIONING** - Commit changes regularly with descriptive messages

### Git Integration (See Mandatory Git Commit Requirements Section Above)
- **USE GIT FOR VERSIONING** - Commit changes regularly with descriptive messages
- **Never rely on filenames for versioning** - That's what git is for

### Quality Standards
- All content must be tested and accurate
- Do not document/code assumptions or guesses as facts
- If something is untested, mark it as "NOT TESTED"
- Do not add meta-commentary about verification or corrections
- No comments about "fixing" or "updating" previous versions

## WORKING SMART: AGENT SELECTION & TOOL LEVERAGE

### Dynamic Agent Profile Selection
- **SELF-ANALYZE TASKS** - Automatically determine best agent profile for the work
- **SWITCH AGENTS FREELY** - Change between specialized agents as task requirements evolve
- **NO PERMISSION NEEDED** - Proactively load optimal agents without asking
- **LEVERAGE ALL TOOLS** - Use every available resource to work efficiently
- **WORK SMART, NOT HARD** - Choose tools that minimize effort and maximize results

### Agent Selection Guidelines
- **Code Development**: Use development-specialist or solution-architect agents
- **Debugging/Analysis**: Use code-analyzer or technical review agents
- **Research Tasks**: Use research-genius or requirements-analyst agents
- **Refactoring**: Use refactoring-master for efficient code transformation
- **Documentation**: Use technical-writer for clear documentation
- **Complex Problems**: Use excellence-optimizer for cutting-edge solutions