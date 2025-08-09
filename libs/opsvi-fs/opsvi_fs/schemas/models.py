#!/usr/bin/env python3
"""Schema models for file locations and metadata."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FileLocation:
    """Provider-agnostic locator.

    path: full path or key; bucket/container optional for cloud providers
    """

    path: str
    bucket: str | None = None


@dataclass(slots=True)
class FileStat:
    path: str
    size: int
    is_dir: bool


@dataclass(slots=True)
class ListEntry:
    path: str
    is_dir: bool
