"""Tests for the visualization generator."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from proj_mapper.output.visualization import (
    VisualizationGenerator,
    VisualizationConfig,
    VisualizationType,
    VisualizationFormat,
    DotRenderer
)


@pytest.fixture
def test_map_data():
    """Create test map data."""
    return {
        "project_map": {
            "project": {
                "name": "Test Project",
                "code_elements": [
                    {
                        "id": "module1",
                        "name": "module1",
                        "element_type": "module",
                        "classes": [
                            {
                                "id": "class1",
                                "name": "Class1",
                                "element_type": "class"
                            }
                        ],
                        "functions": [
                            {
                                "id": "func1",
                                "name": "function1",
                                "element_type": "function"
                            }
                        ]
                    }
                ]
            }
        },
        "relationship_graph": {
            "nodes": [
                {
                    "id": "node1",
                    "label": "Node 1",
                    "type": "code"
                },
                {
                    "id": "node2",
                    "label": "Node 2",
                    "type": "documentation"
                }
            ],
            "edges": [
                {
                    "source": "node1",
                    "target": "node2",
                    "label": "references",
                    "weight": 0.8
                }
            ]
        },
        "documentation_structure": {
            "documents": [
                {
                    "path": "doc1.md",
                    "title": "Document 1",
                    "sections": [
                        {
                            "id": "section1",
                            "title": "Section 1",
                            "level": 1
                        }
                    ],
                    "references": [
                        {
                            "type": "code",
                            "target": "class1",
                            "confidence": 0.9
                        }
                    ]
                }
            ]
        }
    }


class TestVisualizationGenerator:
    """Tests for the VisualizationGenerator class."""
    
    def test_initialization(self):
        """Test generator initialization."""
        generator = VisualizationGenerator()
        assert generator is not None
        assert generator.config is not None
    
    def test_generate_relationship_visualization(self, test_map_data):
        """Test generating a relationship visualization."""
        generator = VisualizationGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Generate visualization
            output_path = generator.generate_visualization(
                map_data=test_map_data,
                vis_type=VisualizationType.RELATIONSHIP,
                output_dir=output_dir,
                project_name="test"
            )
            
            # Check if file was created
            assert output_path is not None
            assert output_path.exists()
            assert output_path.suffix == ".dot"
            
            # Check file content
            with open(output_path, "r") as f:
                content = f.read()
                assert "digraph G {" in content
                assert '"node1"' in content
                assert '"node2"' in content
                assert "references" in content
    
    def test_generate_dependency_visualization(self, test_map_data):
        """Test generating a dependency visualization."""
        generator = VisualizationGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Generate visualization
            output_path = generator.generate_visualization(
                map_data=test_map_data,
                vis_type=VisualizationType.DEPENDENCY,
                output_dir=output_dir,
                project_name="test"
            )
            
            # Check if file was created
            assert output_path is not None
            assert output_path.exists()
            assert output_path.suffix == ".dot"
    
    def test_generate_module_visualization(self, test_map_data):
        """Test generating a module visualization."""
        generator = VisualizationGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Generate visualization
            output_path = generator.generate_visualization(
                map_data=test_map_data,
                vis_type=VisualizationType.MODULE,
                output_dir=output_dir,
                project_name="test"
            )
            
            # Check if file was created
            assert output_path is not None
            assert output_path.exists()
            assert output_path.suffix == ".dot"
            
            # Check file content
            with open(output_path, "r") as f:
                content = f.read()
                assert "module1" in content
                assert "Class1" in content
                assert "function1" in content
    
    def test_generate_documentation_visualization(self, test_map_data):
        """Test generating a documentation visualization."""
        generator = VisualizationGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Generate visualization
            output_path = generator.generate_visualization(
                map_data=test_map_data,
                vis_type=VisualizationType.DOCUMENTATION,
                output_dir=output_dir,
                project_name="test"
            )
            
            # Check if file was created
            assert output_path is not None
            assert output_path.exists()
            assert output_path.suffix == ".dot"
            
            # Check file content
            with open(output_path, "r") as f:
                content = f.read()
                assert "doc1.md" in content
                assert "Section 1" in content
                assert "class1" in content
    
    def test_unsupported_format(self, test_map_data):
        """Test handling of unsupported output format."""
        config = VisualizationConfig(output_format=VisualizationFormat.SVG)
        generator = VisualizationGenerator(config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Generate visualization
            output_path = generator.generate_visualization(
                map_data=test_map_data,
                vis_type=VisualizationType.RELATIONSHIP,
                output_dir=output_dir,
                project_name="test"
            )
            
            # Should return None for unsupported format
            assert output_path is None
    
    def test_missing_data(self):
        """Test handling of missing data."""
        generator = VisualizationGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Generate visualization with empty data
            output_path = generator.generate_visualization(
                map_data={},
                vis_type=VisualizationType.RELATIONSHIP,
                output_dir=output_dir,
                project_name="test"
            )
            
            # Should return None for missing data
            assert output_path is None


class TestDotRenderer:
    """Tests for the DotRenderer class."""
    
    def test_render_graph(self):
        """Test rendering a graph in DOT format."""
        config = VisualizationConfig()
        renderer = DotRenderer(config)
        
        graph_data = {
            "nodes": [
                {"id": "n1", "label": "Node 1", "type": "code"},
                {"id": "n2", "label": "Node 2", "type": "documentation"}
            ],
            "edges": [
                {
                    "source": "n1",
                    "target": "n2",
                    "label": "references",
                    "weight": 0.8
                }
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.dot"
            
            # Render graph
            renderer.render(graph_data, output_path)
            
            # Check file content
            with open(output_path, "r") as f:
                content = f.read()
                assert "digraph G {" in content
                assert '"n1"' in content
                assert '"n2"' in content
                assert "references" in content
                assert "0.80" in content  # Weight should be formatted
    
    def test_theme_customization(self):
        """Test theme customization in DOT output."""
        config = VisualizationConfig(theme="dark")
        renderer = DotRenderer(config)
        
        graph_data = {
            "nodes": [{"id": "n1", "label": "Node 1", "type": "code"}],
            "edges": []
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.dot"
            
            # Render graph
            renderer.render(graph_data, output_path)
            
            # Check theme-specific attributes
            with open(output_path, "r") as f:
                content = f.read()
                assert 'bgcolor="#222222"' in content
                assert 'fontcolor="#FFFFFF"' in content 