# Example 1: Bulk Lint Fixes

## Scenario
Apply organization-wide linting rules across multiple repositories using Cursor Agent CLI (when stable) or Claude Code (current fallback).

## Current Status
⚠️ **Cursor CLI Blocked**: Due to CI=1 hanging bug, using Claude Code as fallback

## Implementation (Claude Code Fallback)

### Setup Script
```bash
#!/bin/bash
# bulk-lint-fixes.sh

# Configuration
REPOS=(
    "github.com/org/service-a"
    "github.com/org/service-b"
    "github.com/org/service-c"
)

LINT_RULES=".claude/lint-rules.md"
```

### MCP Orchestration Request
```python
import asyncio
from opsvi_mcp.servers.multi_agent_orchestrator import orchestrate_task

async def bulk_lint_fixes():
    """Execute bulk lint fixes across repositories"""
    
    tasks = []
    for repo in REPOS:
        task = {
            "description": f"Apply lint rules to {repo}",
            "type": "rule_based_edit",
            "context": {
                "repository": repo,
                "rules_file": LINT_RULES,
                "create_pr": True
            }
        }
        tasks.append(orchestrate_task(
            task=task["description"],
            task_type="lint_enforcement",
            constraints={"generate_pr": True},
            preferred_agent="claude_code"  # Cursor blocked
        ))
    
    # Execute in parallel via MCP
    results = await asyncio.gather(*tasks)
    
    # Generate summary report
    return generate_lint_report(results)

if __name__ == "__main__":
    asyncio.run(bulk_lint_fixes())
```

### Lint Rules Configuration
```markdown
<!-- .claude/lint-rules.md -->
# Project Linting Rules

## Python Standards
1. Use Black formatter with line-length=100
2. Sort imports with isort
3. Type hints required for public functions
4. Docstrings in Google style

## JavaScript Standards
1. ESLint with Airbnb config
2. Prettier for formatting
3. No console.log in production code

## Apply these fixes:
- Remove trailing whitespace
- Ensure files end with newline
- Convert tabs to spaces (4 for Python, 2 for JS)
```

### Expected Output
```json
{
  "execution_summary": {
    "repositories_processed": 3,
    "files_modified": 47,
    "prs_created": 3,
    "duration_seconds": 180
  },
  "pull_requests": [
    {
      "repo": "service-a",
      "pr_url": "https://github.com/org/service-a/pull/123",
      "changes": "+89 -76 lines",
      "status": "ready_for_review"
    }
  ],
  "lint_violations_fixed": {
    "trailing_whitespace": 156,
    "import_sorting": 23,
    "missing_type_hints": 45,
    "formatting": 89
  }
}
```

## Future Implementation (When Cursor CLI is Fixed)

```bash
#!/bin/bash
# cursor-lint-fixes.sh (CURRENTLY BLOCKED)

for repo in "${REPOS[@]}"; do
    cd /workspace/$repo
    
    # Would use Cursor CLI with rules
    cursor-agent chat \
        --headless \
        --rules ".cursor/rules/lint.json" \
        "Apply all linting rules and create PR" \
        --output-format json > results/$repo.json
done
```

### Cursor Rules Format (Future)
```json
{
  "alwaysApply": true,
  "description": "Organization linting standards",
  "globs": ["**/*.py", "**/*.js"],
  "rules": [
    {
      "pattern": "console\\.log",
      "replacement": "logger.debug",
      "fileTypes": ["js", "ts"]
    }
  ]
}
```

## Monitoring & Validation

```python
def validate_lint_fixes(pr_url: str) -> bool:
    """Validate that lint fixes don't break functionality"""
    
    # 1. Check CI status
    ci_status = check_github_checks(pr_url)
    if not ci_status.passing:
        return False
    
    # 2. Run test suite in sandbox (OpenAI Codex)
    test_result = await spawn_codex_sandbox(
        task="Run test suite for PR",
        repository_url=pr_url,
        generate_pr=False
    )
    
    # 3. Check for semantic changes
    diff_analysis = analyze_diff_semantics(pr_url)
    if diff_analysis.has_logic_changes:
        flag_for_human_review(pr_url)
    
    return test_result.success
```

## Rollback Plan

```bash
# If issues detected, revert PRs
for pr in failed_prs; do
    gh pr close $pr --delete-branch
    git revert $pr.merge_commit
done
```

---
*Note: This example currently uses Claude Code due to Cursor CLI's CI=1 bug. Will migrate to Cursor CLI once stable.*