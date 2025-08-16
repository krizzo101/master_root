"""Integration tests for the Relationship Mapping Subsystem."""

import pytest

from proj_mapper.core.pipeline import Pipeline, PipelineContext
from proj_mapper.models.code import CodeElement, CodeElementType
from proj_mapper.models.documentation import DocumentationElement, DocumentationElementType
from proj_mapper.models.relationship import Relationship, RelationshipType
from proj_mapper.relationship.pipeline_stages import (
    RelationshipDetectionStage,
    RelationshipScoringStage,
    CrossReferenceResolutionStage,
    RelationshipGraphBuildingStage,
    RelationshipServiceStage
)


class TestRelationshipSubsystem:
    """Integration tests for the Relationship Mapping Subsystem."""
    
    def test_full_pipeline_execution(self):
        """Test the complete relationship mapping pipeline execution."""
        # Setup pipeline
        pipeline = Pipeline(name="relationship_mapping_pipeline")
        
        # Add stages
        pipeline.add_stage("detection", RelationshipDetectionStage())
        pipeline.add_stage("scoring", RelationshipScoringStage())
        pipeline.add_stage("cross_ref", CrossReferenceResolutionStage())
        pipeline.add_stage("graph_building", RelationshipGraphBuildingStage())
        pipeline.add_stage("service", RelationshipServiceStage())
        
        # Create context with mock analysis results
        context = PipelineContext()
        
        # Add code elements
        code_class = CodeElement(
            id="class1",
            name="TestClass",
            element_type=CodeElementType.CLASS,
            file_path="test_file.py",
            line_range=(1, 20),
            metadata={"imports": ["another_module"]}
        )
        
        code_method = CodeElement(
            id="method1",
            name="test_method",
            element_type=CodeElementType.FUNCTION,
            file_path="test_file.py",
            line_range=(5, 10),
            metadata={"parent": "class1"}
        )
        
        # Add documentation elements
        doc_class = DocumentationElement(
            id="doc_class1",
            title="TestClass",
            element_type=DocumentationElementType.CLASS,
            file_path="test_doc.md",
            content="This is documentation for TestClass",
            metadata={}
        )
        
        doc_method = DocumentationElement(
            id="doc_method1",
            title="test_method",
            element_type=DocumentationElementType.FUNCTION,
            file_path="test_doc.md",
            content="This documents test_method in TestClass",
            metadata={"parent_section": "doc_class1"}
        )
        
        # Create analysis results structure
        analysis_results = {
            "code": {
                "test_file.py": {
                    "elements": [code_class, code_method]
                }
            },
            "documentation": {
                "test_doc.md": {
                    "elements": [doc_class, doc_method]
                }
            }
        }
        
        context.set("analysis_results", analysis_results)
        
        # Execute pipeline
        result = pipeline.execute(context)
        
        # Verify pipeline execution
        assert pipeline.has_executed
        
        # Verify detection stage output
        assert context.contains("code_elements")
        assert context.contains("doc_elements")
        assert context.contains("relationships")
        
        code_elements = context.get("code_elements")
        doc_elements = context.get("doc_elements")
        relationships = context.get("relationships")
        
        assert len(code_elements) == 2
        assert len(doc_elements) == 2
        assert len(relationships) > 0
        
        # Verify scoring stage
        assert context.get_metadata("relationship_scoring_completed") is True
        
        # Verify cross-reference resolution
        assert context.get_metadata("reference_resolution_count") is not None
        
        # Verify graph building
        graph = context.get("relationship_graph")
        assert graph is not None
        assert context.get_metadata("graph_total_nodes") == 4  # 2 code + 2 doc elements
        assert context.get_metadata("graph_total_edges") > 0
        
        # Verify service creation
        service = context.get("relationship_service")
        assert service is not None
        assert service.graph is graph
        
        # Test service functionality
        class_related = service.get_related_elements("class1")
        assert len(class_related) > 0
        
        # Verify final result is the service
        assert result is service
    
    def test_subsystem_with_minimal_data(self):
        """Test the relationship subsystem with minimal data."""
        # Setup pipeline
        pipeline = Pipeline(name="relationship_mapping_pipeline")
        
        # Add stages
        pipeline.add_stage("detection", RelationshipDetectionStage())
        pipeline.add_stage("scoring", RelationshipScoringStage())
        pipeline.add_stage("cross_ref", CrossReferenceResolutionStage())
        pipeline.add_stage("graph_building", RelationshipGraphBuildingStage())
        pipeline.add_stage("service", RelationshipServiceStage())
        
        # Create context with minimal analysis results
        context = PipelineContext()
        
        # Add single code and doc element
        code_element = CodeElement(
            id="code1",
            name="MinimalClass",
            element_type=CodeElementType.CLASS,
            file_path="minimal.py",
            line_range=(1, 5)
        )
        
        doc_element = DocumentationElement(
            id="doc1",
            title="MinimalClass",  # Same name for cross-reference matching
            element_type=DocumentationElementType.SECTION,
            file_path="minimal.md",
            content="Documentation for MinimalClass"
        )
        
        # Create analysis results structure
        analysis_results = {
            "code": {
                "minimal.py": {
                    "elements": [code_element]
                }
            },
            "documentation": {
                "minimal.md": {
                    "elements": [doc_element]
                }
            }
        }
        
        context.set("analysis_results", analysis_results)
        
        # Execute pipeline
        result = pipeline.execute(context)
        
        # Verify pipeline execution
        assert pipeline.has_executed
        
        # Verify elements and relationships
        code_elements = context.get("code_elements")
        doc_elements = context.get("doc_elements")
        relationships = context.get("relationships")
        
        assert len(code_elements) == 1
        assert len(doc_elements) == 1
        assert len(relationships) > 0  # Should find at least one relationship due to name matching
        
        # Verify graph building
        graph = context.get("relationship_graph")
        assert context.get_metadata("graph_total_nodes") == 2  # 1 code + 1 doc element
        assert context.get_metadata("graph_total_edges") > 0
        
        # Test service functionality with minimal data
        service = context.get("relationship_service")
        related = service.get_related_elements("code1")
        assert len(related) > 0  # Should find the relationship
    
    def test_relationship_confidence_scoring(self):
        """Test that relationship confidence scoring works correctly."""
        # Setup pipeline with just detection and scoring stages
        pipeline = Pipeline(name="scoring_test_pipeline")
        pipeline.add_stage("detection", RelationshipDetectionStage())
        pipeline.add_stage("scoring", RelationshipScoringStage())
        
        # Create context with analysis results
        context = PipelineContext()
        
        # Add elements with different matching characteristics
        
        # 1. Perfect name match
        perfect_code = CodeElement(
            id="perfect_match_code",
            name="PerfectMatch",
            element_type=CodeElementType.CLASS,
            file_path="test.py",
            line_range=(1, 10)
        )
        
        perfect_doc = DocumentationElement(
            id="perfect_match_doc",
            title="PerfectMatch",
            element_type=DocumentationElementType.CLASS,
            file_path="test.md",
            content="Documentation for PerfectMatch class"
        )
        
        # 2. Partial name match
        partial_code = CodeElement(
            id="partial_match_code",
            name="PartialMatchClass",
            element_type=CodeElementType.CLASS,
            file_path="test.py",
            line_range=(15, 25)
        )
        
        partial_doc = DocumentationElement(
            id="partial_match_doc",
            title="Partial Match",
            element_type=DocumentationElementType.SECTION,
            file_path="test.md",
            content="Documentation for Partial Match Class"
        )
        
        # Create analysis results structure
        analysis_results = {
            "code": {
                "test.py": {
                    "elements": [perfect_code, partial_code]
                }
            },
            "documentation": {
                "test.md": {
                    "elements": [perfect_doc, partial_doc]
                }
            }
        }
        
        context.set("analysis_results", analysis_results)
        
        # Execute pipeline
        relationships = pipeline.execute(context)
        
        # Verify relationships were detected and scored
        assert len(relationships) > 0
        
        # Find the relationships for each pair
        perfect_match_rel = None
        partial_match_rel = None
        
        for rel in relationships:
            if rel.source_id == "perfect_match_code" and rel.target_id == "perfect_match_doc":
                perfect_match_rel = rel
            elif rel.source_id == "partial_match_code" and rel.target_id == "partial_match_doc":
                partial_match_rel = rel
        
        # Perfect match should have higher confidence than partial match
        assert perfect_match_rel is not None
        
        if partial_match_rel is not None:
            assert perfect_match_rel.confidence > partial_match_rel.confidence
        
        # Perfect match should have high confidence
        assert perfect_match_rel.confidence >= 0.8
    
    def test_cross_reference_resolution(self):
        """Test that cross-reference resolution works correctly."""
        # Setup pipeline with detection and cross-reference stages
        pipeline = Pipeline(name="cross_ref_test_pipeline")
        pipeline.add_stage("detection", RelationshipDetectionStage())
        pipeline.add_stage("cross_ref", CrossReferenceResolutionStage())
        
        # Create context with analysis results
        context = PipelineContext()
        
        # Create code elements
        code_class = CodeElement(
            id="class_id",
            name="ReferenceClass",
            element_type=CodeElementType.CLASS,
            file_path="test.py",
            line_range=(1, 20)
        )
        
        # Create documentation with explicit reference
        doc_with_ref = DocumentationElement(
            id="doc_with_ref",
            title="Documentation with Reference",
            element_type=DocumentationElementType.SECTION,
            file_path="test.md",
            content="This documentation refers to ReferenceClass which is important."
        )
        
        # Create analysis results structure
        analysis_results = {
            "code": {
                "test.py": {
                    "elements": [code_class]
                }
            },
            "documentation": {
                "test.md": {
                    "elements": [doc_with_ref]
                }
            }
        }
        
        context.set("analysis_results", analysis_results)
        
        # Execute pipeline
        relationships = pipeline.execute(context)
        
        # Verify cross-references were resolved
        assert len(relationships) > 0
        
        # Find reference relationship
        reference_rel = None
        for rel in relationships:
            if (rel.source_id == "doc_with_ref" and 
                rel.target_id == "class_id" and 
                rel.relationship_type == RelationshipType.REFERENCES):
                reference_rel = rel
                break
        
        # Verify reference was found
        assert reference_rel is not None
        assert reference_rel.metadata.get("source", "") == "cross_ref" 