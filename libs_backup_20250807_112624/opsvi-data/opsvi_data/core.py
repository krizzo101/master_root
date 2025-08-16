"""Core stubs for opsvi-data."""

from __future__ import annotations

import logging
from dataclasses import dataclass

LOG = logging.getLogger("opsvi-data.core")


@dataclass(slots=True)
class BaseOpsviData:
    """Base class – extend me."""

    name: str

    def run(self) -> None:
        """Execute the primary action (no-op stub)."""
        LOG.info("Running %s (stub)", self.name)
