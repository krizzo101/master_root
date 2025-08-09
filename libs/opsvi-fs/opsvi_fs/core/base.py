#!/usr/bin/env python3
"""
Core base abstractions for opsvi-fs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ComponentError(Exception):
    """Generic component error for opsvi-fs."""


@dataclass(slots=True)
class BaseComponent:
    """Base component with a name for logging and diagnostics."""

    name: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.__class__.__name__}(name={self.name!r})"
