"""File models for Project Mapper.

This module is maintained for backward compatibility.
All code has been moved to the file/ package.
"""

# Import everything from the new modular structure for backward compatibility
from proj_mapper.models.file.types import FileType
from proj_mapper.models.file.discovered import DiscoveredFile
from proj_mapper.models.file.project import DiscoveredProject

__all__ = [
    "FileType",
    "DiscoveredFile",
    "DiscoveredProject",
] 