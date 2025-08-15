"""Integration tests for the relationship mapping pipeline stage."""

import pytest
from pathlib import Path
import tempfile

from proj_mapper.pipeline import PipelineContext
from proj_mapper.models.code import CodeElement, CodeElementType
from proj_mapper.models.documentation import DocumentationElement, DocumentationType
from proj_mapper.models.relationship import RelationshipType
from proj_mapper.relationship.pipeline_stage import RelationshipMappingStage

class TestRelationshipMappingPipeline:
    """Test cases for the relationship mapping pipeline stage."""
    
    def test_relationship_mapping_pipeline(self):
        """Test that the relationship mapping works correctly within a pipeline."""
        # Create a pipeline context
        context = PipelineContext()
        
        # Create sample code elements
        code_elements = [
            CodeElement(
                id="class_1",
                name="TestClass",
                element_type=CodeElementType.CLASS,
                location="/path/to/file.py",
                file_path="/path/to/file.py",
                line_start=1,
                docstring="This is a test class for demonstration.",
                metadata={"base_classes": ["BaseClass"]}
            ),
            CodeElement(
                id="class_2",
                name="BaseClass",
                element_type=CodeElementType.CLASS,
                location="/path/to/base.py",
                file_path="/path/to/base.py",
                line_start=1,
                docstring="This is a base class.",
                metadata={}
            )
        ]
        
        # Add code elements to context
        context.set_result("code_analysis", {"python": {"elements": code_elements}})
        
        # Create sample documentation elements
        doc_elements = [
            DocumentationElement(
                title="doc_1",
                element_type=DocumentationType.SECTION,
                location="/path/to/doc.md",
                content="# Test Documentation\n\nThis is documentation for TestClass.",
                parent=None
            ),
            DocumentationElement(
                title="doc_2",
                element_type=DocumentationType.CODE_BLOCK,
                location="/path/to/doc.md",
                content="```python\nclass TestClass(BaseClass):\n    def test_method(self):\n        pass\n```",
                parent="doc_1"
            )
        ]
        
        # Add documentation elements to context
        context.set_result("documentation_analysis", {"markdown": {"elements": doc_elements}})
        
        # Create and run the relationship mapping stage
        stage = RelationshipMappingStage()
        result_context = stage.process(context)
        
        # Get mapped relationships
        relationships = result_context.get_result("relationships")
        
        # Verify relationships were found
        assert relationships is not None
        assert len(relationships) > 0
        
        # Check for specific relationships
        doc_refs = [r for r in relationships if r.relationship_type == RelationshipType.REFERENCES]
        
        # Documentation should reference the class
        doc_refs_from_doc = [r for r in doc_refs if r.source_id == "doc_1"]
        assert len(doc_refs_from_doc) >= 1
        assert any(r.target_id == "class_1" for r in doc_refs_from_doc)
        
        # Code block should reference both classes
        code_block_refs = [r for r in doc_refs if r.source_id == "doc_2"]
        assert len(code_block_refs) >= 2
        assert any(r.target_id == "class_1" for r in code_block_refs)
        assert any(r.target_id == "class_2" for r in code_block_refs)
        
        # Verify confidence scores
        for relationship in relationships:
            assert 0 < relationship.confidence <= 1 