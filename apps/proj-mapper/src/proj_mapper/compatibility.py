"""
Compatibility layer for proj-mapper migration
Provides adapters between proj-mapper and opsvi libraries
"""

from pathlib import Path
from typing import Any, Dict, List, Optional


class StorageAdapter:
    """Adapter for storage operations"""

    def __init__(self):
        # Will eventually use opsvi_data
        from proj_mapper.storage import FileStorage as OriginalStorage

        self.storage = OriginalStorage()

    def save(self, data: Any, path: Path):
        return self.storage.save(data, path)

    def load(self, path: Path):
        return self.storage.load(path)


class ModelAdapter:
    """Adapter for model operations"""

    @staticmethod
    def create_project_map(**kwargs):
        from proj_mapper.models import ProjectMap

        return ProjectMap(**kwargs)

    @staticmethod
    def create_file_info(**kwargs):
        from proj_mapper.models import FileInfo

        return FileInfo(**kwargs)


class PipelineAdapter:
    """Adapter for pipeline operations"""

    def __init__(self):
        from proj_mapper.pipeline import Pipeline as OriginalPipeline

        self.pipeline = OriginalPipeline()

    def run(self, stages: List[Any], data: Any):
        return self.pipeline.run(stages, data)


# Export adapters as if they were the original classes
FileStorage = StorageAdapter
ProjectMap = ModelAdapter.create_project_map
FileInfo = ModelAdapter.create_file_info
Pipeline = PipelineAdapter
