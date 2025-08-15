#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/home/opsvi/master_root/apps/proj-mapper"
SRC_DIR="$PROJECT_ROOT/src"
MAPS_DIR="$SRC_DIR/.maps"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python3"

# Prefer venv python; fallback to system python
if [[ -x "$PYTHON_BIN" ]]; then
  PY="$PYTHON_BIN"
else
  PY="python3"
fi

echo "[1/4] Analyzing project: $SRC_DIR"
PYTHONPATH="$SRC_DIR" "$PY" "$SRC_DIR/proj_mapper/cli/main.py" analyze "$SRC_DIR"

mkdir -p "$MAPS_DIR"

DOT_OUT="$MAPS_DIR/smoke_visualization.dot"
HTML_OUT="$MAPS_DIR/smoke_visualization.html"

echo "[2/4] Generating DOT visualization -> $DOT_OUT"
PYTHONPATH="$SRC_DIR" "$PY" "$SRC_DIR/proj_mapper/cli/main.py" visualize "$SRC_DIR" -f dot -o "$DOT_OUT"

if [[ ! -f "$DOT_OUT" ]]; then
  echo "ERROR: DOT visualization not found at $DOT_OUT" >&2
  exit 1
fi

echo "[3/4] Generating HTML visualization -> $HTML_OUT"
PYTHONPATH="$SRC_DIR" "$PY" "$SRC_DIR/proj_mapper/cli/main.py" visualize "$SRC_DIR" -f html -o "$HTML_OUT"

if [[ ! -f "$HTML_OUT" ]]; then
  echo "ERROR: HTML visualization not found at $HTML_OUT" >&2
  exit 1
fi

ls -lh "$DOT_OUT" "$HTML_OUT" || true

echo "[4/4] Smoke test completed successfully."
