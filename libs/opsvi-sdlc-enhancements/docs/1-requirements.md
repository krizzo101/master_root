# SDLC Enhancements - Requirements Document

## Problem Statement

The current SDLC process has several gaps identified during the Hello DisneyWorld test project:
1. **No formal POSTMORTEM phase** to review and learn from each project
2. No branch cleanup/merge process after project completion
3. Missing git workflow integration (PR creation, branch management)
4. No mechanism to capture lessons learned into the process
5. Missing .gitignore validation for project directories
6. Incomplete artifact tracking and validation
7. No automated process improvement mechanism
8. No structured review of plan vs actual execution

## User Stories

### As a Developer
1. I want completed projects to be properly merged or cleaned up so that feature branches don't accumulate
2. I want the SDLC process to detect and fix its own issues so that it improves over time
3. I want automatic PR creation when appropriate so that code review happens
4. I want .gitignore issues detected early so that my work isn't lost

### As a Team Lead
1. I want all projects to follow consistent git workflows so that collaboration is smooth
2. I want lessons learned captured automatically so that mistakes aren't repeated
3. I want process violations to be impossible so that quality is maintained

## Functional Requirements

### 1. POSTMORTEM Phase (New 8th Phase)
- Mandatory phase after PRODUCTION
- Cannot close project without postmortem
- Structured review template
- Automatic knowledge capture
- Branch cleanup decision
- Process improvement proposals

#### Postmortem Components
1. **Plan vs Actual Analysis**
   - Compare planned tasks with actual execution
   - Time estimates vs actual time
   - Planned deliverables vs actual deliverables

2. **Violations & Shortcuts Review**
   - List any SDLC violations
   - Document shortcuts taken
   - Explain why violations occurred
   - Impact assessment

3. **Success & Failure Analysis**
   - What went well
   - What failed
   - Root cause analysis
   - Prevention strategies

4. **Knowledge Capture**
   - Patterns identified
   - Reusable components created
   - Lessons learned
   - Updates needed to SDLC

5. **Branch Disposition**
   - Merge to main
   - Create PR for review
   - Archive branch
   - Delete branch

6. **Artifacts Archive**
   - Ensure all artifacts committed
   - Create project summary
   - Update project index

### 2. Branch Management Enhancement
- Add branch cleanup task to Production phase
- Provide options: merge to main, create PR, or delete branch
- Validate all changes are committed before cleanup
- Ensure no uncommitted work is lost

### 2. Pull Request Integration
- Automatic PR creation with structured description
- Include SDLC artifacts in PR description
- Link to relevant documentation
- Add reviewers if configured

### 3. Knowledge Capture Integration
- Automatically capture lessons learned
- Update SDLC process based on failures
- Store patterns of success and failure
- Query knowledge before starting projects

### 4. Git Ignore Validation
- Check .gitignore before project creation
- Warn if project directory will be ignored
- Offer to fix .gitignore automatically
- Validate after each phase

### 5. Artifact Validation Enhancement
- Verify all required artifacts exist
- Check artifact content validity
- Ensure artifacts are committed to git
- Generate missing artifacts report

### 6. Self-Improvement Mechanism
- Track SDLC process violations
- Identify patterns of failure
- Automatically generate improvement proposals
- Test improvements before adoption

## Non-Functional Requirements

### Reliability
- Process must be idempotent (can be run multiple times safely)
- Must handle git conflicts gracefully
- Should not lose any work

### Usability
- Clear prompts for user decisions
- Helpful error messages with fix suggestions
- Progressive disclosure of complexity

### Performance
- Pre-flight checks < 5 seconds
- Artifact validation < 10 seconds
- Knowledge queries < 2 seconds

## Interface Specifications

### New Commands

#### POSTMORTEM Command
```bash
sdlc-postmortem.sh <project-path>
# Generates postmortem template
# Validates all phases complete
# Runs analysis tools
# Captures knowledge
# Handles branch cleanup
```

#### Postmortem Template
```markdown
# POSTMORTEM: <project-name>
Date: <date>
Duration: <actual-duration>
Phase: POSTMORTEM

## 1. Plan vs Actual
| Metric | Planned | Actual | Variance |
|--------|---------|--------|----------|
| Duration | X hours | Y hours | +Z% |
| Tasks | N tasks | M completed | -K tasks |
| Test Coverage | 80% | X% | -Y% |
| Commits | - | N commits | - |

## 2. SDLC Compliance
### Violations Detected:
- [ ] Skipped resource_discovery in Discovery
- [ ] No TDD in Development
- [ ] Incomplete test coverage
- [ ] Artifacts not created
- [ ] Tools not used

### Why Violations Occurred:
<explanation>

## 3. What Went Well
- Item 1
- Item 2

## 4. What Failed
- Issue 1: <description>
  - Root Cause: <cause>
  - Prevention: <how to prevent>

## 5. Knowledge to Capture
- Pattern: <pattern-description>
- Reusable Component: <component>
- Lesson: <lesson-learned>

## 6. Process Improvements
- Suggestion 1: <improvement>
- Suggestion 2: <improvement>

## 7. Branch Disposition
- [ ] Merge to main
- [ ] Create PR
- [ ] Archive branch
- [ ] Delete branch

## 8. Sign-off
- [ ] All artifacts committed
- [ ] Knowledge captured
- [ ] Branch cleaned up
- [ ] Postmortem complete
```

#### Branch Cleanup Command
```bash
sdlc-branch-cleanup.sh <project-path>
# Options:
#   --merge       Merge to main
#   --pr          Create pull request
#   --delete      Delete branch
#   --archive     Move to archive branch
```

#### Knowledge Integration
```python
# Before starting project
mcp__knowledge__knowledge_query(
    query_type="search",
    query_text="sdlc violations common failures"
)

# After project completion
mcp__knowledge__knowledge_store(
    knowledge_type="WORKFLOW",
    content={
        "project": "name",
        "violations": [...],
        "fixes_applied": [...],
        "outcome": "success|failure"
    }
)
```

## Success Criteria

1.  No feature branches left orphaned after project completion
2.  All work properly committed and tracked
3.  .gitignore issues detected before work begins
4.  Process improvements captured and applied
5.  100% of SDLC projects have complete artifacts
6.  Knowledge system prevents repeated mistakes

## Existing Solutions Analysis

### Current SDLC Tools
- `sdlc-preflight.sh` - Pre-flight checks (needs .gitignore enhancement)
- `sdlc-gates.md` - Artifact gates (needs validation logic)
- `plan-to-tasks.py` - Task conversion (working well)
- `sdlc-tool-verification.py` - Tool audit (needs knowledge integration)
- `sdlc-task-enforcer.md` - Task rules (needs automation)

### What's Missing
- Branch lifecycle management
- PR creation automation
- Knowledge system integration
- Self-improvement mechanisms

## Decision

**Build enhancements to existing SDLC tools** rather than creating new ones. Extend current scripts with new capabilities and add missing components.

## Research Findings

### Git Best Practices
- Feature branches should be deleted after merge
- PRs should include context and documentation
- Branch protection rules prevent direct main pushes
- Squash commits for cleaner history

### Knowledge Management
- Capture failures immediately when they occur
- Query before starting similar work
- Update process documentation automatically
- Version control all process changes

## Next Steps

1. Design branch management integration
2. Plan knowledge system hooks
3. Enhance existing tools
4. Add self-improvement mechanisms
