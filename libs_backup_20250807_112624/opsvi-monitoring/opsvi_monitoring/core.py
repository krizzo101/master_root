"""Core stubs for opsvi-monitoring."""

from __future__ import annotations

import logging
from dataclasses import dataclass

LOG = logging.getLogger("opsvi-monitoring.core")


@dataclass(slots=True)
class BaseOpsviMonitoring:
    """Base class – extend me."""

    name: str

    def run(self) -> None:
        """Execute the primary action (no-op stub)."""
        LOG.info("Running %s (stub)", self.name)
