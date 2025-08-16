"""Unit tests for real_file module.

This module contains tests for functions and classes defined in real_file.py.
"""

import pytest

from src.tools.code_generation.o3_code_generator.real_file import (
    DataProcessor,
    transform_values,
)


def test_transform_values_success() -> None:
    """Test that transform_values returns correct sum."""
    assert transform_values(1, 2) == 3


def test_transform_values_type_error() -> None:
    """Test that transform_values raises TypeError for invalid input types."""
    with pytest.raises(TypeError):
        transform_values(1, "a")


class TestDataProcessor:
    """Unit tests for DataProcessor class methods."""

    def setup_method(self) -> None:
        """Initialize a DataProcessor instance before each test."""
        self.processor = DataProcessor()

    def test_process_data_int(self) -> None:
        """Test that process_data doubles integer inputs."""
        assert self.processor.process_data(5) == 10

    def test_process_data_str(self) -> None:
        """Test that process_data repeats string inputs."""
        assert self.processor.process_data("a") == "aa"

    def test_process_data_type_error(self) -> None:
        """Test that process_data raises TypeError for unsupported input types."""
        with pytest.raises(TypeError):
            self.processor.process_data(3.14)
