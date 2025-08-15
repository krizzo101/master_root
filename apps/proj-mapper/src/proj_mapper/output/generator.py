"""Map generator for project mapping.

This module contains the MapGenerator class that creates different types of maps.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Type, Union

from proj_mapper.models.code import CodeElement
from proj_mapper.models.documentation import DocumentationElement
from proj_mapper.models.relationship import Relationship
from proj_mapper.models.project import Project, ProjectMap
from proj_mapper.output.chunking import ChunkingStrategy, HierarchicalChunkingStrategy
from proj_mapper.output.config import GeneratorConfig, MapFormatType
from proj_mapper.output.storage.base import MapStorageProvider
from proj_mapper.output.storage.file_storage import LocalFileSystemStorage

# Configure logging
logger = logging.getLogger(__name__)


class MapTemplate:
    """Base class for map templates."""
    
    @property
    def name(self) -> str:
        """Get the template name.
        
        Returns:
            The template name
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def generate(self, graph: Any, config: GeneratorConfig) -> Dict[str, Any]:
        """Generate a map from the relationship graph.
        
        Args:
            graph: The relationship graph
            config: The generator configuration
            
        Returns:
            The generated map structure
        """
        raise NotImplementedError("Subclasses must implement this method")


class MapGenerator:
    """Generator for creating different types of project maps.
    
    This class handles the conversion of code and documentation elements and their
    relationships into various map formats, including HTML, JSON, and specialized 
    formats for visualization tools.
    """
    
    def __init__(
        self, 
        storage_provider: Optional[MapStorageProvider] = None,
        chunking_strategy: Optional[ChunkingStrategy] = None
    ):
        """Initialize the map generator.
        
        Args:
            storage_provider: Provider for storing maps (default: LocalFileSystemStorage)
            chunking_strategy: Strategy for chunking large maps (default: HierarchicalChunkingStrategy)
        """
        self.storage_provider = storage_provider or LocalFileSystemStorage()
        self.chunking_strategy = chunking_strategy or HierarchicalChunkingStrategy()
    
    def generate_project_map(
        self,
        code_elements: List[CodeElement],
        doc_elements: List[DocumentationElement],
        relationships: List[Relationship],
        project_name: str,
        output_dir: Optional[Path] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProjectMap:
        """Generate a complete project map.
        
        Args:
            code_elements: List of code elements
            doc_elements: List of documentation elements
            relationships: List of relationships
            project_name: Name of the project
            output_dir: Directory to output map files (optional)
            metadata: Additional metadata for the project map
            
        Returns:
            The generated project map
        """
        logger.info(f"Generating project map for {project_name}")
        
        # Create the project structure
        project = Project(
            name=project_name,
            created_at=datetime.now(),
            code_elements=code_elements,
            doc_elements=doc_elements,
            relationships=relationships,
            metadata=metadata or {}
        )
        
        project_map = ProjectMap(
            project=project
        )
        
        # Save the map if output_dir is specified
        if output_dir:
            output_path = output_dir / f"{project_name.lower().replace(' ', '_')}_map.json"
            self._save_map(project_map, output_path)
            logger.info(f"Project map saved to {output_path}")
        
        return project_map
    
    def generate_relationship_graph(
        self,
        relationships: List[Relationship],
        code_elements: List[CodeElement],
        doc_elements: List[DocumentationElement],
        project_name: str,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Generate a graph representation of relationships.
        
        Args:
            relationships: List of relationships
            code_elements: List of code elements
            doc_elements: List of documentation elements
            project_name: Name of the project
            output_dir: Directory to output graph file (optional)
            
        Returns:
            Dictionary with nodes and edges for visualization
        """
        logger.info(f"Generating relationship graph for {project_name}")
        
        # Create nodes for code elements
        code_nodes = []
        code_id_map = {}
        for i, element in enumerate(code_elements):
            node_id = f"code_{i}"
            code_id_map[element.id] = node_id
            code_nodes.append({
                "id": node_id,
                "type": "code",
                "label": getattr(element, "name", "Unknown"),
                "element_type": element.element_type.value,
                "metadata": {
                    "id": element.id,
                    "location": str(element.location.file_path)
                }
            })
        
        # Create nodes for doc elements
        doc_nodes = []
        doc_id_map = {}
        for i, element in enumerate(doc_elements):
            node_id = f"doc_{i}"
            doc_id_map[element.title] = node_id
            doc_nodes.append({
                "id": node_id,
                "type": "documentation",
                "label": element.title,
                "element_type": element.element_type.value,
                "metadata": {
                    "id": element.title,
                    "location": str(element.location.file_path)
                }
            })
        
        # Create edges for relationships
        edges = []
        for i, rel in enumerate(relationships):
            # Get source and target node IDs
            source_id = code_id_map.get(rel.source_id) if rel.source_type == "code" else doc_id_map.get(rel.source_id)
            target_id = code_id_map.get(rel.target_id) if rel.target_type == "code" else doc_id_map.get(rel.target_id)
            
            if source_id and target_id:
                edges.append({
                    "id": f"edge_{i}",
                    "source": source_id,
                    "target": target_id,
                    "label": rel.relationship_type.name,
                    "weight": rel.confidence,
                    "metadata": rel.metadata
                })
        
        # Combine nodes and edges
        graph = {
            "nodes": code_nodes + doc_nodes,
            "edges": edges,
            "metadata": {
                "project_name": project_name,
                "generated_at": datetime.now().isoformat(),
                "num_code_elements": len(code_elements),
                "num_doc_elements": len(doc_elements),
                "num_relationships": len(relationships)
            }
        }
        
        # Save the graph if output_dir is specified
        if output_dir:
            output_path = output_dir / f"{project_name.lower().replace(' ', '_')}_graph.json"
            with open(output_path, 'w') as f:
                json.dump(graph, f, indent=2, default=str)
            logger.info(f"Relationship graph saved to {output_path}")
        
        return graph
    
    def _save_map(self, project_map: ProjectMap, output_path: Path) -> None:
        """Save the project map to the specified path.
        
        Args:
            project_map: The project map to save
            output_path: The path to save the map to
        """
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if chunking is needed
        if self.chunking_strategy.should_chunk(project_map):
            logger.info("Chunking project map due to size")
            chunks = self.chunking_strategy.chunk(project_map)
            self.storage_provider.save_chunked(chunks, output_path)
        else:
            # Convert to dictionary
            map_dict = project_map.dict()
            self.storage_provider.save(map_dict, output_path)
    
    def generate_documentation_structure_map(
        self,
        doc_elements: List[DocumentationElement],
        relationships: List[Relationship],
        project_name: str,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Generate a map of documentation structure.
        
        Args:
            doc_elements: List of documentation elements
            relationships: List of relationships
            project_name: Name of the project
            output_dir: Directory to output map file (optional)
            
        Returns:
            Dictionary representing documentation structure
        """
        logger.info(f"Generating documentation structure map for {project_name}")
        
        # Create a hierarchy of documentation elements
        doc_hierarchy = {}
        doc_map = {doc.title: doc for doc in doc_elements}
        
        # Group by file to create a tree structure
        file_groups: Dict[str, List[DocumentationElement]] = {}
        for doc in doc_elements:
            file_path = str(doc.location.file_path)
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(doc)
        
        # Create a tree for each file
        doc_structure = {
            "name": project_name,
            "type": "project",
            "children": []
        }
        
        for file_path, elements in file_groups.items():
            file_node = {
                "name": os.path.basename(file_path),
                "type": "file",
                "path": file_path,
                "children": []
            }
            
            # Find root elements (those without a parent or parent not in this file)
            root_elements = [doc for doc in elements if not doc.parent or doc.parent not in doc_map]
            
            # Add root elements and their children
            for root in root_elements:
                root_node = self._build_doc_tree(root, elements, doc_map)
                file_node["children"].append(root_node)
            
            doc_structure["children"].append(file_node)
        
        # Save the structure if output_dir is specified
        if output_dir:
            output_path = output_dir / f"{project_name.lower().replace(' ', '_')}_doc_structure.json"
            with open(output_path, 'w') as f:
                json.dump(doc_structure, f, indent=2, default=str)
            logger.info(f"Documentation structure map saved to {output_path}")
        
        return doc_structure
    
    def _build_doc_tree(
        self, 
        doc: DocumentationElement, 
        file_elements: List[DocumentationElement],
        doc_map: Dict[str, DocumentationElement]
    ) -> Dict[str, Any]:
        """Build a tree structure for a documentation element and its children.
        
        Args:
            doc: The root documentation element
            file_elements: All elements in the same file
            doc_map: Map of doc element titles to elements
            
        Returns:
            Dictionary representing the element and its children
        """
        node = {
            "id": doc.title,
            "name": doc.title,
            "type": doc.element_type.value,
            "content": doc.content[:100] + "..." if len(doc.content) > 100 else doc.content,
            "children": []
        }
        
        # Add children
        for child_doc in file_elements:
            if child_doc.parent == doc.title:
                child_node = self._build_doc_tree(child_doc, file_elements, doc_map)
                node["children"].append(child_node)
        
        return node 