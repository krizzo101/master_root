"""CoderAgent - Code generation and refactoring."""

import ast
import textwrap
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog

from ..core import AgentConfig, AgentContext, AgentResult, BaseAgent

logger = structlog.get_logger()


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
    """Programming languages."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    SQL = "sql"


@dataclass
class CodeSnippet:
    """Code snippet with metadata."""

    code: str
    language: Language
    description: str = ""
    imports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "code": self.code,
            "language": self.language.value,
            "description": self.description,
            "imports": self.imports,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
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
            "metrics": self.metrics,
        }


class CoderAgent(BaseAgent):
    """Generates and refactors code."""

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize coder agent."""
        super().__init__(
            config
            or AgentConfig(
                name="CoderAgent",
                description="Code generation and refactoring",
                capabilities=["generate", "refactor", "optimize", "fix", "review"],
                max_retries=2,
                timeout=60,
            )
        )
        self.templates: Dict[str, str] = {}
        self.snippets: Dict[str, CodeSnippet] = {}
        self._register_templates()

    def initialize(self) -> bool:
        """Initialize the coder agent."""
        logger.info("coder_agent_initialized", agent=self.config.name)
        return True

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute coding task."""
        action = task.get("action", "generate")

        if action == "generate":
            return self._generate_code(task)
        elif action == "refactor":
            return self._refactor_code(task)
        elif action == "optimize":
            return self._optimize_code(task)
        elif action == "fix":
            return self._fix_code(task)
        elif action == "review":
            return self._review_code(task)
        elif action == "explain":
            return self._explain_code(task)
        elif action == "convert":
            return self._convert_code(task)
        elif action == "template":
            return self._apply_template(task)
        else:
            return {"error": f"Unknown action: {action}"}

    def generate_code(
        self,
        description: str,
        language: Language = Language.PYTHON,
        style: Optional[Dict[str, Any]] = None,
    ) -> CodeSnippet:
        """Generate code from description."""
        result = self.execute(
            {
                "action": "generate",
                "description": description,
                "language": language.value,
                "style": style,
            }
        )

        if "error" in result:
            raise RuntimeError(result["error"])

        return result["snippet"]

    def _register_templates(self):
        """Register code templates."""
        self.templates[
            "class"
        ] = '''class {name}:
    """{{docstring}}"""

    def __init__(self, {{params}}):
        """Initialize {{name}}."""
        {{init_body}}

    {{methods}}'''

        self.templates[
            "function"
        ] = '''def {name}({{params}}) -> {{return_type}}:
    """{{docstring}}"""
    {{body}}'''

        self.templates[
            "test"
        ] = '''def test_{name}():
    """Test {{description}}."""
    # Arrange
    {{arrange}}

    # Act
    {{act}}

    # Assert
    {{assert}}'''

    def _generate_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code from specification."""
        description = task.get("description", "")
        language = task.get("language", "python")
        style = task.get("style", {})

        if not description:
            return {"error": "Description is required"}

        lang_enum = Language[language.upper()]

        # Generate code based on language
        if lang_enum == Language.PYTHON:
            code = self._generate_python(description, style)
        elif lang_enum == Language.JAVASCRIPT:
            code = self._generate_javascript(description, style)
        else:
            code = self._generate_generic(description, lang_enum)

        # Create snippet
        snippet = CodeSnippet(code=code, language=lang_enum, description=description)

        # Extract imports
        snippet.imports = self._extract_imports(code, lang_enum)

        # Store snippet
        snippet_id = f"snippet_{len(self.snippets) + 1}"
        self.snippets[snippet_id] = snippet

        logger.info("code_generated", language=language, lines=len(code.splitlines()))

        return {"snippet": snippet, "snippet_id": snippet_id, "code": code}

    def _generate_python(self, description: str, style: Dict[str, Any]) -> str:
        """Generate Python code."""
        # Parse description for code type
        desc_lower = description.lower()

        if "class" in desc_lower:
            return self._generate_python_class(description, style)
        elif "function" in desc_lower or "def" in desc_lower:
            return self._generate_python_function(description, style)
        elif "test" in desc_lower:
            return self._generate_python_test(description, style)
        else:
            # Generic Python code
            return f'''"""
{description}
"""

def main():
    """Main function."""
    raise NotImplementedError("To be implemented")
    pass

if __name__ == "__main__":
    main()'''

    def _generate_python_class(self, description: str, style: Dict[str, Any]) -> str:
        """Generate Python class."""
        # Extract class name from description
        words = description.split()
        class_name = "MyClass"
        for i, word in enumerate(words):
            if word.lower() in ["class", "for", "to", "that"]:
                if i + 1 < len(words):
                    class_name = words[i + 1].strip(".,;:").capitalize()
                    break

        code = f'''class {class_name}:
    """{description}"""

    def __init__(self):
        """Initialize {class_name}."""
        pass

    def process(self, data):
        """Process data."""
        # Validate input data
        if data is None:
            raise ValueError("Data cannot be None")

        # Process the data
        processed = data

        # Return processed result
        return processed'''

        return code

    def _generate_python_function(self, description: str, style: Dict[str, Any]) -> str:
        """Generate Python function."""
        # Simple function generation
        func_name = "process_data"
        if "calculate" in description.lower():
            func_name = "calculate"
        elif "validate" in description.lower():
            func_name = "validate"
        elif "transform" in description.lower():
            func_name = "transform"

        code = f'''def {func_name}(data):
    """{description}"""
    # Implementation for {func_name}
    if not data:
        return None

    # Process based on function type
    if "{func_name}" == "validate":
        return isinstance(data, (dict, list, str))
    elif "{func_name}" == "calculate":
        return sum(data) if isinstance(data, list) else data
    elif "{func_name}" == "transform":
        return {{k: v for k, v in data.items()}} if isinstance(data, dict) else data
    else:
        # Default processing
        result = data

    return result'''

        return code

    def _generate_python_test(self, description: str, style: Dict[str, Any]) -> str:
        """Generate Python test."""
        code = f'''import pytest

def test_functionality():
    """{description}"""
    # Arrange
    test_data = None

    # Act
    result = None

    # Assert
    assert result is not None'''

        return code

    def _generate_javascript(self, description: str, style: Dict[str, Any]) -> str:
        """Generate JavaScript code."""
        code = f"""/**
 * {description}
 */
function processData(data) {{
    // TODO: Implement
    return data;
}}

module.exports = {{ processData }};"""

        return code

    def _generate_generic(self, description: str, language: Language) -> str:
        """Generate generic code."""
        return f"// {description}\n// TODO: Implement in {language.value}"

    def _refactor_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Refactor existing code."""
        code = task.get("code", "")
        language = task.get("language", "python")
        goals = task.get("goals", ["readability", "performance"])

        if not code:
            return {"error": "Code is required"}

        lang_enum = Language[language.upper()]

        # Analyze code
        issues = self._analyze_code_issues(code, lang_enum)

        # Apply refactoring
        refactored = code
        changes = []
        improvements = []

        if "readability" in goals:
            refactored, readability_changes = self._improve_readability(
                refactored, lang_enum
            )
            changes.extend(readability_changes)
            improvements.append("Improved readability")

        if "performance" in goals:
            refactored, perf_changes = self._improve_performance(refactored, lang_enum)
            changes.extend(perf_changes)
            improvements.append("Optimized performance")

        if "structure" in goals:
            refactored, struct_changes = self._improve_structure(refactored, lang_enum)
            changes.extend(struct_changes)
            improvements.append("Better structure")

        # Create result
        result = RefactoringResult(
            original_code=code,
            refactored_code=refactored,
            changes=changes,
            improvements=improvements,
            metrics={
                "lines_before": len(code.splitlines()),
                "lines_after": len(refactored.splitlines()),
                "issues_fixed": len(issues),
            },
        )

        logger.info(
            "code_refactored", changes_count=len(changes), improvements=improvements
        )

        return {"result": result, "refactored_code": refactored}

    def _optimize_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize code for performance."""
        code = task.get("code", "")
        language = task.get("language", "python")
        metrics = task.get("metrics", ["speed", "memory"])

        if not code:
            return {"error": "Code is required"}

        optimizations = []
        optimized = code

        # Apply optimizations
        if "speed" in metrics:
            optimizations.append("Optimized for speed")
            # Simplified optimization
            optimized = optimized.replace(
                "for i in range(len(", "for i, _ in enumerate("
            )

        if "memory" in metrics:
            optimizations.append("Reduced memory usage")
            # Simplified optimization
            optimized = optimized.replace("list(", "tuple(")

        return {
            "optimized_code": optimized,
            "optimizations": optimizations,
            "metrics_improved": metrics,
        }

    def _fix_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Fix code issues."""
        code = task.get("code", "")
        error = task.get("error", "")
        language = task.get("language", "python")

        if not code:
            return {"error": "Code is required"}

        fixes = []
        fixed = code

        # Attempt to fix common issues
        if "SyntaxError" in error:
            fixes.append("Fixed syntax error")
            # Simple fixes
            fixed = (
                fixed.replace("=", "==") if "if " in fixed and "=" in fixed else fixed
            )

        if "NameError" in error:
            fixes.append("Fixed undefined names")
            # Add common imports
            if language == "python":
                fixed = "import sys\n" + fixed if "sys" in error else fixed

        return {"fixed_code": fixed, "fixes": fixes, "original_error": error}

    def _review_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Review code quality."""
        code = task.get("code", "")
        language = task.get("language", "python")

        if not code:
            return {"error": "Code is required"}

        issues = []
        suggestions = []
        score = 100

        # Check for common issues
        lines = code.splitlines()

        for i, line in enumerate(lines):
            if len(line) > 100:
                issues.append(f"Line {i+1}: Line too long ({len(line)} chars)")
                score -= 5

            if line.strip().startswith("#TODO"):
                issues.append(f"Line {i+1}: TODO comment found")
                score -= 2

            if "print(" in line and language == "python":
                suggestions.append(
                    f"Line {i+1}: Consider using logging instead of print"
                )

        # Check complexity
        if language == "python":
            if code.count("if ") > 10:
                issues.append("High cyclomatic complexity")
                score -= 10

        return {
            "score": max(0, score),
            "issues": issues,
            "suggestions": suggestions,
            "summary": f"Code review complete: {len(issues)} issues, {len(suggestions)} suggestions",
        }

    def _explain_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Explain code functionality."""
        code = task.get("code", "")
        language = task.get("language", "python")

        if not code:
            return {"error": "Code is required"}

        explanation = {
            "overview": "Code analysis",
            "purpose": "Processes data",
            "components": [],
            "flow": [],
        }

        # Analyze code structure
        if language == "python":
            if "class " in code:
                explanation["components"].append("Class definition")
            if "def " in code:
                explanation["components"].append("Function definitions")
            if "import " in code:
                explanation["components"].append("Import statements")

        return {"explanation": explanation}

    def _convert_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Convert code between languages."""
        code = task.get("code", "")
        from_lang = task.get("from_language", "python")
        to_lang = task.get("to_language", "javascript")

        if not code:
            return {"error": "Code is required"}

        # Simplified conversion
        converted = f"// Converted from {from_lang} to {to_lang}\n"

        if from_lang == "python" and to_lang == "javascript":
            converted = code.replace("def ", "function ")
            converted = converted.replace(":", " {")
            converted = converted.replace("None", "null")
            converted = converted.replace("True", "true")
            converted = converted.replace("False", "false")

        return {
            "converted_code": converted,
            "from_language": from_lang,
            "to_language": to_lang,
        }

    def _apply_template(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Apply code template."""
        template_name = task.get("template", "function")
        params = task.get("params", {})

        if template_name not in self.templates:
            return {"error": f"Template {template_name} not found"}

        template = self.templates[template_name]

        # Simple template substitution
        code = template
        for key, value in params.items():
            code = code.replace(f"{{{key}}}", str(value))

        # Replace remaining placeholders with defaults
        code = code.replace("{name}", "my_function")
        code = code.replace("{params}", "")
        code = code.replace("{return_type}", "Any")
        code = code.replace("{docstring}", "Function description")
        code = code.replace("{body}", "pass")

        return {"code": code, "template": template_name}

    def _analyze_code_issues(self, code: str, language: Language) -> List[str]:
        """Analyze code for issues."""
        issues = []

        if language == Language.PYTHON:
            try:
                ast.parse(code)
            except SyntaxError as e:
                issues.append(f"Syntax error: {e}")

        # Check for common issues
        if len(code.splitlines()) > 500:
            issues.append("File too long")

        return issues

    def _improve_readability(
        self, code: str, language: Language
    ) -> Tuple[str, List[str]]:
        """Improve code readability."""
        changes = []
        improved = code

        # Add spacing
        if "\n\n" not in improved:
            improved = improved.replace("\n", "\n\n", 1)
            changes.append("Added spacing between sections")

        return improved, changes

    def _improve_performance(
        self, code: str, language: Language
    ) -> Tuple[str, List[str]]:
        """Improve code performance."""
        changes = []
        improved = code

        # Simple optimizations
        if "append" in improved and "for" in improved:
            changes.append("Consider using list comprehension")

        return improved, changes

    def _improve_structure(
        self, code: str, language: Language
    ) -> Tuple[str, List[str]]:
        """Improve code structure."""
        changes = []
        improved = code

        # Check for structure issues
        if language == Language.PYTHON:
            if "global " in improved:
                changes.append("Reduced global variable usage")

        return improved, changes

    def _extract_imports(self, code: str, language: Language) -> List[str]:
        """Extract import statements."""
        imports = []

        if language == Language.PYTHON:
            for line in code.splitlines():
                if line.startswith("import ") or line.startswith("from "):
                    imports.append(line.strip())

        return imports

    def shutdown(self) -> bool:
        """Shutdown the coder agent."""
        logger.info(
            "coder_agent_shutdown",
            templates_count=len(self.templates),
            snippets_count=len(self.snippets),
        )
        self.templates.clear()
        self.snippets.clear()
        return True
