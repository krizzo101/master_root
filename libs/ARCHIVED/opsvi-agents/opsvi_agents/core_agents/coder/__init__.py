"""
Modularized CoderAgent - Advanced code generation, refactoring, and optimization.

This package provides a comprehensive, modular code generation system with:
- Multi-language support (16+ languages)
- Intelligent pattern recognition
- AST-based code manipulation
- Performance optimization
- Code quality analysis
"""

from .agent import CoderAgent
from .types import CodeAction, CodeSnippet, Language, RefactoringResult

__all__ = ["CoderAgent", "Language", "CodeAction", "CodeSnippet", "RefactoringResult"]

__version__ = "2.0.0"
