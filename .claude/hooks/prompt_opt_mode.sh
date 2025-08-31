#!/bin/bash
# Script to manage prompt optimizer mode

CONFIG_FILE="/home/opsvi/master_root/.claude/hooks/prompt_opt_config.json"

show_status() {
    if [ -f "$CONFIG_FILE" ]; then
        MODE=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['mode'])" 2>/dev/null || echo "opt-out")
    else
        MODE="opt-out"
    fi

    echo "Current prompt optimizer mode: $MODE"
    echo ""
    echo "Available modes:"
    echo "  always   - Always optimize (bypass with !raw)"
    echo "  opt-in   - Only optimize with !! or !opt prefix"
    echo "  opt-out  - Optimize by default (skip with !skip or !noopt)"
    echo "  disabled - Never optimize"
    echo ""
    echo "Per-prompt controls:"
    echo "  !!       - Force optimization (opt-in mode)"
    echo "  !skip    - Skip optimization (opt-out mode)"
    echo "  !raw     - Send exact text (any mode)"
    echo "  [RAW]    - Preserve wrapped sections (any mode)"
}

set_mode() {
    MODE=$1
    if [[ ! "$MODE" =~ ^(always|opt-in|opt-out|disabled)$ ]]; then
        echo "Error: Invalid mode '$MODE'"
        echo "Valid modes: always, opt-in, opt-out, disabled"
        exit 1
    fi

    python3 -c "
import json
config = json.load(open('$CONFIG_FILE'))
config['mode'] = '$MODE'
json.dump(config, open('$CONFIG_FILE', 'w'), indent=2)
"
    echo "Prompt optimizer mode set to: $MODE"
}

if [ $# -eq 0 ]; then
    show_status
elif [ "$1" == "status" ]; then
    show_status
elif [ "$1" == "set" ] && [ $# -eq 2 ]; then
    set_mode "$2"
else
    echo "Usage: $0 [status|set <mode>]"
    echo ""
    echo "Examples:"
    echo "  $0              # Show current status"
    echo "  $0 status       # Show current status"
    echo "  $0 set opt-in   # Set to opt-in mode"
    echo "  $0 set disabled # Disable optimizer"
    exit 1
fi
