"""Tests for the relationship mapping pipeline stages."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from proj_mapper.core.pipeline import PipelineContext
from proj_mapper.models.code import CodeElement, CodeElementType
from proj_mapper.models.documentation import DocumentationElement, DocumentationType
from proj_mapper.models.relationship import Relationship, RelationshipType
from proj_mapper.relationship.pipeline_stages import (
    RelationshipDetectionStage,
    RelationshipScoringStage,
    CrossReferenceResolutionStage,
    RelationshipGraphBuildingStage,
    RelationshipServiceStage,
    RelationshipService
)


class TestRelationshipDetectionStage:
    """Tests for the RelationshipDetectionStage class."""
    
    def test_process_with_missing_analysis_results(self):
        """Test process with missing analysis results."""
        # Setup
        stage = RelationshipDetectionStage()
        context = PipelineContext()
        
        # Execute and Assert
        with pytest.raises(ValueError, match="Analysis results not available in context"):
            stage.process(context, None)
    
    @patch('proj_mapper.relationship.detector.RelationshipDetector.detect_all_relationships')
    def test_process_with_valid_input(self, mock_detect):
        """Test process with valid input."""
        # Setup mock detector
        mock_relationships = [
            Relationship("code1", "doc1", RelationshipType.DOCUMENTS, confidence=0.8),
            Relationship("code2", "doc2", RelationshipType.REFERENCES, confidence=0.7)
        ]
        mock_detect.return_value = mock_relationships
        
        # Setup context
        context = PipelineContext()
        context.set_data("analysis_results", {
            "code": {
                "file1.py": {
                    "elements": [
                        CodeElement(
                            id="code1", 
                            name="Class1", 
                            element_type=CodeElementType.CLASS, 
                            file_path="file1.py", 
                            line_start=1,
                            line_end=10
                        ),
                        CodeElement(
                            id="code2", 
                            name="func1", 
                            element_type=CodeElementType.FUNCTION, 
                            file_path="file1.py", 
                            line_start=11,
                            line_end=20
                        )
                    ]
                }
            },
            "documentation": {
                "doc1.md": {
                    "elements": [
                        DocumentationElement(
                            title="doc1", 
                            element_type=DocumentationType.MARKDOWN, 
                            location="doc1.md", 
                            content="Class documentation"
                        ),
                        DocumentationElement(
                            title="doc2", 
                            element_type=DocumentationType.MARKDOWN, 
                            location="doc1.md", 
                            content="Function documentation"
                        )
                    ]
                }
            }
        })
        
        # Execute
        stage = RelationshipDetectionStage()
        result = stage.process(context, None)
        
        # Assert
        assert result == mock_relationships
        assert context.get_data("relationships") == mock_relationships
        assert context.get_data("code_elements") is not None
        assert context.get_data("doc_elements") is not None
        assert context.get_metadata("relationship_detection_count") == 2
        
        # Verify detector was called with correct elements
        code_elements = context.get_data("code_elements")
        doc_elements = context.get_data("doc_elements")
        mock_detect.assert_called_once_with(code_elements=code_elements, doc_elements=doc_elements)
    
    def test_extract_code_elements(self):
        """Test extracting code elements from analysis results."""
        # Setup
        stage = RelationshipDetectionStage()
        code_element = CodeElement(
            id="code1", 
            name="Class1", 
            element_type=CodeElementType.CLASS, 
            file_path="file1.py", 
            line_start=1,
            line_end=10
        )
        
        analysis_results = {
            "code": {
                "file1.py": {
                    "elements": [code_element]
                }
            }
        }
        
        # Execute
        result = stage._extract_code_elements(analysis_results)
        
        # Assert
        assert len(result) == 1
        assert result[0] == code_element
    
    def test_extract_doc_elements(self):
        """Test extracting documentation elements from analysis results."""
        # Setup
        stage = RelationshipDetectionStage()
        doc_element = DocumentationElement(
            title="doc1", 
            element_type=DocumentationType.SECTION, 
            location="doc1.md", 
            content="Content"
        )
        
        analysis_results = {
            "documentation": {
                "doc1.md": {
                    "elements": [doc_element]
                }
            }
        }
        
        # Execute
        result = stage._extract_doc_elements(analysis_results)
        
        # Assert
        assert len(result) == 1
        assert result[0] == doc_element


class TestRelationshipScoringStage:
    """Tests for the RelationshipScoringStage class."""
    
    @patch('proj_mapper.relationship.scoring.ConfidenceScorer.score_relationships')
    def test_process(self, mock_score):
        """Test process method."""
        # Setup
        stage = RelationshipScoringStage()
        context = PipelineContext()
        
        # Create input relationships
        input_relationships = [
            Relationship("code1", "doc1", RelationshipType.DOCUMENTS, confidence=0.0),
            Relationship("code2", "doc2", RelationshipType.REFERENCES, confidence=0.0)
        ]
        
        # Setup mock scorer output
        scored_relationships = [
            Relationship("code1", "doc1", RelationshipType.DOCUMENTS, confidence=0.8),
            Relationship("code2", "doc2", RelationshipType.REFERENCES, confidence=0.7)
        ]
        mock_score.return_value = scored_relationships
        
        # Execute
        result = stage.process(context, input_relationships)
        
        # Assert
        assert result == scored_relationships
        assert context.get_data("relationships") == scored_relationships
        assert context.get_metadata("relationship_scoring_completed") is True
        mock_score.assert_called_once_with(input_relationships)


class TestCrossReferenceResolutionStage:
    """Tests for the CrossReferenceResolutionStage class."""
    
    def test_process_with_missing_elements(self):
        """Test process with missing elements."""
        # Setup
        stage = CrossReferenceResolutionStage()
        context = PipelineContext()
        
        # Execute and Assert
        with pytest.raises(ValueError, match="Code and documentation elements not available in context"):
            stage.process(context, [])
    
    @patch('proj_mapper.relationship.cross_ref.CrossReferenceResolver.add_code_elements')
    @patch('proj_mapper.relationship.cross_ref.CrossReferenceResolver.add_documentation_elements')
    @patch('proj_mapper.relationship.cross_ref.CrossReferenceResolver.resolve_all_references')
    def test_process_with_valid_input(self, mock_resolve, mock_add_doc, mock_add_code):
        """Test process with valid input."""
        # Setup
        stage = CrossReferenceResolutionStage()
        context = PipelineContext()
        
        # Setup elements in context
        code_elements = [
            CodeElement(
                id="code1", 
                name="Class1", 
                element_type=CodeElementType.CLASS, 
                file_path="file1.py", 
                line_start=1,
                line_end=10
            )
        ]
        doc_elements = [
            DocumentationElement(
                title="doc1", 
                element_type=DocumentationType.SECTION, 
                location="doc1.md", 
                content="Content"
            )
        ]
        context.set_data("code_elements", code_elements)
        context.set_data("doc_elements", doc_elements)
        
        # Setup existing relationships
        existing_relationships = [
            Relationship("code1", "doc1", RelationshipType.DOCUMENTS, confidence=0.8)
        ]
        
        # Setup mock reference matches
        mock_match1 = MagicMock()
        mock_match1.to_relationship.return_value = Relationship(
            "code1", "doc2", RelationshipType.REFERENCES, confidence=0.7, metadata={"source": "cross_ref"}
        )
        mock_match2 = MagicMock()
        mock_match2.to_relationship.return_value = Relationship(
            "code2", "doc1", RelationshipType.REFERENCES, confidence=0.6, metadata={"source": "cross_ref"}
        )
        mock_resolve.return_value = [mock_match1, mock_match2]
        
        # Execute
        result = stage.process(context, existing_relationships)
        
        # Assert
        assert len(result) == 3  # 1 existing + 2 new
        assert context.get_metadata("reference_resolution_count") == 2
        mock_add_code.assert_called_once_with(code_elements)
        mock_add_doc.assert_called_once_with(doc_elements)
        mock_resolve.assert_called_once()


class TestRelationshipGraphBuildingStage:
    """Tests for the RelationshipGraphBuildingStage class."""
    
    @patch('proj_mapper.relationship.graph.RelationshipGraph.add_code_element')
    @patch('proj_mapper.relationship.graph.RelationshipGraph.add_documentation_element')
    @patch('proj_mapper.relationship.graph.RelationshipGraph.add_relationship')
    def test_process(self, mock_add_rel, mock_add_doc, mock_add_code):
        """Test process method."""
        # Setup
        stage = RelationshipGraphBuildingStage()
        context = PipelineContext()
        
        # Setup elements in context
        code_elements = [
            CodeElement(
                id="code1", 
                name="Class1", 
                element_type=CodeElementType.CLASS, 
                file_path="file1.py", 
                line_start=1,
                line_end=10
            )
        ]
        doc_elements = [
            DocumentationElement(
                title="doc1", 
                element_type=DocumentationType.SECTION, 
                location="doc1.md", 
                content="Content"
            )
        ]
        context.set_data("code_elements", code_elements)
        context.set_data("doc_elements", doc_elements)
        
        # Setup relationships
        relationships = [
            Relationship("code1", "doc1", RelationshipType.DOCUMENTS, confidence=0.8)
        ]
        
        # Set node and edge counts to mock stats
        stage.graph.nodes = {"code1": Mock(), "doc1": Mock()}
        stage.graph.edges = [Mock()]
        
        # Execute
        result = stage.process(context, relationships)
        
        # Assert
        assert result is stage.graph
        assert context.get_data("relationship_graph") is stage.graph
        assert context.get_metadata("graph_total_nodes") == 2
        assert context.get_metadata("graph_total_edges") == 1
        
        # Verify method calls
        assert mock_add_code.call_count == len(code_elements)
        assert mock_add_doc.call_count == len(doc_elements)
        assert mock_add_rel.call_count == len(relationships)


class TestRelationshipServiceStage:
    """Tests for the RelationshipServiceStage class."""
    
    def test_process(self):
        """Test process method."""
        # Setup
        stage = RelationshipServiceStage()
        context = PipelineContext()
        graph = Mock()
        
        # Execute
        result = stage.process(context, graph)
        
        # Assert
        assert isinstance(result, RelationshipService)
        assert result.graph is graph
        assert context.get_data("relationship_service") is result


class TestRelationshipService:
    """Tests for the RelationshipService class."""
    
    def test_get_related_elements_direct(self):
        """Test getting directly related elements."""
        # Setup
        graph = Mock()
        service = RelationshipService(graph)
        
        # Setup node with outgoing edges
        node = Mock()
        graph.get_node.return_value = node
        
        # Setup target nodes
        target1 = Mock()
        target1.id = "doc1"
        target1.node_type = "documentation"
        
        target2 = Mock()
        target2.id = "doc2"
        target2.node_type = "documentation"
        
        # Setup edges
        edge1 = Mock()
        edge1.target = target1
        edge1.relationship_type = "DOCUMENTS"
        edge1.confidence = 0.9
        edge1.metadata = {"key": "value1"}
        
        edge2 = Mock()
        edge2.target = target2
        edge2.relationship_type = "REFERENCES"
        edge2.confidence = 0.4  # Below threshold
        edge2.metadata = {"key": "value2"}
        
        # Setup outgoing edges on node
        node.outgoing_edges = [edge1, edge2]
        
        # Execute
        result = service.get_related_elements("code1", min_confidence=0.5)
        
        # Assert
        assert "DOCUMENTS" in result
        assert len(result["DOCUMENTS"]) == 1
        assert result["DOCUMENTS"][0]["id"] == "doc1"
        assert result["DOCUMENTS"][0]["confidence"] == 0.9
        assert "REFERENCES" not in result  # Filtered by confidence
    
    def test_find_relationships(self):
        """Test finding relationships with filters."""
        # Setup
        graph = Mock()
        service = RelationshipService(graph)
        
        # Setup edges
        edge1 = Mock()
        edge1.confidence = 0.9
        rel1 = Mock()
        edge1.to_relationship.return_value = rel1
        edge1.source.id = "code1"
        edge1.target.id = "doc1"
        edge1.relationship_type = "DOCUMENTS"
        edge1.confidence = 0.9
        
        edge2 = Mock()
        edge2.confidence = 0.7
        rel2 = Mock()
        edge2.to_relationship.return_value = rel2
        edge2.source.id = "code2"
        edge2.target.id = "doc2"
        edge2.relationship_type = "REFERENCES"
        edge2.confidence = 0.7
        
        # Setup graph methods
        graph.get_edges_by_type.side_effect = lambda t: [edge1] if t == "DOCUMENTS" else [edge2]
        graph.edges = [edge1, edge2]
        
        # Test 1: Filter by relationship type
        graph.get_edges_by_type.reset_mock()
        result1 = service.find_relationships(relationship_types=["DOCUMENTS"])
        graph.get_edges_by_type.assert_called_once_with("DOCUMENTS")
        assert len(result1) == 1
        assert result1[0] is rel1
        
        # Test 2: Filter by source
        result2 = service.find_relationships(source_id="code1")
        assert len(result2) == 1
        assert result2[0] is rel1
        
        # Test 3: Filter by target
        result3 = service.find_relationships(target_id="doc2")
        assert len(result3) == 1
        assert result3[0] is rel2
        
        # Test 4: Multiple filters
        result4 = service.find_relationships(
            source_id="code1",
            relationship_types=["DOCUMENTS"],
            min_confidence=0.8
        )
        assert len(result4) == 1
        assert result4[0] is rel1
    
    def test_get_relationship_stats(self):
        """Test getting relationship statistics."""
        # Setup
        graph = Mock()
        service = RelationshipService(graph)
        
        # Setup stats
        stats = {
            "total_nodes": 10,
            "total_edges": 15,
            "code_nodes": 5,
            "doc_nodes": 5
        }
        graph.get_stats.return_value = stats
        
        # Execute
        result = service.get_relationship_stats()
        
        # Assert
        assert result == stats
        graph.get_stats.assert_called_once() 