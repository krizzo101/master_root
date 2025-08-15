"""JSON encoder utilities.

This module provides custom JSON encoders for project data.
"""

import json
from enum import Enum
from typing import Any, Dict, Type, Callable
from pathlib import Path

# Registry of serializer functions
_SERIALIZERS = {}

def register_serializer(cls: Type, serializer_func: Callable[[Any], Dict[str, Any]]) -> None:
    """Register a serializer function for a class.
    
    Args:
        cls: The class to register a serializer for
        serializer_func: Function that converts instances to dictionaries
    """
    _SERIALIZERS[cls] = serializer_func

# Import Location class without creating a circular import
try:
    from proj_mapper.models.code import Location
except ImportError:
    # Define a type for runtime checking only
    class Location:
        def to_dict(self):
            return {}


class EnumEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Enum values, Location objects, and Path objects.
    
    This encoder converts Enum objects to their string values, Location objects
    to dictionary representations, and Path objects to strings for JSON serialization.
    """
    
    def default(self, obj: Any) -> Any:
        """Override default encoding behavior.
        
        Args:
            obj: The object to encode
            
        Returns:
            JSON-serializable representation of the object
        """
        # Check for custom serializers first
        obj_type = type(obj)
        if obj_type in _SERIALIZERS:
            return _SERIALIZERS[obj_type](obj)
        
        if isinstance(obj, Enum):
            # Return the name of the enum value
            return obj.name
        elif isinstance(obj, Location):
            # Handle Location objects using their to_dict method
            return obj.to_dict()
        elif isinstance(obj, Path):
            # Convert Path objects to strings
            return str(obj)
        
        # Let the default encoder handle other types
        return super().default(obj) 