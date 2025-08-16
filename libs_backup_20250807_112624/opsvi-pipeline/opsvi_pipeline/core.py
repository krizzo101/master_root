"""Core stubs for opsvi-pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass

LOG = logging.getLogger("opsvi-pipeline.core")


@dataclass(slots=True)
class BaseOpsviPipeline:
    """Base class – extend me."""

    name: str

    def run(self) -> None:
        """Execute the primary action (no-op stub)."""
        LOG.info("Running %s (stub)", self.name)
