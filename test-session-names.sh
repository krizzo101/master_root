#!/bin/bash

# Test script to show what session names look like now

CHAT_LOGS_DIR="/home/opsvi/.claude/projects/-home-opsvi-master-root"

echo "🎯 Current Session Names (with summaries):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get recent sessions with improved names
get_recent_sessions() {
    local sessions=()
    local current_time=$(date +%s)

    while IFS= read -r -d '' filepath; do
        local last_modified=$(stat -c %Y "$filepath" 2>/dev/null || echo 0)
        local age=$((current_time - last_modified))

        if [[ $age -lt 14400 ]]; then  # 4 hours
            local session_id=$(basename "$filepath" .jsonl)

            # Get latest summary from session
            local summary=$(jq -r 'select(.type=="summary") | .summary' "$filepath" 2>/dev/null | tail -1)
            if [[ -z "$summary" || "$summary" == "null" ]]; then
                summary="No summary available"
            fi

            # Truncate summary if too long
            if [[ ${#summary} -gt 50 ]]; then
                summary="${summary:0:47}..."
            fi

            # Get branch info
            local branch=$(tail -n 3 "$filepath" 2>/dev/null | jq -r 'select(.gitBranch) | .gitBranch' 2>/dev/null | tail -n 1 || echo "")

            local display_name="${session_id:0:8}: $summary"
            [[ -n "$branch" ]] && display_name="$display_name [$branch]"

            sessions+=("$session_id|$filepath|$display_name")
        fi
    done < <(find "$CHAT_LOGS_DIR" -name "*.jsonl" -type f -print0 2>/dev/null)

    printf '%s\n' "${sessions[@]}" | sort -t'|' -k3
}

available_sessions=($(get_recent_sessions))

if [[ ${#available_sessions[@]} -eq 0 ]]; then
    echo "❌ No active sessions found"
else
    for i in "${!available_sessions[@]}"; do
        IFS='|' read -r session_id filepath display_name <<< "${available_sessions[$i]}"
        echo "  $((i+1)). $display_name"
    done
fi
