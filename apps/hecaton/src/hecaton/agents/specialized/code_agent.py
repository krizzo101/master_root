import re
from typing import Any, Dict, List, Optional

from .base_agent import Agent


class CodeAgent(Agent):
    """Specialized agent for code generation and manipulation tasks."""

    def __init__(self, name="CodeAgent", **kwargs):
        """Initialize CodeAgent with code-specific capabilities.

        Args:
            name: Name for this agent instance
            **kwargs: Additional arguments (ignored)
        """
        capabilities = [
            "generate_function",
            "generate_class",
            "refactor_code",
            "add_documentation",
            "optimize_code",
            "convert_language",
        ]
        super().__init__(name=name, capabilities=capabilities)
        self.supported_languages = ["python", "javascript", "java", "cpp", "go"]

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code generation or manipulation task.

        Args:
            task: Task dictionary with keys:
                - type: Task type (e.g., 'generate_function')
                - language: Target programming language
                - specifications: Task-specific parameters

        Returns:
            Dictionary with generated code and metadata
        """
        task_type = task.get("type", "")
        language = task.get("language", "python")
        specs = task.get("specifications", {})

        result = {"success": False, "code": "", "message": "", "metadata": {}}

        try:
            if task_type == "generate_function":
                result = self.generate_function(language, specs)
            elif task_type == "generate_class":
                result = self.generate_class(language, specs)
            elif task_type == "refactor_code":
                result = self.refactor_code(specs.get("code", ""), specs)
            elif task_type == "add_documentation":
                result = self.add_documentation(specs.get("code", ""), language)
            elif task_type == "optimize_code":
                result = self.optimize_code(specs.get("code", ""), language)
            else:
                result["message"] = f"Unsupported task type: {task_type}"
        except Exception as e:
            result["message"] = f"Error executing task: {str(e)}"

        self.log_task(task, result)
        return result

    def generate_function(self, language: str, specs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a function based on specifications.

        Args:
            language: Programming language
            specs: Function specifications (name, params, return_type, logic)

        Returns:
            Generated function code
        """
        name = specs.get("name", "generated_function")
        params = specs.get("params", [])
        return_type = specs.get("return_type", "Any")
        logic = specs.get("logic", "pass")

        if language == "python":
            param_str = ", ".join(params) if params else ""
            code = f"""def {name}({param_str}) -> {return_type}:
    \"\"\"Generated function by CodeAgent.\"\"\"
    {logic}"""
        elif language == "javascript":
            param_str = ", ".join(params) if params else ""
            code = f"""function {name}({param_str}) {{
    // Generated function by CodeAgent
    {logic}
}}"""
        else:
            code = f"// Function generation for {language} not implemented yet"

        return {
            "success": True,
            "code": code,
            "message": f"Function '{name}' generated successfully",
            "metadata": {"lines": len(code.splitlines())},
        }

    def generate_class(self, language: str, specs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a class based on specifications.

        Args:
            language: Programming language
            specs: Class specifications (name, attributes, methods)

        Returns:
            Generated class code
        """
        name = specs.get("name", "GeneratedClass")
        attributes = specs.get("attributes", [])
        methods = specs.get("methods", [])

        if language == "python":
            code = f"class {name}:\n"
            code += '    """Generated class by CodeAgent."""\n\n'
            code += "    def __init__(self):\n"
            for attr in attributes:
                code += f"        self.{attr} = None\n"
            if not attributes:
                code += "        pass\n"
            for method in methods:
                code += f"\n    def {method}(self):\n"
                code += '        """Generated method."""\n'
                code += "        pass\n"
        elif language == "javascript":
            code = f"class {name} {{\n"
            code += "    constructor() {\n"
            for attr in attributes:
                code += f"        this.{attr} = null;\n"
            code += "    }\n"
            for method in methods:
                code += f"\n    {method}() {{\n"
                code += "        // Generated method\n"
                code += "    }\n"
            code += "}"
        else:
            code = f"// Class generation for {language} not implemented yet"

        return {
            "success": True,
            "code": code,
            "message": f"Class '{name}' generated successfully",
            "metadata": {"lines": len(code.splitlines())},
        }

    def refactor_code(self, code: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Refactor provided code based on options.

        Args:
            code: Original code to refactor
            options: Refactoring options

        Returns:
            Refactored code
        """
        refactored = code

        if options.get("snake_to_camel"):
            refactored = re.sub(r"_([a-z])", lambda m: m.group(1).upper(), refactored)

        if options.get("remove_comments"):
            refactored = re.sub(r"#.*$", "", refactored, flags=re.MULTILINE)
            refactored = re.sub(r"//.*$", "", refactored, flags=re.MULTILINE)

        if options.get("add_type_hints") and "def " in code:
            refactored = re.sub(r"def (\w+)\((.*?)\):", r"def \1(\2) -> Any:", refactored)

        return {
            "success": True,
            "code": refactored,
            "message": "Code refactored successfully",
            "metadata": {
                "original_lines": len(code.splitlines()),
                "refactored_lines": len(refactored.splitlines()),
            },
        }

    def add_documentation(self, code: str, language: str) -> Dict[str, Any]:
        """Add documentation to code.

        Args:
            code: Code to document
            language: Programming language

        Returns:
            Documented code
        """
        lines = code.splitlines()
        documented = []

        for line in lines:
            if language == "python" and line.strip().startswith("def "):
                documented.append(line)
                indent = len(line) - len(line.lstrip())
                documented.append(" " * (indent + 4) + '"""Auto-generated documentation."""')
            elif language == "javascript" and "function " in line:
                documented.append(line)
                documented.append("    // Auto-generated documentation")
            else:
                documented.append(line)

        result_code = "\n".join(documented)

        return {
            "success": True,
            "code": result_code,
            "message": "Documentation added successfully",
            "metadata": {"docs_added": len(documented) - len(lines)},
        }

    def optimize_code(self, code: str, language: str) -> Dict[str, Any]:
        """Apply basic optimizations to code.

        Args:
            code: Code to optimize
            language: Programming language

        Returns:
            Optimized code
        """
        optimized = code

        if language == "python":
            optimized = re.sub(r"if\s+\w+\s+==\s+True:", r"if \1:", optimized)
            optimized = re.sub(r"if\s+\w+\s+==\s+False:", r"if not \1:", optimized)
            optimized = re.sub(r"\s+\n", "\n", optimized)

        optimized = re.sub(r"\n{3,}", "\n\n", optimized)

        return {
            "success": True,
            "code": optimized,
            "message": "Code optimized successfully",
            "metadata": {"optimizations_applied": "basic"},
        }
