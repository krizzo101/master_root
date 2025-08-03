<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"MULTI-AGENT GIT PROTOCOL","description":"Documentation establishing safe, coordinated version control practices for multiple autonomous agents operating simultaneously in the same repository.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to identify major thematic sections based on the protocol's structure, focusing on high-level divisions rather than every subheading. Capture key procedural instructions, examples, and critical concepts such as safety principles, branch strategy, commit protocols, conflict resolution, coordination mechanisms, emergency procedures, monitoring, and enforcement. Ensure all line numbers are accurate and sections do not overlap. Provide a navigable file map with concise section names and descriptions, and highlight important code blocks, tables, and examples that aid comprehension and navigation.","sections":[{"name":"Introduction and Purpose","description":"Overview of the protocol's purpose and critical principles guiding multi-agent git operations.","line_start":7,"line_end":24},{"name":"Branch Strategy","description":"Recommended branching approaches for agents, including agent-specific branches and coordinated main branch strategy.","line_start":25,"line_end":40},{"name":"Pre-Operation Protocols","description":"Mandatory checks and procedures before modifying files, including git status checks, analyzing uncommitted changes, and file ownership tracking.","line_start":41,"line_end":67},{"name":"Commit Protocols","description":"Guidelines for commit message formatting, atomic commits, and pre-commit validation to ensure safe and clear version control.","line_start":68,"line_end":92},{"name":"Startup Behavior Revision","description":"Comparison of old unsafe startup behaviors with new safe procedures emphasizing assessment and verification before changes.","line_start":93,"line_end":109},{"name":"Conflict Resolution","description":"Procedures for detecting, analyzing, and resolving conflicts with emphasis on manual review and coordination without auto-resolution.","line_start":110,"line_end":129},{"name":"Coordination Mechanisms","description":"Tools and communication methods for coordinating agent sessions, including session coordination files and commit message conventions.","line_start":130,"line_end":151},{"name":"Implementation Checklist","description":"Step-by-step checklist for immediate changes, workflow updates, and safety mechanisms to implement the protocol effectively.","line_start":152,"line_end":171},{"name":"Emergency Procedures","description":"Instructions for handling conflicts and suspected data loss to protect repository integrity and ensure recovery.","line_start":172,"line_end":186},{"name":"Monitoring and Validation","description":"Regular health checks and session audits to monitor repository state and agent activities for compliance and safety.","line_start":187,"line_end":203},{"name":"Examples","description":"Practical examples demonstrating safe agent startup and file modification workflows.","line_start":204,"line_end":235},{"name":"Enforcement","description":"Mandatory enforcement statement emphasizing the protocol's immediate effect and importance for all agent operations.","line_start":236,"line_end":247}],"key_elements":[{"name":"Safety First Principles","description":"Critical safety rules including no automatic commits, always checking git status, and backing up before destructive operations.","line":14},{"name":"Agent Identification Format","description":"Specification for unique agent session identifiers and commit message inclusion.","line":20},{"name":"Agent-Specific Branches Example","description":"Code block showing naming conventions for agent-specific branches.","line":27},{"name":"Pre-Operation Git Status Check","description":"Mandatory git commands to check repository status before file modifications.","line":43},{"name":"File Ownership Tracking Session Log","description":"Example session log format tracking modified files per agent session.","line":58},{"name":"Commit Message Format Examples","description":"Examples of standardized commit messages including agent IDs and action descriptions.","line":70},{"name":"Pre-Commit Validation Commands","description":"Commands to review staged changes ensuring only the agent's changes are committed.","line":85},{"name":"Old vs New Startup Behavior","description":"Comparison of unsafe old startup behavior and recommended safe startup procedures.","line":95},{"name":"Conflict Detection Commands","description":"Git commands used to detect conflicts before proceeding with operations.","line":112},{"name":"Session Coordination File Example","description":"YAML example showing active agent sessions, branches, and claimed files for coordination.","line":134},{"name":"Commit Communication Examples","description":"Sample commit messages used for inter-agent communication during coordination.","line":145},{"name":"Implementation Checklist Items","description":"Lists of tasks for immediate changes, workflow updates, and safety mechanisms to implement the protocol.","line":154},{"name":"Emergency Procedures Steps","description":"Stepwise instructions for handling conflicts and suspected data loss scenarios.","line":174},{"name":"Git Health Check Commands","description":"Commands for regular repository validation and health monitoring.","line":189},{"name":"Safe Agent Startup Example","description":"Step-by-step bash commands demonstrating safe agent startup procedure.","line":206},{"name":"Safe File Modification Example","description":"Commands illustrating pre-check, modification, validation, and commit of files safely.","line":223},{"name":"Protocol Enforcement Statement","description":"Final mandatory enforcement notice emphasizing protocol compliance and activation.","line":236}]}
-->
<!-- FILE_MAP_END -->

# MULTI-AGENT GIT PROTOCOL

## PURPOSE
Establish safe, coordinated version control practices for multiple autonomous agents operating simultaneously in the same repository.

## CRITICAL PRINCIPLES

### 🚨 SAFETY FIRST
- **NEVER commit automatically** without explicit verification
- **ALWAYS check git status** before any file modifications
- **NEVER commit changes made by other agents** without explicit coordination
- **ALWAYS backup before destructive operations**

### 🤖 AGENT IDENTIFICATION
- Each agent session MUST have a unique identifier
- Format: `AGENT-{session-id}` or `AGENT-{user}-{timestamp}`
- All commits MUST include agent ID in message: `[AGENT-ID] action: description`

## BRANCH STRATEGY

### Option A: Agent-Specific Branches (RECOMMENDED)
```bash
# Each agent works on own branch
agent-{id}-{task-name}
# Examples:
agent-session1-rule-updates
agent-alice-database-fixes
```

### Option B: Coordinated Main Branch
- Only when agents are working on completely separate files
- Requires strict file ownership tracking
- Higher risk - use with caution

## PRE-OPERATION PROTOCOLS

### 1. GIT STATUS CHECK (MANDATORY)
```bash
# Before ANY file modification
git status --porcelain
git diff --name-only
```

### 2. ANALYZE UNCOMMITTED CHANGES
If uncommitted changes exist:
- **Files I modified**: Commit with my agent ID
- **Files modified by others**:
  - DO NOT TOUCH without coordination
  - Document in session log
  - Consider stashing or separate handling

### 3. FILE OWNERSHIP TRACKING
Maintain session log of files modified:
```
SESSION: agent-{id}
MODIFIED FILES:
- file1.txt (created)
- file2.py (modified lines 10-25)
- file3.md (deleted)
```

## COMMIT PROTOCOLS

### 1. COMMIT MESSAGE FORMAT
```
[AGENT-{ID}] {action}: {description}

Examples:
[AGENT-SESSION1] create: multi-agent git protocol
[AGENT-ALICE] fix: database connection timeout issue
[AGENT-BOB] update: documentation for new API endpoints
```

### 2. ATOMIC COMMITS
- One logical change per commit
- Complete, working state
- Include tests/validation when applicable

### 3. PRE-COMMIT VALIDATION
```bash
# Validate before committing
git diff --cached --stat
git diff --cached --name-only
# Review changes are only YOUR changes
```

## STARTUP BEHAVIOR REVISION

### ❌ OLD (DANGEROUS)
```
- Auto-commit before changes
- Auto-commit after changes
- No conflict checking
```

### ✅ NEW (SAFE)
```
- Check git status and report
- Document any uncommitted changes
- Only commit if orphaned changes from previous sessions
- Focus on assessment, not modification
```

## CONFLICT RESOLUTION

### 1. DETECTION
```bash
git status
git diff
git log --oneline -10  # Check recent commits
```

### 2. RESOLUTION STRATEGY
- **PAUSE** all operations if conflicts detected
- **ANALYZE** what changes conflict and why
- **COORDINATE** with other agents if needed
- **DOCUMENT** resolution in commit message

### 3. NEVER AUTO-RESOLVE
- Always require explicit review
- Use interactive merge tools when needed
- Document decision-making process

## COORDINATION MECHANISMS

### 1. SESSION COORDINATION FILE
```yaml
# .agent-sessions.yml
active_sessions:
  - agent_id: "agent-session1"
    branch: "agent-session1-protocols"
    start_time: "2025-06-28T11:15:00Z"
    files_claimed: ["protocols/", "rules/"]
  - agent_id: "agent-alice"
    branch: "main"
    files_claimed: ["src/database/"]
```

### 2. COMMIT COMMUNICATION
Use commit messages to communicate:
```
[AGENT-A] note: modified shared config, agent-b please review
[AGENT-B] merge: integrated agent-a changes, tested successfully
```

## IMPLEMENTATION CHECKLIST

### 1. IMMEDIATE CHANGES
- [ ] Remove auto-commit from startup workflow
- [ ] Add git status check to all file operations
- [ ] Implement agent ID system
- [ ] Create session tracking mechanism

### 2. WORKFLOW UPDATES
- [ ] Update startup workflow to assessment-only
- [ ] Add git safety checks to file modification tools
- [ ] Implement pre-commit validation
- [ ] Add conflict detection

### 3. SAFETY MECHANISMS
- [ ] Dry-run mode for git operations
- [ ] Backup creation before major changes
- [ ] Session file ownership tracking
- [ ] Agent coordination logging

## EMERGENCY PROCEDURES

### If Conflicts Occur
1. **STOP** all agent operations
2. **BACKUP** current state
3. **ANALYZE** conflicts manually
4. **COORDINATE** resolution strategy
5. **TEST** resolution before proceeding

### If Data Loss Suspected
1. **IMMEDIATELY** create backup branch
2. **USE** git reflog to find lost commits
3. **DOCUMENT** incident in session log
4. **IMPLEMENT** additional safeguards

## MONITORING AND VALIDATION

### Git Health Checks
```bash
# Regular validation
git fsck
git status
git log --oneline -20
git branch -v
```

### Session Audit
- Track which agent modified which files
- Monitor for unauthorized changes
- Validate commit attribution
- Check for orphaned changes

## EXAMPLES

### Safe Agent Startup
```bash
# 1. Check current state
git status
git log --oneline -5

# 2. Document findings
echo "Git clean, no conflicts detected" > session.log

# 3. Create agent branch if needed
git checkout -b agent-session1-task

# 4. Proceed with work
```

### Safe File Modification
```bash
# 1. Pre-check
git status file.txt
git diff file.txt

# 2. Modify file
# ... make changes ...

# 3. Validate and commit
git add file.txt
git diff --cached file.txt
git commit -m "[AGENT-SESSION1] update: improve file.txt functionality"
```

## ENFORCEMENT

This protocol is **MANDATORY** for all agent operations involving version control. Violations risk data loss and operational conflicts.

**ACTIVATION**: This protocol takes effect immediately and supersedes all previous git-related behavioral directives.
