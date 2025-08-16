#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
SANDBOX_DIR="${ROOT_DIR}/_gen_sandbox"

mkdir -p "${SANDBOX_DIR}"
cp "${ROOT_DIR}/libs/recommended_structure.yaml" "${SANDBOX_DIR}/"
cp "${ROOT_DIR}/libs/templates.yaml" "${SANDBOX_DIR}/"
cp "${ROOT_DIR}/libs/file_manifest.yaml" "${SANDBOX_DIR}/"

python3 "${ROOT_DIR}/libs/generate_ecosystem_v2.py" \
  --libs-dir "${SANDBOX_DIR}" \
  --file-manifest "${SANDBOX_DIR}/file_manifest.yaml" \
  --dry-run --diff "$@"

