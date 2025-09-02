#!/bin/bash
# Convenient viewer for prompt optimization logs

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOGGER="$SCRIPT_DIR/prompt_opt_logger.py"
LOG_DIR="$SCRIPT_DIR/logs/prompt_opt"

show_help() {
    echo "Prompt Optimization Log Viewer"
    echo "=============================="
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  stats    - Show optimization statistics"
    echo "  tail     - Show last 10 log entries"
    echo "  today    - Show all of today's entries"
    echo "  watch    - Live tail of logs (updates every 2s)"
    echo "  clear    - Clear today's logs"
    echo "  help     - Show this help"
    echo ""
    echo "Log location: $LOG_DIR"
}

case "$1" in
    stats)
        /home/opsvi/miniconda/bin/python "$LOGGER" stats
        ;;
    tail)
        /home/opsvi/miniconda/bin/python "$LOGGER" tail
        ;;
    today)
        TODAY=$(date +%Y%m%d)
        LOG_FILE="$LOG_DIR/prompt_opt_${TODAY}.jsonl"
        if [ -f "$LOG_FILE" ]; then
            echo "Today's prompt optimization log entries:"
            echo "========================================"
            cat "$LOG_FILE" | jq -r '"\(.timestamp) | \(.event) | \(.data | tostring | .[0:100])"'
        else
            echo "No logs for today yet."
        fi
        ;;
    watch)
        echo "Watching prompt optimization logs (Ctrl+C to stop)..."
        watch -n 2 "/home/opsvi/miniconda/bin/python '$LOGGER' tail"
        ;;
    clear)
        TODAY=$(date +%Y%m%d)
        LOG_FILE="$LOG_DIR/prompt_opt_${TODAY}.jsonl"
        if [ -f "$LOG_FILE" ]; then
            echo "Clearing today's logs..."
            > "$LOG_FILE"
            echo "Logs cleared."
        else
            echo "No logs to clear."
        fi
        ;;
    help|"")
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
