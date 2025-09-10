#!/bin/bash
# Chat Import Execution Wrapper
# Easy-to-use script for running chat import with background execution + monitoring

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎯 Chat Log PostgreSQL Import - Background Execution + Monitoring"
echo "=" * 80

# Check if arguments provided
if [ $# -eq 0 ]; then
    echo "Usage:"
    echo "  $0 --complete                    # Run all 3 phases with monitoring"
    echo "  $0 --phase 1                     # Run Phase 1 (Infrastructure) only"
    echo "  $0 --phase 2                     # Run Phase 2 (Processing) only"
    echo "  $0 --phase 3                     # Run Phase 3 (Production) only"
    echo "  $0 --validate                    # Validate system readiness only"
    echo ""
    echo "Examples:"
    echo "  $0 --complete                    # Most common - full import"
    echo "  $0 --phase 1                     # Infrastructure setup only"
    echo "  $0 --validate                    # Check if system is ready"
    echo ""
    echo "Features:"
    echo "  ✅ Background orchestrator execution (18 parallel agents)"
    echo "  ✅ Real-time monitoring in foreground"
    echo "  ✅ Comprehensive progress tracking"
    echo "  ✅ Graceful shutdown with Ctrl+C"
    echo ""
    exit 1
fi

# Parse arguments and pass to Python script
if [[ "$1" == "--validate" ]]; then
    echo "🔍 Running system validation only..."
    python3 run_chat_import_with_monitoring.py --validate-only
elif [[ "$1" == "--complete" ]]; then
    echo "🚀 Running complete chat import (all 3 phases)..."
    echo "📊 Orchestrator will run in background, monitoring in foreground"
    echo "⚠️  Press Ctrl+C to stop execution and monitoring"
    echo ""
    python3 run_chat_import_with_monitoring.py --complete
elif [[ "$1" == "--phase" && "$2" =~ ^[1-3]$ ]]; then
    echo "🚀 Running Phase $2 only..."
    echo "📊 Orchestrator will run in background, monitoring in foreground"
    echo "⚠️  Press Ctrl+C to stop execution and monitoring"
    echo ""
    python3 run_chat_import_with_monitoring.py --phase "$2"
else
    echo "❌ Invalid arguments. Use --help or no arguments to see usage."
    exit 1
fi
