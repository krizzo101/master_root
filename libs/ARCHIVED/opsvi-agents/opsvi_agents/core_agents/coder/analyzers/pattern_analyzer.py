"""
Pattern analysis for code generation intent extraction.
"""

import re
from typing import Any, Dict, List

from ..types import AnalysisResult


class PatternAnalyzer:
    """Analyzes descriptions to extract patterns and intent."""

    def __init__(self):
        """Initialize pattern analyzer with pattern definitions."""
        self.patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize pattern definitions."""
        return {
            "python": {
                "data_structures": {
                    "list": r"\b(list|array|collection|items|elements)\b",
                    "dict": r"\b(dict|map|mapping|hashtable|lookup)\b",
                    "set": r"\b(set|unique|distinct)\b",
                    "tuple": r"\b(tuple|immutable|pair|coordinate)\b",
                },
                "async_patterns": {
                    "async": r"\b(async|asynchronous|concurrent|parallel)\b",
                    "await": r"\b(await|wait for|fetch|load)\b",
                },
                "design_patterns": {
                    "singleton": r"\b(singleton|single instance|global)\b",
                    "factory": r"\b(factory|creator|builder)\b",
                    "observer": r"\b(observer|listener|event|subscriber)\b",
                    "decorator": r"\b(decorator|wrapper|enhance)\b",
                },
                "operations": {
                    "crud": r"\b(create|read|update|delete|CRUD)\b",
                    "validation": r"\b(validate|check|verify|ensure)\b",
                    "transformation": r"\b(transform|convert|map|process)\b",
                    "calculation": r"\b(calculate|compute|sum|average|total)\b",
                },
            }
        }

    def analyze(self, description: str, language: str = "python") -> AnalysisResult:
        """Analyze description to extract intent and parameters."""
        result = AnalysisResult()
        desc_lower = description.lower()

        # Extract entity name
        result.entity = self._extract_entity(description)

        # Detect patterns
        if language in self.patterns:
            lang_patterns = self.patterns[language]

            # Check async patterns
            for pattern in lang_patterns.get("async_patterns", {}).values():
                if re.search(pattern, desc_lower):
                    result.is_async = True
                    break

            # Check design patterns
            for pattern_name, pattern in lang_patterns.get(
                "design_patterns", {}
            ).items():
                if re.search(pattern, desc_lower):
                    result.patterns.append(pattern_name)

            # Detect operations
            for op_type, pattern in lang_patterns.get("operations", {}).items():
                if re.search(pattern, desc_lower):
                    result.operations.append(op_type)

        # Extract parameters
        result.parameters = self._extract_parameters(description)

        # Detect return type
        result.return_type = self._extract_return_type(description)

        # Assess complexity
        result.complexity = self._assess_complexity(description, result)

        return result

    def _extract_entity(self, description: str) -> str:
        """Extract entity name from description."""
        # First check for explicit class names with capital letters
        class_name_pattern = r"\b([A-Z][a-zA-Z]*(?:Manager|Service|Controller|Handler|Repository|Model|Factory|Builder|Agent|Component|Provider|Adapter))\b"
        match = re.search(class_name_pattern, description)
        if match:
            return match.group(1)

        # Look for other patterns
        entity_patterns = [
            r"(?:class|function)\s+(?:for|named|called)\s+(\w+)",
            r"(?:create|build|make|generate)\s+(?:a|an)?\s+(\w+)\s+(?:class|function|component)",
            r"(\w+)\s+(?:class|function|service|manager|controller)",
        ]

        for pattern in entity_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                entity = match.group(1)
                if entity.lower() not in [
                    "a",
                    "an",
                    "the",
                    "that",
                    "this",
                    "for",
                    "with",
                    "from",
                    "to",
                    "inherits",
                ]:
                    return entity

        return ""

    def _extract_parameters(self, description: str) -> List[Dict[str, Any]]:
        """Extract parameters from description."""
        params = []

        # Look for parameter descriptions
        param_patterns = [
            r"(?:takes|accepts|parameters?|with)\s+([^.]+?)(?:\s+and|\s+to|\s+for|$)",
            r"parameters?\s*:\s*([^.]+)",
        ]

        for pattern in param_patterns:
            match = re.search(pattern, description.lower())
            if match:
                param_text = match.group(1)
                param_names = re.split(r"[,;]\s*|\s+and\s+", param_text)
                for name in param_names:
                    name = name.strip()
                    if name and name not in ["a", "an", "the"]:
                        params.append(
                            {"name": name, "type": "Any", "description": f"The {name}"}
                        )
                break

        return params

    def _extract_return_type(self, description: str) -> str:
        """Extract return type from description."""
        return_patterns = [
            r"returns?\s+(?:a|an)?\s*(\w+)",
            r"->\s*(\w+)",
            r"yields?\s+(?:a|an)?\s*(\w+)",
        ]

        for pattern in return_patterns:
            match = re.search(pattern, description.lower())
            if match:
                ret_type = match.group(1)
                type_map = {
                    "list": "List[Any]",
                    "dict": "Dict[str, Any]",
                    "string": "str",
                    "number": "float",
                    "integer": "int",
                    "boolean": "bool",
                    "none": "None",
                }
                return type_map.get(ret_type, ret_type.capitalize())

        return "Any"

    def _assess_complexity(self, description: str, result: AnalysisResult) -> str:
        """Assess complexity of the requested code."""
        if len(result.patterns) > 1 or len(result.operations) > 2:
            return "complex"
        elif result.is_async or result.patterns:
            return "moderate"
        else:
            return "simple"
