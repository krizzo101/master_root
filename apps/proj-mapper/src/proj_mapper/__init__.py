"""Project Mapper - Map and analyze project structure.

This package provides tools for analyzing projects, detecting relationships
between code and documentation, and generating structured maps optimized
for AI consumption.
"""

__version__ = "1.0.0"

# Core services
from proj_mapper.core.config import Configuration
from proj_mapper.core.file_discovery import FileDiscovery
from proj_mapper.core.pipeline import Pipeline, PipelineContext, PipelineStage
from proj_mapper.core.project_manager import ProjectManager

# Models
from proj_mapper.models.base import BaseModel
from proj_mapper.models.file import FileType, DiscoveredFile
from proj_mapper.models.code import CodeElementType, CodeElement, Visibility
from proj_mapper.models.documentation import DocumentationType, DocumentationElement
from proj_mapper.models.relationship import RelationshipType, Relationship
from proj_mapper.models.project import Project, ProjectMap

# Import modules - use delayed import to avoid circular references
def _import_modules():
    """Import modules, delaying to avoid circular references."""
    import proj_mapper.analysis
    import proj_mapper.relationship
    import proj_mapper.output
    import proj_mapper.cli
    import proj_mapper.pipeline
    return {
        "analysis": proj_mapper.analysis,
        "relationship": proj_mapper.relationship,
        "output": proj_mapper.output,
        "cli": proj_mapper.cli,
        "pipeline": proj_mapper.pipeline
    }

# These will be populated on first access via __getattr__
_modules = {}

def __getattr__(name):
    """Lazy-load modules when accessed."""
    global _modules
    if not _modules and name in {"analysis", "relationship", "output", "cli", "pipeline"}:
        _modules = _import_modules()
    if name in _modules:
        return _modules[name]
    raise AttributeError(f"module 'proj_mapper' has no attribute '{name}'")

__all__ = [
    # Meta
    "__version__",
    
    # Modules
    "analysis",
    "relationship", 
    "output",
    "cli",
    "pipeline",
    
    # Core
    "Configuration",
    "FileDiscovery",
    "Pipeline",
    "PipelineContext",
    "PipelineStage",
    "ProjectManager",
    
    # Models
    "BaseModel",
    "FileType",
    "DiscoveredFile",
    "CodeElementType",
    "CodeElement",
    "Visibility",
    "DocumentationType",
    "DocumentationElement",
    "RelationshipType",
    "Relationship",
    "Project",
    "ProjectMap",
]
