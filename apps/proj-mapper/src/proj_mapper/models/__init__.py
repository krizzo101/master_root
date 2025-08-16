"""Data models for Project Mapper.

This package contains the data models used to represent projects, files, code elements,
documentation elements, and relationships between them.
"""

from proj_mapper.models.file import DiscoveredFile, FileType
from proj_mapper.models.project import Project, ProjectMap
from proj_mapper.models.code import CodeElement, CodeElementType, Location, Visibility, CodeReference
from proj_mapper.models.documentation import DocumentationElement, DocumentationType
from proj_mapper.models.relationship import Relationship, RelationshipType

__all__ = [
    "DiscoveredFile",
    "FileType",
    "Project", 
    "ProjectMap",
    "CodeElement",
    "CodeElementType",
    "Location",
    "Visibility",
    "CodeReference",
    "DocumentationElement",
    "DocumentationType",
    "Relationship",
    "RelationshipType",
]
