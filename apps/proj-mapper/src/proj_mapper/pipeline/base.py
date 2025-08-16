"""Base classes for the pipeline architecture."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class PipelineContext:
    """Context object passed between pipeline stages."""
    
    _results: Dict[str, Any] = field(default_factory=dict)
    
    def set_result(self, key: str, value: Any) -> None:
        """Set a result in the context.
        
        Args:
            key: Result key
            value: Result value
        """
        self._results[key] = value
        
    def get_result(self, key: str, default: Any = None) -> Any:
        """Get a result from the context.
        
        Args:
            key: Result key
            default: Default value if key not found
            
        Returns:
            Result value or default
        """
        return self._results.get(key, default)
        
    def has_result(self, key: str) -> bool:
        """Check if a result exists in the context.
        
        Args:
            key: Result key
            
        Returns:
            True if result exists, False otherwise
        """
        return key in self._results

class PipelineStage(ABC):
    """Base class for pipeline stages."""
    
    @abstractmethod
    def process(self, context: PipelineContext) -> PipelineContext:
        """Process the pipeline context.
        
        Args:
            context: Pipeline context
            
        Returns:
            Updated context
        """
        pass 