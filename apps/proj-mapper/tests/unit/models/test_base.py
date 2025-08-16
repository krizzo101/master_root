"""Unit tests for the BaseModel class."""

import pytest
from datetime import datetime
from pathlib import Path

from proj_mapper.models.base import BaseModel


class TestModel(BaseModel):
    """Test model for BaseModel tests."""
    
    name: str
    value: int
    optional_value: str = None
    nested_path: Path = None


def test_base_model_initialization():
    """Test BaseModel initialization with valid data."""
    model = TestModel(name="test", value=42)
    assert model.name == "test"
    assert model.value == 42
    assert model.optional_value is None


def test_base_model_from_dict():
    """Test creating a model from a dictionary."""
    data = {"name": "from_dict", "value": 100, "optional_value": "optional"}
    model = TestModel.from_dict(data)
    assert model.name == "from_dict"
    assert model.value == 100
    assert model.optional_value == "optional"


def test_base_model_to_dict():
    """Test converting a model to a dictionary."""
    model = TestModel(name="to_dict", value=200, optional_value="test")
    data = model.to_dict()
    assert isinstance(data, dict)
    assert data["name"] == "to_dict"
    assert data["value"] == 200
    assert data["optional_value"] == "test"


def test_base_model_with_path():
    """Test BaseModel with Path objects are properly handled."""
    path = Path("/test/path")
    model = TestModel(name="path_test", value=300, nested_path=path)
    data = model.to_dict()
    assert data["nested_path"] == str(path)
    
    # Test round-trip conversion
    new_model = TestModel.from_dict(data)
    # Pydantic automatically converts string paths back to Path objects based on type annotation
    assert isinstance(new_model.nested_path, Path)
    assert str(new_model.nested_path) == str(path)


def test_base_model_with_datetime():
    """Test BaseModel with datetime objects are properly handled."""
    # Create a custom model with datetime
    class DateTimeModel(BaseModel):
        timestamp: datetime
    
    now = datetime.now()
    model = DateTimeModel(timestamp=now)
    data = model.to_dict()
    assert data["timestamp"] == now.isoformat()


def test_base_model_model_version():
    """Test the model_version class variable."""
    assert hasattr(BaseModel, "model_version")
    assert BaseModel.model_version == "1.0.0"


def test_base_model_extra_fields():
    """Test BaseModel handling of extra fields."""
    # BaseModel should allow extra fields
    model = TestModel(name="extra", value=500, extra_field="extra")
    assert hasattr(model, "extra_field")
    assert model.extra_field == "extra" 