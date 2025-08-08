#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)

python3 "${ROOT_DIR}/tools/libs_check.py"
"${ROOT_DIR}/scripts/generate_libs.sh" --no-touch-missing

ruff check "${ROOT_DIR}/libs/generate_ecosystem_v2.py"
black --check "${ROOT_DIR}/libs/generate_ecosystem_v2.py"
mypy --python-version 3.12 "${ROOT_DIR}/libs/generate_ecosystem_v2.py"

