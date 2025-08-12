"""
Schemas package for O3 Code Generator

This package contains the input and output schema definitions.
"""

from .input_schema import CodeGenerationInput
from .output_schema import CodeGenerationOutput

__all__ = ["CodeGenerationInput", "CodeGenerationOutput"]
