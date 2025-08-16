"""Project map model for Project Mapper.

This module defines the ProjectMap class that represents a complete project map.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from proj_mapper.models.project import Project
from proj_mapper.models.file import DiscoveredFile


@dataclass
class ProjectMap:
    """Represents a complete project map.

    Attributes:
        project: The project this map represents
        files: List of discovered files
        code_analysis: Results of code analysis
        doc_analysis: Results of documentation analysis
        relationships: Detected relationships
        metadata: Additional metadata about the map
    """

    project: Project
    files: List[DiscoveredFile]
    code_analysis: Optional[Dict[str, Any]] = None
    doc_analysis: Optional[Dict[str, Any]] = None
    relationships: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize additional attributes after instance creation."""
        if 'timestamp' not in self.metadata:
            self.metadata['timestamp'] = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the project map to a dictionary.

        Returns:
            Dictionary representation of the project map
        """
        return {
            'project': {
                'name': self.project.name,
                'root_path': str(self.project.root_path)
            },
            'files': [file.to_dict() for file in self.files],
            'code_analysis': self.code_analysis,
            'doc_analysis': self.doc_analysis,
            'relationships': self.relationships,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectMap':
        """Create a project map from a dictionary.

        Args:
            data: Dictionary containing project map data

        Returns:
            ProjectMap instance
        """
        # Create project instance
        project_data = data['project']
        project = Project(
            name=project_data['name'],
            root_path=project_data['root_path']
        )

        # Create file instances
        files = []
        for file_data in data['files']:
            file = DiscoveredFile(**file_data)
            files.append(file)

        # Create project map
        return cls(
            project=project,
            files=files,
            code_analysis=data.get('code_analysis'),
            doc_analysis=data.get('doc_analysis'),
            relationships=data.get('relationships'),
            metadata=data.get('metadata', {})
        )