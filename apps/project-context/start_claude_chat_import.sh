#!/bin/bash

# Claude Chat Import Starter Script
# Comprehensive chat log import with monitoring and error handling

set -e  # Exit on error

echo "🚀 Claude Chat Import - Unified Context System"
echo "=" $(printf '%.0s' {1..50})

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="claude_chat_import_$(date +%Y%m%d_%H%M%S).log"
CONFIG_FILE="config/claude_chat_import_config.yaml"

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check if Python script exists
if [[ ! -f "$SCRIPT_DIR/execute_claude_chat_import.py" ]]; then
    echo "❌ Error: execute_claude_chat_import.py not found"
    exit 1
fi

# Check if configuration exists
if [[ ! -f "$SCRIPT_DIR/$CONFIG_FILE" ]]; then
    echo "❌ Error: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Check if data directory exists
if [[ ! -d "/home/opsvi/.claude/projects" ]]; then
    echo "❌ Error: Claude projects directory not found: /home/opsvi/.claude/projects"
    exit 1
fi

# Check Python environment
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    exit 1
fi

# Check database connectivity
echo "🔌 Checking database connection..."
if ! python3 -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context')
    conn.close()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
" 2>/dev/null; then
    echo "❌ Error: Cannot connect to database"
    exit 1
fi

# Check disk space (require at least 5GB free)
echo "💾 Checking disk space..."
AVAILABLE_SPACE=$(df "$SCRIPT_DIR" | tail -1 | awk '{print $4}')
REQUIRED_SPACE=5242880  # 5GB in KB

if [[ $AVAILABLE_SPACE -lt $REQUIRED_SPACE ]]; then
    echo "❌ Error: Insufficient disk space. Available: $(($AVAILABLE_SPACE/1024/1024))GB, Required: 5GB"
    exit 1
fi

echo "💾 Disk space OK: $(($AVAILABLE_SPACE/1024/1024))GB available"

# Memory check (recommend at least 6GB)
echo "🧠 Checking system memory..."
AVAILABLE_MEMORY=$(free -m | awk 'NR==2{print $7}')
RECOMMENDED_MEMORY=6144  # 6GB in MB

if [[ $AVAILABLE_MEMORY -lt $RECOMMENDED_MEMORY ]]; then
    echo "⚠️  Warning: Low available memory. Available: ${AVAILABLE_MEMORY}MB, Recommended: 6GB"
    echo "   Import may be slower or fail due to memory constraints."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "🧠 Memory OK: ${AVAILABLE_MEMORY}MB available"
fi

# Show import summary
echo ""
echo "📋 Import Summary:"
echo "   • Source: /home/opsvi/.claude/projects"
echo "   • Estimated files: ~1,700 JSONL files"
echo "   • Estimated data: ~691MB"
echo "   • Configuration: $CONFIG_FILE"
echo "   • Log file: $LOG_FILE"
echo ""

# Confirm execution
read -p "🎯 Start Claude chat import? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Import cancelled by user"
    exit 0
fi

# Start import process
echo ""
echo "🔥 Starting import process..."
echo "📝 Logs will be written to: $LOG_FILE"
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the import with comprehensive logging
cd "$SCRIPT_DIR"

# Start background monitoring (if available)
if command -v htop &> /dev/null; then
    echo "🔍 Starting system monitoring in background..."
    htop -d 30 > /dev/null 2>&1 &
    HTOP_PID=$!

    # Function to cleanup on exit
    cleanup() {
        if [[ -n $HTOP_PID ]]; then
            kill $HTOP_PID 2>/dev/null || true
        fi
    }
    trap cleanup EXIT
fi

# Execute the import
START_TIME=$(date +%s)

if python3 execute_claude_chat_import.py 2>&1 | tee "logs/$LOG_FILE"; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    HOURS=$((DURATION / 3600))
    MINUTES=$(((DURATION % 3600) / 60))
    SECONDS=$((DURATION % 60))

    echo ""
    echo "🎉 Import completed successfully!"
    echo "⏱️  Total time: ${HOURS}h ${MINUTES}m ${SECONDS}s"
    echo "📄 Full log: logs/$LOG_FILE"

    # Show summary files created
    echo ""
    echo "📊 Generated files:"
    find . -name "claude_chat_import_summary_*.json" -newer logs/$LOG_FILE 2>/dev/null | head -5 | while read file; do
        echo "   • $file"
    done

    echo ""
    echo "✨ Next steps:"
    echo "   1. Review the import summary JSON file"
    echo "   2. Validate data quality with sample queries"
    echo "   3. Test semantic search functionality"
    echo "   4. Configure MCP integration"

else
    echo ""
    echo "❌ Import failed!"
    echo "📄 Check logs: logs/$LOG_FILE"
    echo "🔧 Troubleshooting:"
    echo "   1. Verify database connection"
    echo "   2. Check disk space and memory"
    echo "   3. Review error messages in log file"
    echo "   4. Consider reducing batch size in configuration"
    exit 1
fi
