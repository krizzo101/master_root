"""Unit tests for the output generator component."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from proj_mapper.output.generator import MapGenerator
from proj_mapper.output.formatters import JSONFormatter
from proj_mapper.models.relationship import RelationshipMap


@pytest.fixture
def sample_relationship_map():
    """Return a sample relationship map for testing."""
    rel_map = RelationshipMap()
    rel_map.add_node("file1.py", "code", {"type": "file", "language": "python"})
    rel_map.add_node("file2.py", "code", {"type": "file", "language": "python"})
    rel_map.add_node("readme.md", "documentation", {"type": "file", "language": "markdown"})
    
    rel_map.add_relationship(
        "file1.py", "readme.md", "documented_by", confidence=0.8,
        metadata={"type": "documentation", "description": "Documentation for file1"}
    )
    rel_map.add_relationship(
        "file1.py", "file2.py", "imports", confidence=0.9,
        metadata={"type": "code", "description": "File1 imports File2"}
    )
    
    return rel_map


@pytest.fixture
def map_generator():
    """Return a MapGenerator instance for testing."""
    return MapGenerator(output_dir=Path("/tmp/maps"))


class TestMapGenerator:
    """Tests for the MapGenerator class."""
    
    def test_initialization(self, map_generator):
        """Test that the map generator initializes correctly."""
        assert map_generator.output_dir == Path("/tmp/maps")
        assert isinstance(map_generator.formatters, dict)
        
    def test_register_formatter(self, map_generator):
        """Test registering a formatter."""
        formatter = MagicMock()
        formatter.format_name = "test"
        
        map_generator.register_formatter(formatter)
        
        assert map_generator.formatters["test"] == formatter
    
    @patch("proj_mapper.output.generator.JSONFormatter")
    def test_generate_json_map(self, mock_json_formatter, map_generator, sample_relationship_map):
        """Test generating a JSON map."""
        # Setup mock
        mock_formatter_instance = MagicMock()
        mock_json_formatter.return_value = mock_formatter_instance
        mock_formatter_instance.format.return_value = {"test": "formatted_data"}
        
        # Register formatter
        map_generator.register_formatter(mock_json_formatter.return_value)
        
        # Test generate
        with patch("pathlib.Path.mkdir"), patch("builtins.open", MagicMock()):
            result = map_generator.generate(sample_relationship_map, "json")
            
        assert result is not None
        mock_formatter_instance.format.assert_called_once_with(sample_relationship_map)
    
    @patch("pathlib.Path.mkdir")
    @patch("builtins.open", new_callable=MagicMock)
    def test_write_output_file(self, mock_open, mock_mkdir, map_generator, sample_relationship_map):
        """Test writing the output file."""
        # Setup
        file_manager = mock_open.return_value.__enter__.return_value
        
        # Register real formatter
        map_generator.register_formatter(JSONFormatter())
        
        # Test
        map_generator.generate(sample_relationship_map, "json")
        
        # Assert
        mock_mkdir.assert_called()
        mock_open.assert_called()
        file_manager.write.assert_called()
        
    def test_chunking_large_map(self, map_generator, sample_relationship_map):
        """Test chunking a large map."""
        # Create a larger relationship map
        for i in range(100):
            sample_relationship_map.add_node(f"file{i}.py", "code", {"type": "file"})
            
        for i in range(99):
            sample_relationship_map.add_relationship(
                f"file{i}.py", f"file{i+1}.py", "references", 0.5, {}
            )
            
        # Setup
        map_generator.chunk_size = 10  # Small chunk size for testing
        map_generator.register_formatter(JSONFormatter())
        
        # Test with patching to avoid actual file writes
        with patch("pathlib.Path.mkdir"), patch("builtins.open", MagicMock()):
            result = map_generator.generate(sample_relationship_map, "json", chunked=True)
            
        # Verify chunking occurred
        assert result.get("chunks") is not None
        assert len(result.get("chunks", [])) > 1


class TestJSONFormatter:
    """Tests for the JSONFormatter class."""
    
    def test_initialization(self):
        """Test JSON formatter initialization."""
        formatter = JSONFormatter()
        assert formatter.format_name == "json"
        
    def test_format_map(self, sample_relationship_map):
        """Test formatting a relationship map to JSON."""
        formatter = JSONFormatter()
        
        result = formatter.format(sample_relationship_map)
        
        # Validate structure
        assert "schema_version" in result
        assert "nodes" in result
        assert "relationships" in result
        assert "metadata" in result
        
        # Validate content
        assert len(result["nodes"]) == 3
        assert len(result["relationships"]) == 2
        
        # Ensure serializable to JSON
        json_str = json.dumps(result)
        assert json_str is not None
    
    def test_format_empty_map(self):
        """Test formatting an empty relationship map."""
        formatter = JSONFormatter()
        empty_map = RelationshipMap()
        
        result = formatter.format(empty_map)
        
        assert len(result["nodes"]) == 0
        assert len(result["relationships"]) == 0
        
    def test_map_node_conversion(self, sample_relationship_map):
        """Test proper conversion of map nodes to JSON."""
        formatter = JSONFormatter()
        
        result = formatter.format(sample_relationship_map)
        
        # Find a specific node
        python_nodes = [n for n in result["nodes"] if n["id"] == "file1.py"]
        assert len(python_nodes) == 1
        assert python_nodes[0]["type"] == "code"
        assert python_nodes[0]["metadata"]["language"] == "python"
        
    def test_relationship_conversion(self, sample_relationship_map):
        """Test proper conversion of relationships to JSON."""
        formatter = JSONFormatter()
        
        result = formatter.format(sample_relationship_map)
        
        # Find a specific relationship
        import_rels = [r for r in result["relationships"] if r["type"] == "imports"]
        assert len(import_rels) == 1
        assert import_rels[0]["source"] == "file1.py"
        assert import_rels[0]["target"] == "file2.py"
        assert import_rels[0]["confidence"] == 0.9 