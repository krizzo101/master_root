#!/usr/bin/env python3
"""Misc path utilities."""
from __future__ import annotations

import os


def normpath(p: str) -> str:
    return os.path.normpath(p).replace("\\", "/")
