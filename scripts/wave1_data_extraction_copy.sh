#!/usr/bin/env bash
# wave1_data_extraction_copy.sh ── SAFE Wave-1: copy Neo4j & Chroma adapters into libs/opsvi-data
set -euo pipefail

ROOT="/home/opsvi/master_root"
BRANCH="feature/w1-opsvi-data-copy"
NEW_LIB_DIR="$ROOT/libs/opsvi-data"
PKG_DIR="$NEW_LIB_DIR/opsvi_data"

# 1) Branch
cd "$ROOT"
current_branch=$(git rev-parse --abbrev-ref HEAD || echo "")
if [[ "$current_branch" != "$BRANCH" ]]; then
  git checkout -b "$BRANCH"
fi

# 2) Scaffold
mkdir -p "$PKG_DIR"/{graph,vector,schemas,tests}

# pyproject.toml
cat > "$NEW_LIB_DIR/pyproject.toml" <<'EOF'
[tool.poetry]
name = "opsvi-data"
version = "0.1.0"
description = "Shared data clients (graph/vector) for OPSVI platform"
packages = [{ include = "opsvi_data" }]

[tool.poetry.dependencies]
python = ">=3.10,<4.0"
neo4j = "^5"
chromadb = "^0.5"
pydantic = "^2"
EOF

# __init__.py
cat > "$PKG_DIR/__init__.py" <<'EOF'
"""OPSVI Data Layer"""
from . import graph as graph  # re-export namespace
from . import vector as vector
EOF

# 3) Copy adapters from actual paths (non-destructive)
SRC_G_GRAPH="$ROOT/intake/custom/auto_forge/src/auto_forge/infrastructure/memory/graph"
SRC_G_VECTOR="$ROOT/intake/custom/auto_forge/src/auto_forge/infrastructure/memory/vector"
SRC_SKG_JSON="$ROOT/intake/custom/SKG_Cursor/src/skg/storage/json_storage.py"

# graph
if [[ -f "$SRC_G_GRAPH/client.py" ]]; then cp "$SRC_G_GRAPH/client.py" "$PKG_DIR/graph/"; fi
if [[ -f "$SRC_G_GRAPH/driver.py" ]]; then cp "$SRC_G_GRAPH/driver.py" "$PKG_DIR/graph/"; fi
if [[ -f "$SRC_G_GRAPH/queries.py" ]]; then cp "$SRC_G_GRAPH/queries.py" "$PKG_DIR/graph/"; fi

# vector
if [[ -f "$SRC_G_VECTOR/chroma_client.py" ]]; then cp "$SRC_G_VECTOR/chroma_client.py" "$PKG_DIR/vector/"; fi

# optional json storage
if [[ -f "$SRC_SKG_JSON" ]]; then cp "$SRC_SKG_JSON" "$PKG_DIR/graph/json_storage.py"; fi

# 4) Minimal smoke test
cat > "$PKG_DIR/tests/test_imports.py" <<'EOF'
import importlib

def test_import_graph_client_module():
    assert importlib.import_module('opsvi_data.graph.client')

def test_import_vector_chroma_module():
    assert importlib.import_module('opsvi_data.vector.chroma_client')
EOF

# 5) Add & commit (no push)
git add "$NEW_LIB_DIR"

git commit -m "feat(opsvi-data): copy Neo4j & Chroma adapters into new shared lib (wave1 safe copy)"

echo "✅ opsvi-data package created with copied adapters. Next: wire consumers to use opsvi_data.* and add real tests."
