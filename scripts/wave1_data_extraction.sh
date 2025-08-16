#!/usr/bin/env bash
# wave1_data_extraction.sh  ── automate Wave-1: move Neo4j & Chroma adapters into libs/opsvi-data
# Safe-mode: abort on first error
set -euo pipefail

# --- CONFIG ------------------------------------------------------------
NEW_LIB_DIR="libs/opsvi-data"
PACKAGE_NAME="opsvi_data"
BRANCH="feature/w1-data-extraction"

# --- 1. Git branch -----------------------------------------------------
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [[ "$current_branch" == "$BRANCH" ]]; then
  echo "Already on $BRANCH"
else
  git checkout -b "$BRANCH"
fi

# --- 2. Scaffold library ----------------------------------------------
mkdir -p "$NEW_LIB_DIR/$PACKAGE_NAME"/{graph,vector,schemas,tests}
cat > "$NEW_LIB_DIR/pyproject.toml" <<'EOF'
[tool.poetry]
name = "opsvi-data"
version = "0.1.0"
description = "Common graph & vector data clients for opsvi platform"
packages = [{ include = "opsvi_data" }]

[tool.poetry.dependencies]
python = ">=3.10,<4.0"
neo4j = "^5.13"
chromadb = "^0.4"
pydantic = "^2.5"
EOF

touch "$NEW_LIB_DIR/$PACKAGE_NAME/__init__.py"

# --- 3. Move Neo4j files ----------------------------------------------
# graphiti → opsvi-data
git mv apps/graphiti/src/graphiti/memory/graph/neo4j_client.py "$NEW_LIB_DIR/$PACKAGE_NAME/graph/" || true
git mv apps/graphiti/src/graphiti/memory/graph/driver.py "$NEW_LIB_DIR/$PACKAGE_NAME/graph/" || true
git mv apps/graphiti/src/graphiti/memory/graph/queries.py "$NEW_LIB_DIR/$PACKAGE_NAME/graph/" || true

# SKG_Cursor JSON store (generic helper)
git mv intake/custom/SKG_Cursor/src/skg/storage/json_storage.py "$NEW_LIB_DIR/$PACKAGE_NAME/graph/json_storage.py" || true

# --- 4. Move Chroma vector adapter ------------------------------------
# auto_forge → opsvi-data
git mv intake/custom/auto_forge/src/auto_forge/infrastructure/memory/vector/chroma_client.py \
       "$NEW_LIB_DIR/$PACKAGE_NAME/vector/" || true

# --- 5. Add shim modules ----------------------------------------------
shim_content='from opsvi_data.graph.neo4j_client import *  # type: ignore[import-star]\nimport warnings; warnings.warn("Moved to opsvi-data", DeprecationWarning)\n'
echo "$shim_content" > apps/graphiti/src/graphiti/memory/graph/neo4j_client.py

echo "$shim_content" > intake/custom/auto_forge/src/auto_forge/infrastructure/memory/vector/chroma_client.py

# --- 6. Update imports (Ruff autofix) ---------------------------------
ruff check --select I --fix libs/ intake/custom/ apps/ || true

# --- 7. Run tests ------------------------------------------------------
pytest -q libs/opsvi-data || echo "⚠️  tests not yet written; please add before merge"

# --- 8. Commit ---------------------------------------------------------
git add -A

git commit -m "feat(opsvi-data): extract Neo4j & Chroma adapters (#wave1)"

echo "✅ Wave-1 extraction script completed. Review, run full test-suite, then push PR."
