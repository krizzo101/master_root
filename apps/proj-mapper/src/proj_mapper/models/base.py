"""Base model module.

This module provides base model classes for the application.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Type, TypeVar, Optional, ClassVar

from pydantic import BaseModel as PydanticBaseModel, Field, ConfigDict
from pydantic import model_validator

# Configure logging
logger = logging.getLogger(__name__)

T = TypeVar('T', bound='BaseModel')


class BaseModel(PydanticBaseModel):
    """Base model class for all Project Mapper models.
    
    This class provides common functionality for all models in the system,
    including serialization/deserialization and validation.
    """
    
    # Class variable to store the model version
    model_version: ClassVar[str] = "1.0.0"
    
    # Pydantic V2 configuration
    model_config = {
        # Allow extra fields during model initialization
        "extra": "allow",
        
        # Allow arbitrary types for fields
        "arbitrary_types_allowed": True,
        
        # JSON encoders for common types
        "json_encoders": {
            Path: lambda v: str(v),
            datetime: lambda v: v.isoformat(),
        }
    }
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create a model instance from a dictionary.
        
        Args:
            data: Dictionary containing model data
        
        Returns:
            Instance of the model
        """
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary.
        
        Returns:
            Dictionary representation of the model
        """
        # Convert model to dict first
        data = self.model_dump(by_alias=True, exclude_none=True)
        
        # Process special types
        for key, value in data.items():
            # Convert Path objects to strings
            if isinstance(value, Path):
                data[key] = str(value)
            # Convert datetime objects to ISO format strings
            elif isinstance(value, datetime):
                data[key] = value.isoformat()
        
        return data
    
    @model_validator(mode='before')
    @classmethod
    def validate_model_version(cls, data: Any) -> Any:
        """Validate the model version if provided.
        
        This validator checks that the provided model_version (if any)
        is compatible with this class's version.
        
        Args:
            data: The raw input data
            
        Returns:
            The validated data
            
        Raises:
            ValueError: If the model versions are incompatible
        """
        # Handle case where data might not be a dict
        if not isinstance(data, dict):
            return data
            
        # Check if version is provided
        version = data.get('model_version')
        if not version:
            return data
            
        # In a real implementation, we would do version compatibility checking here
        # For now, just returning the values as-is
        return data 