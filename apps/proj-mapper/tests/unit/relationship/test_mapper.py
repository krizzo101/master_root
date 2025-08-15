"""Unit tests for the relationship mapper."""

import pytest
from typing import Dict, List, Any

from proj_mapper.models.code import CodeElement, CodeElementType, Location
from proj_mapper.models.documentation import DocumentationElement, DocumentationType
from proj_mapper.models.relationship import RelationshipType, Relationship
from proj_mapper.relationship.mapper import RelationshipMapper


@pytest.fixture
def code_elements() -> List[CodeElement]:
    """Create sample code elements for testing."""
    elements = []
    
    # Create a class element
    class_element = CodeElement(
        id="class_1",
        name="TestClass",
        element_type=CodeElementType.CLASS,
        file_path="/path/to/file.py",
        line_start=1,
        line_end=20,
        docstring="This is a test class for demonstration.",
        visibility="public",
        metadata={"base_classes": ["BaseClass"]}
    )
    # Add base_classes to make it available directly
    class_element.metadata["base_classes"] = ["BaseClass"]
    elements.append(class_element)
    
    # Create a method element
    method_element = CodeElement(
        id="method_1",
        name="test_method",
        element_type=CodeElementType.FUNCTION,
        file_path="/path/to/file.py",
        line_start=5,
        line_end=10,
        docstring="This method does testing.",
        visibility="public",
        metadata={"parent_class": "class_1"}
    )
    elements.append(method_element)
    
    # Create a base class element
    base_class_element = CodeElement(
        id="class_2",
        name="BaseClass",
        element_type=CodeElementType.CLASS,
        file_path="/path/to/base.py",
        line_start=1,
        line_end=20,
        docstring="This is a base class.",
        visibility="public",
        metadata={}
    )
    elements.append(base_class_element)
    
    return elements


@pytest.fixture
def doc_elements() -> List[DocumentationElement]:
    """Create sample documentation elements for testing."""
    elements = []
    
    # Create a section element
    section_element = DocumentationElement(
        title="doc_1",
        element_type=DocumentationType.SECTION,
        location=Location(file_path="/path/to/doc.md", start_line=1, end_line=5),
        content="# Test Documentation\n\nThis is documentation for TestClass and test_method.",
        parent=None
    )
    elements.append(section_element)
    
    # Create a code block element
    code_block_element = DocumentationElement(
        title="doc_2",
        element_type=DocumentationType.CODE_BLOCK,
        location=Location(file_path="/path/to/doc.md", start_line=6, end_line=10),
        content="```python\nclass TestClass(BaseClass):\n    def test_method(self):\n        pass\n```",
        parent="doc_1"
    )
    elements.append(code_block_element)
    
    return elements


class TestRelationshipMapper:
    """Tests for the RelationshipMapper class."""
    
    def test_initialization(self):
        """Test mapper initialization."""
        mapper = RelationshipMapper()
        assert mapper is not None
        assert hasattr(mapper, 'code_elements')
        assert hasattr(mapper, 'doc_elements')
        assert hasattr(mapper, 'relationships')
    
    def test_add_elements(self, code_elements, doc_elements):
        """Test adding elements to the mapper."""
        mapper = RelationshipMapper()
        
        # Add code elements
        mapper.add_code_elements(code_elements)
        assert len(mapper.code_elements) == len(code_elements)
        
        # Add doc elements
        mapper.add_doc_elements(doc_elements)
        assert len(mapper.doc_elements) == len(doc_elements)
    
    def test_map_relationships(self, code_elements, doc_elements):
        """Test mapping relationships between elements."""
        mapper = RelationshipMapper()
        mapper.add_code_elements(code_elements)
        mapper.add_doc_elements(doc_elements)
        
        # Map relationships
        relationships = mapper.map_relationships()
        
        # Verify relationships were created
        assert len(relationships) > 0
        
        # Check for doc -> code references
        doc_to_code_refs = [r for r in relationships if 
                           r.source_type == "documentation" and 
                           r.target_type == "code"]
        assert len(doc_to_code_refs) > 0
        
        # Check for parent-child doc relationships
        doc_hierarchy_refs = [r for r in relationships if 
                             r.source_type == "documentation" and 
                             r.target_type == "documentation"]
        assert len(doc_hierarchy_refs) > 0
    
    def test_confidence_calculation(self, code_elements, doc_elements):
        """Test confidence score calculation."""
        mapper = RelationshipMapper()
        
        # Get a code and doc element
        code_element = code_elements[0]  # TestClass
        doc_element = doc_elements[1]    # Code block with TestClass
        
        # Calculate confidence
        confidence = mapper._calculate_confidence(doc_element, code_element)
        
        # Should have high confidence for code in code block
        assert confidence > 0.7
    
    def test_context_extraction(self):
        """Test context extraction around references."""
        mapper = RelationshipMapper()
        
        content = "This is a test context with TestClass appearing in the middle."
        reference = "testclass"
        
        context = mapper._extract_context(content.lower(), reference, context_size=10)
        
        # Check that the context contains the reference
        assert reference in context.lower()
        # Check that the context is shorter than the full content
        assert len(context) < len(content) 