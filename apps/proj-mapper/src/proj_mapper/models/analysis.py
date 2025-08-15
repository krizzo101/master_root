"""Analysis result models.

This module contains models that represent the results of file analysis.
"""

from typing import Dict, List, Optional, Any, Set, Union
from pathlib import Path

from pydantic import Field

from proj_mapper.models.base import BaseModel
from proj_mapper.models.code import CodeElement, CodeElementType, Location
from proj_mapper.models.documentation import DocumentationElement, DocumentationType
from proj_mapper.models.file import DiscoveredFile


class AnalysisResult(BaseModel):
    """Base class for all analysis results.
    
    Analysis results contain the extracted information from a file.
    """
    
    file_path: str = Field(..., description="Path to the analyzed file")
    success: bool = Field(True, description="Whether the analysis was successful")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CodeAnalysisResult(AnalysisResult):
    """Analysis result for code files.
    
    Contains extracted code elements from a file.
    """
    
    elements: List[CodeElement] = Field(default_factory=list, description="Extracted code elements")
    imports: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted imports")
    module_docstring: Optional[str] = Field(None, description="Module-level docstring")
    summary: Optional[str] = Field(None, description="Summary of the file")
    module_name: Optional[str] = Field(None, description="Module name")
    
    def add_element(self, element: CodeElement) -> None:
        """Add a code element to the result.
        
        Args:
            element: The code element to add
        """
        self.elements.append(element)
    
    def get_elements_by_type(self, element_type: Union[CodeElementType, str]) -> List[CodeElement]:
        """Get elements of a specific type.
        
        Args:
            element_type: The element type to filter by
            
        Returns:
            List of elements matching the type
        """
        if isinstance(element_type, str):
            element_type = CodeElementType(element_type)
        return [elem for elem in self.elements if elem.element_type == element_type]
    
    def add_import(self, import_from: Optional[str], import_what: str, alias: Optional[str] = None) -> None:
        """Add an import statement to the result.
        
        Args:
            import_from: Module imported from (None for direct imports)
            import_what: What was imported
            alias: Optional alias for the import
        """
        self.imports.append({
            "from": import_from,
            "import": import_what,
            "alias": alias
        })


class DocumentationAnalysisResult(AnalysisResult):
    """Analysis result for documentation files.
    
    Contains extracted documentation elements from a file.
    """
    
    elements: List[DocumentationElement] = Field(default_factory=list, 
                                               description="Extracted documentation elements")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extracted metadata")
    summary: Optional[str] = Field(None, description="Summary of the documentation")
    title: Optional[str] = Field(None, description="Document title")
    
    def add_element(self, element: DocumentationElement) -> None:
        """Add a documentation element to the result.
        
        Args:
            element: The documentation element to add
        """
        self.elements.append(element)
    
    def get_elements_by_type(
        self, element_type: Union[DocumentationType, str]
    ) -> List[DocumentationElement]:
        """Get elements of a specific type.
        
        Args:
            element_type: The element type to filter by
            
        Returns:
            List of elements matching the type
        """
        if isinstance(element_type, str):
            element_type = DocumentationType(element_type)
        return [elem for elem in self.elements if elem.element_type == element_type]
    
    def get_sections(self) -> List[DocumentationElement]:
        """Get all section elements.
        
        Returns:
            List of section elements
        """
        return self.get_elements_by_type(DocumentationType.SECTION)


class AnalysisResultCollection(BaseModel):
    """Collection of analysis results.
    
    This class represents the combined results of analyzing multiple files.
    """
    
    results: Dict[str, AnalysisResult] = Field(default_factory=dict, 
                                             description="Mapping of file paths to analysis results")
    code_results: Dict[str, CodeAnalysisResult] = Field(default_factory=dict, 
                                                      description="Mapping of file paths to code analysis results")
    doc_results: Dict[str, DocumentationAnalysisResult] = Field(default_factory=dict, 
                                                              description="Mapping of file paths to doc analysis results")
    
    def add_result(self, result: AnalysisResult) -> None:
        """Add an analysis result to the collection.
        
        Args:
            result: The analysis result to add
        """
        self.results[result.file_path] = result
        
        # Also add to type-specific collections
        if isinstance(result, CodeAnalysisResult):
            self.code_results[result.file_path] = result
        elif isinstance(result, DocumentationAnalysisResult):
            self.doc_results[result.file_path] = result
    
    def get_result(self, file_path: Union[str, Path]) -> Optional[AnalysisResult]:
        """Get the analysis result for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            The analysis result, or None if not found
        """
        return self.results.get(str(file_path))
    
    def get_code_result(self, file_path: Union[str, Path]) -> Optional[CodeAnalysisResult]:
        """Get the code analysis result for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            The code analysis result, or None if not found
        """
        return self.code_results.get(str(file_path))
    
    def get_doc_result(self, file_path: Union[str, Path]) -> Optional[DocumentationAnalysisResult]:
        """Get the documentation analysis result for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            The documentation analysis result, or None if not found
        """
        return self.doc_results.get(str(file_path))
    
    def get_all_code_elements(self) -> List[CodeElement]:
        """Get all code elements from all analysis results.
        
        Returns:
            List of all code elements
        """
        elements: List[CodeElement] = []
        for result in self.code_results.values():
            elements.extend(result.elements)
        return elements
    
    def get_all_doc_elements(self) -> List[DocumentationElement]:
        """Get all documentation elements from all analysis results.
        
        Returns:
            List of all documentation elements
        """
        elements: List[DocumentationElement] = []
        for result in self.doc_results.values():
            elements.extend(result.elements)
        return elements 