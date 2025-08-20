#!/bin/bash

# SDLC Postmortem Engine
# Orchestrates the comprehensive postmortem review process for SDLC projects
# Part of SDLC Enhancement Suite

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT_PATH=""
AUTO_MODE=false
TEMPLATE_ONLY=false
ANALYZE_ONLY=false
CLEANUP_ONLY=false

# Usage function
usage() {
    cat << EOF
Usage: $0 <project-path> [options]

SDLC Postmortem Engine - Comprehensive project review and improvement

Arguments:
    project-path    Path to the project directory (required)

Options:
    --auto          Run in automated mode (no prompts)
    --template      Generate template only
    --analyze       Run analysis only
    --cleanup       Handle branch cleanup only
    -h, --help      Show this help message

Examples:
    $0 apps/my-project                    # Full postmortem
    $0 libs/opsvi-auth --auto            # Automated postmortem
    $0 apps/my-app --template            # Generate template only

EOF
    exit 0
}

# Error handling
error_exit() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

# Success message
success_msg() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Warning message
warning_msg() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Info message
info_msg() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Parse command line arguments
parse_args() {
    if [ $# -eq 0 ]; then
        usage
    fi

    PROJECT_PATH="$1"
    shift

    while [ $# -gt 0 ]; do
        case "$1" in
            --auto)
                AUTO_MODE=true
                ;;
            --template)
                TEMPLATE_ONLY=true
                ;;
            --analyze)
                ANALYZE_ONLY=true
                ;;
            --cleanup)
                CLEANUP_ONLY=true
                ;;
            -h|--help)
                usage
                ;;
            *)
                error_exit "Unknown option: $1"
                ;;
        esac
        shift
    done
}

# Validate project exists
validate_project() {
    if [ ! -d "$PROJECT_PATH" ]; then
        error_exit "Project directory not found: $PROJECT_PATH"
    fi

    if [ ! -d "$PROJECT_PATH/.sdlc" ]; then
        error_exit "Not an SDLC project (missing .sdlc directory): $PROJECT_PATH"
    fi

    success_msg "Found SDLC project at: $PROJECT_PATH"
}

# Check all phases completed
validate_phases() {
    info_msg "Validating SDLC phase completion..."

    local phases=("discovery" "design" "planning" "development" "testing" "deployment" "production")
    local all_complete=true

    for phase in "${phases[@]}"; do
        local gate_file="$PROJECT_PATH/.sdlc/${phase}-complete.json"
        if [ -f "$gate_file" ]; then
            success_msg "Phase $phase: COMPLETE"
        else
            warning_msg "Phase $phase: INCOMPLETE (missing ${phase}-complete.json)"
            all_complete=false
        fi
    done

    if [ "$all_complete" = false ]; then
        if [ "$AUTO_MODE" = false ]; then
            read -p "Some phases are incomplete. Continue anyway? (y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                error_exit "Postmortem cancelled"
            fi
        else
            warning_msg "Proceeding with incomplete phases (auto mode)"
        fi
    else
        success_msg "All SDLC phases completed"
    fi
}

# Generate postmortem template
generate_template() {
    info_msg "Generating postmortem template..."

    local template_file="$PROJECT_PATH/docs/6-postmortem.md"
    local project_name=$(basename "$PROJECT_PATH")
    local date=$(date +%Y-%m-%d)

    # Create docs directory if it doesn't exist
    mkdir -p "$PROJECT_PATH/docs"

    cat > "$template_file" << 'EOF'
# SDLC Postmortem Report

**Project:** PROJECT_NAME
**Date:** DATE
**Author:** [Your Name]
**Compliance Score:** [To be calculated]

## Executive Summary

[Provide a brief overview of the project, its goals, and overall outcome]

## Process Compliance

### Phase Completion Status

| Phase | Status | Artifacts | Violations |
|-------|--------|-----------|------------|
| Discovery | ✅/❌ | requirements.md | None/List |
| Design | ✅/❌ | design.md | None/List |
| Planning | ✅/❌ | planning.md | None/List |
| Development | ✅/❌ | Code, tests | None/List |
| Testing | ✅/❌ | Test results | None/List |
| Deployment | ✅/❌ | Deployment config | None/List |
| Production | ✅/❌ | Handover docs | None/List |

### Compliance Score Calculation

- Total phases: 7
- Completed phases: X
- Compliance score: X/7 = XX%

## Violations Detected

### Critical Violations
[List any critical process violations]

### Major Violations
[List any major process violations]

### Minor Violations
[List any minor process violations]

## What Went Well

1. [Success point 1]
2. [Success point 2]
3. [Success point 3]

## What Could Be Improved

1. [Improvement area 1]
2. [Improvement area 2]
3. [Improvement area 3]

## Lessons Learned

### Technical Lessons
- [Technical lesson 1]
- [Technical lesson 2]

### Process Lessons
- [Process lesson 1]
- [Process lesson 2]

### Team/Communication Lessons
- [Communication lesson 1]
- [Communication lesson 2]

## Action Items

| Action | Owner | Due Date | Priority |
|--------|-------|----------|----------|
| [Action 1] | [Owner] | [Date] | High/Medium/Low |
| [Action 2] | [Owner] | [Date] | High/Medium/Low |

## Knowledge Captured

### Patterns to Replicate
- [Pattern 1]
- [Pattern 2]

### Anti-patterns to Avoid
- [Anti-pattern 1]
- [Anti-pattern 2]

## Branch Disposition

**Recommendation:** [merge/pr/archive/delete]

**Justification:**
[Explain why this branch disposition is recommended]

## Process Improvements Proposed

1. [Improvement proposal 1]
2. [Improvement proposal 2]

## Appendix

### Metrics
- Lines of code: X
- Test coverage: X%
- Documentation pages: X
- Commits: X
- Time spent: X hours

### References
- Requirements: docs/1-requirements.md
- Design: docs/2-design.md
- Planning: docs/3-planning.md
- Testing: docs/4-testing.md
- Deployment: docs/5-deployment.md

---
Generated on DATE by SDLC Postmortem Engine
EOF

    # Replace placeholders
    sed -i "s/PROJECT_NAME/$project_name/g" "$template_file"
    sed -i "s/DATE/$date/g" "$template_file"

    success_msg "Postmortem template created: $template_file"
}

# Run violation analysis
run_analysis() {
    info_msg "Running violation analysis..."

    local analyzer_script="$HOME/master_root/.claude/commands/sdlc-violation-analyzer.py"

    if [ -f "$analyzer_script" ]; then
        python3 "$analyzer_script" "$PROJECT_PATH" || warning_msg "Violation analyzer not fully implemented yet"
    else
        warning_msg "Violation analyzer not found, skipping analysis"
    fi
}

# Capture knowledge
capture_knowledge() {
    info_msg "Capturing knowledge and lessons learned..."

    # This would integrate with the knowledge system
    # For now, just create a placeholder
    local knowledge_file="$PROJECT_PATH/.sdlc/knowledge-captured.json"

    cat > "$knowledge_file" << EOF
{
    "captured": "$(date -Iseconds)",
    "project": "$(basename "$PROJECT_PATH")",
    "lessons": [],
    "patterns": [],
    "anti_patterns": [],
    "stored_in_knowledge_system": false
}
EOF

    success_msg "Knowledge capture placeholder created"
}

# Handle branch disposition
handle_branch() {
    info_msg "Handling branch disposition..."

    local current_branch=$(git -C "$PROJECT_PATH" branch --show-current 2>/dev/null || echo "unknown")

    if [ "$current_branch" = "main" ] || [ "$current_branch" = "master" ]; then
        warning_msg "Already on main branch, no branch handling needed"
        return
    fi

    info_msg "Current branch: $current_branch"

    if [ "$AUTO_MODE" = false ]; then
        echo "Branch disposition options:"
        echo "1) Create pull request"
        echo "2) Merge to main"
        echo "3) Archive branch"
        echo "4) Delete branch"
        echo "5) Keep as-is"

        read -p "Select option (1-5): " -n 1 -r
        echo

        case $REPLY in
            1)
                info_msg "Creating pull request..."
                # Would use gh pr create here
                warning_msg "PR creation not implemented in scaffold"
                ;;
            2)
                info_msg "Merging to main..."
                warning_msg "Direct merge not implemented in scaffold"
                ;;
            3)
                info_msg "Archiving branch..."
                git -C "$PROJECT_PATH" tag "archive/${current_branch}-$(date +%Y%m%d)"
                success_msg "Branch archived with tag"
                ;;
            4)
                info_msg "Branch will be deleted after switching to main"
                warning_msg "Branch deletion not implemented in scaffold"
                ;;
            5)
                info_msg "Keeping branch as-is"
                ;;
            *)
                warning_msg "Invalid option, keeping branch as-is"
                ;;
        esac
    else
        info_msg "Auto mode: Recommending PR creation"
    fi
}

# Create final artifact
create_artifact() {
    info_msg "Creating postmortem artifact..."

    local artifact_file="$PROJECT_PATH/.sdlc/postmortem-complete.json"

    cat > "$artifact_file" << EOF
{
    "phase": "postmortem",
    "completed": "$(date -Iseconds)",
    "postmortem_doc": "docs/6-postmortem.md",
    "violations": [],
    "compliance_score": 1.0,
    "lessons_captured": [],
    "branch_disposition": "pending",
    "improvements_proposed": [],
    "knowledge_stored": false
}
EOF

    success_msg "Postmortem artifact created: $artifact_file"
}

# Main execution
main() {
    echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     SDLC Postmortem Engine v1.0     ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
    echo

    # Parse arguments
    parse_args "$@"

    # Validate project
    validate_project

    # Handle different modes
    if [ "$TEMPLATE_ONLY" = true ]; then
        generate_template
        exit 0
    fi

    if [ "$ANALYZE_ONLY" = true ]; then
        run_analysis
        exit 0
    fi

    if [ "$CLEANUP_ONLY" = true ]; then
        handle_branch
        exit 0
    fi

    # Full postmortem flow
    validate_phases
    generate_template
    run_analysis
    capture_knowledge
    handle_branch
    create_artifact

    echo
    success_msg "Postmortem complete!"
    info_msg "Next steps:"
    echo "  1. Edit the postmortem document: $PROJECT_PATH/docs/6-postmortem.md"
    echo "  2. Fill in subjective sections and insights"
    echo "  3. Review and commit the postmortem"
    echo "  4. Complete branch disposition as decided"
}

# Run main function
main "$@"
