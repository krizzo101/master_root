#!/usr/bin/env python3
"""
Scaffold libs/ for open-source code generation toolchains.

This script prepares standard directories and config templates for:
- OpenAPI (clients in Python/TypeScript)
- AsyncAPI (docs/stubs)
- Protobuf via Buf (multi-language)
- JSON Schema → models (Pydantic) generators

Usage examples:
  python scripts/scaffold_libs_codegen.py --dry-run
  python scripts/scaffold_libs_codegen.py --yes --libs opsvi-http opsvi-gateway

Idempotent: existing files are preserved (won't overwrite by default).
Use --force to overwrite template files if needed.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
LIBS_DIR = REPO_ROOT / "libs"


@dataclass
class WritePlan:
    path: Path
    content: str
    mode: str = "text"  # only text supported; kept for future extension
    overwrite: bool = False


def _print(msg: str) -> None:
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def plan_write(path: Path, content: str, overwrite: bool = False) -> Optional[WritePlan]:
    if path.exists() and not overwrite:
        return None
    return WritePlan(path=path, content=content, overwrite=overwrite)


def default_openapi_config() -> str:
    cfg = {
        "packageName": "generated_client",
        "projectName": "generated-client",
        "enumPropertyNaming": "original",
        "useSingleRequestParameter": True,
        "hideGenerationTimestamp": True,
    }
    return json.dumps(cfg, indent=2) + "\n"


def default_buf_yaml(module_name: str) -> str:
    return (
        "version: v1\n"
        f"name: buf.build/opsvi/{module_name}\n"
        "breaking:\n  use:\n    - FILE\n"  # conservative defaults
        "lint:\n  use:\n    - DEFAULT\n"
    )


def default_buf_gen_yaml() -> str:
    return (
        "version: v1\n"
        "plugins:\n"
        "  - name: python\n    out: gen/python\n"
        "  - name: go\n    out: gen/go\n"
    )


def default_asyncapi_spec() -> str:
    return (
        "asyncapi: '2.6.0'\n"
        "info:\n  title: Placeholder AsyncAPI\n  version: 0.1.0\n"
        "defaultContentType: application/json\n"
        "channels: {}\n"
    )


def default_openapi_spec() -> str:
    return (
        "openapi: 3.0.3\n"
        "info:\n  title: Placeholder API\n  version: 0.1.0\n"
        "paths: {}\n"
    )


def default_codegen_md(tooling: Sequence[str]) -> str:
    lines = [
        "# Code Generation\n",
        "\n",
        "This library is scaffolded for the following toolchains:\n",
    ]
    for t in tooling:
        lines.append(f"- {t}\n")
    lines.extend(
        [
            "\n",
            "## Suggested commands\n",
            "- OpenAPI (python client): `openapi-python-client generate --path openapi/openapi.yaml --output clients/python`\n",
            "- OpenAPI (ts client): `openapi-generator-cli generate -i openapi/openapi.yaml -g typescript-fetch -o clients/ts`\n",
            "- Buf (protobuf): `buf generate` (run from this lib directory)\n",
            "- datamodel-codegen: `datamodel-codegen --input schemas/schema.json --output gen/models.py`\n",
        ]
    )
    return "".join(lines)


def scaffold_http(lib_dir: Path, force: bool) -> List[WritePlan]:
    plans: List[WritePlan] = []
    # dirs
    for d in [
        lib_dir / "openapi",
        lib_dir / "clients" / "python",
        lib_dir / "clients" / "ts",
    ]:
        ensure_dir(d)
    # files
    openapi_yaml = plan_write(lib_dir / "openapi" / "openapi.yaml", default_openapi_spec(), overwrite=force)
    if openapi_yaml:
        plans.append(openapi_yaml)
    cfg = plan_write(lib_dir / ".openapi-config.json", default_openapi_config(), overwrite=force)
    if cfg:
        plans.append(cfg)
    readme = plan_write(lib_dir / "CODEGEN.md", default_codegen_md(["OpenAPI (python, ts)"]), overwrite=False)
    if readme:
        plans.append(readme)
    # .gitkeep in empty client dirs
    for keep_dir in [lib_dir / "clients" / "python", lib_dir / "clients" / "ts"]:
        keep = plan_write(keep_dir / ".gitkeep", "", overwrite=force)
        if keep:
            plans.append(keep)
    return plans


def scaffold_gateway(lib_dir: Path, force: bool) -> List[WritePlan]:
    # same as HTTP; gateway often aggregates OpenAPI
    return scaffold_http(lib_dir, force)


def scaffold_communication(lib_dir: Path, force: bool) -> List[WritePlan]:
    plans: List[WritePlan] = []
    # dirs
    for d in [
        lib_dir / "proto",
        lib_dir / "gen" / "python",
        lib_dir / "gen" / "go",
        lib_dir / "asyncapi",
    ]:
        ensure_dir(d)
    # files
    buf_yaml = plan_write(lib_dir / "buf.yaml", default_buf_yaml(lib_dir.name), overwrite=force)
    if buf_yaml:
        plans.append(buf_yaml)
    buf_gen = plan_write(lib_dir / "buf.gen.yaml", default_buf_gen_yaml(), overwrite=force)
    if buf_gen:
        plans.append(buf_gen)
    asyncapi_spec = plan_write(lib_dir / "asyncapi" / "spec.yaml", default_asyncapi_spec(), overwrite=force)
    if asyncapi_spec:
        plans.append(asyncapi_spec)
    # placeholder proto
    proto = plan_write(
        lib_dir / "proto" / "placeholder.proto",
        "syntax = \"proto3\";\npackage opsvi.communication;\nmessage Placeholder { string id = 1; }\n",
        overwrite=False,
    )
    if proto:
        plans.append(proto)
    readme = plan_write(lib_dir / "CODEGEN.md", default_codegen_md(["Buf (protobuf)", "AsyncAPI"]), overwrite=False)
    if readme:
        plans.append(readme)
    # .gitkeep for gen dirs
    for keep_dir in [lib_dir / "gen" / "python", lib_dir / "gen" / "go"]:
        keep = plan_write(keep_dir / ".gitkeep", "", overwrite=force)
        if keep:
            plans.append(keep)
    return plans


def scaffold_schema_models(lib_dir: Path, force: bool, include_quicktype_md: bool = False) -> List[WritePlan]:
    plans: List[WritePlan] = []
    # dirs
    for d in [lib_dir / "schemas", lib_dir / "gen"]:
        ensure_dir(d)
    # files
    schema = plan_write(lib_dir / "schemas" / "schema.json", "{}\n", overwrite=False)
    if schema:
        plans.append(schema)
    readme = plan_write(
        lib_dir / "CODEGEN.md",
        default_codegen_md(["datamodel-code-generator" + (", quicktype" if include_quicktype_md else "")]),
        overwrite=False,
    )
    if readme:
        plans.append(readme)
    keep = plan_write(lib_dir / "gen" / ".gitkeep", "", overwrite=force)
    if keep:
        plans.append(keep)
    return plans


def make_plans(target_libs: Sequence[str], force: bool) -> Dict[Path, List[WritePlan]]:
    plans_by_lib: Dict[Path, List[WritePlan]] = {}
    for name in target_libs:
        lib_dir = LIBS_DIR / name
        if not lib_dir.exists():
            _print(f"[WARN] Skipping '{name}': {lib_dir} does not exist")
            continue
        lib_plans: List[WritePlan] = []
        if name in {"opsvi-http", "opsvi-gateway"}:
            lib_plans.extend(scaffold_http(lib_dir, force))
        if name == "opsvi-communication":
            lib_plans.extend(scaffold_communication(lib_dir, force))
        if name in {"opsvi-data", "opsvi-rag", "opsvi-llm"}:
            lib_plans.extend(scaffold_schema_models(lib_dir, force, include_quicktype_md=(name in {"opsvi-rag", "opsvi-llm"})))
        # Always ensure presence of top-level gen/ and schemas/ if applicable
        plans_by_lib[lib_dir] = lib_plans
    return plans_by_lib


def apply_plans(plans_by_lib: Dict[Path, List[WritePlan]], dry_run: bool) -> None:
    total_files = 0
    for lib_dir, plans in plans_by_lib.items():
        if not plans:
            _print(f"[INFO] {lib_dir.name}: nothing to do (already scaffolded)")
            continue
        _print(f"[INFO] {lib_dir.name}: {len(plans)} file(s) to write")
        for plan in plans:
            total_files += 1
            rel = plan.path.relative_to(REPO_ROOT)
            if dry_run:
                _print(f"  DRY-RUN write -> {rel}")
                continue
            plan.path.parent.mkdir(parents=True, exist_ok=True)
            plan.path.write_text(plan.content, encoding="utf-8")
            _print(f"  wrote {rel}")
    _print(f"[DONE] {'planned' if dry_run else 'created'} {total_files} file(s)")


def detect_default_libs() -> List[str]:
    # Limit to known libraries where codegen makes sense
    candidates = [
        "opsvi-http",
        "opsvi-gateway",
        "opsvi-communication",
        "opsvi-data",
        "opsvi-rag",
        "opsvi-llm",
    ]
    return [c for c in candidates if (LIBS_DIR / c).exists()]


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scaffold libs/ for code generation toolchains")
    parser.add_argument(
        "--libs",
        nargs="*",
        help="Subset of libs to scaffold (default: autodetect opsvi-*)",
    )
    parser.add_argument("--yes", action="store_true", help="Apply changes (default: dry-run)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing template files")
    parser.add_argument("--root", type=str, default=str(REPO_ROOT), help="Repository root (auto-detected)")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if root != REPO_ROOT:
        _print(f"[WARN] Using overridden root: {root}")
    if not (root / "libs").exists():
        _print(f"[ERROR] libs/ not found under {root}")
        return 2

    target_libs = args.libs or detect_default_libs()
    if not target_libs:
        _print("[ERROR] No target libs detected; specify with --libs")
        return 2

    _print(f"Root: {root}")
    _print(f"Libs: {', '.join(target_libs)}")
    plans_by_lib = make_plans(target_libs, force=args.force)
    apply_plans(plans_by_lib, dry_run=not args.yes)
    if not args.yes:
        _print("[HINT] Re-run with --yes to apply changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
