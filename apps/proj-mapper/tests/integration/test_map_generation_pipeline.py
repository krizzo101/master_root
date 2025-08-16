"""Integration tests for the map generation pipeline."""

import pytest
import tempfile
from pathlib import Path
from typing import Dict, List, Any

from proj_mapper.core.pipeline import Pipeline, PipelineContext
from proj_mapper.models.code import CodeElement, CodeElementType, Location
from proj_mapper.models.documentation import DocumentationElement, DocumentationType
from proj_mapper.models.relationship import Relationship, RelationshipType
from proj_mapper.output.pipeline_stages import MapGenerationStage


class TestMapGenerationPipeline:
    """Integration tests for the map generation pipeline."""
    
    def test_map_generation_pipeline(self):
        """Test that the map generation works correctly within a pipeline."""
        # Create pipeline context
        context = PipelineContext()
        
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
        
        # Create analysis results
        code_analysis_results = [
            {
                "file": {"relative_path": "file.py"},
                "analysis": {"elements": code_elements},
                "success": True
            }
        ]
        
        doc_analysis_results = [
            {
                "file": {"relative_path": "doc.md"},
                "analysis": {"elements": doc_elements},
                "success": True
            }
        ]
        
        # Add analysis results and relationships to context
        context.set("code_analysis_results", code_analysis_results)
        context.set("documentation_analysis_results", doc_analysis_results)
        context.set("relationships", relationships)
        
        # Create temporary directory for map output
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Create pipeline with map generation stage
            pipeline = Pipeline()
            map_stage = MapGenerationStage(
                output_dir=output_dir,
                project_name="Test Project"
            )
            pipeline._context = context  # Set context directly for testing
            pipeline.add_stage(map_stage)
            
            # Run the pipeline
            maps = pipeline.run(None)
            
            # Check results
            assert maps is not None
            assert "project_map" in maps
            assert "relationship_graph" in maps
            assert "documentation_structure" in maps
            
            # Check context
            assert context.contains("generated_maps")
            
            # Verify maps in context
            generated_maps = context.get("generated_maps")
            assert generated_maps["project_map"] == maps["project_map"]
            
            # Check files were created
            project_map_file = output_dir / "test_project_map.json"
            graph_file = output_dir / "test_project_graph.json"
            doc_structure_file = output_dir / "test_project_doc_structure.json"
            
            assert project_map_file.exists()
            assert graph_file.exists()
            assert doc_structure_file.exists() 