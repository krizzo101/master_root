"""
O3 Code Generator Utilities - Shared utility modules for eliminating code duplication.

This package provides centralized utility modules that eliminate ~3,000+ lines of
duplicated code across the O3 Code Generator application.
"""

__version__ = "1.0.0"
__author__ = "O3 Code Generator Team"
__all__ = [
    "BaseProcessor",
    "DirectoryManager",
    "FileGenerator",
    "UniversalInputLoader",
    "O3ModelGenerator",
    "OpenAIModel",
    "OutputFormatter",
    "PromptBuilder",
]

# Thin alias for backward-compatibility with refactored code
from .o3_model_generator import O3ModelGenerator as OpenAIModel
