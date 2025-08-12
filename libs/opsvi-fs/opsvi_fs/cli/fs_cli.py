#!/usr/bin/env python3
"""Minimal CLI for opsvi-fs health/stat/ls."""
from __future__ import annotations

import argparse

from ..config.settings import LibrarySettings
from ..providers.local_adapter import LocalStorageProvider
from ..schemas.models import FileLocation


def main() -> int:
    ap = argparse.ArgumentParser(prog="opsvi-fs")
    ap.add_argument("command", choices=["health", "stat", "ls"])
    ap.add_argument("path", nargs="?", default=".")
    args = ap.parse_args()

    cfg = LibrarySettings()
    # For now: local provider only
    fs = LocalStorageProvider(root=cfg.fs_root)

    if args.command == "health":
        print("healthy" if fs.health_check() else "unhealthy")
        return 0
    loc = FileLocation(path=args.path)
    if args.command == "stat":
        st = fs.stat(loc)
        print(st)
        return 0
    if args.command == "ls":
        for e in fs.list(loc):
            print(("d " if e.is_dir else "f ") + e.path)
        return 0
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
