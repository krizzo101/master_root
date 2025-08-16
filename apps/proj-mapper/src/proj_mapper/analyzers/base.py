"""Base classes for analyzers.

This module defines the base classes used by all analyzers.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Union, TypeVar, Generic, Type

from proj_mapper.models.file import DiscoveredFile
from proj_mapper.models.code import CodeElement
from proj_mapper.models.documentation import DocumentationElement
from proj_mapper.models.base import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for elements - use BaseModel as the bound since both CodeElement and DocumentationElement derive from it
T = TypeVar('T', bound=BaseModel)


class AnalysisResult:
    """Base class for analysis results.
    
    This class provides the common interface for all analysis results,
    and implements basic functionality for tracking elements, imports,
    exports, and dependencies.
    """
    
    def __init__(self, file: Union[str, DiscoveredFile]):
        """Initialize the analysis result.
        
        Args:
            file: The file that was analyzed, either as a DiscoveredFile object
                or a string path
        """
        self.file_path = file.path if isinstance(file, DiscoveredFile) else str(file)
        self.success = True
        self.error_message = None
        self.elements = []  # List to store all elements
        self.imports = []
        self.exports = []
        self.dependencies = []
        self.module_name = None
        self.module_type = None
        self.documentation = None
        self.metadata = {}
    
    def add_element(self, element: BaseModel) -> None:
        """Add an element to the result.
        
        Args:
            element: The element to add
        """
        self.elements.append(element)
    
    def add_import(self, import_path: str, alias: Optional[str] = None) -> None:
        """Add an import to the result.
        
        Args:
            import_path: The import path
            alias: Optional alias used for the import
        """
        self.imports.append({
            'path': import_path,
            'alias': alias
        })
    
    def add_export(self, name: str, type_: str) -> None:
        """Add an export to the result.
        
        Args:
            name: The exported name
            type_: The type of export
        """
        self.exports.append({
            'name': name,
            'type': type_
        })
    
    def add_dependency(self, target: str, type_: str) -> None:
        """Add a dependency to the result.
        
        Args:
            target: The target of the dependency
            type_: The type of dependency
        """
        self.dependencies.append({
            'target': target,
            'type': type_
        })
    
    def set_module(self, name: str, type_: str) -> None:
        """Set the module information.
        
        Args:
            name: The module name
            type_: The module type
        """
        self.module_name = name
        self.module_type = type_
    
    def set_documentation(self, documentation: str) -> None:
        """Set the documentation.
        
        Args:
            documentation: The documentation
        """
        self.documentation = documentation
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set a metadata value.
        
        Args:
            key: The metadata key
            value: The metadata value
        """
        self.metadata[key] = value
    
    def get_elements(self, element_type: Type[T] = None) -> List[T]:
        """Get elements of a specific type.
        
        Args:
            element_type: Optional element type to filter by
            
        Returns:
            List of elements matching the specified type
        """
        if element_type is None:
            return self.elements
        
        return [elem for elem in self.elements if isinstance(elem, element_type)]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary.
        
        Returns:
            Dictionary representation of the result
        """
        elements_dict = [
            elem.to_dict() if hasattr(elem, 'to_dict') else str(elem)
            for elem in self.elements
        ]
        
        return {
            'file_path': self.file_path,
            'success': self.success,
            'error_message': self.error_message,
            'elements': elements_dict,
            'imports': self.imports,
            'exports': self.exports,
            'dependencies': self.dependencies,
            'module_name': self.module_name,
            'module_type': self.module_type,
            'documentation': self.documentation,
            'metadata': self.metadata
        }


class Analyzer(ABC):
    """Base class for all analyzers.
    
    An analyzer is responsible for analyzing a specific type of file,
    such as Python code, JavaScript code, Markdown documentation, etc.
    """
    
    @abstractmethod
    def can_analyze(self, file: DiscoveredFile) -> bool:
        """Check if this analyzer can analyze the given file.
        
        Args:
            file: The file to check
            
        Returns:
            True if this analyzer can handle the file
        """
        pass
    
    def get_file_filter(self) -> List[str]:
        """Get file patterns for selecting files for this analyzer.
        
        Returns:
            List of glob patterns for files this analyzer can handle
        """
        # Default implementation returns empty list
        # Subclasses should override this with specific patterns
        return []


class AnalyzerRegistry:
    """Registry for analyzer classes.
    
    This class provides a way to register and retrieve analyzers.
    """
    
    def __init__(self):
        """Initialize an empty analyzer registry."""
        self._analyzers: Dict[str, Type[Analyzer]] = {}
    
    def register_analyzer(self, analyzer_class: Type[Analyzer]) -> None:
        """Register an analyzer class.
        
        Args:
            analyzer_class: The analyzer class to register
        """
        name = analyzer_class.__name__
        self._analyzers[name] = analyzer_class
        logger.debug(f"Registered analyzer class: {name}")
    
    def get_analyzer(self, name: str) -> Optional[Type[Analyzer]]:
        """Get an analyzer class by name.
        
        Args:
            name: Name of the analyzer to get
            
        Returns:
            The analyzer class, or None if not found
        """
        return self._analyzers.get(name)
    
    def get_analyzer_for_file(self, file: DiscoveredFile) -> Optional[Analyzer]:
        """Get an analyzer for the specified file.
        
        Args:
            file: The file to get an analyzer for
            
        Returns:
            An analyzer that can analyze the file, or None if not found
        """
        # Try each registered analyzer class
        for analyzer_class in self._analyzers.values():
            analyzer = analyzer_class()
            if analyzer.can_analyze(file):
                logger.debug(f"Found analyzer {analyzer_class.__name__} for file: {file.relative_path}")
                return analyzer
        
        logger.debug(f"No analyzer found for file: {file.relative_path}")
        return None


class AnalyzerFactory:
    """Factory for creating appropriate analyzers.
    
    This class provides a way to create analyzers for specific files.
    """
    
    def __init__(self, registry: AnalyzerRegistry = None):
        """Initialize an analyzer factory.
        
        Args:
            registry: Optional analyzer registry to use (creates a new one if None)
        """
        self._registry = registry or AnalyzerRegistry()
        # Register built-in analyzers from the class registry
        for name, cls in Analyzer.get_registered_analyzers().items():
            self._registry.register_analyzer(cls)
    
    def get_analyzer_for_file(self, file: DiscoveredFile) -> Optional[Analyzer]:
        """Get an appropriate analyzer for the given file.
        
        Args:
            file: The file to get an analyzer for
            
        Returns:
            An analyzer instance if a suitable analyzer is found, None otherwise
        """
        # Try all registered analyzers
        for analyzer_class in self._registry.get_all_analyzers().values():
            analyzer = analyzer_class()
            if analyzer.can_analyze(file):
                logger.debug(f"Using {analyzer_class.__name__} for {file.relative_path}")
                return analyzer
        
        logger.debug(f"No suitable analyzer found for {file.relative_path}")
        return None 