#!/bin/bash
# Post-edit hook for Claude Code
# Add your formatting/linting commands here

# Example: Format Python files
# if [[ "$1" == *.py ]]; then
#     black "$1" 2>/dev/null || true
#     ruff check "$1" 2>/dev/null || true
# fi

# Example: Format JavaScript/TypeScript
# if [[ "$1" == *.js ]] || [[ "$1" == *.ts ]]; then
#     prettier --write "$1" 2>/dev/null || true
# fi

exit 0
