"""
AST Analyzer Component

Performs deep structural analysis of Python code using Abstract Syntax Trees.
Extracts import patterns, class structures, method calls, error handling patterns,
and logging patterns to identify code organization and style.
"""

import ast
from dataclasses import dataclass
from pathlib import Path

from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger


@dataclass
class ImportPattern:
    """Pattern information for imports."""

    import_type: str  # 'absolute', 'relative', 'standard_library', 'third_party'
    import_statement: str
    line_number: int
    module_name: str
    alias: str | None = None


@dataclass
class ClassPattern:
    """Pattern information for classes."""

    class_name: str
    line_number: int
    has_docstring: bool
    has_init: bool
    method_count: int
    attribute_count: int
    inheritance: list[str]
    decorators: list[str]


@dataclass
class MethodPattern:
    """Pattern information for methods."""

    method_name: str
    line_number: int
    is_static: bool
    is_class_method: bool
    has_docstring: bool
    parameter_count: int
    return_type: str | None
    decorators: list[str]


@dataclass
class ErrorHandlingPattern:
    """Pattern information for error handling."""

    pattern_type: str  # 'try_except', 'bare_except', 'specific_except'
    line_number: int
    exception_types: list[str]
    has_logging: bool
    has_raise: bool


@dataclass
class LoggingPattern:
    """Pattern information for logging."""

    logger_type: str  # 'O3Logger', 'standard_logging', 'print'
    method_name: str
    line_number: int
    log_level: str
    has_context: bool


@dataclass
class FileAnalysis:
    """Complete analysis of a single file."""

    file_path: Path
    import_patterns: list[ImportPattern]
    class_patterns: list[ClassPattern]
    method_patterns: list[MethodPattern]
    error_handling_patterns: list[ErrorHandlingPattern]
    logging_patterns: list[LoggingPattern]
    has_main_function: bool
    has_setup_logger: bool
    uses_absolute_imports: bool
    uses_shared_utilities: bool


class ASTAnalyzer:
    """
    Performs deep structural analysis of Python code using AST.

    Extracts patterns for imports, classes, methods, error handling,
    logging, and overall code organization.
    """

    def __init__(self) -> None:
        """Initialize the AST analyzer and its logger."""
        self.logger = get_logger()
        self.standard_library: set[str] = {
            "os",
            "sys",
            "pathlib",
            "typing",
            "dataclasses",
            "collections",
            "datetime",
            "json",
            "yaml",
            "logging",
            "ast",
            "re",
            "math",
            "random",
            "itertools",
            "functools",
            "contextlib",
            "abc",
        }
        self.shared_utilities: set[str] = {
            "src.tools.code_generation.o3_code_generator.utils.directory_manager",
            "src.tools.code_generation.o3_code_generator.utils.file_generator",
            "src.tools.code_generation.o3_code_generator.utils.input_loader",
            "src.tools.code_generation.o3_code_generator.utils.output_formatter",
            "src.tools.code_generation.o3_code_generator.utils.prompt_builder",
            "src.tools.code_generation.o3_code_generator.o3_logger.logger",
        }
        self.logger.log_info("Initialized ASTAnalyzer")

    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """
        Analyze a single Python file.

        Args:
            file_path: Path to the Python file to analyze

        Returns:
            FileAnalysis: Complete analysis of the file
        """
        self.logger.log_debug(f"Analyzing file: {file_path}")
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content, filename=str(file_path))
            import_patterns = self._extract_import_patterns(tree)
            class_patterns = self._extract_class_patterns(tree)
            method_patterns = self._extract_method_patterns(tree)
            error_handling_patterns = self._extract_error_handling_patterns(tree)
            logging_patterns = self._extract_logging_patterns(tree)
            has_main = self._has_main_function(tree)
            has_setup = self._has_setup_logger(tree)
            uses_abs = self._uses_absolute_imports(import_patterns)
            uses_shared = self._uses_shared_utilities(import_patterns)
            return FileAnalysis(
                file_path=file_path,
                import_patterns=import_patterns,
                class_patterns=class_patterns,
                method_patterns=method_patterns,
                error_handling_patterns=error_handling_patterns,
                logging_patterns=logging_patterns,
                has_main_function=has_main,
                has_setup_logger=has_setup,
                uses_absolute_imports=uses_abs,
                uses_shared_utilities=uses_shared,
            )
        except SyntaxError as e:
            self.logger.log_warning(f"Syntax error in {file_path}: {e}")
            return FileAnalysis(
                file_path=file_path,
                import_patterns=[],
                class_patterns=[],
                method_patterns=[],
                error_handling_patterns=[],
                logging_patterns=[],
                has_main_function=False,
                has_setup_logger=False,
                uses_absolute_imports=False,
                uses_shared_utilities=False,
            )
        except Exception as e:
            self.logger.log_error(f"Error analyzing {file_path}: {e}")
            raise

    def _extract_import_patterns(self, tree: ast.AST) -> list[ImportPattern]:
        """Extract import patterns from AST."""
        patterns: list[ImportPattern] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    itype = self._classify_import(alias.name)
                    patterns.append(
                        ImportPattern(
                            import_type=itype,
                            import_statement=f"import {alias.name}",
                            line_number=node.lineno,
                            module_name=alias.name,
                            alias=alias.asname,
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                itype = self._classify_import(module)
                names = ", ".join(n.name for n in node.names)
                patterns.append(
                    ImportPattern(
                        import_type=itype,
                        import_statement=f"from {module} import {names}",
                        line_number=node.lineno,
                        module_name=module,
                        alias=None,
                    )
                )
        return patterns

    def _classify_import(self, module_name: str) -> str:
        """Classify an import as absolute, relative, standard_library, or third_party."""
        if not module_name:
            return "unknown"
        if module_name.startswith("."):
            return "relative"
        if module_name.startswith("src."):
            return "absolute"
        base = module_name.split(".")[0]
        if base in self.standard_library:
            return "standard_library"
        return "third_party"

    def _extract_class_patterns(self, tree: ast.AST) -> list[ClassPattern]:
        """Extract class patterns from AST."""
        patterns: list[ClassPattern] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                inheritance: list[str] = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        inheritance.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        inheritance.append(self._get_attribute_name(base))
                decorators: list[str] = [
                    self._get_attribute_name(d)
                    if isinstance(d, ast.Attribute)
                    else d.id
                    for d in node.decorator_list
                ]
                method_count = 0
                attribute_count = 0
                has_init = False
                for child in node.body:
                    if isinstance(child, ast.FunctionDef):
                        method_count += 1
                        if child.name == "__init__":
                            has_init = True
                    elif isinstance(child, ast.Assign):
                        attribute_count += 1
                patterns.append(
                    ClassPattern(
                        class_name=node.name,
                        line_number=node.lineno,
                        has_docstring=ast.get_docstring(node) is not None,
                        has_init=has_init,
                        method_count=method_count,
                        attribute_count=attribute_count,
                        inheritance=inheritance,
                        decorators=decorators,
                    )
                )
        return patterns

    def _extract_method_patterns(self, tree: ast.AST) -> list[MethodPattern]:
        """Extract method patterns from AST."""
        patterns: list[MethodPattern] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                is_static = False
                is_class = False
                decorators: list[str] = []
                for d in node.decorator_list:
                    if isinstance(d, ast.Attribute):
                        name = self._get_attribute_name(d)
                    elif isinstance(d, ast.Name):
                        name = d.id
                    elif isinstance(d, ast.Call):
                        # Handle function calls in decorators
                        if isinstance(d.func, ast.Name):
                            name = d.func.id
                        elif isinstance(d.func, ast.Attribute):
                            name = self._get_attribute_name(d.func)
                        else:
                            name = "unknown_decorator"
                    else:
                        name = "unknown_decorator"
                    decorators.append(name)
                    if name == "staticmethod":
                        is_static = True
                    elif name == "classmethod":
                        is_class = True
                return_type = None
                if node.returns:
                    if isinstance(node.returns, ast.Name):
                        return_type = node.returns.id
                    elif isinstance(node.returns, ast.Attribute):
                        return_type = self._get_attribute_name(node.returns)
                patterns.append(
                    MethodPattern(
                        method_name=node.name,
                        line_number=node.lineno,
                        is_static=is_static,
                        is_class_method=is_class,
                        has_docstring=ast.get_docstring(node) is not None,
                        parameter_count=len(node.args.args),
                        return_type=return_type,
                        decorators=decorators,
                    )
                )
        return patterns

    def _extract_error_handling_patterns(
        self, tree: ast.AST
    ) -> list[ErrorHandlingPattern]:
        """Extract error handling patterns from AST."""
        patterns: list[ErrorHandlingPattern] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    exc_types: list[str] = []
                    if handler.type:
                        if isinstance(handler.type, ast.Name):
                            exc_types.append(handler.type.id)
                        elif isinstance(handler.type, ast.Tuple):
                            for exc in handler.type.elts:
                                if isinstance(exc, ast.Name):
                                    exc_types.append(exc.id)
                    ptype = "bare_except" if not exc_types else "specific_except"
                    has_log = self._has_logging_in_node(handler)
                    has_r = self._has_raise_in_node(handler)
                    patterns.append(
                        ErrorHandlingPattern(
                            pattern_type=ptype,
                            line_number=handler.lineno,
                            exception_types=exc_types,
                            has_logging=has_log,
                            has_raise=has_r,
                        )
                    )
        return patterns

    def _extract_logging_patterns(self, tree: ast.AST) -> list[LoggingPattern]:
        """Extract logging patterns from AST."""
        patterns: list[LoggingPattern] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    name = self._get_attribute_name(node.func)
                    if any(
                        name.endswith(f".{lvl}")
                        for lvl in ("log_info", "log_debug", "log_warning", "log_error")
                    ):
                        log_level = name.split(".")[-1]
                        patterns.append(
                            LoggingPattern(
                                logger_type="O3Logger",
                                method_name=name,
                                line_number=node.lineno,
                                log_level=log_level,
                                has_context=bool(node.args or node.keywords),
                            )
                        )
                elif isinstance(node.func, ast.Name) and node.func.id == "print":
                    patterns.append(
                        LoggingPattern(
                            logger_type="print",
                            method_name="print",
                            line_number=node.lineno,
                            log_level="info",
                            has_context=bool(node.args),
                        )
                    )
        return patterns

    def _has_main_function(self, tree: ast.AST) -> bool:
        """Check if file has a main function."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "main":
                return True
        return False

    def _has_setup_logger(self, tree: ast.AST) -> bool:
        """Check if file has setup_logger call."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "setup_logger":
                    return True
                if isinstance(node.func, ast.Attribute) and self._get_attribute_name(
                    node.func
                ).endswith(".setup_logger"):
                    return True
        return False

    def _uses_absolute_imports(self, patterns: list[ImportPattern]) -> bool:
        """Check if file uses absolute imports."""
        return any(p.import_type == "absolute" for p in patterns)

    def _uses_shared_utilities(self, patterns: list[ImportPattern]) -> bool:
        """Check if file uses shared utilities."""
        return any(p.module_name in self.shared_utilities for p in patterns)

    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Get the full name of an attribute node."""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        if isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_name(node.value)}.{node.attr}"
        return node.attr

    def _has_logging_in_node(self, node: ast.AST) -> bool:
        """Check if a node contains logging calls."""
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                name = self._get_attribute_name(child.func)
                if any(
                    name.endswith(f".{lvl}")
                    for lvl in ("log_info", "log_debug", "log_warning", "log_error")
                ):
                    return True
        return False

    def _has_raise_in_node(self, node: ast.AST) -> bool:
        """Check if a node contains raise statements."""
        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                return True
        return False
