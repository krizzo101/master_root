#!/bin/bash
# SDLC Phase Executor with Comprehensive Debug Logging
# Wraps claude-code MCP calls with detailed logging at every step

set -euo pipefail

# Setup logging
LOG_DIR="/home/opsvi/master_root/.sdlc-logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SESSION_LOG="$LOG_DIR/session_${TIMESTAMP}.log"
PHASE_LOG="$LOG_DIR/phase_${TIMESTAMP}.log"
DEBUG_LOG="$LOG_DIR/debug_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Log function
log() {
    local level=$1
    shift
    local message="$@"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message" | tee -a "$SESSION_LOG"
    if [ "$level" == "DEBUG" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S.%N')] $message" >> "$DEBUG_LOG"
    fi
}

# Phase executor function
execute_phase() {
    local PHASE=$1
    local PROJECT_PATH=$2
    local TASK_DESCRIPTION=$3

    log "INFO" "=========================================="
    log "INFO" "EXECUTING SDLC PHASE: $PHASE"
    log "INFO" "PROJECT: $PROJECT_PATH"
    log "INFO" "=========================================="

    # Create phase-specific log
    PHASE_EXEC_LOG="$LOG_DIR/${PHASE}_${TIMESTAMP}_execution.log"

    # Log pre-execution state
    log "DEBUG" "Pre-execution directory listing:"
    ls -la "$PROJECT_PATH" >> "$DEBUG_LOG" 2>&1 || true

    log "DEBUG" "Git status before execution:"
    git status --short >> "$DEBUG_LOG" 2>&1 || true

    # Create a wrapper script that captures everything
    WRAPPER_SCRIPT="/tmp/sdlc_phase_wrapper_${TIMESTAMP}.py"
    cat > "$WRAPPER_SCRIPT" << 'EOF'
import json
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

phase = sys.argv[1]
project_path = sys.argv[2]
task_description = sys.argv[3]
log_file = sys.argv[4]

def log_step(step, data=None):
    with open(log_file, 'a') as f:
        entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'data': data
        }
        f.write(json.dumps(entry) + '\n')

log_step('START', {'phase': phase, 'project': project_path})

# Import MCP client
try:
    log_step('IMPORT_MCP', 'Importing claude-code-wrapper')
    # This would be the actual MCP call
    # For now, showing the structure
    log_step('MCP_CALL', {
        'task': task_description,
        'outputFormat': 'json',
        'permissionMode': 'bypassPermissions'
    })

    # Simulate MCP execution tracking
    result = {
        'status': 'executing',
        'phase': phase,
        'steps_completed': []
    }

    log_step('EXECUTION_TRACKING', result)

except Exception as e:
    log_step('ERROR', str(e))
    sys.exit(1)

log_step('COMPLETE', {'phase': phase})
EOF

    log "INFO" "Starting phase execution with detailed tracking..."
    log "DEBUG" "Wrapper script created at: $WRAPPER_SCRIPT"
    log "DEBUG" "Phase execution log: $PHASE_EXEC_LOG"

    # Execute the phase
    echo -e "${YELLOW}Executing $PHASE phase...${NC}"

    # Call the actual MCP tool with logging
    log "DEBUG" "Calling mcp__claude-code-wrapper__claude_run"
    log "DEBUG" "Task: $TASK_DESCRIPTION"

    # Here we would normally call the MCP tool
    # For now, showing what would be logged
    echo "Would execute: mcp__claude-code-wrapper__claude_run with task"
    echo "All output would be captured to: $PHASE_EXEC_LOG"

    # Log post-execution state
    log "DEBUG" "Post-execution directory listing:"
    ls -la "$PROJECT_PATH" >> "$DEBUG_LOG" 2>&1 || true

    log "DEBUG" "Git diff after execution:"
    git diff --stat >> "$DEBUG_LOG" 2>&1 || true

    log "DEBUG" "New files created:"
    find "$PROJECT_PATH" -type f -newer "$SESSION_LOG" >> "$DEBUG_LOG" 2>&1 || true

    log "INFO" "Phase $PHASE execution complete"
    log "INFO" "Logs available at:"
    log "INFO" "  - Session: $SESSION_LOG"
    log "INFO" "  - Debug: $DEBUG_LOG"
    log "INFO" "  - Phase: $PHASE_EXEC_LOG"
}

# Main execution
if [ $# -lt 3 ]; then
    echo "Usage: $0 <phase> <project-path> <task-description>"
    exit 1
fi

PHASE=$1
PROJECT_PATH=$2
TASK_DESCRIPTION=$3

log "INFO" "SDLC Phase Executor Starting"
log "INFO" "Timestamp: $TIMESTAMP"
log "INFO" "Log Directory: $LOG_DIR"

# Verify project exists
if [ ! -d "$PROJECT_PATH" ]; then
    log "ERROR" "Project path does not exist: $PROJECT_PATH"
    exit 1
fi

# Execute the phase with full logging
execute_phase "$PHASE" "$PROJECT_PATH" "$TASK_DESCRIPTION"

echo -e "${GREEN}Phase execution complete. Check logs at:${NC}"
echo "  $LOG_DIR/"
