"""
Code Generator for Self-Modification System

Generates improvement code based on learned patterns and templates.
Supports multiple generation strategies and pattern-based improvements.

Created: 2025-08-15
"""

import ast
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
import textwrap
import re


class GenerationType(Enum):
    """Types of code generation strategies"""

    PATTERN_BASED = "pattern_based"
    TEMPLATE_BASED = "template_based"
    OPTIMIZATION = "optimization"
    REFACTORING = "refactoring"
    FEATURE_ADDITION = "feature_addition"
    BUG_FIX = "bug_fix"
    PERFORMANCE = "performance"


@dataclass
class CodeTemplate:
    """Template for code generation"""

    name: str
    template: str
    variables: Dict[str, Any]
    description: str
    category: GenerationType
    requirements: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)

    def render(self, **kwargs) -> str:
        """Render template with provided variables"""
        template_vars = {**self.variables, **kwargs}
        return self.template.format(**template_vars)

    def validate_variables(self, provided: Dict[str, Any]) -> bool:
        """Validate that all required variables are provided"""
        required = set(self.variables.keys())
        provided_keys = set(provided.keys())
        return required.issubset(provided_keys)


@dataclass
class ImprovementPattern:
    """Pattern for code improvement"""

    pattern_id: str
    name: str
    description: str
    detection_pattern: str  # Regex or AST pattern
    improvement_template: CodeTemplate
    success_rate: float = 0.0
    applications: int = 0
    last_applied: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)

    def matches(self, code: str) -> bool:
        """Check if pattern matches the code"""
        if self.detection_pattern.startswith("ast:"):
            # AST-based pattern matching
            pattern = self.detection_pattern[4:]
            try:
                tree = ast.parse(code)
                return self._match_ast_pattern(tree, pattern)
            except SyntaxError:
                return False
        else:
            # Regex-based pattern matching
            return bool(re.search(self.detection_pattern, code))

    def _match_ast_pattern(self, tree: ast.AST, pattern: str) -> bool:
        """Match AST pattern against tree"""
        # Simplified AST pattern matching
        for node in ast.walk(tree):
            if pattern in ast.dump(node):
                return True
        return False

    def update_metrics(self, success: bool):
        """Update pattern metrics after application"""
        self.applications += 1
        if success:
            self.success_rate = (
                self.success_rate * (self.applications - 1) + 1.0
            ) / self.applications
        else:
            self.success_rate = (self.success_rate * (self.applications - 1)) / self.applications
        self.last_applied = datetime.now()


@dataclass
class GeneratedCode:
    """Container for generated code"""

    code: str
    generation_type: GenerationType
    template_used: Optional[str] = None
    pattern_used: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 0.0

    def get_hash(self) -> str:
        """Get hash of generated code"""
        return hashlib.sha256(self.code.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "code": self.code,
            "generation_type": self.generation_type.value,
            "template_used": self.template_used,
            "pattern_used": self.pattern_used,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "hash": self.get_hash(),
        }


class CodeGenerator:
    """Main code generator for self-modification"""

    def __init__(self, templates_dir: Optional[Path] = None, patterns_file: Optional[Path] = None):
        """Initialize code generator"""
        self.templates: Dict[str, CodeTemplate] = {}
        self.patterns: Dict[str, ImprovementPattern] = {}
        self.generation_history: List[GeneratedCode] = []

        # Load templates and patterns
        if templates_dir:
            self._load_templates(templates_dir)
        else:
            self._initialize_default_templates()

        if patterns_file and patterns_file.exists():
            self._load_patterns(patterns_file)
        else:
            self._initialize_default_patterns()

    def _initialize_default_templates(self):
        """Initialize default code templates"""
        # Error handling template
        self.templates["error_handler"] = CodeTemplate(
            name="error_handler",
            template=textwrap.dedent(
                """
                try:
                    {original_code}
                except {exception_type} as e:
                    {error_handling}
                    {recovery_action}
            """
            ),
            variables={
                "original_code": "",
                "exception_type": "Exception",
                "error_handling": 'self.logger.error(f"Error: {e}")',
                "recovery_action": "raise",
            },
            description="Add error handling to code block",
            category=GenerationType.BUG_FIX,
        )

        # Caching decorator template
        self.templates["cache_decorator"] = CodeTemplate(
            name="cache_decorator",
            template=textwrap.dedent(
                """
                @lru_cache(maxsize={cache_size})
                def {function_name}({parameters}):
                    {function_body}
            """
            ),
            variables={
                "cache_size": 128,
                "function_name": "",
                "parameters": "",
                "function_body": "",
            },
            description="Add caching to function",
            category=GenerationType.PERFORMANCE,
        )

        # Async conversion template
        self.templates["async_conversion"] = CodeTemplate(
            name="async_conversion",
            template=textwrap.dedent(
                """
                async def {function_name}({parameters}):
                    {async_body}
                    return await {async_call}
            """
            ),
            variables={"function_name": "", "parameters": "", "async_body": "", "async_call": ""},
            description="Convert function to async",
            category=GenerationType.OPTIMIZATION,
        )

        # Logging template
        self.templates["add_logging"] = CodeTemplate(
            name="add_logging",
            template=textwrap.dedent(
                """
                {indent}self.logger.{level}(
                {indent}    "{message}",
                {indent}    {context}
                {indent})
                {original_code}
            """
            ),
            variables={
                "indent": "    ",
                "level": "info",
                "message": "",
                "context": "{}",
                "original_code": "",
            },
            description="Add logging to code",
            category=GenerationType.FEATURE_ADDITION,
        )

        # Validation template
        self.templates["input_validation"] = CodeTemplate(
            name="input_validation",
            template=textwrap.dedent(
                """
                def {function_name}({parameters}):
                    # Input validation
                    {validation_checks}
                    
                    # Original function body
                    {function_body}
            """
            ),
            variables={
                "function_name": "",
                "parameters": "",
                "validation_checks": "",
                "function_body": "",
            },
            description="Add input validation to function",
            category=GenerationType.BUG_FIX,
        )

    def _initialize_default_patterns(self):
        """Initialize default improvement patterns"""
        # Pattern for missing error handling
        self.patterns["missing_error_handling"] = ImprovementPattern(
            pattern_id="missing_error_handling",
            name="Missing Error Handling",
            description="Detect functions without try-except blocks",
            detection_pattern=r"def\s+\w+\([^)]*\):[^}]*(?!try:)",
            improvement_template=self.templates["error_handler"],
            tags=["safety", "error-handling"],
        )

        # Pattern for repeated calculations
        self.patterns["repeated_calculation"] = ImprovementPattern(
            pattern_id="repeated_calculation",
            name="Repeated Calculation",
            description="Detect functions with repeated expensive calculations",
            detection_pattern="ast:Call(func=Name)",
            improvement_template=self.templates["cache_decorator"],
            tags=["performance", "optimization"],
        )

        # Pattern for synchronous I/O
        self.patterns["sync_io"] = ImprovementPattern(
            pattern_id="sync_io",
            name="Synchronous I/O",
            description="Detect synchronous I/O operations that could be async",
            detection_pattern=r"(requests\.|urllib\.|open\()",
            improvement_template=self.templates["async_conversion"],
            tags=["performance", "async"],
        )

    def generate_improvement(
        self, code: str, improvement_type: GenerationType, context: Optional[Dict[str, Any]] = None
    ) -> GeneratedCode:
        """Generate code improvement based on type and context"""
        context = context or {}

        # Find matching patterns
        matching_patterns = self._find_matching_patterns(code, improvement_type)

        if matching_patterns:
            # Use best pattern
            pattern = self._select_best_pattern(matching_patterns)
            generated = self._apply_pattern(code, pattern, context)
            generated.pattern_used = pattern.pattern_id
            pattern.update_metrics(True)
        else:
            # Use template directly
            template = self._select_template(improvement_type, context)
            if template:
                generated = self._apply_template(code, template, context)
                generated.template_used = template.name
            else:
                # Fallback to basic generation
                generated = self._generate_basic(code, improvement_type, context)

        # Add to history
        self.generation_history.append(generated)

        # Calculate confidence
        generated.confidence = self._calculate_confidence(generated)

        return generated

    def _find_matching_patterns(
        self, code: str, improvement_type: GenerationType
    ) -> List[ImprovementPattern]:
        """Find patterns matching the code and improvement type"""
        matching = []
        for pattern in self.patterns.values():
            if pattern.improvement_template.category == improvement_type:
                if pattern.matches(code):
                    matching.append(pattern)
        return matching

    def _select_best_pattern(self, patterns: List[ImprovementPattern]) -> ImprovementPattern:
        """Select best pattern based on success rate and recency"""
        return max(
            patterns,
            key=lambda p: (
                p.success_rate,
                -((datetime.now() - p.last_applied).days if p.last_applied else float("inf")),
            ),
        )

    def _apply_pattern(
        self, code: str, pattern: ImprovementPattern, context: Dict[str, Any]
    ) -> GeneratedCode:
        """Apply improvement pattern to code"""
        # Extract variables from code
        variables = self._extract_variables(code, pattern)
        variables.update(context)

        # Render template
        improved_code = pattern.improvement_template.render(**variables)

        return GeneratedCode(
            code=improved_code,
            generation_type=pattern.improvement_template.category,
            pattern_used=pattern.pattern_id,
            metadata={"variables": variables},
        )

    def _extract_variables(self, code: str, pattern: ImprovementPattern) -> Dict[str, Any]:
        """Extract template variables from code"""
        variables = {}

        # Parse code AST
        try:
            tree = ast.parse(code)

            # Extract function information
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    variables["function_name"] = node.name
                    variables["parameters"] = ", ".join(arg.arg for arg in node.args.args)
                    variables["function_body"] = ast.unparse(node.body)
                    break

            variables["original_code"] = code

        except SyntaxError:
            variables["original_code"] = code

        return variables

    def _select_template(
        self, improvement_type: GenerationType, context: Dict[str, Any]
    ) -> Optional[CodeTemplate]:
        """Select appropriate template for improvement type"""
        for template in self.templates.values():
            if template.category == improvement_type:
                if not context or template.validate_variables(context):
                    return template
        return None

    def _apply_template(
        self, code: str, template: CodeTemplate, context: Dict[str, Any]
    ) -> GeneratedCode:
        """Apply template to generate improved code"""
        variables = self._extract_variables(code, None)
        variables.update(context)

        improved_code = template.render(**variables)

        return GeneratedCode(
            code=improved_code,
            generation_type=template.category,
            template_used=template.name,
            metadata={"variables": variables},
        )

    def _generate_basic(
        self, code: str, improvement_type: GenerationType, context: Dict[str, Any]
    ) -> GeneratedCode:
        """Basic code generation fallback"""
        # Simple improvements based on type
        improved_code = code

        if improvement_type == GenerationType.BUG_FIX:
            # Add basic error handling
            improved_code = f"try:\n{textwrap.indent(code, '    ')}\nexcept Exception as e:\n    print(f'Error: {{e}}')\n    raise"
        elif improvement_type == GenerationType.PERFORMANCE:
            # Add basic caching comment
            improved_code = f"# TODO: Add caching for performance\n{code}"
        elif improvement_type == GenerationType.FEATURE_ADDITION:
            # Add logging comment
            improved_code = f"# TODO: Add logging\n{code}"

        return GeneratedCode(code=improved_code, generation_type=improvement_type, metadata=context)

    def _calculate_confidence(self, generated: GeneratedCode) -> float:
        """Calculate confidence score for generated code"""
        confidence = 0.5  # Base confidence

        # Increase for pattern-based generation
        if generated.pattern_used:
            pattern = self.patterns.get(generated.pattern_used)
            if pattern:
                confidence = pattern.success_rate

        # Increase for template-based generation
        elif generated.template_used:
            confidence = 0.7

        # Decrease for basic generation
        else:
            confidence = 0.3

        # Adjust based on code complexity
        try:
            tree = ast.parse(generated.code)
            complexity = len(list(ast.walk(tree)))
            if complexity < 10:
                confidence *= 1.1
            elif complexity > 50:
                confidence *= 0.9
        except SyntaxError:
            confidence *= 0.5

        return min(confidence, 1.0)

    def learn_pattern(
        self,
        original_code: str,
        improved_code: str,
        improvement_type: GenerationType,
        success: bool = True,
    ) -> ImprovementPattern:
        """Learn new pattern from successful improvement"""
        # Generate pattern ID
        pattern_id = hashlib.sha256(f"{original_code}{improved_code}".encode()).hexdigest()[:16]

        # Create detection pattern
        detection_pattern = self._create_detection_pattern(original_code)

        # Create improvement template
        template = CodeTemplate(
            name=f"learned_{pattern_id}",
            template=improved_code,
            variables=self._extract_variables(original_code, None),
            description=f"Learned pattern for {improvement_type.value}",
            category=improvement_type,
        )

        # Create pattern
        pattern = ImprovementPattern(
            pattern_id=pattern_id,
            name=f"Learned Pattern {pattern_id}",
            description=f"Pattern learned from code improvement",
            detection_pattern=detection_pattern,
            improvement_template=template,
            success_rate=1.0 if success else 0.0,
            applications=1,
            last_applied=datetime.now(),
            tags=["learned", improvement_type.value],
        )

        # Add to patterns
        self.patterns[pattern_id] = pattern
        self.templates[template.name] = template

        return pattern

    def _create_detection_pattern(self, code: str) -> str:
        """Create detection pattern from code"""
        # Try to create AST pattern
        try:
            tree = ast.parse(code)
            # Get main node type
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    return f"ast:{node.__class__.__name__}"
            return f"ast:{tree.body[0].__class__.__name__}"
        except SyntaxError:
            # Fallback to regex pattern
            # Extract key identifiers
            identifiers = re.findall(r"\b[a-zA-Z_]\w*\b", code)[:3]
            if identifiers:
                return "|".join(identifiers)
            return code[:50]  # First 50 characters

    def save_patterns(self, filepath: Path):
        """Save learned patterns to file"""
        patterns_data = {}
        for pattern_id, pattern in self.patterns.items():
            patterns_data[pattern_id] = {
                "name": pattern.name,
                "description": pattern.description,
                "detection_pattern": pattern.detection_pattern,
                "template_name": pattern.improvement_template.name,
                "success_rate": pattern.success_rate,
                "applications": pattern.applications,
                "last_applied": pattern.last_applied.isoformat() if pattern.last_applied else None,
                "tags": pattern.tags,
            }

        with open(filepath, "w") as f:
            json.dump(patterns_data, f, indent=2)

    def _load_patterns(self, filepath: Path):
        """Load patterns from file"""
        with open(filepath, "r") as f:
            patterns_data = json.load(f)

        for pattern_id, data in patterns_data.items():
            if data["template_name"] in self.templates:
                pattern = ImprovementPattern(
                    pattern_id=pattern_id,
                    name=data["name"],
                    description=data["description"],
                    detection_pattern=data["detection_pattern"],
                    improvement_template=self.templates[data["template_name"]],
                    success_rate=data.get("success_rate", 0.0),
                    applications=data.get("applications", 0),
                    last_applied=datetime.fromisoformat(data["last_applied"])
                    if data.get("last_applied")
                    else None,
                    tags=data.get("tags", []),
                )
                self.patterns[pattern_id] = pattern

    def _load_templates(self, templates_dir: Path):
        """Load templates from directory"""
        for template_file in templates_dir.glob("*.json"):
            with open(template_file, "r") as f:
                data = json.load(f)
                template = CodeTemplate(
                    name=data["name"],
                    template=data["template"],
                    variables=data["variables"],
                    description=data["description"],
                    category=GenerationType[data["category"]],
                    requirements=data.get("requirements", []),
                    constraints=data.get("constraints", []),
                    examples=data.get("examples", []),
                )
                self.templates[template.name] = template
