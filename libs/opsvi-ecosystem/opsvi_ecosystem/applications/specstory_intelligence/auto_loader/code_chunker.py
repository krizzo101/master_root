"""
Code Chunker for Auto-Loader
Splits code files into logical chunks (functions, classes) for ingestion.
"""

import ast
import os
from typing import Any


def chunk_python_code(source_code: str) -> list[dict[str, Any]]:
    """
    Chunk Python code into functions and classes.
    Returns (chunks, relationships, imports):
      - chunks: list of dicts with type, name, start_line, end_line, code, docstring, decorators, visibility, complexity, inherits, uses
      - relationships: list of (from_name, to_name, rel_type)
      - imports: list of imported module names
    """
    chunks = []
    relationships = []
    imports = []
    try:
        tree = ast.parse(source_code)
        # Collect all function/class names for reference
        name_map = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name_map[node] = node.name
        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        # Extract chunks and relationships
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start_line = node.lineno
                end_line = getattr(node, "end_lineno", None)
                if end_line is None:
                    # Fallback: estimate end line
                    end_line = node.body[-1].lineno if node.body else node.lineno
                chunk_code = "\n".join(
                    source_code.splitlines()[start_line - 1 : end_line]
                )
                # Extract docstring if present
                docstring = ast.get_docstring(node)
                # Decorators
                decorators = []
                if hasattr(node, "decorator_list"):
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Name):
                            decorators.append(dec.id)
                        elif isinstance(dec, ast.Attribute):
                            decorators.append(dec.attr)
                # Visibility
                name = node.name
                if name.startswith("__"):
                    visibility = "private"
                elif name.startswith("_"):
                    visibility = "protected"
                else:
                    visibility = "public"
                # Complexity (stub: lines of code)
                complexity = end_line - start_line + 1
                # Inherits (for classes)
                inherits = []
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            inherits.append(base.id)
                        elif isinstance(base, ast.Attribute):
                            inherits.append(base.attr)
                # Uses (stub: types/classes used in function body)
                uses = set()
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Name):
                        uses.add(subnode.id)
                uses = list(uses - {name})
                chunk = {
                    "type": ("class" if isinstance(node, ast.ClassDef) else "function"),
                    "name": name,
                    "start_line": start_line,
                    "end_line": end_line,
                    "code": chunk_code,
                    "docstring": docstring,
                    "decorators": decorators,
                    "visibility": visibility,
                    "complexity": complexity,
                    "inherits": inherits,
                    "uses": uses,
                }
                chunks.append(chunk)
                # Find calls within this function/class
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Call):
                        # Try to get the function name being called
                        func = subnode.func
                        if isinstance(func, ast.Name):
                            callee = func.id
                        elif isinstance(func, ast.Attribute):
                            callee = func.attr
                        else:
                            callee = None
                        if callee:
                            relationships.append((name, callee, "calls"))
                # Inherits relationships
                for base in inherits:
                    relationships.append((name, base, "inherits"))
                # Uses relationships
                for used in uses:
                    relationships.append((name, used, "uses"))
    except Exception as e:
        # Fallback: treat whole file as one chunk
        chunks.append(
            {
                "type": "file",
                "name": "<whole_file>",
                "start_line": 1,
                "end_line": len(source_code.splitlines()),
                "code": source_code,
                "error": str(e),
                "docstring": None,
                "decorators": [],
                "visibility": "public",
                "complexity": len(source_code.splitlines()),
                "inherits": [],
                "uses": [],
            }
        )
    return chunks, relationships, imports


def chunk_code_file(filepath: str) -> list[dict[str, Any]]:
    """
    Detect language by extension and chunk code accordingly.
    Currently supports Python. Stubs for other languages.
    Returns (chunks, relationships, imports) for Python, else (chunks, [], [])
    """
    _, ext = os.path.splitext(filepath)
    with open(filepath, encoding="utf-8") as f:
        code = f.read()
    if ext == ".py":
        return chunk_python_code(code)
    # TODO: Add support for JS, TS, etc.
    return (
        [
            {
                "type": "file",
                "name": os.path.basename(filepath),
                "start_line": 1,
                "end_line": len(code.splitlines()),
                "code": code,
                "note": "No chunker for this language yet.",
                "docstring": None,
                "decorators": [],
                "visibility": "public",
                "complexity": len(code.splitlines()),
                "inherits": [],
                "uses": [],
            }
        ],
        [],
        [],
    )
