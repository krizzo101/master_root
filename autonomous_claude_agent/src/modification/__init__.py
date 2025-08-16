"""
Self-Modification System for Autonomous Claude Agent

This module provides safe, validated self-modification capabilities with:
- AST-based code manipulation
- Pattern-based code generation
- Comprehensive validation
- Automatic test generation
- Git version control integration
- Rollback capabilities

Created: 2025-08-15
"""

from .code_generator import CodeGenerator, CodeTemplate, ImprovementPattern, GeneratedCode

from .ast_modifier import ASTModifier, SafeModification, ModificationResult, ASTAnalyzer

from .validator import CodeValidator, ValidationResult, SecurityValidator, PerformanceValidator

from .test_generator import TestGenerator, TestCase, TestSuite, CoverageAnalyzer

from .version_control import VersionController, ModificationVersion, RollbackManager, ChangeTracker

__all__ = [
    # Code Generation
    "CodeGenerator",
    "CodeTemplate",
    "ImprovementPattern",
    "GeneratedCode",
    # AST Modification
    "ASTModifier",
    "SafeModification",
    "ModificationResult",
    "ASTAnalyzer",
    # Validation
    "CodeValidator",
    "ValidationResult",
    "SecurityValidator",
    "PerformanceValidator",
    # Test Generation
    "TestGenerator",
    "TestCase",
    "TestSuite",
    "CoverageAnalyzer",
    # Version Control
    "VersionController",
    "ModificationVersion",
    "RollbackManager",
    "ChangeTracker",
]

__version__ = "1.0.0"
