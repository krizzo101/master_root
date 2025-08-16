"""
Type definitions for the CoderAgent module.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class CodeAction(Enum):
    """Code manipulation actions."""
    GENERATE = "generate"
    REFACTOR = "refactor"
    OPTIMIZE = "optimize"
    FIX = "fix"
    REVIEW = "review"
    EXPLAIN = "explain"
    CONVERT = "convert"
    TEMPLATE = "template"


class Language(Enum):
    """Programming languages with full support."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    SQL = "sql"
    CSHARP = "csharp"
    RUBY = "ruby"
    PHP = "php"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    SCALA = "scala"
    REACT = "react"
    VUE = "vue"


@dataclass
class CodeSnippet:
    """Enhanced code snippet with comprehensive metadata."""
    code: str
    language: Language
    description: str = ""
    imports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    complexity: Dict[str, Any] = field(default_factory=dict)
    patterns_used: List[str] = field(default_factory=list)
    test_coverage: Optional[float] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    documentation: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "code": self.code,
            "language": self.language.value,
            "description": self.description,
            "imports": self.imports,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "complexity": self.complexity,
            "patterns_used": self.patterns_used,
            "test_coverage": self.test_coverage,
            "performance_metrics": self.performance_metrics,
            "documentation": self.documentation
        }


@dataclass
class RefactoringResult:
    """Refactoring operation result."""
    original_code: str
    refactored_code: str
    changes: List[str]
    improvements: List[str]
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_code": self.original_code,
            "refactored_code": self.refactored_code,
            "changes": self.changes,
            "improvements": self.improvements,
            "metrics": self.metrics
        }


@dataclass
class AnalysisResult:
    """Code analysis result."""
    entity: str = ""
    intent: str = ""
    operations: List[str] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: str = "Any"
    is_async: bool = False
    patterns: List[str] = field(default_factory=list)
    complexity: str = "simple"
    language_hints: Dict[str, Any] = field(default_factory=dict)