#!/bin/bash

# Background Process Monitor for GenFileMap
# This script helps monitor background processes and extract key information from logs

LOG_FILE="${1:-logs/test_background.log}"
PROCESS_NAME="${2:-genfilemap}"

echo "🔍 GenFileMap Background Process Monitor"
echo "📁 Log file: $LOG_FILE"
echo "🔄 Process: $PROCESS_NAME"
echo "⏰ Started at: $(date)"
echo "----------------------------------------"

# Function to check if process is still running
check_process() {
    if pgrep -f "$PROCESS_NAME" > /dev/null; then
        echo "✅ Process is running"
        return 0
    else
        echo "❌ Process has finished"
        return 1
    fi
}

# Function to get log file size and line count
log_stats() {
    if [[ -f "$LOG_FILE" ]]; then
        local size=$(du -h "$LOG_FILE" | cut -f1)
        local lines=$(wc -l < "$LOG_FILE")
        echo "📊 Log stats: $size, $lines lines"
    else
        echo "⚠️  Log file not found: $LOG_FILE"
    fi
}

# Function to extract key information from logs
analyze_logs() {
    if [[ ! -f "$LOG_FILE" ]]; then
        echo "⚠️  Log file not found for analysis"
        return 1
    fi

    echo ""
    echo "🔍 LOG ANALYSIS:"
    echo "----------------------------------------"

    # Count different types of debug messages
    echo "📈 Debug Message Counts:"
    grep -c "DEBUG-PROCESSOR" "$LOG_FILE" 2>/dev/null && echo "  - PROCESSOR: $(grep -c "DEBUG-PROCESSOR" "$LOG_FILE")" || echo "  - PROCESSOR: 0"
    grep -c "DEBUG-EXTRACT" "$LOG_FILE" 2>/dev/null && echo "  - EXTRACT: $(grep -c "DEBUG-EXTRACT" "$LOG_FILE")" || echo "  - EXTRACT: 0"
    grep -c "DEBUG-AST" "$LOG_FILE" 2>/dev/null && echo "  - AST: $(grep -c "DEBUG-AST" "$LOG_FILE")" || echo "  - AST: 0"
    grep -c "DEBUG-API" "$LOG_FILE" 2>/dev/null && echo "  - API: $(grep -c "DEBUG-API" "$LOG_FILE")" || echo "  - API: 0"
    grep -c "DEBUG-CODE" "$LOG_FILE" 2>/dev/null && echo "  - CODE: $(grep -c "DEBUG-CODE" "$LOG_FILE")" || echo "  - CODE: 0"

    # Check for errors
    echo ""
    echo "❌ Error Summary:"
    local error_count=$(grep -c "ERROR" "$LOG_FILE" 2>/dev/null || echo "0")
    echo "  - Total errors: $error_count"

    if [[ $error_count -gt 0 ]]; then
        echo "  - Recent errors:"
        grep "ERROR" "$LOG_FILE" | tail -3 | sed 's/^/    /'
    fi

    # Check for validation results
    echo ""
    echo "✅ Validation Summary:"
    local validation_count=$(grep -c "validation" "$LOG_FILE" 2>/dev/null || echo "0")
    echo "  - Validation mentions: $validation_count"

    if grep -q "AI validation" "$LOG_FILE" 2>/dev/null; then
        echo "  - AI validation results found"
        grep "AI validation" "$LOG_FILE" | tail -2 | sed 's/^/    /'
    fi

    # Check for completion indicators
    echo ""
    echo "🏁 Process Status:"
    if grep -q "Configuration loading complete" "$LOG_FILE" 2>/dev/null; then
        echo "  ✅ Configuration loaded"
    fi

    if grep -q "Starting GenFileMap process" "$LOG_FILE" 2>/dev/null; then
        echo "  ✅ Process started"
    fi

    if grep -q "Processed.*files" "$LOG_FILE" 2>/dev/null; then
        echo "  ✅ File processing completed"
        grep "Processed.*files" "$LOG_FILE" | tail -1 | sed 's/^/    /'
    fi
}

# Function to show recent log entries
show_recent() {
    local lines="${1:-10}"
    if [[ -f "$LOG_FILE" ]]; then
        echo ""
        echo "📝 Recent log entries (last $lines lines):"
        echo "----------------------------------------"
        tail -n "$lines" "$LOG_FILE"
    fi
}

# Function to search for specific patterns
search_logs() {
    local pattern="$1"
    if [[ -f "$LOG_FILE" && -n "$pattern" ]]; then
        echo ""
        echo "🔍 Search results for '$pattern':"
        echo "----------------------------------------"
        grep -n "$pattern" "$LOG_FILE" | head -10
    fi
}

# Main monitoring loop
main() {
    case "${3:-monitor}" in
        "analyze")
            analyze_logs
            ;;
        "recent")
            show_recent "${4:-20}"
            ;;
        "search")
            search_logs "$4"
            ;;
        "monitor")
            while true; do
                clear
                echo "🔍 GenFileMap Background Process Monitor"
                echo "📁 Log file: $LOG_FILE"
                echo "⏰ Current time: $(date)"
                echo "----------------------------------------"

                check_process
                log_stats

                if ! check_process; then
                    echo ""
                    echo "🏁 Process completed. Running final analysis..."
                    analyze_logs
                    break
                fi

                show_recent 5

                echo ""
                echo "⏳ Refreshing in 5 seconds... (Ctrl+C to stop)"
                sleep 5
            done
            ;;
        *)
            echo "Usage: $0 [log_file] [process_name] [command] [args]"
            echo "Commands:"
            echo "  monitor  - Real-time monitoring (default)"
            echo "  analyze  - Analyze completed logs"
            echo "  recent   - Show recent log entries"
            echo "  search   - Search for pattern in logs"
            ;;
    esac
}

main "$@"