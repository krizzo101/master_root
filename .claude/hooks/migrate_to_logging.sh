#!/bin/bash
# Migration script to enable comprehensive logging in answer_review.py

set -e

HOOKS_DIR="$(dirname "$0")"
BACKUP_DIR="${HOOKS_DIR}/backups/$(date +%Y%m%d_%H%M%S)"

echo "=== Answer Review Logging Migration ==="
echo "This script will:"
echo "1. Backup the current answer_review.py"
echo "2. Replace it with the logging-enabled version"
echo "3. Set up log directories"
echo "4. Configure environment variables"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup current files
echo "Creating backups in $BACKUP_DIR..."
cp -p "${HOOKS_DIR}/answer_review.py" "${BACKUP_DIR}/answer_review.py.bak" 2>/dev/null || true
cp -p "${HOOKS_DIR}/answer_review_wrapper.sh" "${BACKUP_DIR}/answer_review_wrapper.sh.bak" 2>/dev/null || true

# Replace with logging version
echo "Installing logging-enabled version..."
cp "${HOOKS_DIR}/answer_review_with_logging.py" "${HOOKS_DIR}/answer_review.py"
chmod +x "${HOOKS_DIR}/answer_review.py"

# Make analysis script executable
chmod +x "${HOOKS_DIR}/analyze_review_logs.py"

# Create log directories
echo "Setting up log directories..."
LOG_DIR="${HOOKS_DIR}/logs"
mkdir -p "${LOG_DIR}/audit"
mkdir -p "${LOG_DIR}/operational"
mkdir -p "${LOG_DIR}/metrics"

# Create environment config if it doesn't exist
ENV_FILE="${HOOKS_DIR}/.review_logging.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating environment configuration..."
    cat > "$ENV_FILE" << 'EOF'
# Review Logging Configuration
export REVIEW_LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
export ENABLE_API_AUDIT="false"  # Set to true to log API calls
export DEBUG=""  # Set to any value to enable console debug output

# Add to your shell profile or wrapper script:
# source /path/to/.claude/hooks/.review_logging.env
EOF
    echo "Environment config created at: $ENV_FILE"
fi

echo ""
echo "=== Migration Complete ==="
echo ""
echo "Log directories created at: $LOG_DIR"
echo "Backups saved at: $BACKUP_DIR"
echo ""
echo "To analyze logs, run:"
echo "  python ${HOOKS_DIR}/analyze_review_logs.py"
echo ""
echo "To view real-time logs:"
echo "  tail -f ${LOG_DIR}/operational/answer_review_*.log | jq ."
echo ""
echo "To enable debug output:"
echo "  export DEBUG=1"
echo ""
echo "To rollback if needed:"
echo "  cp ${BACKUP_DIR}/answer_review.py.bak ${HOOKS_DIR}/answer_review.py"