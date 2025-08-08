"""Coordinator base for opsvi-pipeline."""
from opsvi_pipeline.core.base import OpsviPipelineManager

class Coordinator(OpsviPipelineManager):
    async def coordinate(self) -> None:
        pass
