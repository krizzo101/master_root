"""Unit tests for the map generator."""

import json
import tempfile
from pathlib import Path
import pytest
from typing import Dict, List, Any

from proj_mapper.models.code import CodeElement, CodeElementType, Location
from proj_mapper.models.documentation import DocumentationElement, DocumentationType
from proj_mapper.models.relationship import Relationship, RelationshipType
from proj_mapper.output.generator import MapGenerator


@pytest.fixture
def test_elements():
    """Create test elements for map generation."""
    # Create code elements
    code_elements = [
        CodeElement(
            id="class_1",
            name="TestClass",
            element_type=CodeElementType.CLASS,
            location=Location(file_path="/path/to/file.py", start_line=1, end_line=20),
            docstring="This is a test class for demonstration.",
            visibility="public",
            metadata={"base_classes": ["BaseClass"]}
        ),
        CodeElement(
            id="method_1",
            name="test_method",
            element_type=CodeElementType.FUNCTION,
            location=Location(file_path="/path/to/file.py", start_line=5, end_line=10),
            docstring="This method does testing.",
            visibility="public",
            metadata={"parent_class": "class_1"}
        )
    ]
    
    # Create documentation elements
    doc_elements = [
        DocumentationElement(
            title="doc_1",
            element_type=DocumentationType.SECTION,
            location=Location(file_path="/path/to/doc.md", start_line=1, end_line=5),
            content="# Test Documentation\n\nThis is documentation for TestClass.",
            parent=None
        ),
        DocumentationElement(
            title="doc_2",
            element_type=DocumentationType.CODE_BLOCK,
            location=Location(file_path="/path/to/doc.md", start_line=6, end_line=10),
            content="```python\nclass TestClass(BaseClass):\n    def test_method(self):\n        pass\n```",
            parent="doc_1"
        )
    ]
    
    # Create relationships
    relationships = [
        Relationship(
            source_id="doc_1",
            target_id="class_1",
            relationship_type=RelationshipType.REFERENCES,
            source_type="documentation",
            target_type="code",
            confidence=0.8,
            metadata={}
        ),
        Relationship(
            source_id="doc_1",
            target_id="doc_2",
            relationship_type=RelationshipType.CONTAINS,
            source_type="documentation",
            target_type="documentation",
            confidence=1.0,
            metadata={}
        )
    ]
    
    return {
        "code_elements": code_elements,
        "doc_elements": doc_elements,
        "relationships": relationships
    }


class TestMapGenerator:
    """Tests for the MapGenerator class."""
    
    def test_initialization(self):
        """Test generator initialization."""
        generator = MapGenerator()
        assert generator is not None
        assert hasattr(generator, 'storage_provider')
        assert hasattr(generator, 'chunking_strategy')
    
    def test_generate_project_map(self, test_elements):
        """Test generating a project map."""
        generator = MapGenerator()
        
        # Generate project map
        project_map = generator.generate_project_map(
            code_elements=test_elements["code_elements"],
            doc_elements=test_elements["doc_elements"],
            relationships=test_elements["relationships"],
            project_name="Test Project"
        )
        
        # Check project map properties
        assert project_map is not None
        assert project_map.project.name == "Test Project"
        assert len(project_map.project.code_elements) == len(test_elements["code_elements"])
        assert len(project_map.project.doc_elements) == len(test_elements["doc_elements"])
        assert len(project_map.project.relationships) == len(test_elements["relationships"])
    
    def test_generate_relationship_graph(self, test_elements):
        """Test generating a relationship graph."""
        generator = MapGenerator()
        
        # Generate relationship graph
        graph = generator.generate_relationship_graph(
            relationships=test_elements["relationships"],
            code_elements=test_elements["code_elements"],
            doc_elements=test_elements["doc_elements"],
            project_name="Test Project"
        )
        
        # Check graph properties
        assert graph is not None
        assert "nodes" in graph
        assert "edges" in graph
        assert "metadata" in graph
        
        # Check nodes
        nodes = graph["nodes"]
        assert len(nodes) == len(test_elements["code_elements"]) + len(test_elements["doc_elements"])
        
        # Check edges
        edges = graph["edges"]
        assert len(edges) > 0
    
    def test_generate_documentation_structure_map(self, test_elements):
        """Test generating a documentation structure map."""
        generator = MapGenerator()
        
        # Generate documentation structure map
        doc_structure = generator.generate_documentation_structure_map(
            doc_elements=test_elements["doc_elements"],
            relationships=test_elements["relationships"],
            project_name="Test Project"
        )
        
        # Check structure properties
        assert doc_structure is not None
        assert "name" in doc_structure
        assert "children" in doc_structure
        assert doc_structure["name"] == "Test Project"
    
    def test_saving_maps(self, test_elements):
        """Test saving maps to disk."""
        generator = MapGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Generate and save project map
            project_map = generator.generate_project_map(
                code_elements=test_elements["code_elements"],
                doc_elements=test_elements["doc_elements"],
                relationships=test_elements["relationships"],
                project_name="Test Project",
                output_dir=output_dir
            )
            
            # Check if file was created
            map_file = output_dir / "test_project_map.json"
            assert map_file.exists()
            
            # Check file content
            with open(map_file, 'r') as f:
                data = json.load(f)
                assert "project" in data
                assert data["project"]["name"] == "Test Project" 