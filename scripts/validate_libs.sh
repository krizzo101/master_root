#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)

python3 "${ROOT_DIR}/tools/libs_check.py"
"${ROOT_DIR}/scripts/generate_libs.sh" --no-touch-missing

ruff check "${ROOT_DIR}/libs/generate_ecosystem_v2.py"
black --check "${ROOT_DIR}/libs/generate_ecosystem_v2.py"
mypy --python-version 3.12 "${ROOT_DIR}/libs/generate_ecosystem_v2.py"

# AI populator dry-run
python3 "${ROOT_DIR}/tools/ai_populate.py" --libs-dir "${ROOT_DIR}/_gen_sandbox" --dry-run

# Import smoke test for generated libs
python3 - << 'PY'
import sys, os, pathlib, importlib
root = pathlib.Path('.').resolve()
sandbox = root / '_gen_sandbox'
failures = []
for lib_dir in sorted(p for p in sandbox.iterdir() if p.is_dir()):
    pkg = lib_dir.name.replace('-', '_')
    pkg_path = lib_dir / pkg
    if not pkg_path.exists():
        continue
    sys.path.insert(0, str(lib_dir))
    try:
        importlib.import_module(pkg)
        importlib.import_module(f"{pkg}.config.settings")
        importlib.import_module(f"{pkg}.core.base")
        importlib.import_module(f"{pkg}.exceptions.base")
    except Exception as e:  # noqa: BLE001
        failures.append((lib_dir.name, str(e)))
    finally:
        sys.path.pop(0)
if failures:
    print('Import smoke failures:')
    for name, err in failures:
        print(f"  - {name}: {err}")
    raise SystemExit(1)
print('Import smoke OK for generated libs')
PY

