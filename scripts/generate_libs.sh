#!/usr/bin/env bash
set -euo pipefail

ts() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
SANDBOX_DIR="${ROOT_DIR}/_gen_sandbox"

echo "[$(ts)] generate_libs: start ROOT_DIR=${ROOT_DIR}"

mkdir -p "${SANDBOX_DIR}"
echo "[$(ts)] generate_libs: sandbox at ${SANDBOX_DIR}"
cp "${ROOT_DIR}/libs/recommended_structure.yaml" "${SANDBOX_DIR}/"
cp "${ROOT_DIR}/libs/templates.yaml" "${SANDBOX_DIR}/"
cp "${ROOT_DIR}/libs/file_manifest.yaml" "${SANDBOX_DIR}/"
echo "[$(ts)] generate_libs: copied configs to sandbox"

echo "[$(ts)] generate_libs: invoking generator"
python3 "${ROOT_DIR}/libs/generate_ecosystem_v2.py" \
  --libs-dir "${SANDBOX_DIR}" \
  --file-manifest "${SANDBOX_DIR}/file_manifest.yaml" "$@"
status=$?
echo "[$(ts)] generate_libs: generator exit=${status}"
if [ $status -ne 0 ]; then
  echo "[$(ts)] generate_libs: failed; see ${SANDBOX_DIR} for copies of configs and ${SANDBOX_DIR}/templates.yaml"
fi
exit ${status}
