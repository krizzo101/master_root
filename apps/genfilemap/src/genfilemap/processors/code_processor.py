"""
Code file processor for genfilemap.

This module provides specialized processing for code files like Python, JavaScript, etc.
"""

import re
import json
import asyncio
import os
import ast
import inspect
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List, Set
from pathlib import Path

from genfilemap.processors.base import FileProcessor
from genfilemap.prompting.prompts import get_code_system_message, get_code_user_prompt
from genfilemap.utils.file_utils import extract_existing_file_map, calculate_file_hash
from genfilemap.core.validation import validate_file_map_comprehensive, correct_file_map


class CodeFileProcessor(FileProcessor):
    """Processor for code files"""

    async def analyze_structure(self, content: str) -> Dict[str, Any]:
        """
        Analyze the Python code structure using AST and build a detailed map
        """
        try:
            tree = ast.parse(content)
            content_lines = content.split("\n")

            result = {
                "file_metadata": {"type": "python", "language": "python"},
            "code_elements": {
                "imports": [],
                    "from_imports": [],
                    "classes": [],
                    "functions": [],
                    "constants": [],
                },
                "key_elements": [],
                "sections": [],
            }

            # Process imports
            import_data = self._process_imports(tree, content_lines)
            result["code_elements"]["imports"] = import_data["imports"]
            result["code_elements"]["from_imports"] = import_data["from_imports"]

            # Add important imports to key_elements
            for imp in import_data["imports"]:
                result["key_elements"].append(
                    {"name": imp["module"], "type": "import", "line": imp["line"]}
                )

            for imp in import_data["from_imports"]:
                # Use the full import statement for key_elements
                result["key_elements"].append(
                    {
                        "name": imp[
                            "statement"
                        ],  # Use full statement like "from pathlib import Path"
                        "type": "import",
                        "line": imp["line"],
                    }
                )

            # Process class definitions
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_info = self._extract_class_info(node, content_lines)
                    result["code_elements"]["classes"].append(class_info)

                    # Add class to key_elements
                    result["key_elements"].append(
                        {"name": node.name, "type": "class", "line": node.lineno}
                    )

                # Process top-level functions (both regular and async)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    function_info = self._extract_function_info(node, content_lines)
                    result["code_elements"]["functions"].append(function_info)

                    # Add function to key_elements
                    result["key_elements"].append(
                        {"name": node.name, "type": "function", "line": node.lineno}
                    )

            # Process top-level constants
                elif isinstance(node, ast.Assign) and all(
                    isinstance(target, ast.Name) for target in node.targets
                ):
                    # Only include constants (names in ALL_CAPS)
                    for target in node.targets:
                        if (
                            target.id.isupper()
                            or target.id.startswith("_")
                            and target.id[1:].isupper()
                        ):
                            # Try to get the value if it's a simple constant
                            value = ""
                            type_name = ""

                            # Determine the type based on the node value
                            if isinstance(node.value, ast.Dict):
                                value = "{}"  # Simple placeholder for dict
                                type_name = "dict"

                                # Try to reconstruct the dictionary
                                try:
                                    dict_content = {}
                                    for i, key_node in enumerate(node.value.keys):
                                        if isinstance(
                                            key_node, (ast.Str, ast.Constant)
                                        ):
                                            key = ast.literal_eval(key_node)
                                            if i < len(node.value.values):
                                                value_node = node.value.values[i]
                                                if isinstance(
                                                    value_node,
                                                    (
                                                        ast.Str,
                                                        ast.Num,
                                                        ast.NameConstant,
                                                        ast.Constant,
                                                        ast.List,
                                                    ),
                                                ):
                                                    try:
                                                        dict_content[key] = (
                                                            ast.literal_eval(value_node)
                                                        )
                                                    except:
                                                        dict_content[key] = str(
                                                            self._get_code_segment(
                                                                content_lines,
                                                                value_node.lineno,
                                                                value_node.col_offset,
                                                            )
                                                        )
                                    # Use Python formatting to match source exactly
                                    value = str(dict_content)
                                except:
                                    # If reconstruction fails, use generic dict
                                    value = "{}"
                            elif isinstance(node.value, ast.List):
                                value = "[]"  # Simple placeholder for list
                                type_name = "list"
                            elif isinstance(
                                node.value,
                                (ast.Str, ast.Num, ast.NameConstant, ast.Constant),
                            ):
                                try:
                                    value = ast.literal_eval(node.value)
                                    type_name = type(value).__name__
                                except:
                                    value = self._get_code_segment(
                                        content_lines,
                                        node.value.lineno,
                                        node.value.col_offset,
                                    )
                            else:
                                # For complex expressions, just get the text
                                value = self._get_code_segment(
                                    content_lines,
                                    node.value.lineno,
                                    node.value.col_offset,
                                )

                            # Determine type if possible and not already set
                            if not type_name:
                                if hasattr(node, "annotation") and node.annotation:
                                    type_name = self._get_code_segment(
                                        content_lines,
                                        node.annotation.lineno,
                                        node.annotation.col_offset,
                                    )
                            elif value is not None:
                                    # Make a best guess based on the value string
                                    if str(value).startswith("{") and str(
                                        value
                                    ).endswith("}"):
                                        type_name = "dict"
                                    elif str(value).startswith("[") and str(
                                        value
                                    ).endswith("]"):
                                        type_name = "list"
                                    elif str(value).startswith("'") or str(
                                        value
                                    ).startswith('"'):
                                        type_name = "str"
                                    elif str(value).lower() in ("true", "false"):
                                        type_name = "bool"
                                    elif str(value).replace(".", "").isdigit():
                                        type_name = (
                                            "float" if "." in str(value) else "int"
                                        )
                                    else:
                                        type_name = "str"  # Default fallback

                            # Convert value to string with proper JSON formatting
                            if isinstance(value, dict):
                                # Use JSON formatting for dictionaries to ensure double quotes
                                import json

                                string_value = json.dumps(value)
                            else:
                                string_value = str(value) if value is not None else ""

                            const_info = {
                                "name": target.id,
                                "line": node.lineno,
                                "value": string_value,
                                "type": type_name,
                            }

                            result["code_elements"]["constants"].append(const_info)

                            # Add constant to key_elements
                            result["key_elements"].append(
                                {
                                    "name": target.id,
                                    "type": "constant",
                                    "line": node.lineno,
                                }
                            )

            return result

        except SyntaxError as e:
            self.debug_print(f"Syntax error parsing Python code: {str(e)}")
            # Return empty structures on error
            return {
                "file_metadata": {"type": "python", "language": "python"},
                "code_elements": {
                    "imports": [],
                    "from_imports": [],
                    "classes": [],
                    "functions": [],
                    "constants": [],
                },
                "key_elements": [],
                "sections": [],
            }
        except Exception as e:
            self.debug_print(f"Error extracting Python code elements: {str(e)}")
            return {
                "file_metadata": {"type": "python", "language": "python"},
                "code_elements": {
                    "imports": [],
                    "from_imports": [],
                    "classes": [],
                    "functions": [],
                    "constants": [],
                },
                "key_elements": [],
                "sections": [],
            }

    def _process_imports(
        self, tree: ast.Module, content_lines: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extract import statements from the AST - only top-level imports"""
        imports = []
        from_imports = []

        # Only look at top-level nodes, not nested ones (fixes fake import issue)
        for node in tree.body:
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(
                        {
                            "module": name.name,
                            "alias": name.asname,
                            "line": node.lineno,
                            "statement": f"import {name.name}"
                            + (f" as {name.asname}" if name.asname else ""),
                        }
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for name in node.names:
                    from_imports.append(
                        {
                            "module": module,
                            "name": name.name,
                            "alias": name.asname,
                            "line": node.lineno,
                            "statement": f"from {module} import {name.name}"
                            + (f" as {name.asname}" if name.asname else ""),
                        }
                    )

        return {"imports": imports, "from_imports": from_imports}

    def _extract_function_info(self, node, content_lines: List[str]) -> Dict[str, Any]:
        """Extract detailed information about a function from its AST node"""
        # Detect if this is an async function
        is_async = isinstance(node, ast.AsyncFunctionDef)
        function_info = {
            "name": node.name,
            "line": node.lineno,
            "parameters": [],
            "is_async": is_async,
        }

        # Extract return type if available
        if node.returns:
            try:
                return_type_raw = self._get_code_segment(
                    content_lines, node.returns.lineno, node.returns.col_offset
                )
                # Clean up return type (remove trailing colon if present)
                return_type = return_type_raw.rstrip(":")
                function_info["return_type"] = return_type
            except:
                pass

        # Extract docstring if available
        if (
            len(node.body) > 0
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, (ast.Str, ast.Constant))
        ):
            if isinstance(node.body[0].value, ast.Str):
                function_info["description"] = node.body[0].value.s
            else:  # ast.Constant
                function_info["description"] = node.body[0].value.value

        # Extract parameters
        for arg in node.args.args:
            param = {"name": arg.arg}

            # Get type annotation if available
            if arg.annotation:
                try:
                    type_raw = self._get_code_segment(
                        content_lines, arg.annotation.lineno, arg.annotation.col_offset
                    )

                    # Clean up type annotation
                    # 1. Remove any trailing colons or parentheses
                    # 2. Remove any return type indicators
                    # 3. Strip any commas that might come from multiple parameters on same line

                    # Remove return type if present (anything after '-> ')
                    type_clean = re.sub(r"\)\s*->\s*.*$", "", type_raw)

                    # Remove trailing punctuation like colons, parentheses, commas
                    type_clean = type_clean.rstrip(":),")

                    # Remove any parameter names that might have been captured
                    # This pattern matches a type followed by a comma and another parameter name
                    type_clean = re.sub(
                        r"([\w\[\]\.]+)\s*,\s*\w+\s*:", r"\1", type_clean
                    )

                    # Remove duplicate words (like "str str")
                    type_clean = re.sub(r"(\b\w+\b)\s+\1\b", r"\1", type_clean)

                    # Handle the case where another parameter type is in the annotation
                    if "," in type_clean:
                        type_clean = type_clean.split(",")[0].strip()

                    param["type"] = type_clean
                except:
                    param["type"] = "unknown"
            else:
                # Always provide a type field, even for 'self' parameters with no annotation
                if arg.arg == "self" or arg.arg == "cls":
                    param["type"] = "self"
                else:
                    param["type"] = "unknown"

            function_info["parameters"].append(param)

        # Extract defaults for parameters
        defaults = [None] * (
            len(node.args.args) - len(node.args.defaults)
        ) + node.args.defaults
        for i, default in enumerate(defaults):
            if default:
                try:
                    default_value = ast.literal_eval(default)
                    function_info["parameters"][i]["default"] = str(default_value)
                except:
                    try:
                        function_info["parameters"][i]["default"] = (
                            self._get_code_segment(
                                content_lines, default.lineno, default.col_offset
                            )
                        )
                    except:
                        function_info["parameters"][i]["default"] = "complex_expression"

        # Build full signature
        params_text = []
        for i, param in enumerate(function_info["parameters"]):
            param_str = param["name"]
            if (
                "type" in param
                and param["type"] != "self"
                and param["type"] != "unknown"
            ):
                param_str += f": {param['type']}"
            if "default" in param:
                param_str += f" = {param['default']}"
            params_text.append(param_str)

        # Add *args if present
        if node.args.vararg:
            vararg_str = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation:
                vararg_type = self._get_code_segment(
                    content_lines,
                    node.args.vararg.annotation.lineno,
                    node.args.vararg.annotation.col_offset,
                )
                # Clean up vararg type
                vararg_type = vararg_type.rstrip(":")
                vararg_str += f": {vararg_type}"
            params_text.append(vararg_str)

        # Add **kwargs if present
        if node.args.kwarg:
            kwarg_str = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation:
                kwarg_type = self._get_code_segment(
                    content_lines,
                    node.args.kwarg.annotation.lineno,
                    node.args.kwarg.annotation.col_offset,
                )
                # Clean up kwarg type
                kwarg_type = kwarg_type.rstrip(":")
                kwarg_str += f": {kwarg_type}"
            params_text.append(kwarg_str)

        # Combine everything into a full signature
        async_prefix = "async " if is_async else ""
        signature = f"{async_prefix}{node.name}({', '.join(params_text)})"
        if "return_type" in function_info:
            signature += f" -> {function_info['return_type']}"

        function_info["signature"] = signature
        return function_info

    def _get_code_segment(self, lines: List[str], lineno: int, col_offset: int) -> str:
        """
        Extract a code segment from the given line and column.
        This is a simple helper for getting annotations and expressions.
        """
        if lineno <= 0 or lineno > len(lines):
            return ""

        # Zero-indexed line
        line = lines[lineno - 1]

        if col_offset >= len(line):
            return ""

        # Very basic extraction - this could be improved for more complex expressions
        # For now, just take the rest of the line and clean it up
        segment = line[col_offset:].strip()
        # Remove trailing commas, parentheses, etc.
        segment = re.sub(r"[,\)\]]+$", "", segment)

        return segment

    def _extract_js_code_elements(self, content: str) -> Dict[str, Any]:
        """
        Extract code elements from JavaScript/TypeScript using regex patterns.

        This is more limited than AST parsing but provides reasonable results for common patterns.
        """
        result = {
            "code_elements": {
                "functions": [],
                "classes": [],
                "imports": [],
                "constants": [],
            }
        }

        lines = content.split("\n")

        # Extract imports
        import_patterns = [
            # ES6 imports
            r'^\s*import\s+(?:{[^}]+}|\*\s+as\s+\w+|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]',
            # Require imports
            r'^\s*(?:const|let|var)\s+(\w+)\s*=\s*require\([\'"]([^\'"]+)[\'"]\)',
            # Import defaults
            r'^\s*import\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]',
        ]

        for i, line in enumerate(lines):
            for pattern in import_patterns:
                match = re.search(pattern, line)
                if match:
                    result["code_elements"]["imports"].append(
                        {"statement": line.strip(), "line": i + 1}
                    )
                    break

        # Extract constants (all-caps variables are assumed to be constants)
        const_pattern = r"^\s*(?:const|let|var)\s+([A-Z][A-Z0-9_]*)\s*=\s*(.+?);?\s*$"
        for i, line in enumerate(lines):
            match = re.search(const_pattern, line)
            if match:
                name = match.group(1)
                value = match.group(2).strip()

                # Try to determine type
                type_name = ""
                if (
                    value.startswith('"')
                    or value.startswith("'")
                    or value.startswith("`")
                ):
                    type_name = "string"
                elif value == "true" or value == "false":
                    type_name = "boolean"
                elif re.match(r"^-?\d+(?:\.\d+)?$", value):
                    type_name = "number"
                elif value.startswith("["):
                    type_name = "array"
                elif value.startswith("{"):
                    type_name = "object"

                result["code_elements"]["constants"].append(
                    {"name": name, "line": i + 1, "value": value, "type": type_name}
                )

        # Extract functions using various formats
        function_patterns = [
            # Regular function declarations
            r"^\s*function\s+(\w+)\s*\((.*?)\)",
            # Arrow functions with explicit name
            r"^\s*(?:const|let|var)\s+(\w+)\s*=\s*(?:\(.*?\)|[^=]+)\s*=>\s*",
            # Class methods
            r"^\s*(\w+)\s*\((.*?)\)\s*{",
            # Async functions
            r"^\s*async\s+function\s+(\w+)\s*\((.*?)\)",
            # Async arrow functions
            r"^\s*(?:const|let|var)\s+(\w+)\s*=\s*async\s*(?:\(.*?\)|[^=]+)\s*=>\s*",
        ]

        i = 0
        while i < len(lines):
            line = lines[i]
            for pattern in function_patterns:
                match = re.search(pattern, line)
                if match:
                    name = match.group(1)
                    params_str = match.group(2) if len(match.groups()) > 1 else ""

                    # Extract parameters
                    parameters = []
                    if params_str:
                        # Split by commas, but respect nested structures
                        # This is a simplification and won't handle all cases
                        param_parts = []
                        current = ""
                        nesting = 0
                        for char in params_str:
                            if char == "," and nesting == 0:
                                param_parts.append(current.strip())
                                current = ""
                            else:
                                current += char
                                if char in "({[":
                                    nesting += 1
                                elif char in ")}]":
                                    nesting -= 1
                        if current:
                            param_parts.append(current.strip())

                        for param in param_parts:
                            param = param.strip()
                            if not param:
                                continue

                            param_info = {"name": param}

                            # Check for TypeScript type annotations
                            type_match = re.match(
                                r"(\w+)\s*:\s*(.+?)(?:\s*=\s*(.+))?$", param
                            )
                            if type_match:
                                param_info["name"] = type_match.group(1)
                                param_info["type"] = type_match.group(2)
                                if type_match.group(3):
                                    param_info["default"] = type_match.group(3)
                            else:
                                # Check for default values
                                default_match = re.match(
                                    r"(\w+)(?:\s*=\s*(.+))?$", param
                                )
                                if default_match and default_match.group(2):
                                    param_info["name"] = default_match.group(1)
                                    param_info["default"] = default_match.group(2)

                            parameters.append(param_info)

                    # Look for return type annotation (TypeScript)
                    return_type = ""
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        return_match = re.match(r"^\s*:\s*(.+?)\s*(?:{|=>)", next_line)
                        if return_match:
                            return_type = return_match.group(1)

                    # Get description from comment if available
                    description = ""
                    if i > 0:
                        prev_line = lines[i - 1]
                        comment_match = re.match(
                            r"^\s*(?://|/\*\*?)\s*(.+?)(?:\*/)?$", prev_line
                        )
                        if comment_match:
                            description = comment_match.group(1)
                        else:
                            # Look for JSDoc style comment block
                            j = i - 1
                            jsdoc_lines = []
                            while j >= 0 and j >= i - 10:  # Look back up to 10 lines
                                if re.match(r"^\s*\*/", lines[j]):
                                    # End of JSDoc block
                                    k = j - 1
                                    while (
                                        k >= 0 and k >= j - 20
                                    ):  # Look back up to 20 lines in the block
                                        if re.match(r"^\s*/\*\*", lines[k]):
                                            # Start of JSDoc block
                                            jsdoc_lines = [
                                                re.sub(r"^\s*\*\s*", "", l)
                                                for l in lines[k + 1 : j]
                                            ]
                                            jsdoc_lines = [
                                                l for l in jsdoc_lines if l.strip()
                                            ]
                                            description = " ".join(jsdoc_lines)
                                            break
                                        k -= 1
                                    break
                                j -= 1

                    # Build function signature
                    signature = f"{name}({params_str})"
                    if return_type:
                        signature += f": {return_type}"

                    function_info = {
                        "name": name,
                        "signature": signature,
                        "line": i + 1,
                        "parameters": parameters,
                    }

                    if return_type:
                        function_info["return_type"] = return_type

                    if description:
                        function_info["description"] = description

                    result["code_elements"]["functions"].append(function_info)
                    break

            # Extract classes
            class_match = re.match(
                r"^\s*class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{", line
            )
            if class_match:
                class_name = class_match.group(1)
                parent_class = (
                    class_match.group(2)
                    if len(class_match.groups()) > 1 and class_match.group(2)
                    else None
                )

                # Get description from comment if available
                description = ""
                if i > 0:
                    prev_line = lines[i - 1]
                    comment_match = re.match(
                        r"^\s*(?://|/\*\*?)\s*(.+?)(?:\*/)?$", prev_line
                    )
                    if comment_match:
                        description = comment_match.group(1)

                class_info = {
                    "name": class_name,
                    "line": i + 1,
                    "methods": [],
                    "properties": [],
                }

                if parent_class:
                    class_info["inherits_from"] = [parent_class]

                if description:
                    class_info["description"] = description

                # Find the end of the class to look for methods and properties
                # This is a simplification and won't handle all nesting cases correctly
                class_end = i + 1
                nesting = 1
                while class_end < len(lines) and nesting > 0:
                    for char in lines[class_end]:
                        if char == "{":
                            nesting += 1
                        elif char == "}":
                            nesting -= 1
                            if nesting == 0:
                                break
                    class_end += 1

                # Extract class properties and methods
                # This is a simplified approach that won't catch everything
                j = i + 1
                while j < class_end:
                    # Check for property declarations
                    prop_match = re.match(
                        r"^\s*(?:static\s+)?(\w+)\s*(?:=|;)", lines[j]
                    )
                    if prop_match:
                        prop_name = prop_match.group(1)

                        # Get type if available (TypeScript)
                        type_match = re.match(
                            r"^\s*(?:static\s+)?(\w+)\s*:\s*(.+?)(?:\s*=|;)", lines[j]
                        )
                        prop_type = type_match.group(2) if type_match else ""

                        class_info["properties"].append(
                            {"name": prop_name, "line": j + 1, "type": prop_type}
                        )

                    j += 1

                result["code_elements"]["classes"].append(class_info)

            i += 1

        return result

    async def generate_file_map(
        self, content: str, comment_style: tuple, force: bool = False
    ) -> Optional[str]:
        """
        Generate a file map for the given content.

        Uses iterative refinement if enabled in config, otherwise falls back to deterministic approach.
        """
        self.debug_print(f"Processing file: {self.file_path}")
        self.debug_print(f"Force flag set: {force}")
        self.debug_print(f"Content length: {len(content)} characters")

        # Check if iterative refinement is enabled
        config = getattr(self, "config", {})
        use_iterative_refinement = config.get("validation", {}).get(
            "iterative_refinement", False
        )

        if use_iterative_refinement:
            self.debug_print("Using iterative refinement approach")
            return await self.generate_file_map_with_refinement(
                content, comment_style, force
            )

        # Check if we need to regenerate
        existing_map = None
        remaining_content = content

        if not force:
            self.debug_print("Attempting to extract existing file map...")
            existing_map, remaining_content = extract_existing_file_map(
                content, comment_style
            )

        if existing_map:
                self.debug_print(f"Extracted file map of length: {len(existing_map)}")
                self.debug_print(f"Remaining content length: {len(remaining_content)}")

                # Calculate hash for remaining content
                self.debug_print("Calculating hash for remaining content...")
                current_hash = self.calculate_content_hash(remaining_content)

                # Try to extract stored hash from existing map
                stored_hash = self.extract_stored_hash(existing_map)

                self.debug_print(f"Stored hash: {stored_hash}")
                self.debug_print(f"Current hash: {current_hash}")

                if stored_hash == current_hash:
                    self.debug_print(
                        "Hash matches and we have an existing map, checking if valid..."
                    )

                    # Try to parse the existing map to see if it's valid
                    if self.is_valid_file_map(existing_map):
                        self.debug_print(
                            "Existing map is valid, no regeneration needed"
                        )
                        return None  # No changes needed
                    else:
                        self.debug_print("Existing map is invalid, regenerating...")
                else:
                    self.debug_print("Hash mismatch or no stored hash, regenerating...")
        else:
                self.debug_print("No existing map found, generating new one...")

        # Use the deterministic approach
        return await self.generate_file_map_deterministic(content, comment_style, force)

    def _extract_python_code_elements(self, content: str) -> Dict[str, Any]:
        """
        Extract detailed code elements from Python code using AST.

        This provides much more accurate and detailed information about functions, classes,
        methods, parameters, return types (if annotated), etc.
        """
        result = {
            "code_elements": {
                "functions": [],
                "classes": [],
                "imports": [],
                "constants": [],
            },
            "key_elements": [],  # Initialize key_elements
        }

        try:
            tree = ast.parse(content)

            # DEBUG
            self.debug_print(f"DEBUG-AST: Successfully parsed content with AST")

            # Track line numbers and content
            content_lines = content.split("\n")

            # Process imports
            import_data = self._process_imports(tree, content_lines)
            result["code_elements"]["imports"] = import_data["imports"]

            # Add imports to key_elements
            for imp in import_data["imports"]:
                if isinstance(imp, dict) and "module" in imp:
                    result["key_elements"].append(
                        {
                            "name": imp["module"],
                            "type": "import",
                            "line": imp["line"] if "line" in imp else 0,
                        }
                    )
                elif isinstance(imp, dict) and "statement" in imp:
                    # Extract module name from import statement
                    match = re.search(r"import\s+(\w+)", imp.get("statement", ""))
                    if match:
                        result["key_elements"].append(
                            {
                                "name": match.group(1),
                                "type": "import",
                                "line": imp.get("line", 0),
                            }
                        )

            # DEBUG
            self.debug_print(
                f"DEBUG-AST: Found {len(result['code_elements']['imports'])} imports"
            )

            # Process top-level constants
            for node in tree.body:
                if isinstance(node, ast.Assign) and all(
                    isinstance(target, ast.Name) for target in node.targets
                ):
                    # Only include constants (names in ALL_CAPS)
                    for target in node.targets:
                        if (
                            target.id.isupper()
                            or target.id.startswith("_")
                            and target.id[1:].isupper()
                        ):
                            # Try to get the value if it's a simple constant
                            value = ""
                            type_name = ""

                            # Determine the type based on the node value
                            if isinstance(node.value, ast.Dict):
                                value = "{}"  # Simple placeholder for dict
                                type_name = "dict"
                            elif isinstance(node.value, ast.List):
                                value = "[]"  # Simple placeholder for list
                                type_name = "list"
                            elif isinstance(
                                node.value,
                                (ast.Str, ast.Num, ast.NameConstant, ast.Constant),
                            ):
                                try:
                                    value = ast.literal_eval(node.value)
                                    type_name = type(value).__name__
                                except:
                                    value = self._get_code_segment(
                                        content_lines,
                                        node.value.lineno,
                                        node.value.col_offset,
                                    )
                            else:
                                # For complex expressions, just get the text
                                value = self._get_code_segment(
                                    content_lines,
                                    node.value.lineno,
                                    node.value.col_offset,
                                )

                            # Determine type if not already set
                            if not type_name:
                                if hasattr(node, "annotation") and node.annotation:
                                    type_name = self._get_code_segment(
                                        content_lines,
                                        node.annotation.lineno,
                                        node.annotation.col_offset,
                                    )
                                elif value is not None:
                                    # Make a best guess based on the value string
                                    if str(value).startswith("{") and str(
                                        value
                                    ).endswith("}"):
                                        type_name = "dict"
                                    elif str(value).startswith("[") and str(
                                        value
                                    ).endswith("]"):
                                        type_name = "list"
                                    elif str(value).startswith("'") or str(
                                        value
                                    ).startswith('"'):
                                        type_name = "str"
                                    elif str(value).lower() in ("true", "false"):
                                        type_name = "bool"
                                    elif str(value).replace(".", "").isdigit():
                                        type_name = (
                                            "float" if "." in str(value) else "int"
                                        )
                                    else:
                                        type_name = "str"  # Default fallback

                            # Convert value to string with proper JSON formatting
                            if isinstance(value, dict):
                                # Use JSON formatting for dictionaries to ensure double quotes
                                import json

                                string_value = json.dumps(value)
                            else:
                                string_value = str(value) if value is not None else ""

                            const_info = {
                                "name": target.id,
                                "line": node.lineno,
                                "value": string_value,
                                "type": type_name,
                            }

                            result["code_elements"]["constants"].append(const_info)

                            # Add to key_elements
                            result["key_elements"].append(
                                {
                                    "name": target.id,
                                    "type": "constant",
                                    "line": node.lineno,
                                }
                            )

            # DEBUG
            self.debug_print(
                f"DEBUG-AST: Found {len(result['code_elements']['constants'])} constants"
            )

            # Process functions
            for node in [
                n
                for n in tree.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]:
                function_info = self._extract_function_info(node, content_lines)
                result["code_elements"]["functions"].append(function_info)

                # Add to key_elements
                result["key_elements"].append(
                    {"name": node.name, "type": "function", "line": node.lineno}
                )

            # DEBUG
            self.debug_print(
                f"DEBUG-AST: Found {len(result['code_elements']['functions'])} functions"
            )

            # Process classes
            for node in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
                class_info = self._extract_class_info(node, content_lines)
                result["code_elements"]["classes"].append(class_info)

                # Add to key_elements
                result["key_elements"].append(
                    {"name": node.name, "type": "class", "line": node.lineno}
                )

            return result

        except SyntaxError as e:
            self.debug_print(f"Syntax error parsing Python code: {str(e)}")
            # Return empty structures on error
            return result
        except Exception as e:
            self.debug_print(f"Error extracting Python code elements: {str(e)}")
            return result

    def _extract_class_info(
        self, node: ast.ClassDef, content_lines: List[str]
    ) -> Dict[str, Any]:
        """Extract detailed information about a class from its AST node"""
        class_info = {
            "name": node.name,
            "line": node.lineno,
            "inherits_from": [
                self._get_code_segment(content_lines, base.lineno, base.col_offset)
                for base in node.bases
            ],
            "methods": [],
            "properties": [],
        }

        # Add docstring if available
        if (
            len(node.body) > 0
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, (ast.Str, ast.Constant))
        ):
            if isinstance(node.body[0].value, ast.Str):
                class_info["description"] = node.body[0].value.s
            else:  # ast.Constant
                class_info["description"] = node.body[0].value.value

        # Extract methods and class variables
        for class_node in node.body:
            if isinstance(class_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._extract_function_info(class_node, content_lines)
                class_info["methods"].append(method_info)
            elif isinstance(class_node, ast.Assign):
                for target in class_node.targets:
                    if isinstance(target, ast.Name):
                        prop_type = ""
                        try:
                            if (
                                hasattr(class_node, "annotation")
                                and class_node.annotation
                            ):
                                prop_type = self._get_code_segment(
                                    content_lines,
                                    class_node.annotation.lineno,
                                    class_node.annotation.col_offset,
                                )
                        except:
                            pass

                        class_info["properties"].append(
                            {
                                "name": target.id,
                                "line": class_node.lineno,
                                "type": prop_type,
                            }
                        )

        return class_info

    def build_deterministic_file_map(
        self, content: str, ast_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build file map structure deterministically from AST data.
        Only descriptions and section organization should involve AI.
        """
        # Start with the imports from regular import statements
        all_imports = ast_data["code_elements"]["imports"].copy()

        # Add from_imports to the imports array
        if "from_imports" in ast_data["code_elements"]:
            for from_import in ast_data["code_elements"]["from_imports"]:
                all_imports.append(
                    {
                        "module": from_import["module"],
                        "alias": from_import.get("alias"),
                        "line": from_import["line"],
                        "statement": from_import["statement"],
                    }
                )

        # Build the complete file map structure from AST data
        file_map = {
            "file_metadata": {
                "type": ast_data["file_metadata"]["type"],
                "language": ast_data["file_metadata"]["language"],
            },
            "code_elements": {
                "functions": ast_data["code_elements"]["functions"],
                "classes": ast_data["code_elements"]["classes"],
                "imports": all_imports,  # Use the merged imports
                "constants": ast_data["code_elements"]["constants"],
            },
            "key_elements": ast_data["key_elements"],
            "sections": [],  # Will be populated by AI
        }

        return file_map

    async def generate_file_map_deterministic(
        self, content: str, comment_style: tuple, force: bool = False
    ) -> str:
        """
        Generate file map using deterministic AST extraction + AI descriptions.
        This ensures 100% accuracy for structural elements.
        """
        # Extract existing file map to get the remaining content (without file map)
        existing_map, remaining_content = extract_existing_file_map(
            content, comment_style
        )

        # Use the remaining content (original source) for AST analysis
        # This ensures line numbers are correct relative to the actual source code
        ast_data = await self.analyze_structure(remaining_content)

        # Build the deterministic file map structure
        base_file_map = self.build_deterministic_file_map(remaining_content, ast_data)

        # Add required metadata fields
        base_file_map["file_metadata"].update(
            {
                "title": os.path.basename(self.file_path),
                "description": f"Python module with {len(base_file_map['code_elements']['functions'])} functions and {len(base_file_map['code_elements']['classes'])} classes",
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
            }
        )

        # Create deterministic sections based on code structure
        base_file_map["sections"] = self.create_deterministic_sections(
            remaining_content, ast_data
        )

        # Only ask AI for descriptions of functions and classes
        try:
            ai_prompt = self.create_simple_description_prompt(
                remaining_content, base_file_map
            )

            response = await self.api_client.generate_completion(
                system_message="You are a code documentation expert. Add brief descriptions for functions and classes.",
                user_message=ai_prompt,
                model=self.model,
                max_tokens=1500,
            )

            # Parse AI response to get descriptions only
            ai_descriptions = self.parse_simple_descriptions(response)

            # Merge AI descriptions with deterministic structure
            final_file_map = self.merge_simple_descriptions(
                base_file_map, ai_descriptions
            )

        except Exception as e:
            self.debug_print(f"Error getting AI descriptions: {e}")
            # Use deterministic structure without AI descriptions
            final_file_map = base_file_map

        # FIXED: Apply FILE_MAP line number offset to account for the header that will be inserted
        # The new single-line format uses 2 lines total (1 FILE_MAP line + 1 blank line)
        file_map_offset = 2

        self.debug_print(
            f"DEBUG-CODE: Applying FILE_MAP offset of {file_map_offset} lines to all line numbers"
        )

        # Adjust section line numbers
        for section in final_file_map.get("sections", []):
            if "line_start" in section:
                section["line_start"] += file_map_offset
            if "line_end" in section:
                section["line_end"] += file_map_offset

        # Adjust key element line numbers
        for element in final_file_map.get("key_elements", []):
            if "line" in element:
                element["line"] += file_map_offset

        # Adjust code element line numbers
        for func in final_file_map.get("code_elements", {}).get("functions", []):
            if "line" in func:
                func["line"] += file_map_offset

        for cls in final_file_map.get("code_elements", {}).get("classes", []):
            if "line" in cls:
                cls["line"] += file_map_offset
            # Also adjust method line numbers within classes
            for method in cls.get("methods", []):
                if "line" in method:
                    method["line"] += file_map_offset

        for imp in final_file_map.get("code_elements", {}).get("imports", []):
            if "line" in imp:
                imp["line"] += file_map_offset

        for imp in final_file_map.get("code_elements", {}).get("from_imports", []):
            if "line" in imp:
                imp["line"] += file_map_offset

        for const in final_file_map.get("code_elements", {}).get("constants", []):
            if "line" in const:
                const["line"] += file_map_offset

        self.debug_print(f"DEBUG-CODE: Line number offset applied successfully")

        # Add content hash for change detection
        content_hash = self.calculate_content_hash(remaining_content)
        final_file_map["content_hash"] = content_hash

        # Format as file map comment
        return self.format_file_map(final_file_map, comment_style)

    def create_deterministic_sections(
        self, content: str, ast_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create sections deterministically based on code structure."""
        sections = []
        lines = content.split("\n")

        # Find docstring section
        if lines and lines[0].strip().startswith('"""'):
            docstring_end = 1
            for i in range(1, len(lines)):
                if '"""' in lines[i]:
                    docstring_end = i + 1
                    break
            sections.append(
                {
                    "name": "Module Docstring",
                    "description": "Module-level documentation describing the file's purpose.",
                    "line_start": 1,
                    "line_end": docstring_end,
                }
            )

        # Find imports section
        imports = ast_data["code_elements"]["imports"] + ast_data["code_elements"].get(
            "from_imports", []
        )
        if imports:
            import_lines = [imp["line"] for imp in imports]
            sections.append(
                {
                    "name": "Imports",
                    "description": "Import statements for required modules and libraries.",
                    "line_start": min(import_lines),
                    "line_end": max(import_lines),
                }
            )

        # Add function sections
        for func in ast_data["code_elements"]["functions"]:
            # Find function end by looking for next function or class
            func_end = func["line"] + 5  # Default estimate
            all_elements = (
                ast_data["code_elements"]["functions"]
                + ast_data["code_elements"]["classes"]
                + ast_data["code_elements"]["constants"]
            )

            next_elements = [
                elem for elem in all_elements if elem["line"] > func["line"]
            ]
            if next_elements:
                func_end = min(elem["line"] for elem in next_elements) - 1

            sections.append(
                {
                    "name": f"{func['name']} Function",
                    "description": f"Function {func['name']} implementation.",
                    "line_start": func["line"],
                    "line_end": func_end,
                }
            )

        # Add class sections
        for cls in ast_data["code_elements"]["classes"]:
            # Estimate class end
            class_end = cls["line"] + 10  # Default estimate
            if cls.get("methods"):
                last_method_line = max(method["line"] for method in cls["methods"])
                class_end = last_method_line + 3

            sections.append(
                {
                    "name": f"{cls['name']} Class",
                    "description": f"Class {cls['name']} definition and methods.",
                    "line_start": cls["line"],
                    "line_end": class_end,
                }
            )

        # Add constants section
        if ast_data["code_elements"]["constants"]:
            const_lines = [
                const["line"] for const in ast_data["code_elements"]["constants"]
            ]
            sections.append(
                {
                    "name": "Constants",
                    "description": "Global constants and configuration values.",
                    "line_start": min(const_lines),
                    "line_end": max(const_lines),
                }
            )

        return sections

    def create_simple_description_prompt(
        self, content: str, base_file_map: Dict[str, Any]
    ) -> str:
        """Create a simple prompt for AI to add only descriptions."""
        functions_list = "\n".join(
            [
                f"- {func['name']}: {func.get('signature', func['name'])}"
                for func in base_file_map["code_elements"]["functions"]
            ]
        )
        classes_list = "\n".join(
            [
                f"- {cls['name']}: {len(cls.get('methods', []))} methods"
                for cls in base_file_map["code_elements"]["classes"]
            ]
        )

        return f"""Add brief descriptions for these code elements:

Functions:
{functions_list}

Classes:
{classes_list}

Return only JSON:
{{
  "functions": {{"function_name": "brief description"}},
  "classes": {{"class_name": "brief description"}}
}}"""

    def parse_simple_descriptions(self, response: str) -> Dict[str, Any]:
        """Parse AI response to extract simple descriptions."""
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_content = response[json_start:json_end]
                return json.loads(json_content)
        except:
            pass

        return {"functions": {}, "classes": {}}

    def merge_simple_descriptions(
        self, base_file_map: Dict[str, Any], ai_descriptions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge AI-generated descriptions with deterministic structure."""
        final_map = base_file_map.copy()

        # Add descriptions to functions
        function_descriptions = ai_descriptions.get("functions", {})
        for func in final_map["code_elements"]["functions"]:
            if func["name"] in function_descriptions:
                func["description"] = function_descriptions[func["name"]]

        # Add descriptions to classes
        class_descriptions = ai_descriptions.get("classes", {})
        for cls in final_map["code_elements"]["classes"]:
            if cls["name"] in class_descriptions:
                cls["description"] = class_descriptions[cls["name"]]

        return final_map

    def format_file_map(self, file_map: Dict[str, Any], comment_style: tuple) -> str:
        """Format the file map as a comment block."""
        import json

        # FIXED: Use compact JSON formatting to prevent massive multi-line dumps
        # Single-line JSON formatting - most compact representation
        json_str = json.dumps(file_map, separators=(",", ":"))

        # FIXED: Put everything on one line with proper bookend tags
        return f"# FILE_MAP_BEGIN {json_str} FILE_MAP_END\n\n"

    def calculate_content_hash(self, content: str) -> str:
        """Calculate hash for content."""
        import hashlib

        return hashlib.md5(content.encode()).hexdigest()

    def extract_stored_hash(self, existing_map: str) -> Optional[str]:
        """Extract stored hash from existing file map."""
        # Look for hash in the file map JSON
        import re

        # Try new single-line format first
        json_match = re.search(r"# FILE_MAP_BEGIN (.*?) FILE_MAP_END", existing_map)
        if json_match:
            try:
                import json

                file_map_data = json.loads(json_match.group(1))
                return file_map_data.get("content_hash")
            except:
                pass

        # Fall back to old multi-line format for backward compatibility
        json_match = re.search(
            r"# FILE_MAP_BEGIN\s*\n# (.*?)\s*\n# FILE_MAP_END", existing_map, re.DOTALL
        )
        if json_match:
            try:
                import json

                file_map_data = json.loads(json_match.group(1))
                return file_map_data.get("content_hash")
            except:
                pass
            return None

    def is_valid_file_map(self, existing_map: str) -> bool:
        """Check if existing file map is valid."""
        import re
        import json

        # Try new single-line format first
        json_match = re.search(r"# FILE_MAP_BEGIN (.*?) FILE_MAP_END", existing_map)
        if json_match:
            try:
                file_map_data = json.loads(json_match.group(1))
                # Check for required fields
                required_fields = ["file_metadata", "code_elements", "key_elements"]
                return all(field in file_map_data for field in required_fields)
            except:
                pass

        # Fall back to old multi-line format for backward compatibility
        json_match = re.search(
            r"# FILE_MAP_BEGIN\s*\n# (.*?)\s*\n# FILE_MAP_END", existing_map, re.DOTALL
        )
        if json_match:
            try:
                file_map_data = json.loads(json_match.group(1))
                # Check for required fields
                required_fields = ["file_metadata", "code_elements", "key_elements"]
                return all(field in file_map_data for field in required_fields)
            except:
                pass
        return False

    async def generate_file_map_with_refinement(
        self, content: str, comment_style: tuple, force: bool = False
    ) -> str:
        """
        Generate file map using iterative refinement: Generate → Validate → Correct → Validate.
        This ensures consistently high-quality FILE_MAPs.
        """
        from genfilemap.core.validation import (
            validate_file_map_comprehensive,
            correct_file_map,
        )

        self.debug_print(f"Starting iterative refinement for: {self.file_path}")

        # Extract existing file map to get the remaining content (without file map)
        existing_map, remaining_content = extract_existing_file_map(
            content, comment_style
        )

        # STEP 1: Generate initial file map using deterministic approach
        self.debug_print("STEP 1: Generating initial file map...")
        initial_file_map = await self.generate_file_map_deterministic(
            content, comment_style, force
        )

        if not initial_file_map:
            self.debug_print("No file map generated, returning None")
            return None

        # Extract JSON from the formatted file map for validation
        import re

        json_match = re.search(r"# FILE_MAP_BEGIN (.*?) FILE_MAP_END", initial_file_map)
        if not json_match:
            self.debug_print("Could not extract JSON from generated file map")
            return initial_file_map  # Return as-is if we can't extract JSON

        file_map_json = json_match.group(1)

        # STEP 2: Comprehensive validation
        self.debug_print("STEP 2: Performing comprehensive validation...")
        validation_result = await validate_file_map_comprehensive(
            file_path=self.file_path,
            content=remaining_content,
            file_map_json=file_map_json,
            api_client=self.api_client,
            model=self.model,
            config=getattr(self, "config", None),
        )

        # STEP 3: Check if correction is needed
        if validation_result.get("is_valid", False):
            self.debug_print("STEP 3: File map is valid, no correction needed")
            return initial_file_map

        self.debug_print(
            f"STEP 3: Validation found issues: {validation_result.get('summary', 'Unknown issues')}"
        )

        # STEP 4: Apply corrections
        self.debug_print("STEP 4: Applying corrections...")
        correction_result = await correct_file_map(
            file_path=self.file_path,
            content=remaining_content,
            file_map_json=file_map_json,
            validation_result=validation_result,
            api_client=self.api_client,
            model=self.model,
            config=getattr(self, "config", None),
        )

        if not correction_result.get("corrected", False):
            self.debug_print(
                f"STEP 4: Correction failed: {correction_result.get('reason', 'Unknown reason')}"
            )
            return initial_file_map  # Return original if correction failed

        corrected_json = correction_result["file_map_json"]
        self.debug_print(
            f"STEP 4: Corrections applied: {correction_result.get('summary', 'Corrections applied')}"
        )

        # STEP 5: Final validation of corrected file map
        self.debug_print("STEP 5: Final validation of corrected file map...")
        final_validation = await validate_file_map_comprehensive(
            file_path=self.file_path,
            content=remaining_content,
            file_map_json=corrected_json,
            api_client=self.api_client,
            model=self.model,
            config=getattr(self, "config", None),
        )

        if final_validation.get("is_valid", False):
            self.debug_print(
                "STEP 5: Final validation successful - returning corrected file map"
            )
            # Format the corrected JSON back into file map format
            corrected_file_map_data = json.loads(corrected_json)
            return self.format_file_map(corrected_file_map_data, comment_style)
        else:
            self.debug_print(
                f"STEP 5: Final validation still failed: {final_validation.get('summary', 'Unknown issues')}"
            )
            # Return the corrected version anyway, as it's likely better than the original
            corrected_file_map_data = json.loads(corrected_json)
            return self.format_file_map(corrected_file_map_data, comment_style)
