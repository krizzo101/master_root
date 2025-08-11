#!/usr/bin/env python3
"""
Dev Agent Validator - Enforce Code Map Checking

This tool enforces that dev agents MUST check the code map before making
any code changes to prevent guessing function names, parameters, variables, etc.

Usage:
    python dev_agent_validator.py check-before-change --function "function_name" --parameters "param1" "param2"
    python dev_agent_validator.py search-function --query "search_term"
    python dev_agent_validator.py validate-import --module "module_name"
"""

import argparse
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

# Add the tools directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from code_mapper import CodeMapManager


class DevAgentValidator:
    """Validator to enforce code map checking for dev agents"""

    def __init__(self):
        self.code_manager = CodeMapManager()
        self.validation_rules = {
            "function_calls": True,
            "variable_names": True,
            "import_statements": True,
            "class_usage": True,
            "parameter_validation": True,
        }

    def check_before_change(
        self,
        function_name: str,
        parameters: List[str] = None,
        file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        MANDATORY: Check function signature before making changes

        This MUST be called before any function call or modification
        """
        print("🔍 MANDATORY CODE MAP CHECK - Validating function call...")

        # Load the code map
        try:
            self.code_manager.load_map()
        except Exception as e:
            return {
                "valid": False,
                "error": f"Failed to load code map: {e}",
                "action": "Run 'python code_mapper.py analyze' first",
            }

        # Validate the function call
        result = self.code_manager.validate_function_call(
            function_name, parameters or [], file_path
        )

        if result["valid"]:
            print(f"✅ VALID: {result['signature']}")
            print(f"   📁 File: {result['file']}:{result['line']}")
            return result
        else:
            print(f"❌ INVALID: {result['error']}")
            if "suggestions" in result:
                print(f"💡 Suggestions: {', '.join(result['suggestions'])}")
            return result

    def search_function(self, query: str) -> List[Dict[str, Any]]:
        """Search for functions in the codebase"""
        print(f"🔍 Searching for functions: {query}")

        try:
            self.code_manager.load_map()
        except Exception as e:
            print(f"❌ Failed to load code map: {e}")
            return []

        functions = self.code_manager.search_functions(query)
        results = []

        for func in functions:
            result = {
                "name": func.name,
                "signature": f"{func.name}({', '.join(func.parameters)})",
                "file": func.file_path,
                "line": func.line_number,
                "is_method": func.is_method,
                "class_name": func.class_name,
                "docstring": func.docstring,
            }
            results.append(result)
            print(f"  📋 {result['signature']} - {result['file']}:{result['line']}")

        return results

    def search_class(self, query: str) -> List[Dict[str, Any]]:
        """Search for classes in the codebase"""
        print(f"🔍 Searching for classes: {query}")

        try:
            self.code_manager.load_map()
        except Exception as e:
            print(f"❌ Failed to load code map: {e}")
            return []

        classes = self.code_manager.search_classes(query)
        results = []

        for cls in classes:
            result = {
                "name": cls.name,
                "file": cls.file_path,
                "line": cls.line_number,
                "bases": cls.bases,
                "methods": cls.methods,
                "attributes": cls.attributes,
                "docstring": cls.docstring,
            }
            results.append(result)
            print(f"  🏗️  {cls.name} - {cls.file_path}:{cls.line_number}")
            print(
                f"     Methods: {', '.join(cls.methods[:5])}{'...' if len(cls.methods) > 5 else ''}"
            )

        return results

    def validate_import(self, module_name: str) -> Dict[str, Any]:
        """Validate if a module is imported in the codebase"""
        print(f"🔍 Validating import: {module_name}")

        try:
            self.code_manager.load_map()
        except Exception as e:
            print(f"❌ Failed to load code map: {e}")
            return {"valid": False, "error": str(e)}

        # Check if module is imported
        imports = [
            imp
            for imp in self.code_manager.code_map.imports
            if module_name in imp.module
        ]

        if imports:
            print(f"✅ Module '{module_name}' is imported in:")
            for imp in imports:
                print(f"   📁 {imp.file_path}:{imp.line_number} - {imp.imports}")
            return {"valid": True, "imports": imports}
        else:
            print(f"❌ Module '{module_name}' is NOT imported in the codebase")
            return {"valid": False, "error": f"Module '{module_name}' not found"}

    def get_function_signature(
        self, function_name: str, file_path: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get complete function signature and information"""
        try:
            self.code_manager.load_map()
        except Exception as e:
            print(f"❌ Failed to load code map: {e}")
            return None

        func = self.code_manager.get_function_signature(function_name, file_path)

        if func:
            return {
                "name": func.name,
                "signature": f"{func.name}({', '.join(func.parameters)})",
                "parameters": func.parameters,
                "default_values": func.default_values,
                "return_type": func.return_type,
                "file": func.file_path,
                "line": func.line_number,
                "docstring": func.docstring,
                "decorators": func.decorators,
                "is_async": func.is_async,
                "is_method": func.is_method,
                "class_name": func.class_name,
            }
        else:
            return None

    def enforce_validation(self, operation: str, **kwargs) -> bool:
        """
        Enforce validation for any code operation

        This is the main entry point that dev agents MUST call before any code changes
        """
        print(f"🔒 ENFORCING VALIDATION for operation: {operation}")

        if operation == "function_call":
            function_name = kwargs.get("function_name")
            parameters = kwargs.get("parameters", [])
            file_path = kwargs.get("file_path")

            if not function_name:
                print("❌ ERROR: function_name is required")
                return False

            result = self.check_before_change(function_name, parameters, file_path)
            return result["valid"]

        elif operation == "variable_usage":
            variable_name = kwargs.get("variable_name")
            if not variable_name:
                print("❌ ERROR: variable_name is required")
                return False

            # Search for variable in code map
            try:
                self.code_manager.load_map()
                variables = [
                    v
                    for v in self.code_manager.code_map.variables
                    if variable_name in v.name
                ]

                if variables:
                    print(f"✅ Variable '{variable_name}' found in codebase:")
                    for var in variables[:3]:  # Show first 3 occurrences
                        print(
                            f"   📁 {var.file_path}:{var.line_number} (scope: {var.scope})"
                        )
                    return True
                else:
                    print(f"❌ Variable '{variable_name}' NOT found in codebase")
                    return False
            except Exception as e:
                print(f"❌ Failed to validate variable: {e}")
                return False

        elif operation == "import_check":
            module_name = kwargs.get("module_name")
            if not module_name:
                print("❌ ERROR: module_name is required")
                return False

            result = self.validate_import(module_name)
            return result["valid"]

        else:
            print(f"❌ Unknown operation: {operation}")
            return False


def main():
    """Main entry point for dev agent validation"""
    parser = argparse.ArgumentParser(
        description="Dev Agent Validator - Enforce Code Map Checking"
    )
    parser.add_argument(
        "command",
        choices=[
            "check-before-change",
            "search-function",
            "search-class",
            "validate-import",
            "get-signature",
            "enforce",
        ],
        help="Command to run",
    )

    parser.add_argument("--function", help="Function name")
    parser.add_argument("--parameters", nargs="*", help="Function parameters")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--module", help="Module name")
    parser.add_argument("--variable", help="Variable name")
    parser.add_argument("--operation", help="Operation type for enforce")
    parser.add_argument("--file", help="File path context")

    args = parser.parse_args()

    validator = DevAgentValidator()

    if args.command == "check-before-change":
        if not args.function:
            print("❌ ERROR: --function is required")
            sys.exit(1)

        result = validator.check_before_change(
            args.function, args.parameters, args.file
        )
        if not result["valid"]:
            sys.exit(1)

    elif args.command == "search-function":
        if not args.query:
            print("❌ ERROR: --query is required")
            sys.exit(1)

        validator.search_function(args.query)

    elif args.command == "search-class":
        if not args.query:
            print("❌ ERROR: --query is required")
            sys.exit(1)

        validator.search_class(args.query)

    elif args.command == "validate-import":
        if not args.module:
            print("❌ ERROR: --module is required")
            sys.exit(1)

        result = validator.validate_import(args.module)
        if not result["valid"]:
            sys.exit(1)

    elif args.command == "get-signature":
        if not args.function:
            print("❌ ERROR: --function is required")
            sys.exit(1)

        signature = validator.get_function_signature(args.function, args.file)
        if signature:
            print("📋 Function Signature:")
            print(f"   Name: {signature['name']}")
            print(f"   Signature: {signature['signature']}")
            print(f"   Parameters: {signature['parameters']}")
            print(f"   Default Values: {signature['default_values']}")
            print(f"   Return Type: {signature['return_type']}")
            print(f"   File: {signature['file']}:{signature['line']}")
            if signature["docstring"]:
                print(f"   Docstring: {signature['docstring'][:100]}...")
        else:
            print(f"❌ Function '{args.function}' not found")
            sys.exit(1)

    elif args.command == "enforce":
        if not args.operation:
            print("❌ ERROR: --operation is required")
            sys.exit(1)

        kwargs = {}
        if args.function:
            kwargs["function_name"] = args.function
        if args.parameters:
            kwargs["parameters"] = args.parameters
        if args.variable:
            kwargs["variable_name"] = args.variable
        if args.module:
            kwargs["module_name"] = args.module
        if args.file:
            kwargs["file_path"] = args.file

        success = validator.enforce_validation(args.operation, **kwargs)
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
