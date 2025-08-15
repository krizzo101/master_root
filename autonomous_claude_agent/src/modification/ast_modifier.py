"""
AST Modifier for Safe Code Modification

Provides AST manipulation capabilities for safe code modification
with comprehensive analysis and transformation features.

Created: 2025-08-15
"""

import ast
import copy
import hashlib
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import textwrap
import difflib


@dataclass
class ModificationResult:
    """Result of a code modification"""

    success: bool
    original_code: str
    modified_code: str
    changes_made: List[str]
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def get_diff(self) -> str:
        """Get diff between original and modified code"""
        original_lines = self.original_code.splitlines(keepends=True)
        modified_lines = self.modified_code.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile="original.py",
            tofile="modified.py",
            lineterm="",
        )

        return "".join(diff)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "success": self.success,
            "original_hash": hashlib.sha256(self.original_code.encode()).hexdigest()[:16],
            "modified_hash": hashlib.sha256(self.modified_code.encode()).hexdigest()[:16],
            "changes_made": self.changes_made,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "diff_lines": len(self.get_diff().splitlines()),
        }


@dataclass
class SafeModification:
    """Container for safe modification operations"""

    target_node_type: type
    modification_func: callable
    validation_func: Optional[callable] = None
    rollback_func: Optional[callable] = None
    description: str = ""
    risk_level: str = "low"  # low, medium, high

    def apply(self, node: ast.AST, context: Dict[str, Any]) -> Tuple[ast.AST, bool]:
        """Apply modification to node"""
        if self.validation_func and not self.validation_func(node, context):
            return node, False

        try:
            modified_node = self.modification_func(node, context)
            return modified_node, True
        except Exception as e:
            if self.rollback_func:
                return self.rollback_func(node, context), False
            return node, False


class ASTAnalyzer:
    """Analyzer for AST structures"""

    @staticmethod
    def analyze_structure(tree: ast.AST) -> Dict[str, Any]:
        """Analyze AST structure and extract metadata"""
        analysis = {
            "node_counts": {},
            "functions": [],
            "classes": [],
            "imports": [],
            "variables": [],
            "complexity": 0,
            "depth": 0,
            "line_count": 0,
        }

        # Count node types
        for node in ast.walk(tree):
            node_type = node.__class__.__name__
            analysis["node_counts"][node_type] = analysis["node_counts"].get(node_type, 0) + 1

            # Extract specific information
            if isinstance(node, ast.FunctionDef):
                analysis["functions"].append(
                    {
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "decorators": [ast.unparse(d) for d in node.decorator_list],
                        "lineno": node.lineno,
                        "complexity": ASTAnalyzer._calculate_complexity(node),
                    }
                )

            elif isinstance(node, ast.ClassDef):
                analysis["classes"].append(
                    {
                        "name": node.name,
                        "bases": [ast.unparse(b) for b in node.bases],
                        "decorators": [ast.unparse(d) for d in node.decorator_list],
                        "lineno": node.lineno,
                        "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                    }
                )

            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis["imports"].append(
                            {"module": alias.name, "alias": alias.asname, "type": "import"}
                        )
                else:
                    for alias in node.names:
                        analysis["imports"].append(
                            {
                                "module": f"{node.module}.{alias.name}"
                                if node.module
                                else alias.name,
                                "alias": alias.asname,
                                "type": "from_import",
                            }
                        )

            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                analysis["variables"].append(node.id)

        # Calculate overall complexity
        analysis["complexity"] = sum(f["complexity"] for f in analysis["functions"])

        # Calculate tree depth
        analysis["depth"] = ASTAnalyzer._calculate_depth(tree)

        # Get line count
        if hasattr(tree, "body") and tree.body:
            last_node = tree.body[-1]
            if hasattr(last_node, "end_lineno"):
                analysis["line_count"] = last_node.end_lineno

        return analysis

    @staticmethod
    def _calculate_complexity(node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a node"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        return complexity

    @staticmethod
    def _calculate_depth(node: ast.AST, current_depth: int = 0) -> int:
        """Calculate maximum depth of AST"""
        max_depth = current_depth
        for child in ast.iter_child_nodes(node):
            child_depth = ASTAnalyzer._calculate_depth(child, current_depth + 1)
            max_depth = max(max_depth, child_depth)
        return max_depth

    @staticmethod
    def find_nodes(tree: ast.AST, node_type: type) -> List[ast.AST]:
        """Find all nodes of specific type"""
        return [node for node in ast.walk(tree) if isinstance(node, node_type)]

    @staticmethod
    def find_node_by_name(tree: ast.AST, name: str, node_type: type = None) -> Optional[ast.AST]:
        """Find node by name"""
        for node in ast.walk(tree):
            if node_type and not isinstance(node, node_type):
                continue
            if hasattr(node, "name") and node.name == name:
                return node
        return None


class ASTModifier:
    """Main AST modifier for safe code modification"""

    def __init__(self):
        """Initialize AST modifier"""
        self.modifications: List[SafeModification] = []
        self.modification_history: List[ModificationResult] = []
        self.analyzer = ASTAnalyzer()
        self._initialize_default_modifications()

    def _initialize_default_modifications(self):
        """Initialize default safe modifications"""
        # Add error handling modification
        self.add_modification(
            SafeModification(
                target_node_type=ast.FunctionDef,
                modification_func=self._add_error_handling,
                validation_func=self._needs_error_handling,
                description="Add error handling to function",
                risk_level="low",
            )
        )

        # Add logging modification
        self.add_modification(
            SafeModification(
                target_node_type=ast.FunctionDef,
                modification_func=self._add_logging,
                validation_func=self._needs_logging,
                description="Add logging to function",
                risk_level="low",
            )
        )

        # Add type hints modification
        self.add_modification(
            SafeModification(
                target_node_type=ast.FunctionDef,
                modification_func=self._add_type_hints,
                validation_func=self._needs_type_hints,
                description="Add type hints to function",
                risk_level="low",
            )
        )

        # Optimize loops modification
        self.add_modification(
            SafeModification(
                target_node_type=ast.For,
                modification_func=self._optimize_loop,
                validation_func=self._can_optimize_loop,
                description="Optimize loop performance",
                risk_level="medium",
            )
        )

    def modify_code(
        self, code: str, modifications: List[str], context: Optional[Dict[str, Any]] = None
    ) -> ModificationResult:
        """Apply modifications to code"""
        context = context or {}
        changes_made = []

        try:
            # Parse original code
            tree = ast.parse(code)
            original_tree = copy.deepcopy(tree)

            # Apply requested modifications
            for mod_name in modifications:
                modification = self._find_modification(mod_name)
                if modification:
                    tree, applied = self._apply_modification(tree, modification, context)
                    if applied:
                        changes_made.append(f"Applied: {modification.description}")

            # Generate modified code
            modified_code = ast.unparse(tree)

            # Validate modified code
            try:
                ast.parse(modified_code)
                success = True
                error = None
            except SyntaxError as e:
                success = False
                error = str(e)
                modified_code = code  # Revert to original

            # Create result
            result = ModificationResult(
                success=success,
                original_code=code,
                modified_code=modified_code,
                changes_made=changes_made,
                error=error,
                metadata={
                    "original_analysis": self.analyzer.analyze_structure(original_tree),
                    "modified_analysis": self.analyzer.analyze_structure(tree) if success else None,
                },
            )

            # Add to history
            self.modification_history.append(result)

            return result

        except Exception as e:
            return ModificationResult(
                success=False, original_code=code, modified_code=code, changes_made=[], error=str(e)
            )

    def _find_modification(self, name: str) -> Optional[SafeModification]:
        """Find modification by name or description"""
        for mod in self.modifications:
            if name.lower() in mod.description.lower():
                return mod
        return None

    def _apply_modification(
        self, tree: ast.AST, modification: SafeModification, context: Dict[str, Any]
    ) -> Tuple[ast.AST, bool]:
        """Apply a modification to the AST"""
        modified = False

        class ModificationTransformer(ast.NodeTransformer):
            def visit(self, node):
                if isinstance(node, modification.target_node_type):
                    new_node, applied = modification.apply(node, context)
                    if applied:
                        nonlocal modified
                        modified = True
                        return new_node
                return self.generic_visit(node)

        transformer = ModificationTransformer()
        tree = transformer.visit(tree)
        ast.fix_missing_locations(tree)

        return tree, modified

    def add_modification(self, modification: SafeModification):
        """Add a new modification type"""
        self.modifications.append(modification)

    def _needs_error_handling(self, node: ast.FunctionDef, context: Dict[str, Any]) -> bool:
        """Check if function needs error handling"""
        # Check if function already has try-except
        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                return False

        # Check if function has potential error points
        for child in ast.walk(node):
            if isinstance(child, (ast.Call, ast.Subscript, ast.Attribute)):
                return True

        return False

    def _add_error_handling(
        self, node: ast.FunctionDef, context: Dict[str, Any]
    ) -> ast.FunctionDef:
        """Add error handling to function"""
        # Wrap function body in try-except
        try_node = ast.Try(
            body=node.body,
            handlers=[
                ast.ExceptHandler(
                    type=ast.Name(id="Exception", ctx=ast.Load()),
                    name="e",
                    body=[
                        ast.Expr(
                            value=ast.Call(
                                func=ast.Name(id="print", ctx=ast.Load()),
                                args=[
                                    ast.JoinedStr(
                                        values=[
                                            ast.Constant(value=f"Error in {node.name}: "),
                                            ast.FormattedValue(
                                                value=ast.Name(id="e", ctx=ast.Load()),
                                                conversion=-1,
                                            ),
                                        ]
                                    )
                                ],
                                keywords=[],
                            )
                        ),
                        ast.Raise(),
                    ],
                )
            ],
            orelse=[],
            finalbody=[],
        )

        node.body = [try_node]
        return node

    def _needs_logging(self, node: ast.FunctionDef, context: Dict[str, Any]) -> bool:
        """Check if function needs logging"""
        # Check if function already has logging
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if hasattr(child.func.value, "id") and "log" in child.func.value.id.lower():
                        return False

        # Add logging to public methods
        return not node.name.startswith("_")

    def _add_logging(self, node: ast.FunctionDef, context: Dict[str, Any]) -> ast.FunctionDef:
        """Add logging to function"""
        # Add logging at start of function
        log_call = ast.Expr(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id="logger", ctx=ast.Load()), attr="debug", ctx=ast.Load()
                ),
                args=[
                    ast.JoinedStr(
                        values=[
                            ast.Constant(value=f"Calling {node.name} with args: "),
                            ast.FormattedValue(
                                value=ast.Name(id="args", ctx=ast.Load()), conversion=-1
                            ),
                            ast.Constant(value=" kwargs: "),
                            ast.FormattedValue(
                                value=ast.Name(id="kwargs", ctx=ast.Load()), conversion=-1
                            ),
                        ]
                    )
                ],
                keywords=[],
            )
        )

        # Add *args, **kwargs if not present
        if not any(arg.arg == "args" for arg in node.args.args):
            node.args.vararg = ast.arg(arg="args", annotation=None)
        if not any(arg.arg == "kwargs" for arg in node.args.args):
            node.args.kwarg = ast.arg(arg="kwargs", annotation=None)

        # Insert logging at beginning
        node.body.insert(0, log_call)

        return node

    def _needs_type_hints(self, node: ast.FunctionDef, context: Dict[str, Any]) -> bool:
        """Check if function needs type hints"""
        # Check if function already has type hints
        for arg in node.args.args:
            if arg.annotation is None:
                return True

        return node.returns is None

    def _add_type_hints(self, node: ast.FunctionDef, context: Dict[str, Any]) -> ast.FunctionDef:
        """Add type hints to function"""
        # Add generic type hints
        for arg in node.args.args:
            if arg.annotation is None:
                arg.annotation = ast.Name(id="Any", ctx=ast.Load())

        if node.returns is None:
            # Try to infer return type
            for child in reversed(node.body):
                if isinstance(child, ast.Return):
                    if child.value is None:
                        node.returns = ast.Constant(value=None)
                    else:
                        node.returns = ast.Name(id="Any", ctx=ast.Load())
                    break
            else:
                node.returns = ast.Constant(value=None)

        return node

    def _can_optimize_loop(self, node: ast.For, context: Dict[str, Any]) -> bool:
        """Check if loop can be optimized"""
        # Check if loop is iterating over range
        if isinstance(node.iter, ast.Call):
            if isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range":
                return True

        # Check if loop has list comprehension potential
        if len(node.body) == 1:
            if isinstance(node.body[0], ast.Expr):
                if isinstance(node.body[0].value, ast.Call):
                    return True

        return False

    def _optimize_loop(self, node: ast.For, context: Dict[str, Any]) -> ast.For:
        """Optimize loop performance"""
        # Simple optimization: convert range(len(x)) to enumerate(x)
        if isinstance(node.iter, ast.Call):
            if isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range":
                if len(node.iter.args) == 1:
                    if isinstance(node.iter.args[0], ast.Call):
                        if isinstance(node.iter.args[0].func, ast.Name):
                            if node.iter.args[0].func.id == "len":
                                # Convert to enumerate
                                node.iter = ast.Call(
                                    func=ast.Name(id="enumerate", ctx=ast.Load()),
                                    args=node.iter.args[0].args,
                                    keywords=[],
                                )

                                # Update target to tuple
                                if isinstance(node.target, ast.Name):
                                    old_target = node.target
                                    node.target = ast.Tuple(
                                        elts=[ast.Name(id="_idx", ctx=ast.Store()), old_target],
                                        ctx=ast.Store(),
                                    )

        return node

    def rollback(self, steps: int = 1) -> Optional[ModificationResult]:
        """Rollback to previous modification state"""
        if len(self.modification_history) >= steps:
            # Get the modification to rollback to
            target_idx = len(self.modification_history) - steps - 1
            if target_idx >= 0:
                target = self.modification_history[target_idx]

                # Create rollback result
                rollback_result = ModificationResult(
                    success=True,
                    original_code=self.modification_history[-1].modified_code,
                    modified_code=target.modified_code,
                    changes_made=[f"Rolled back {steps} modifications"],
                    metadata={"rollback_steps": steps},
                )

                self.modification_history.append(rollback_result)
                return rollback_result

        return None

    def get_modification_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get modification history"""
        history = []
        for result in self.modification_history[-limit:]:
            history.append(result.to_dict())
        return history

    def analyze_code(self, code: str) -> Dict[str, Any]:
        """Analyze code structure"""
        try:
            tree = ast.parse(code)
            return self.analyzer.analyze_structure(tree)
        except SyntaxError as e:
            return {"error": str(e)}

    def suggest_modifications(self, code: str) -> List[Dict[str, Any]]:
        """Suggest possible modifications for code"""
        suggestions = []

        try:
            tree = ast.parse(code)

            # Check each modification
            for mod in self.modifications:
                # Find applicable nodes
                nodes = self.analyzer.find_nodes(tree, mod.target_node_type)

                for node in nodes:
                    if mod.validation_func and mod.validation_func(node, {}):
                        name = getattr(node, "name", str(mod.target_node_type.__name__))
                        suggestions.append(
                            {
                                "modification": mod.description,
                                "target": name,
                                "risk_level": mod.risk_level,
                                "line": getattr(node, "lineno", 0),
                            }
                        )

        except SyntaxError:
            pass

        return suggestions
