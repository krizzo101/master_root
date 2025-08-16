"""Integration test demonstrating relationship mapping functionality."""

import pytest
from proj_mapper.relationship.function_analyzer import FunctionCallAnalyzer
from proj_mapper.relationship.mapper import RelationshipMapper
from proj_mapper.models.code import CodeElement, CodeElementType
from proj_mapper.models.documentation import DocumentationElement, DocumentationType
from proj_mapper.models.relationship import RelationshipType

def test_relationship_mapping_demo():
    """Demonstrate the relationship mapping functionality with a realistic example."""
    
    # Example code that will be analyzed
    example_code = '''
class DataProcessor:
    """Process data using various transformations.
    
    See the data_processing_guide.md for detailed usage.
    """
    
    def __init__(self):
        self.data = None
        
    def load_data(self, filename):
        """Load data from a file.
        
        Args:
            filename: Path to data file
        """
        self.data = self._read_file(filename)
        return self.data
        
    def _read_file(self, filename):
        """Internal method to read file contents."""
        return []
        
    def process(self):
        """Process the loaded data.
        
        Applies transformations as described in the processing guide.
        """
        if not self.data:
            raise ValueError("No data loaded")
            
        self.validate_data()
        result = self.transform_data()
        return result
        
    def validate_data(self):
        """Validate the data format."""
        return True
        
    def transform_data(self):
        """Apply data transformations."""
        return self.data
'''

    # Create code elements
    class_element = CodeElement(
        id="DataProcessor",
        name="DataProcessor",
        element_type=CodeElementType.CLASS,
        location="example.py",
        file_path="example.py",
        line_start=1,
        docstring="""Process data using various transformations.
    
    See the data_processing_guide.md for detailed usage."""
    )
    
    load_data_element = CodeElement(
        id="DataProcessor.load_data",
        name="load_data",
        element_type=CodeElementType.METHOD,
        location="example.py",
        file_path="example.py",
        line_start=10,
        docstring="""Load data from a file.
        
        Args:
            filename: Path to data file""",
        metadata={"parent_id": "DataProcessor", "body": "self.data = self._read_file(filename)"}
    )
    
    read_file_element = CodeElement(
        id="DataProcessor._read_file",
        name="_read_file",
        element_type=CodeElementType.METHOD,
        location="example.py",
        file_path="example.py",
        line_start=20,
        docstring="Internal method to read file contents.",
        metadata={"parent_id": "DataProcessor"}
    )
    
    process_element = CodeElement(
        id="DataProcessor.process",
        name="process",
        element_type=CodeElementType.METHOD,
        location="example.py",
        file_path="example.py",
        line_start=30,
        docstring="""Process the loaded data.
        
        Applies transformations as described in the processing guide.""",
        metadata={"parent_id": "DataProcessor", "body": """if not self.data:
            raise ValueError("No data loaded")
            
        self.validate_data()
        result = self.transform_data()
        return result"""}
    )
    
    validate_data_element = CodeElement(
        id="DataProcessor.validate_data",
        name="validate_data",
        element_type=CodeElementType.METHOD,
        location="example.py",
        file_path="example.py",
        line_start=40,
        docstring="Validate the data format.",
        metadata={"parent_id": "DataProcessor"}
    )
    
    transform_data_element = CodeElement(
        id="DataProcessor.transform_data",
        name="transform_data",
        element_type=CodeElementType.METHOD,
        location="example.py",
        file_path="example.py",
        line_start=45,
        docstring="Apply data transformations.",
        metadata={"parent_id": "DataProcessor"}
    )
    
    # Create documentation element
    doc_element = DocumentationElement(
        title="data_processing_guide.md",
        element_type=DocumentationType.MARKDOWN,
        location="docs/data_processing_guide.md",
        content="""# Data Processing Guide
        
        The DataProcessor class provides functionality for loading and processing data.
        Key methods include:
        - load_data: Loads data from files
        - process: Applies transformations to the data
        """
    )
    
    # Create relationship mapper
    mapper = RelationshipMapper()
    mapper.add_code_elements([
        class_element,
        load_data_element,
        read_file_element,
        process_element,
        validate_data_element,
        transform_data_element
    ])
    mapper.add_doc_elements([doc_element])
    
    # Map relationships
    relationships = mapper.map_relationships()
    
    # Verify relationships were found
    doc_refs = [r for r in relationships if r.relationship_type == RelationshipType.REFERENCES]
    calls = [r for r in relationships if r.relationship_type == RelationshipType.CALLS]
    
    # Documentation should reference the class
    assert any(r.source_id == "data_processing_guide.md" and r.target_id == "DataProcessor" 
              for r in doc_refs), "Documentation should reference DataProcessor class"
              
    # Class should reference documentation
    assert any(r.source_id == "DataProcessor" and r.target_id == "data_processing_guide.md" 
              for r in doc_refs), "Class should reference documentation guide"
              
    # Process method should call validate_data and transform_data
    process_calls = [r for r in calls if r.source_id == "DataProcessor.process"]
    assert len(process_calls) == 2, "Process method should make two calls"
    assert any(r.target_id == "DataProcessor.validate_data" for r in process_calls)
    assert any(r.target_id == "DataProcessor.transform_data" for r in process_calls)
    
    # Load data should call read_file
    load_data_calls = [r for r in calls if r.source_id == "DataProcessor.load_data"]
    assert len(load_data_calls) == 1, "Load data should call read_file"
    assert load_data_calls[0].target_id == "DataProcessor._read_file"
    
    # Verify confidence scores
    for relationship in relationships:
        assert 0 < relationship.confidence <= 1, "Confidence scores should be between 0 and 1"
        
        # Method calls should have high confidence
        if relationship.relationship_type == RelationshipType.CALLS:
            assert relationship.confidence >= 0.9, "Method calls should have high confidence" 