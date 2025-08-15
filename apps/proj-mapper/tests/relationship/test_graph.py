"""Tests for the relationship graph module."""

import pytest
from unittest.mock import Mock
from pathlib import Path

from proj_mapper.models.code import CodeElement, CodeElementType, Location
from proj_mapper.models.documentation import DocumentationElement, DocumentationType
from proj_mapper.models.relationship import Relationship, RelationshipType
from proj_mapper.relationship.graph import Node, Edge, RelationshipGraph


class TestNode:
    """Tests for the Node class."""
    
    def test_init(self):
        """Test node initialization."""
        node = Node("test_id", CodeElementType.CLASS, {"name": "test"})
        
        assert node.id == "test_id"
        assert node.node_type == CodeElementType.CLASS
        assert node.data == {"name": "test"}
        assert node.outgoing_edges == []
        assert node.incoming_edges == []
    
    def test_add_outgoing_edge(self):
        """Test adding outgoing edge."""
        source = Node("source", CodeElementType.CLASS, {})
        target = Node("target", DocumentationType.SECTION, {})
        edge = Edge(source, target, RelationshipType.REFERENCES, 0.8, {})
        
        source.add_outgoing_edge(edge)
        
        assert edge in source.outgoing_edges
        assert len(source.outgoing_edges) == 1
    
    def test_add_incoming_edge(self):
        """Test adding incoming edge."""
        source = Node("source", CodeElementType.CLASS, {})
        target = Node("target", DocumentationType.SECTION, {})
        edge = Edge(source, target, RelationshipType.REFERENCES, 0.8, {})
        
        target.add_incoming_edge(edge)
        
        assert edge in target.incoming_edges
        assert len(target.incoming_edges) == 1
    
    def test_str_representation(self):
        """Test string representation."""
        node = Node("test_id", CodeElementType.CLASS, {"name": "TestClass"})
        
        # Check that the string representation contains the id and type
        assert "test_id" in str(node)
        assert "CLASS" in str(node) or "CodeElementType.CLASS" in str(node)


class TestEdge:
    """Tests for the Edge class."""
    
    def test_init(self):
        """Test edge initialization."""
        source = Node("source", CodeElementType.CLASS, {})
        target = Node("target", DocumentationType.SECTION, {})
        edge = Edge(source, target, RelationshipType.REFERENCES, 0.8, {"detection_rule": "test"})
        
        assert edge.source == source
        assert edge.target == target
        assert edge.relationship_type == RelationshipType.REFERENCES
        assert edge.confidence == 0.8
        assert edge.metadata == {"detection_rule": "test"}
    
    def test_to_relationship(self):
        """Test conversion to relationship."""
        source = Node("source", CodeElementType.CLASS, {"name": "TestClass"})
        target = Node("target", DocumentationType.SECTION, {"name": "TestDoc"})
        edge = Edge(source, target, RelationshipType.REFERENCES, 0.8, {"detection_rule": "test"})
        
        relationship = edge.to_relationship()
        
        assert isinstance(relationship, Relationship)
        assert relationship.source_id == "source"
        assert relationship.target_id == "target"
        assert relationship.relationship_type == RelationshipType.REFERENCES
        assert relationship.confidence == 0.8
        assert relationship.metadata == {"detection_rule": "test"}
    
    def test_str_representation(self):
        """Test string representation."""
        source = Node("source", CodeElementType.CLASS, {})
        target = Node("target", DocumentationType.SECTION, {})
        edge = Edge(source, target, RelationshipType.REFERENCES, 0.8, {})
        
        # Check that the string representation contains the ids and relationship type
        assert "source" in str(edge)
        assert "target" in str(edge)
        assert "REFERENCES" in str(edge)
        assert "0.8" in str(edge)


class TestRelationshipGraph:
    """Tests for the RelationshipGraph class."""
    
    def test_init(self):
        """Test graph initialization."""
        graph = RelationshipGraph()
        
        assert graph.nodes == {}
        assert graph.edges == []
        assert isinstance(graph._node_type_cache, dict)
    
    def test_add_code_element(self):
        """Test adding code element."""
        graph = RelationshipGraph()
        
        element = CodeElement(
            id="test_id",
            name="TestClass",
            element_type=CodeElementType.CLASS,
            file_path="test.py",
            line_start=1,
            line_end=10
        )
        
        node = graph.add_code_element(element)
        
        assert node.id == "test_id"
        assert node.node_type == CodeElementType.CLASS
        assert node.data == element
        assert CodeElementType.CLASS in graph._node_type_cache
        assert "test_id" in graph._node_type_cache[CodeElementType.CLASS]
    
    def test_add_documentation_element(self):
        """Test adding documentation element."""
        graph = RelationshipGraph()
        
        element = DocumentationElement(
            title="Test Doc",
            element_type=DocumentationType.SECTION,
            location=Location(file_path="doc.md", start_line=1, end_line=10),
            content="Test content"
        )
        
        node = graph.add_documentation_element(element)
        
        assert node.id == "Test Doc"
        assert node.node_type == DocumentationType.SECTION
        assert node.data == element
        assert DocumentationType.SECTION in graph._node_type_cache
        assert "Test Doc" in graph._node_type_cache[DocumentationType.SECTION]
    
    def test_add_edge(self):
        """Test adding edge."""
        graph = RelationshipGraph()
        
        # Add nodes first
        code_element = CodeElement(
            id="code_id",
            name="TestClass",
            element_type=CodeElementType.CLASS,
            file_path="test.py",
            line_start=1,
            line_end=10
        )
        
        doc_element = DocumentationElement(
            title="Test Doc",
            element_type=DocumentationType.SECTION,
            location=Location(file_path="doc.md", start_line=1, end_line=10),
            content="Test content"
        )
        
        source_node = graph.add_code_element(code_element)
        target_node = graph.add_documentation_element(doc_element)
        
        # Add edge
        edge = graph.add_edge(
            source_id="code_id",
            target_id="Test Doc",
            relationship_type=RelationshipType.DOCUMENTS,
            confidence=0.9,
            metadata={"key": "value"}
        )
        
        assert edge is not None
        assert edge in graph.edges
        assert edge in source_node.outgoing_edges
        assert edge in target_node.incoming_edges
        assert edge.relationship_type == RelationshipType.DOCUMENTS
        assert edge.confidence == 0.9
        assert edge.metadata == {"key": "value"}
    
    def test_add_edge_nonexistent_nodes(self):
        """Test adding edge with nonexistent nodes."""
        graph = RelationshipGraph()
        
        # Should return None, not raise an exception
        edge = graph.add_edge(
            source_id="nonexistent1",
            target_id="nonexistent2",
            relationship_type=RelationshipType.DOCUMENTS,
            confidence=0.9
        )
        
        assert edge is None
    
    def test_add_relationship(self):
        """Test adding relationship."""
        graph = RelationshipGraph()
        
        # Add nodes first
        code_element = CodeElement(
            id="code_id",
            name="TestClass",
            element_type=CodeElementType.CLASS,
            file_path="test.py",
            line_start=1,
            line_end=10
        )
        
        doc_element = DocumentationElement(
            title="Test Doc",
            element_type=DocumentationType.SECTION,
            location=Location(file_path="doc.md", start_line=1, end_line=10),
            content="Test content"
        )
        
        graph.add_code_element(code_element)
        graph.add_documentation_element(doc_element)
        
        # Create relationship
        relationship = Relationship(
            source_id="code_id",
            source_type="code",
            target_id="Test Doc",
            target_type="doc",
            relationship_type=RelationshipType.DOCUMENTS,
            confidence=0.9,
            metadata={"key": "value"}
        )
        
        # Add relationship
        edge = graph.add_relationship(relationship)
        
        assert edge is not None
        assert edge in graph.edges
        assert edge.relationship_type == RelationshipType.DOCUMENTS
        assert edge.confidence == 0.9
        assert edge.metadata == {"key": "value"}
    
    def test_get_node(self):
        """Test getting node."""
        graph = RelationshipGraph()
        
        code_element = CodeElement(
            id="test_id",
            name="TestClass",
            element_type=CodeElementType.CLASS,
            file_path="test.py",
            line_start=1,
            line_end=10
        )
        
        graph.add_code_element(code_element)
        
        node = graph.get_node("test_id")
        
        assert node.id == "test_id"
        assert node.data == code_element
        
        # Non-existent node
        assert graph.get_node("non_existent") is None
    
    def test_get_nodes_by_type(self):
        """Test getting nodes by type."""
        graph = RelationshipGraph()
        
        code_element1 = CodeElement(
            id="code1",
            name="TestClass1",
            element_type=CodeElementType.CLASS,
            file_path="test1.py",
            line_start=1,
            line_end=10
        )
        
        code_element2 = CodeElement(
            id="code2",
            name="TestClass2",
            element_type=CodeElementType.CLASS,
            file_path="test2.py",
            line_start=1,
            line_end=10
        )
        
        doc_element = DocumentationElement(
            title="Test Doc",
            element_type=DocumentationType.SECTION,
            location=Location(file_path="doc.md", start_line=1, end_line=10),
            content="Test content"
        )
        
        graph.add_code_element(code_element1)
        graph.add_code_element(code_element2)
        graph.add_documentation_element(doc_element)
        
        code_nodes = graph.get_nodes_by_type(CodeElementType.CLASS)
        doc_nodes = graph.get_nodes_by_type(DocumentationType.SECTION)
        
        assert len(code_nodes) == 2
        assert len(doc_nodes) == 1
        assert all(node.node_type == CodeElementType.CLASS for node in code_nodes)
        assert all(node.node_type == DocumentationType.SECTION for node in doc_nodes)
    
    def test_get_relationships(self):
        """Test getting relationships."""
        graph = RelationshipGraph()
        
        # Add nodes
        code_element = CodeElement(
            id="code_id",
            name="TestClass",
            element_type=CodeElementType.CLASS,
            file_path="test.py",
            line_start=1,
            line_end=10
        )
        
        doc_element1 = DocumentationElement(
            title="Test Doc 1",
            element_type=DocumentationType.SECTION,
            location=Location(file_path="doc1.md", start_line=1, end_line=10),
            content="Test content 1"
        )
        
        doc_element2 = DocumentationElement(
            title="Test Doc 2",
            element_type=DocumentationType.SECTION,
            location=Location(file_path="doc2.md", start_line=1, end_line=10),
            content="Test content 2"
        )
        
        graph.add_code_element(code_element)
        graph.add_documentation_element(doc_element1)
        graph.add_documentation_element(doc_element2)
        
        # Add edges
        graph.add_edge(
            source_id="code_id",
            target_id="Test Doc 1",
            relationship_type=RelationshipType.DOCUMENTS,
            confidence=0.9
        )
        
        graph.add_edge(
            source_id="code_id",
            target_id="Test Doc 2",
            relationship_type=RelationshipType.REFERENCES,
            confidence=0.7
        )
        
        # Get all relationships
        all_relationships = graph.get_relationships()
        assert len(all_relationships) == 2
        
        # Get relationships by source
        source_rels = graph.get_relationships(source_id="code_id")
        assert len(source_rels) == 2
        
        # Get relationships by target
        target_rels = graph.get_relationships(target_id="Test Doc 1")
        assert len(target_rels) == 1
        assert target_rels[0].target_id == "Test Doc 1"
        
        # Get relationships by type
        type_rels = graph.get_relationships(relationship_type=RelationshipType.DOCUMENTS)
        assert len(type_rels) == 1
        assert type_rels[0].relationship_type == RelationshipType.DOCUMENTS
        
        # Get relationships by confidence
        conf_rels = graph.get_relationships(min_confidence=0.8)
        assert len(conf_rels) == 1
        assert conf_rels[0].confidence >= 0.8
    
    def test_get_related_nodes(self):
        """Test getting related nodes."""
        graph = RelationshipGraph()
        
        # Add nodes
        code_element = CodeElement(
            id="code_id",
            name="TestClass",
            element_type=CodeElementType.CLASS,
            file_path="test.py",
            line_start=1,
            line_end=10
        )
        
        doc_element1 = DocumentationElement(
            title="Test Doc 1",
            element_type=DocumentationType.SECTION,
            location=Location(file_path="doc1.md", start_line=1, end_line=10),
            content="Test content 1"
        )
        
        doc_element2 = DocumentationElement(
            title="Test Doc 2",
            element_type=DocumentationType.SECTION,
            location=Location(file_path="doc2.md", start_line=1, end_line=10),
            content="Test content 2"
        )
        
        graph.add_code_element(code_element)
        graph.add_documentation_element(doc_element1)
        graph.add_documentation_element(doc_element2)
        
        # Add edges
        graph.add_edge(
            source_id="code_id",
            target_id="Test Doc 1",
            relationship_type=RelationshipType.DOCUMENTS,
            confidence=0.9
        )
        
        graph.add_edge(
            source_id="code_id",
            target_id="Test Doc 2",
            relationship_type=RelationshipType.REFERENCES,
            confidence=0.7
        )
        
        # Get all related nodes
        related_nodes = graph.get_related_nodes("code_id")
        assert len(related_nodes) == 2
        
        # Get related nodes by relationship type
        type_nodes = graph.get_related_nodes("code_id", relationship_type=RelationshipType.DOCUMENTS)
        assert len(type_nodes) == 1
        assert type_nodes[0].id == "Test Doc 1"
        
        # Get related nodes by confidence
        conf_nodes = graph.get_related_nodes("code_id", min_confidence=0.8)
        assert len(conf_nodes) == 1
        assert conf_nodes[0].id == "Test Doc 1"
        
        # Get related nodes by direction (outgoing only)
        outgoing_nodes = graph.get_related_nodes("code_id", outgoing=True, incoming=False)
        assert len(outgoing_nodes) == 2
        
        # Get related nodes by direction (incoming only)
        incoming_nodes = graph.get_related_nodes("code_id", outgoing=False, incoming=True)
        assert len(incoming_nodes) == 0
        
        # Get related nodes for a documentation node
        doc_related = graph.get_related_nodes("Test Doc 1")
        assert len(doc_related) == 1
        assert doc_related[0].id == "code_id"
    
    def test_serialize(self):
        """Test serializing the graph."""
        graph = RelationshipGraph()
        
        # Add nodes
        code_element = CodeElement(
            id="code_id",
            name="TestClass",
            element_type=CodeElementType.CLASS,
            file_path="test.py",
            line_start=1,
            line_end=10
        )
        
        doc_element = DocumentationElement(
            title="Test Doc",
            element_type=DocumentationType.SECTION,
            location=Location(file_path="doc.md", start_line=1, end_line=10),
            content="Test content"
        )
        
        graph.add_code_element(code_element)
        graph.add_documentation_element(doc_element)
        
        # Add edge
        graph.add_edge(
            source_id="code_id",
            target_id="Test Doc",
            relationship_type=RelationshipType.DOCUMENTS,
            confidence=0.9,
            metadata={"key": "value"}
        )
        
        # Serialize
        data = graph.serialize()
        
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1
        assert "code_id" in data["nodes"]
        assert data["nodes"]["code_id"]["id"] == "code_id"
        assert data["edges"][0]["source"] == "code_id"
        assert data["edges"][0]["target"] == "Test Doc"
        assert data["edges"][0]["relationship_type"] == RelationshipType.DOCUMENTS.value
    
    def test_to_json(self):
        """Test converting graph to JSON."""
        graph = RelationshipGraph()
        
        # Add a node
        code_element = CodeElement(
            id="code_id",
            name="TestClass",
            element_type=CodeElementType.CLASS,
            file_path="test.py",
            line_start=1,
            line_end=10
        )
        
        graph.add_code_element(code_element)
        
        # Convert to JSON
        json_str = graph.to_json()
        
        assert "code_id" in json_str
        assert "nodes" in json_str
        assert "edges" in json_str
    
    def test_str_representation(self):
        """Test string representation."""
        graph = RelationshipGraph()
        
        graph.add_code_element(CodeElement(
            id="code_id",
            name="TestClass",
            element_type=CodeElementType.CLASS,
            file_path="test.py",
            line_start=1,
            line_end=10
        ))
        
        # Check that the string representation contains node and edge counts
        assert "nodes=1" in str(graph) or "nodes=1," in str(graph)
        assert "edges=0" in str(graph) or "edges=0," in str(graph) 