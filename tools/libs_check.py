#!/usr/bin/env python3
"""
libs_check.py — Validate that all template references in structure and manifest
exist in the YAML template registry. Report missing/unused keys with actionable hints.

Exit codes:
 0 = OK
 2 = Missing template references
 3 = YAML load error or unexpected failure
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: Failed to load YAML: {path} — {e}")
        raise e from None


def collect_registry_keys(templates: dict) -> set[str]:
    keys: set[str] = set()

    def walk(d: Any, prefix: str = "") -> None:
        if isinstance(d, dict):
            if "template" in d and isinstance(d["template"], str):
                # template leaf — do not add the leaf value to keys
                pass
            for k, v in d.items():
                # Only collect under file_templates.* namespaces as short keys
                if (
                    prefix.startswith("file_templates.")
                    and isinstance(v, dict)
                    and "template" in v
                ):
                    keys.add(k)
                walk(v, f"{prefix}.{k}" if prefix else k)

    walk(templates)
    return keys


def extract_template_ref(ref: Any) -> str | None:
    if isinstance(ref, str):
        if ref.startswith("*"):
            # Anchors should be resolved when YAML is loaded; ignore raw star refs
            return None
        return ref
    if isinstance(ref, dict):
        t = ref.get("template")
        if isinstance(t, str):
            return t
    return None


def collect_structure_refs(structure: dict, manifest: dict) -> set[str]:
    refs: set[str] = set()

    # From structure libraries
    for _lib, data in (structure.get("libraries") or {}).items():
        for fi in data.get("files") or []:
            t = extract_template_ref(fi.get("template"))
            if t:
                refs.add(t)

    # From manifest library_types and libraries
    for section in (manifest.get("library_types") or {}).values():
        for fi in section.get("files") or []:
            t = extract_template_ref(fi.get("template"))
            if t:
                refs.add(t)
    for section in (manifest.get("libraries") or {}).values():
        for fi in section.get("files") or []:
            t = extract_template_ref(fi.get("template"))
            if t:
                refs.add(t)
    return refs


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    libs_dir = repo / "libs"

    structure = load_yaml(libs_dir / "recommended_structure.yaml")
    templates = load_yaml(libs_dir / "templates.yaml")
    manifest = load_yaml(libs_dir / "file_manifest.yaml")

    registry_keys = collect_registry_keys(templates)
    refs = collect_structure_refs(structure, manifest)

    missing = sorted({r for r in refs if r not in registry_keys})
    # Optionally identify unused registry keys (not referenced)
    unused = sorted({k for k in registry_keys if k not in refs})

    if missing:
        print("ERROR: Missing template keys in registry:")
        for m in missing:
            print(f"  - {m}")
        print(
            "\nHint: Add these keys under file_templates.python_files/config_files/documentation_files in libs/templates.yaml,"
        )
        print(
            "      or correct typos in libs/recommended_structure.yaml or libs/file_manifest.yaml."
        )
        return 2

    print("OK: All referenced templates exist in the registry.")
    if unused:
        print("Note: Unused registry keys:")
        for u in unused:
            print(f"  - {u}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit(3)
