#!/usr/bin/env python3
"""
ai_populate.py — AI-assisted file population planner for OPSVI libs.

- Scans for generated libraries and identifies stub files.
- Dry-run prints a plan; write mode can insert TODO scaffolds.
- Optional OpenAI integration is stubbed (no network calls by default).

Usage:
  python tools/ai_populate.py --libs-dir libs --dry-run
  python tools/ai_populate.py --libs-dir libs --only opsvi-core --write
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable

STUB_MARKER = "AUTO-GENERATED STUB"


def iter_library_packages(libs_dir: Path) -> Iterable[tuple[str, Path, Path]]:
    for lib_dir in sorted(p for p in libs_dir.iterdir() if p.is_dir()):
        pkg_name = lib_dir.name.replace("-", "_")
        pkg_dir = lib_dir / pkg_name
        if pkg_dir.exists():
            yield (lib_dir.name, lib_dir, pkg_dir)


def find_stubs(lib_dir: Path) -> list[Path]:
    stubs: list[Path] = []
    for path in lib_dir.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if STUB_MARKER in text:
            stubs.append(path)
    return stubs


def write_placeholder(path: Path) -> None:
    header = (
        "\n# TODO(ai): Populate implementation using contexts and templates.\n"
    )
    with path.open("a", encoding="utf-8") as f:
        f.write(header)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--libs-dir", default="libs")
    parser.add_argument("--only", nargs="*", default=None)
    parser.add_argument("--type", dest="only_type", nargs="*", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    libs_dir = Path(args.libs_dir)
    only = set(args.only or [])

    any_changes = False
    for lib_name, lib_dir, pkg_dir in iter_library_packages(libs_dir):
        if only and lib_name not in only:
            continue
        stubs = find_stubs(lib_dir)
        if not stubs:
            print(f"{lib_name}: no stubs found")
            continue
        print(f"{lib_name}: {len(stubs)} stub files")
        for s in stubs:
            print(f"  - {s.relative_to(lib_dir)}")
            if args.write and not args.dry_run:
                write_placeholder(s)
                any_changes = True

    if any_changes:
        print("WROTE placeholders to stub files.")
    else:
        print("No changes written.")

    # Note: OpenAI integration intentionally omitted to avoid secrets in CI.
    # Implement later with env OPENAI_API_KEY and approved models (e.g., gpt-5-mini).
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
