"""Integration tests for the Python analyzer with the pipeline system."""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional

import pytest

from proj_mapper.core.pipeline import Pipeline, PipelineContext, PipelineStage
from proj_mapper.analyzers.code.python import PythonAnalyzer
from proj_mapper.models.file import DiscoveredFile, FileType
from proj_mapper.models.code import CodeElementType


class PythonAnalysisStage(PipelineStage):
    """Pipeline stage for analyzing Python files."""
    
    def __init__(self):
        """Initialize the Python analysis stage."""
        self.analyzer = PythonAnalyzer()
    
    def process(self, context: PipelineContext, input_data: List[DiscoveredFile]) -> List[Dict[str, Any]]:
        """Process Python files through the analyzer.
        
        Args:
            context: The pipeline context
            input_data: List of discovered files
            
        Returns:
            List of analysis results
        """
        python_files = [f for f in input_data if f.file_type == FileType.PYTHON]
        
        results = []
        for file in python_files:
            try:
                result = self.analyzer.analyze(file)
                results.append({
                    "file": file,
                    "analysis": result,
                    "success": result.success
                })
            except Exception as e:
                results.append({
                    "file": file,
                    "error": str(e),
                    "success": False
                })
        
        # Update context with analysis results
        context.set("python_analysis_results", results)
        
        return results


@pytest.fixture
def test_project_dir():
    """Create a temporary directory with test Python files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple Python file
        simple_file = Path(temp_dir) / "simple.py"
        simple_content = '''
"""A simple Python module."""

import os
import sys

def hello_world():
    """Print a greeting."""
    print("Hello, world!")

class SimpleClass:
    """A simple class."""
    
    def __init__(self, name):
        """Initialize with a name."""
        self.name = name
        
    def greet(self):
        """Greet the person."""
        return f"Hello, {self.name}!"
'''
        with open(simple_file, 'w') as f:
            f.write(simple_content)

        # Create a more complex Python file with inheritance
        complex_file = Path(temp_dir) / "complex.py"
        complex_content = '''
"""A more complex Python module."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class BaseClass(ABC):
    """An abstract base class."""
    
    @abstractmethod
    def abstract_method(self):
        """An abstract method."""
        pass
        
    def concrete_method(self):
        """A concrete method."""
        return "concrete"

class ChildClass(BaseClass):
    """A child class implementing the abstract base."""
    
    def abstract_method(self):
        """Implementation of the abstract method."""
        return "implemented"
        
    def child_method(self):
        """A method specific to the child."""
        return "child"

def process_data(data: List[Dict]) -> Optional[Dict]:
    """Process a list of dictionaries.
    
    Args:
        data: The data to process
        
    Returns:
        Processed data or None
    """
    if not data:
        return None
        
    result = {}
    for item in data:
        for key, value in item.items():
            if key in result:
                result[key].append(value)
            else:
                result[key] = [value]
                
    return result
'''
        with open(complex_file, 'w') as f:
            f.write(complex_content)

        yield temp_dir


class TestPythonAnalyzerPipeline:
    """Integration tests for the Python analyzer pipeline."""
    
    def test_python_analyzer_pipeline(self, test_project_dir):
        """Test that the Python analyzer works correctly within a pipeline."""
        # Create discovered files
        project_path = Path(test_project_dir)
        
        simple_file = project_path / "simple.py"
        complex_file = project_path / "complex.py"
        
        discovered_files = [
            DiscoveredFile.from_path(simple_file, project_path),
            DiscoveredFile.from_path(complex_file, project_path)
        ]
        
        # Create and run pipeline
        pipeline = Pipeline()
        python_analysis_stage = PythonAnalysisStage()
        pipeline.add_stage(python_analysis_stage)
        
        results = pipeline.run(discovered_files)
        
        # Check results
        assert len(results) == 2
        assert all(r["success"] for r in results)
        
        # Check context
        context = pipeline.context
        assert context.contains("python_analysis_results")
        
        # Verify analysis results in context
        analysis_results = context.get("python_analysis_results")
        assert len(analysis_results) == 2
        
        # Check simple.py analysis
        simple_result = next(r for r in analysis_results 
                          if r["file"].relative_path == "simple.py")
        assert simple_result["success"]
        
        simple_analysis = simple_result["analysis"]
        assert simple_analysis.module_name
        assert simple_analysis.module_docstring == "A simple Python module."
        
        # Check complex.py analysis
        complex_result = next(r for r in analysis_results 
                           if r["file"].relative_path == "complex.py")
        assert complex_result["success"]
        
        complex_analysis = complex_result["analysis"]
        assert complex_analysis.module_name
        assert complex_analysis.module_docstring == "A more complex Python module." 