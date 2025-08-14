# PROJECT DIRECTIVES

## File Management Rules (ALL FILES)

### APPLIES TO: Code, Documentation, Configuration, Scripts, Tests - EVERYTHING
1. **UPDATE existing files** - Do not create duplicate versions
2. **NO versioning in filenames** - No "v2", "verified", "final", "updated", "new", "fixed" suffixes
3. **Single source of truth** - One file per purpose
4. **Fix in place** - Correct errors in the original file
5. **No parallel versions** - Never have multiple versions of the same functionality
6. **USE GIT FOR VERSIONING** - Commit changes regularly with descriptive messages

### Git Commit Requirements
- **PRIORITIZE FUNCTIONALITY** - Focus on working code, not cosmetic improvements
- **COMMIT FREQUENTLY** - After completing each logical unit of work
- **Check git status regularly** - Use `git status` before and after changes
- **Descriptive messages** - Explain functional changes, not formatting fixes
- **Atomic commits** - Each commit should be a single logical change
- **USE --no-verify** - When only formatting/linting issues remain that don't affect functionality
- **Never rely on filenames for versioning** - That's what git is for
- **Commit at least**:
  - After fixing functional errors
  - After implementing new features
  - After significant refactoring that improves performance/functionality
  - Before switching to different tasks
  - Skip commits for pure formatting unless blocking functionality

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

## PROJECT INTELLIGENCE SYSTEM - DYNAMIC USAGE

### CRITICAL: Default-On Intelligence
The `.proj-intel/` directory contains comprehensive indexed knowledge. **Use it by default for ALL non-trivial tasks**, not just when keywords appear.

### What's Available
- **10MB+ of indexed data** about every file, class, function, and import
- **1,221 agent/class definitions** in `agent_architecture.jsonl`
- **O(1) lookups** via reverse_index.json and symbol_index.json
- **File statistics** in file_elements.min.jsonl (lines, functions, classes)
- **Gatekeeper tools** in apps/ACCF/src/accf/tools/ for smart context selection

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