#!/bin/bash
# Post-edit hook for Claude Code
# Formats/lints changed files based on the event payload from stdin when available.

set -euo pipefail

TMP_PAYLOAD="/tmp/claude_post_edit_payload.json"
PAYLOAD=""

# If stdin has JSON, capture it to a tmp file
if [ -t 0 ]; then
  : # no stdin
else
  cat > "$TMP_PAYLOAD" || true
  if [ -s "$TMP_PAYLOAD" ]; then
    PAYLOAD="$TMP_PAYLOAD"
  fi
fi

changed_files=()

# Prefer explicit file list from payload.tool_input.file_path or payload.changedFiles if present
if [ -n "${PAYLOAD}" ] && command -v jq >/dev/null 2>&1; then
  mapfile -t from_tool_input < <(jq -r '(.tool_input.file_path // empty) | select(length>0)' "$PAYLOAD" 2>/dev/null || true)
  mapfile -t from_changed < <(jq -r '.changedFiles[]? // empty' "$PAYLOAD" 2>/dev/null || true)
  changed_files+=("${from_tool_input[@]}" "${from_changed[@]}")
fi

# Fallback to first arg if provided
if [ ${#changed_files[@]} -eq 0 ] && [ "${1-}" != "" ]; then
  changed_files+=("$1")
fi

# If still empty, skip quietly
if [ ${#changed_files[@]} -eq 0 ]; then
  exit 0
fi

format_py() {
  local f="$1"
  if command -v ruff >/dev/null 2>&1; then ruff check --fix "$f" >/dev/null 2>&1 || true; fi
  if command -v black >/dev/null 2>&1; then black --quiet "$f" >/dev/null 2>&1 || true; fi
  if command -v mypy >/dev/null 2>&1; then mypy --pretty "$f" >/dev/null 2>&1 || true; fi
}

format_js_ts() {
  local f="$1"
  if command -v prettier >/dev/null 2>&1; then prettier --write "$f" >/dev/null 2>&1 || true; fi
  if command -v eslint >/dev/null 2>&1; then eslint --fix "$f" >/dev/null 2>&1 || true; fi
}

for file in "${changed_files[@]}"; do
  [ -f "$file" ] || continue
  case "$file" in
    *.py)
      format_py "$file"
      ;;
    *.js|*.jsx|*.ts|*.tsx)
      format_js_ts "$file"
      ;;
    *)
      :
      ;;
  esac
done

exit 0
