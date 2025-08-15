# Git Workflow Standards for AI Factory

## Core Principle
**Every feature, fix, or change gets its own branch. No exceptions.**

## Branch Naming Convention

### Standard Format
```
<type>/<description>-<issue-number>
```

### Branch Types
- `feature/` - New features or enhancements
- `fix/` - Bug fixes
- `hotfix/` - Urgent production fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation updates
- `test/` - Test additions or fixes
- `chore/` - Maintenance tasks

### Examples
```bash
feature/payment-integration-123
fix/auth-token-expiry-456
hotfix/database-connection-789
refactor/user-service-cleanup
docs/api-documentation-update
test/integration-test-suite
chore/dependency-updates
```

## Git Workflow for SDLC Projects

### 1️⃣ Project Initialization (Start of SDLC)
```bash
# Always start from main/master
git checkout main
git pull origin main

# Create feature branch for the project
git checkout -b feature/<project-name>

# Example:
git checkout -b feature/payment-service
```

### 2️⃣ During Development (SDLC Phases)

#### Discovery & Design Phase
```bash
# Commit requirements and design docs
git add docs/requirements/<project-name>.md
git commit -m "docs: add requirements for <project-name>

- Problem statement
- User stories
- Success criteria"

git add docs/design/<project-name>.md
git commit -m "docs: add architecture design for <project-name>

- Component architecture
- API specifications
- Technology choices"
```

#### Development Phase
```bash
# Commit frequently after each logical unit
git add -A
git commit -m "feat: implement <specific-feature>

- What was added
- Why it was added
- Any important notes"

# Use conventional commit messages:
# feat: new feature
# fix: bug fix
# docs: documentation
# style: formatting, missing semicolons, etc
# refactor: code restructuring
# test: adding tests
# chore: maintenance
```

#### Testing Phase
```bash
# Commit test files
git add tests/
git commit -m "test: add unit tests for <component>

- Test coverage: X%
- Test cases covered"

# Commit test fixes
git add -A
git commit -m "fix: resolve failing tests in <component>

- Fixed issue with X
- Updated test expectations"
```

### 3️⃣ Pull Request Process

#### Before Creating PR
```bash
# Ensure branch is up to date with main
git checkout main
git pull origin main
git checkout feature/<project-name>
git rebase main  # or merge if preferred

# Run all tests
npm test  # or appropriate test command
pytest    # or appropriate test command

# Ensure code quality
npm run lint      # or appropriate linter
npm run typecheck # or appropriate type checker
```

#### Creating the PR
```bash
# Push branch to remote
git push -u origin feature/<project-name>

# Create PR using GitHub CLI (if available)
gh pr create \
  --title "feat: <project-name> implementation" \
  --body "## Summary
  
  Implementation of <project-name> following SDLC phases.
  
  ## Changes
  - Completed Discovery phase with requirements
  - Designed architecture with <pattern>
  - Implemented core functionality
  - Added comprehensive tests (X% coverage)
  - Documentation updated
  
  ## Testing
  - [ ] Unit tests pass
  - [ ] Integration tests pass
  - [ ] Manual testing completed
  
  ## Checklist
  - [ ] Code follows project standards
  - [ ] Documentation is updated
  - [ ] Tests are passing
  - [ ] No security vulnerabilities
  
  Closes #<issue-number>"
```

### 4️⃣ Code Review Process

#### As Author
```bash
# Address review comments
git add -A
git commit -m "fix: address review comments

- Updated X per reviewer suggestion
- Refactored Y for clarity
- Added additional tests for Z"

# Push updates
git push
```

#### As Reviewer
- Check SDLC compliance
- Verify test coverage
- Ensure documentation exists
- Validate architecture decisions
- Confirm standards adherence

### 5️⃣ Merging

#### Merge Strategy
```bash
# Option 1: Squash and merge (for feature branches)
# Combines all commits into one
gh pr merge --squash

# Option 2: Rebase and merge (for clean history)
# Maintains individual commits
gh pr merge --rebase

# Option 3: Create merge commit (for preserving context)
# Shows the branch history
gh pr merge --merge
```

#### Post-Merge Cleanup
```bash
# Delete local branch
git checkout main
git pull origin main
git branch -d feature/<project-name>

# Delete remote branch (if not auto-deleted)
git push origin --delete feature/<project-name>
```

## Commit Message Standards

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Examples
```bash
# Simple commit
git commit -m "feat: add user authentication"

# Detailed commit
git commit -m "feat(auth): implement JWT authentication

- Added JWT token generation
- Implemented refresh token logic
- Added token validation middleware

Closes #123"

# Breaking change
git commit -m "feat(api)!: update user endpoint response

BREAKING CHANGE: User endpoint now returns nested object
instead of flat structure. Update clients accordingly."
```

## Git Configuration for AI Agents

### Required Git Config
```bash
# Set user information (if not set globally)
git config user.name "AI Agent"
git config user.email "agent@opsvi.com"

# Set default branch name
git config init.defaultBranch main

# Enable auto-correction
git config help.autocorrect 1

# Set merge strategy
git config pull.rebase false  # Use merge by default
```

### Useful Aliases
```bash
# Add to ~/.gitconfig or .git/config
git config alias.st "status"
git config alias.co "checkout"
git config alias.br "branch"
git config alias.cm "commit -m"
git config alias.last "log -1 HEAD"
git config alias.unstage "reset HEAD --"
git config alias.visual "log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"
```

## Conflict Resolution

### When Conflicts Occur
```bash
# During rebase or merge
git status  # See conflicted files

# For each conflicted file:
# 1. Open file and resolve conflicts
# 2. Look for <<<<<<< HEAD markers
# 3. Choose correct code or combine
# 4. Remove conflict markers

# After resolving
git add <resolved-file>
git rebase --continue  # or git merge --continue

# If things go wrong
git rebase --abort  # or git merge --abort
```

## Special Scenarios

### Hotfix Process
```bash
# Start from main/production
git checkout main
git pull origin main
git checkout -b hotfix/critical-issue

# Make fix
git add -A
git commit -m "hotfix: resolve critical issue

- Fixed X that was causing Y
- Immediate deployment required"

# Fast-track merge
git checkout main
git merge hotfix/critical-issue
git push origin main

# Backport to feature branches if needed
git checkout feature/current-work
git cherry-pick <hotfix-commit-hash>
```

### Working with Multiple Features
```bash
# Use worktrees for parallel development
git worktree add ../project-feature-1 feature/feature-1
git worktree add ../project-feature-2 feature/feature-2

# Switch between them without stashing
cd ../project-feature-1  # Work on feature 1
cd ../project-feature-2  # Work on feature 2

# Clean up when done
git worktree remove ../project-feature-1
```

## Integration with SDLC Enforcer

### Automatic Branch Creation
```python
# When starting new project with SDLC enforcer
from libs.opsvi_mcp.tools.sdlc_enforcer_scoped import ScopedSDLCEnforcer

enforcer = ScopedSDLCEnforcer()
project = enforcer.create_project(
    project_name="payment-service",
    description="Payment processing service",
    root_path="apps/payment-service"
)

# Automatically creates and checks out branch
# git checkout -b feature/payment-service
```

### Phase-Based Commits
```python
# SDLC enforcer can enforce commits at phase transitions
enforcer.advance_phase(project.project_id)
# Triggers: git commit -m "chore: complete <phase> phase for <project>"
```

## Git Hooks for Quality

### Pre-commit Hook
```bash
#!/bin/sh
# .git/hooks/pre-commit

# Run tests before commit
npm test || exit 1

# Run linter
npm run lint || exit 1

# Check for sensitive data
git diff --cached --name-only | xargs grep -E "(api_key|secret|password|token)" && exit 1

exit 0
```

### Commit-msg Hook
```bash
#!/bin/sh
# .git/hooks/commit-msg

# Enforce conventional commits
commit_regex='^(feat|fix|docs|style|refactor|test|chore|hotfix)(\(.+\))?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "Invalid commit message format!"
    echo "Format: <type>(<scope>): <subject>"
    echo "Example: feat(auth): add login endpoint"
    exit 1
fi
```

## Best Practices

### DO ✅
- Create feature branch for EVERY change
- Commit after each logical unit of work
- Write clear, descriptive commit messages
- Keep commits atomic (one change per commit)
- Pull from main frequently to avoid conflicts
- Test before pushing
- Use PR templates
- Delete branches after merging

### DON'T ❌
- Commit directly to main/master
- Mix multiple features in one branch
- Use generic commit messages like "fix" or "update"
- Commit broken code
- Force push to shared branches
- Leave stale branches
- Ignore merge conflicts
- Commit sensitive information

## Troubleshooting

### Common Issues

#### Large Files
```bash
# If accidentally committed large file
git rm --cached large-file.zip
git commit -m "chore: remove large file"

# Use Git LFS for large files
git lfs track "*.zip"
git add .gitattributes
```

#### Wrong Branch
```bash
# If committed to wrong branch
git checkout correct-branch
git cherry-pick <commit-hash>
git checkout wrong-branch
git reset --hard HEAD~1
```

#### Accidental Commit
```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1
```

## Summary

Following this Git workflow ensures:
1. **Clean history** - Easy to understand project evolution
2. **Safe collaboration** - No conflicts or overwrites
3. **SDLC compliance** - Git practices align with SDLC phases
4. **Quality control** - Reviews and tests before merging
5. **Traceability** - Every change is documented

Remember: **Every project starts with a new branch!**