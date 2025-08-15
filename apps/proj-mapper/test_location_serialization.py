#!/usr/bin/env python3
"""Test script to verify Location object serialization."""

from proj_mapper.models.code import Location
from pydantic import BaseModel, Field
import json
from proj_mapper.utils.json_encoder import EnumEncoder


class TestModel(BaseModel):
    """Test model with Location field."""
    
    location: Location = Field(..., description="Test location field")


def test_location_serialization():
    """Test if Location objects can be properly serialized."""
    
    # Create a Location object
    loc = Location(file_path='test.py', start_line=1, end_line=10)
    
    # Test direct JSON serialization
    print("Direct JSON serialization:")
    print(json.dumps(loc, cls=EnumEncoder, indent=2))
    print("\n")
    
    # Test Pydantic model serialization
    test_model = TestModel(location=loc)
    
    # Convert to dict and serialize with our custom encoder
    model_dict = test_model.model_dump()
    print("Pydantic model serialization:")
    print(json.dumps(model_dict, cls=EnumEncoder, indent=2))


if __name__ == "__main__":
    test_location_serialization() 