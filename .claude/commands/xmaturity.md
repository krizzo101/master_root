---
description: Assess and improve team's development maturity with actionable insights
tags: [maturity, assessment, improvement]
---

Assess development maturity and provide improvement roadmap.

Parse assessment options from $ARGUMENTS (--level, --assess, --roadmap, --progress, or specific area like --testing, --ci-cd).

## 1. Quick Maturity Check

First, gather basic project metrics:
!find . -name "*.py" -o -name "*.js" -o -name "*.ts" | wc -l
!find . -name "*test*" -o -name "*spec*" | wc -l
!test -f .github/workflows/ci.yml && echo "CI/CD: GitHub Actions configured" || echo "CI/CD: Not found"
!test -f README.md && wc -l README.md

## 2. Development Practices Assessment

Check version control practices:
!git log --oneline -10 | grep -E "(feat|fix|docs|test|refactor)" | wc -l
!git branch -r | wc -l

Testing maturity:
!python -m pytest --cov=. 2>/dev/null | grep "TOTAL" || npm test 2>/dev/null | grep "Test Suites" || echo "No test coverage data"

Code quality tools:
!test -f .pre-commit-config.yaml && echo "Pre-commit hooks: Configured" || echo "Pre-commit hooks: Not configured"
!test -f pyproject.toml && grep -E "(black|ruff|mypy)" pyproject.toml 2>/dev/null

## 3. CI/CD Maturity

Check for automation:
!find . -name "*.yml" -path "*workflow*" -o -path "*github*" | head -5
!test -f Dockerfile && echo "Containerization: Yes" || echo "Containerization: No"

## 4. Documentation & Knowledge Sharing

!find . -name "*.md" | wc -l
!test -d docs && echo "Documentation folder exists" || echo "No dedicated docs folder"

Think step by step about the maturity assessment and provide:

1. Current maturity level (1-5) with justification
2. Strengths and gaps in each area
3. Specific improvement recommendations
4. 90-day improvement roadmap

Generate maturity report in this format:

```
📊 DEVELOPMENT MATURITY ASSESSMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Level: X.X/5.0 (Level Name)

📈 MATURITY SCORES BY AREA
────────────────────────
🔧 Engineering Practices
- Version Control: X.X/5 ✓
- Testing: X.X/5 ⚠️
- Code Quality: X.X/5 ✓
- Documentation: X.X/5 ❌

🚀 Delivery & Operations
- CI/CD: X.X/5 ⚠️
- Monitoring: X.X/5 ❌
- Security: X.X/5 ⚠️

👥 Team & Culture
- Collaboration: X.X/5 ✓
- Knowledge Sharing: X.X/5 ⚠️

💪 STRENGTHS
───────────
• [Specific strength with evidence]
• [Specific strength with evidence]

🎯 TOP GAPS TO ADDRESS
───────────────────
1. [Gap]: Current state → Target state
   Action: [Specific action to take]

2. [Gap]: Current state → Target state
   Action: [Specific action to take]

📅 90-DAY IMPROVEMENT ROADMAP
─────────────────────────
Week 1-2: Quick Wins
• [Specific task with command/action]
• [Specific task with command/action]

Week 3-4: Foundation
• [Specific task with command/action]
• [Specific task with command/action]

Month 2: Build Momentum
• [Larger improvement initiative]
• [Process implementation]

Month 3: Establish Excellence
• [Advanced practice adoption]
• [Measurement and optimization]

💡 NEXT STEPS
───────────
1. [Immediate action to take today]
2. [Action to take this week]
3. [Process to establish this month]
```

If --roadmap is specified, create detailed implementation plan.
If --progress is specified, compare against previous assessment.
If --benchmark is specified, compare against industry standards.

Maturity Levels:
1. Initial (Ad-hoc): Inconsistent, reactive
2. Managed: Basic processes, some repeatability
3. Defined: Standardized processes, good practices
4. Quantified: Measured, data-driven decisions
5. Optimizing: Continuous improvement, innovation
