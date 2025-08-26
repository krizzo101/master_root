#!/bin/bash
# ============================================================================
# ECOSYSTEM MATURATION LAUNCH SCRIPT
# Transform to world-class AI development environment in 10 days
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WORK_DIR="/home/opsvi/master_root"
MONITOR_DIR="$WORK_DIR/apps/multi-agent-monitor"
WORKFLOW_FILE="$MONITOR_DIR/src/workflows/ecosystem_maturation_safe.yaml"
LOG_DIR="/tmp/maturation_logs"
CHECKPOINT_PREFIX="maturation"

# ============================================================================
# FUNCTIONS
# ============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║       ECOSYSTEM MATURATION - 15 AGENT ASSAULT MODE         ║"
    echo "║                                                            ║"
    echo "║  Transform from Experimental to World-Class in 10 Days    ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_prerequisites() {
    echo -e "${YELLOW}[*] Checking prerequisites...${NC}"

    # Check if we're in the right directory
    if [ ! -f "$WORK_DIR/CLAUDE.md" ]; then
        echo -e "${RED}[!] Not in master_root directory${NC}"
        exit 1
    fi

    # Check if multi-agent-monitor exists
    if [ ! -d "$MONITOR_DIR" ]; then
        echo -e "${RED}[!] Multi-agent-monitor not found${NC}"
        exit 1
    fi

    # Check if workflow file exists
    if [ ! -f "$WORKFLOW_FILE" ]; then
        echo -e "${RED}[!] Workflow file not found: $WORKFLOW_FILE${NC}"
        exit 1
    fi

    # Check git status
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}[!] Git repository has uncommitted changes${NC}"
        read -p "Create checkpoint and continue? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            create_checkpoint "pre_maturation"
        else
            exit 1
        fi
    fi

    # Check tokens
    echo -e "${YELLOW}[*] Checking Claude Code tokens...${NC}"
    python3 -c "
from apps.multi_agent_monitor.src.orchestration.secrets_manager import TokenSecretsManager
manager = TokenSecretsManager()
tokens = manager.list_tokens()
print(f'  ✓ Found {len(tokens)} tokens')
if len(tokens) < 15:
    print('  ⚠ Warning: Less than 15 tokens available')
    print('  Only', len(tokens), 'agents can run in parallel')
"

    # Check disk space
    available_space=$(df -h "$WORK_DIR" | awk 'NR==2 {print $4}')
    echo -e "${GREEN}  ✓ Available disk space: $available_space${NC}"

    echo -e "${GREEN}[✓] Prerequisites check complete${NC}"
}

create_checkpoint() {
    local checkpoint_name="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local branch_name="${CHECKPOINT_PREFIX}/${checkpoint_name}/${timestamp}"

    echo -e "${YELLOW}[*] Creating git checkpoint: $branch_name${NC}"
    git checkout -b "$branch_name"
    git add -A
    git commit -m "Checkpoint: $checkpoint_name at $timestamp" || true
    echo -e "${GREEN}  ✓ Checkpoint created${NC}"
}

validate_tokens() {
    echo -e "${YELLOW}[*] Validating all tokens...${NC}"
    python3 "$MONITOR_DIR/test_system.py" | grep "✅"
}

run_phase() {
    local phase_name="$1"
    local dry_run="${2:-false}"

    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Executing Phase: $phase_name${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

    # Prepare command
    local cmd="python $MONITOR_DIR/safe_execute.py ecosystem_maturation"
    cmd="$cmd --type refactor"
    cmd="$cmd --workflow $WORKFLOW_FILE"
    cmd="$cmd --phase \"$phase_name\""
    cmd="$cmd --safety high"
    cmd="$cmd --tokens 15"
    cmd="$cmd --max-concurrent 15"

    if [ "$dry_run" = "true" ]; then
        cmd="$cmd --dry-run"
        echo -e "${YELLOW}[*] Running in DRY RUN mode${NC}"
    else
        cmd="$cmd --mode safe"
    fi

    # Create log file
    local log_file="$LOG_DIR/$(echo $phase_name | tr ' ' '_')_$(date +%Y%m%d_%H%M%S).log"
    mkdir -p "$LOG_DIR"

    echo -e "${YELLOW}[*] Executing: $cmd${NC}"
    echo -e "${YELLOW}[*] Log file: $log_file${NC}"

    # Execute with real-time output and logging
    $cmd 2>&1 | tee "$log_file"

    # Check result
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo -e "${GREEN}[✓] Phase completed successfully${NC}"
        create_checkpoint "post_${phase_name// /_}"
        return 0
    else
        echo -e "${RED}[!] Phase failed - check log: $log_file${NC}"
        return 1
    fi
}

monitor_progress() {
    echo -e "${YELLOW}[*] Starting monitoring dashboard...${NC}"
    echo -e "${YELLOW}    (Run in separate terminal for real-time monitoring)${NC}"
    echo
    echo "watch -n 1 'python -m apps.multi-agent-monitor.src.monitoring.dashboard'"
    echo
}

launch_maturation() {
    local mode="${1:-interactive}"

    if [ "$mode" = "interactive" ]; then
        echo -e "${YELLOW}Select execution mode:${NC}"
        echo "  1) Dry Run - Preview all changes"
        echo "  2) Phase 0 - Pre-flight validation only"
        echo "  3) Phase 1 - Day 1 Activation Blitz"
        echo "  4) Full Maturation - All phases"
        echo "  5) Custom - Select specific phase"
        echo
        read -p "Enter choice (1-5): " choice

        case $choice in
            1)
                echo -e "${YELLOW}[*] Starting DRY RUN of entire maturation...${NC}"
                run_phase "Pre-Flight Validation" true
                run_phase "Day 1 - Activation Blitz" true
                run_phase "Testing Tsunami" true
                ;;
            2)
                run_phase "Pre-Flight Validation" false
                ;;
            3)
                run_phase "Pre-Flight Validation" false
                if [ $? -eq 0 ]; then
                    run_phase "Day 1 - Activation Blitz" false
                fi
                ;;
            4)
                echo -e "${RED}[!] Full maturation will run for ~10 days${NC}"
                read -p "Are you sure? (yes/no): " confirm
                if [ "$confirm" = "yes" ]; then
                    run_phase "Pre-Flight Validation" false
                    [ $? -eq 0 ] && run_phase "Day 1 - Activation Blitz" false
                    [ $? -eq 0 ] && run_phase "Testing Tsunami" false
                    [ $? -eq 0 ] && run_phase "Production Hardening" false
                    [ $? -eq 0 ] && run_phase "Knowledge & Learning Systems" false
                    [ $? -eq 0 ] && run_phase "Advanced Optimization" false
                    [ $? -eq 0 ] && run_phase "Final Validation & Launch" false
                fi
                ;;
            5)
                echo "Available phases:"
                echo "  - Pre-Flight Validation"
                echo "  - Day 1 - Activation Blitz"
                echo "  - Testing Tsunami"
                echo "  - Production Hardening"
                echo "  - Knowledge & Learning Systems"
                echo "  - Advanced Optimization"
                echo "  - Final Validation & Launch"
                echo
                read -p "Enter phase name: " phase_name
                run_phase "$phase_name" false
                ;;
            *)
                echo -e "${RED}[!] Invalid choice${NC}"
                exit 1
                ;;
        esac
    else
        # Automated mode for CI/CD
        run_phase "Pre-Flight Validation" false
        [ $? -eq 0 ] && run_phase "Day 1 - Activation Blitz" false
    fi
}

show_status() {
    echo -e "${YELLOW}[*] Current maturation status:${NC}"

    # Check git branches
    echo -e "${BLUE}Git checkpoints:${NC}"
    git branch | grep "$CHECKPOINT_PREFIX" | tail -5

    # Check test coverage
    echo -e "${BLUE}Test coverage:${NC}"
    pytest --cov=. --cov-report=term 2>/dev/null | grep TOTAL || echo "  Coverage data not available"

    # Check agent registry
    if [ -f "config/agent_registry.json" ]; then
        echo -e "${BLUE}Agent registry:${NC}"
        echo "  $(jq '.agents | length' config/agent_registry.json) agents registered"
    fi

    # Check knowledge base
    echo -e "${BLUE}Knowledge base:${NC}"
    mcp call mcp__knowledge__knowledge_query --query_type recent --limit 1 2>/dev/null || echo "  Knowledge base not available"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

print_banner

# Parse command line arguments
case "${1:-}" in
    "status")
        show_status
        ;;
    "monitor")
        monitor_progress
        ;;
    "dry-run")
        check_prerequisites
        run_phase "Pre-Flight Validation" true
        run_phase "Day 1 - Activation Blitz" true
        ;;
    "phase")
        check_prerequisites
        run_phase "$2" false
        ;;
    "full")
        echo -e "${RED}[!] WARNING: Full maturation will run for ~10 days${NC}"
        read -p "Type 'TRANSFORM' to confirm: " confirm
        if [ "$confirm" = "TRANSFORM" ]; then
            check_prerequisites
            validate_tokens
            launch_maturation "automated"
        fi
        ;;
    *)
        check_prerequisites
        launch_maturation "interactive"
        ;;
esac

echo
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN} Maturation script completed. Check logs in: $LOG_DIR${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
