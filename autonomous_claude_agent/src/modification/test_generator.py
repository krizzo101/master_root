"""
Test Generator for Self-Modification System

Automatically generates tests for code modifications
including unit tests, integration tests, and property-based tests.

Created: 2025-08-15
"""

import ast
import re
import inspect
import textwrap
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib


@dataclass
class TestCase:
    """Individual test case"""
    name: str
    test_code: str
    target_function: str
    test_type: str  # unit, integration, property, edge_case
    description: str
    assertions: List[str]
    setup_code: Optional[str] = None
    teardown_code: Optional[str] = None
    expected_output: Optional[Any] = None
    tags: List[str] = field(default_factory=list)
    
    def to_pytest(self) -> str:
        """Convert to pytest format"""
        test_lines = []
        
        # Add test function signature
        test_lines.append(f"def test_{self.name}():")
        
        # Add docstring
        test_lines.append(f'    """{self.description}"""')
        
        # Add setup if present
        if self.setup_code:
            test_lines.append("    # Setup")
            for line in self.setup_code.splitlines():
                test_lines.append(f"    {line}")
            test_lines.append("")
        
        # Add test code
        test_lines.append("    # Test")
        for line in self.test_code.splitlines():
            test_lines.append(f"    {line}")
        
        # Add assertions
        test_lines.append("")
        test_lines.append("    # Assertions")
        for assertion in self.assertions:
            test_lines.append(f"    {assertion}")
        
        # Add teardown if present
        if self.teardown_code:
            test_lines.append("")
            test_lines.append("    # Teardown")
            for line in self.teardown_code.splitlines():
                test_lines.append(f"    {line}")
        
        return '\n'.join(test_lines)
    
    def to_unittest(self) -> str:
        """Convert to unittest format"""
        test_lines = []
        
        test_lines.append(f"def test_{self.name}(self):")
        test_lines.append(f'    """{self.description}"""')
        
        if self.setup_code:
            test_lines.append("    # Setup")
            for line in self.setup_code.splitlines():
                test_lines.append(f"    {line}")
            test_lines.append("")
        
        test_lines.append("    # Test")
        for line in self.test_code.splitlines():
            test_lines.append(f"    {line}")
        
        test_lines.append("")
        test_lines.append("    # Assertions")
        for assertion in self.assertions:
            # Convert pytest assertions to unittest
            unittest_assertion = assertion.replace("assert ", "self.assert")
            unittest_assertion = re.sub(r"assert\s+(.+)\s*==\s*(.+)", 
                                      r"self.assertEqual(\1, \2)", 
                                      unittest_assertion)
            unittest_assertion = re.sub(r"assert\s+(.+)\s*!=\s*(.+)", 
                                      r"self.assertNotEqual(\1, \2)", 
                                      unittest_assertion)
            test_lines.append(f"    {unittest_assertion}")
        
        if self.teardown_code:
            test_lines.append("")
            test_lines.append("    # Teardown")
            for line in self.teardown_code.splitlines():
                test_lines.append(f"    {line}")
        
        return '\n'.join(test_lines)


@dataclass
class TestSuite:
    """Collection of test cases"""
    name: str
    description: str
    test_cases: List[TestCase]
    imports: List[str] = field(default_factory=list)
    fixtures: Dict[str, str] = field(default_factory=dict)
    framework: str = "pytest"  # pytest or unittest
    coverage_target: float = 0.8
    
    def generate_test_file(self) -> str:
        """Generate complete test file"""
        lines = []
        
        # Add header
        lines.append('"""')
        lines.append(f"Test Suite: {self.name}")
        lines.append(f"{self.description}")
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append('"""')
        lines.append("")
        
        # Add imports
        if self.framework == "pytest":
            lines.append("import pytest")
        else:
            lines.append("import unittest")
        
        for import_stmt in self.imports:
            lines.append(import_stmt)
        lines.append("")
        
        # Add fixtures (pytest only)
        if self.framework == "pytest" and self.fixtures:
            for fixture_name, fixture_code in self.fixtures.items():
                lines.append(f"@pytest.fixture")
                lines.append(f"def {fixture_name}():")
                for line in fixture_code.splitlines():
                    lines.append(f"    {line}")
                lines.append("")
        
        # Add test class for unittest
        if self.framework == "unittest":
            lines.append(f"class Test{self.name.replace('_', '').title()}(unittest.TestCase):")
            lines.append(f'    """{self.description}"""')
            lines.append("")
            
            # Add test cases
            for test_case in self.test_cases:
                for line in test_case.to_unittest().splitlines():
                    lines.append(f"    {line}")
                lines.append("")
            
            # Add main
            lines.append("")
            lines.append("if __name__ == '__main__':")
            lines.append("    unittest.main()")
        
        else:  # pytest
            # Add test cases
            for test_case in self.test_cases:
                lines.append(test_case.to_pytest())
                lines.append("")
        
        return '\n'.join(lines)
    
    def add_test_case(self, test_case: TestCase):
        """Add test case to suite"""
        self.test_cases.append(test_case)
    
    def get_coverage_estimate(self) -> float:
        """Estimate test coverage"""
        # Simple heuristic based on test types
        test_types = set(tc.test_type for tc in self.test_cases)
        coverage = 0.0
        
        if 'unit' in test_types:
            coverage += 0.4
        if 'integration' in test_types:
            coverage += 0.2
        if 'edge_case' in test_types:
            coverage += 0.2
        if 'property' in test_types:
            coverage += 0.2
        
        # Adjust based on number of tests
        test_count_factor = min(len(self.test_cases) / 10, 1.0)
        coverage *= test_count_factor
        
        return min(coverage, 1.0)


class CoverageAnalyzer:
    """Analyze test coverage for code"""
    
    @staticmethod
    def analyze_coverage(code: str, test_suite: TestSuite) -> Dict[str, Any]:
        """Analyze test coverage for code"""
        coverage = {
            'functions_covered': [],
            'functions_uncovered': [],
            'classes_covered': [],
            'classes_uncovered': [],
            'branches_covered': 0,
            'branches_total': 0,
            'estimated_coverage': 0.0
        }
        
        try:
            tree = ast.parse(code)
            
            # Find all functions and classes
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
            
            # Check which are covered by tests
            test_targets = set()
            for test_case in test_suite.test_cases:
                test_targets.add(test_case.target_function)
                
                # Extract targets from test code
                try:
                    test_tree = ast.parse(test_case.test_code)
                    for node in ast.walk(test_tree):
                        if isinstance(node, ast.Call):
                            if isinstance(node.func, ast.Name):
                                test_targets.add(node.func.id)
                            elif isinstance(node.func, ast.Attribute):
                                test_targets.add(node.func.attr)
                except:
                    pass
            
            # Categorize coverage
            for func in functions:
                if func in test_targets or f"test_{func}" in test_targets:
                    coverage['functions_covered'].append(func)
                else:
                    coverage['functions_uncovered'].append(func)
            
            for cls in classes:
                if cls in test_targets or f"Test{cls}" in test_targets:
                    coverage['classes_covered'].append(cls)
                else:
                    coverage['classes_uncovered'].append(cls)
            
            # Calculate branch coverage (simplified)
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.Try)):
                    coverage['branches_total'] += 1
                    # Heuristic: assume covered if parent function is tested
                    parent_func = CoverageAnalyzer._get_parent_function(tree, node)
                    if parent_func and parent_func.name in coverage['functions_covered']:
                        coverage['branches_covered'] += 1
            
            # Calculate estimated coverage
            total_items = len(functions) + len(classes)
            covered_items = len(coverage['functions_covered']) + len(coverage['classes_covered'])
            
            if total_items > 0:
                coverage['estimated_coverage'] = covered_items / total_items
            else:
                coverage['estimated_coverage'] = 1.0
        
        except SyntaxError:
            pass
        
        return coverage
    
    @staticmethod
    def _get_parent_function(tree: ast.AST, target: ast.AST) -> Optional[ast.FunctionDef]:
        """Get parent function of a node"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if target in ast.walk(node):
                    return node
        return None


class TestGenerator:
    """Generate tests for code modifications"""
    
    def __init__(self, framework: str = "pytest"):
        """Initialize test generator"""
        self.framework = framework
        self.test_templates = self._initialize_templates()
        self.coverage_analyzer = CoverageAnalyzer()
    
    def _initialize_templates(self) -> Dict[str, str]:
        """Initialize test templates"""
        templates = {}
        
        # Unit test template
        templates['unit'] = textwrap.dedent('''
            result = {function_call}
            expected = {expected_value}
        ''').strip()
        
        # Edge case template
        templates['edge_case'] = textwrap.dedent('''
            # Test edge case: {edge_case_description}
            result = {function_call}
        ''').strip()
        
        # Exception test template
        templates['exception'] = textwrap.dedent('''
            with pytest.raises({exception_type}):
                {function_call}
        ''').strip()
        
        # Property test template
        templates['property'] = textwrap.dedent('''
            @hypothesis.given({strategy})
            def test_property_{property_name}({parameters}):
                result = {function_call}
                assert {property_assertion}
        ''').strip()
        
        return templates
    
    def generate_tests(self, code: str, 
                       context: Optional[Dict[str, Any]] = None) -> TestSuite:
        """Generate comprehensive test suite for code"""
        context = context or {}
        
        # Parse code
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return TestSuite(
                name="invalid_code",
                description="Tests for invalid code",
                test_cases=[],
                framework=self.framework
            )
        
        # Extract testable elements
        functions = self._extract_functions(tree)
        classes = self._extract_classes(tree)
        
        # Generate test suite
        suite_name = context.get('suite_name', 'generated_tests')
        suite = TestSuite(
            name=suite_name,
            description=f"Auto-generated test suite for {suite_name}",
            test_cases=[],
            framework=self.framework
        )
        
        # Add necessary imports
        suite.imports.extend([
            "import sys",
            "import os",
            f"# TODO: Add import for module under test"
        ])
        
        # Generate tests for functions
        for func in functions:
            test_cases = self._generate_function_tests(func)
            suite.test_cases.extend(test_cases)
        
        # Generate tests for classes
        for cls in classes:
            test_cases = self._generate_class_tests(cls)
            suite.test_cases.extend(test_cases)
        
        return suite
    
    def _extract_functions(self, tree: ast.AST) -> List[ast.FunctionDef]:
        """Extract function definitions from AST"""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Skip private functions in initial test generation
                if not node.name.startswith('_'):
                    functions.append(node)
        return functions
    
    def _extract_classes(self, tree: ast.AST) -> List[ast.ClassDef]:
        """Extract class definitions from AST"""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node)
        return classes
    
    def _generate_function_tests(self, func: ast.FunctionDef) -> List[TestCase]:
        """Generate tests for a function"""
        test_cases = []
        
        # Generate basic unit test
        unit_test = self._generate_unit_test(func)
        if unit_test:
            test_cases.append(unit_test)
        
        # Generate edge case tests
        edge_tests = self._generate_edge_case_tests(func)
        test_cases.extend(edge_tests)
        
        # Generate exception tests
        exception_tests = self._generate_exception_tests(func)
        test_cases.extend(exception_tests)
        
        return test_cases
    
    def _generate_unit_test(self, func: ast.FunctionDef) -> Optional[TestCase]:
        """Generate basic unit test for function"""
        # Generate function call
        params = self._generate_test_parameters(func)
        function_call = f"{func.name}({', '.join(params)})"
        
        # Generate test code
        test_code = self.test_templates['unit'].format(
            function_call=function_call,
            expected_value="None  # TODO: Set expected value"
        )
        
        # Generate assertions
        assertions = self._generate_assertions(func)
        
        return TestCase(
            name=f"{func.name}_basic",
            test_code=test_code,
            target_function=func.name,
            test_type="unit",
            description=f"Basic test for {func.name}",
            assertions=assertions,
            tags=['unit', 'basic']
        )
    
    def _generate_edge_case_tests(self, func: ast.FunctionDef) -> List[TestCase]:
        """Generate edge case tests for function"""
        test_cases = []
        
        # Common edge cases
        edge_cases = [
            ("empty_input", "Empty input", "''", "[]", "{}"),
            ("none_input", "None input", "None"),
            ("zero_input", "Zero input", "0", "0.0"),
            ("negative_input", "Negative input", "-1", "-999"),
            ("large_input", "Large input", "10**9", "' ' * 10000")
        ]
        
        for case_name, description, *values in edge_cases:
            # Check if edge case applies to function parameters
            if self._edge_case_applies(func, case_name):
                params = self._generate_edge_case_parameters(func, values)
                function_call = f"{func.name}({', '.join(params)})"
                
                test_code = self.test_templates['edge_case'].format(
                    edge_case_description=description,
                    function_call=function_call
                )
                
                test_case = TestCase(
                    name=f"{func.name}_{case_name}",
                    test_code=test_code,
                    target_function=func.name,
                    test_type="edge_case",
                    description=f"Edge case test: {description}",
                    assertions=["assert result is not None  # TODO: Add specific assertion"],
                    tags=['edge_case', case_name]
                )
                
                test_cases.append(test_case)
        
        return test_cases
    
    def _generate_exception_tests(self, func: ast.FunctionDef) -> List[TestCase]:
        """Generate exception tests for function"""
        test_cases = []
        
        # Check if function has exception handling
        has_try = any(isinstance(node, ast.Try) for node in ast.walk(func))
        
        if has_try or self._may_raise_exceptions(func):
            # Generate invalid input test
            params = self._generate_invalid_parameters(func)
            function_call = f"{func.name}({', '.join(params)})"
            
            test_code = self.test_templates['exception'].format(
                exception_type="Exception  # TODO: Specify exception type",
                function_call=function_call
            )
            
            test_case = TestCase(
                name=f"{func.name}_exception",
                test_code=test_code,
                target_function=func.name,
                test_type="exception",
                description=f"Exception handling test for {func.name}",
                assertions=[],  # No assertions needed for exception tests
                tags=['exception', 'error_handling']
            )
            
            test_cases.append(test_case)
        
        return test_cases
    
    def _generate_class_tests(self, cls: ast.ClassDef) -> List[TestCase]:
        """Generate tests for a class"""
        test_cases = []
        
        # Generate initialization test
        init_test = self._generate_init_test(cls)
        if init_test:
            test_cases.append(init_test)
        
        # Generate tests for public methods
        for node in cls.body:
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_') or node.name == '__init__':
                    continue
                
                # Generate method tests
                method_tests = self._generate_method_tests(cls, node)
                test_cases.extend(method_tests)
        
        return test_cases
    
    def _generate_init_test(self, cls: ast.ClassDef) -> Optional[TestCase]:
        """Generate initialization test for class"""
        # Find __init__ method
        init_method = None
        for node in cls.body:
            if isinstance(node, ast.FunctionDef) and node.name == '__init__':
                init_method = node
                break
        
        # Generate initialization test
        params = self._generate_test_parameters(init_method) if init_method else []
        
        test_code = f"instance = {cls.name}({', '.join(params)})"
        
        assertions = [
            f"assert instance is not None",
            f"assert isinstance(instance, {cls.name})"
        ]
        
        return TestCase(
            name=f"{cls.name}_initialization",
            test_code=test_code,
            target_function=cls.name,
            test_type="unit",
            description=f"Test {cls.name} initialization",
            assertions=assertions,
            tags=['class', 'initialization']
        )
    
    def _generate_method_tests(self, cls: ast.ClassDef, 
                              method: ast.FunctionDef) -> List[TestCase]:
        """Generate tests for class method"""
        test_cases = []
        
        # Setup code for creating instance
        setup_code = f"instance = {cls.name}()  # TODO: Add initialization parameters"
        
        # Generate method call
        params = self._generate_test_parameters(method, skip_self=True)
        method_call = f"instance.{method.name}({', '.join(params)})"
        
        test_code = f"result = {method_call}"
        
        test_case = TestCase(
            name=f"{cls.name}_{method.name}",
            test_code=test_code,
            target_function=f"{cls.name}.{method.name}",
            test_type="unit",
            description=f"Test {cls.name}.{method.name}",
            assertions=["assert result is not None  # TODO: Add specific assertion"],
            setup_code=setup_code,
            tags=['class', 'method']
        )
        
        test_cases.append(test_case)
        
        return test_cases
    
    def _generate_test_parameters(self, func: ast.FunctionDef, 
                                 skip_self: bool = False) -> List[str]:
        """Generate test parameters for function"""
        params = []
        
        for i, arg in enumerate(func.args.args):
            if skip_self and i == 0 and arg.arg == 'self':
                continue
            
            # Generate parameter based on type hint or name
            if arg.annotation:
                param = self._generate_value_for_type(arg.annotation)
            else:
                param = self._generate_value_for_name(arg.arg)
            
            params.append(param)
        
        return params
    
    def _generate_value_for_type(self, annotation: ast.AST) -> str:
        """Generate test value based on type annotation"""
        if isinstance(annotation, ast.Name):
            type_name = annotation.id
            if type_name == 'str':
                return "'test_string'"
            elif type_name == 'int':
                return "42"
            elif type_name == 'float':
                return "3.14"
            elif type_name == 'bool':
                return "True"
            elif type_name == 'list':
                return "[1, 2, 3]"
            elif type_name == 'dict':
                return "{'key': 'value'}"
            else:
                return f"None  # TODO: Provide {type_name} instance"
        
        return "None  # TODO: Provide test value"
    
    def _generate_value_for_name(self, param_name: str) -> str:
        """Generate test value based on parameter name"""
        # Common parameter patterns
        if 'name' in param_name.lower() or 'string' in param_name.lower():
            return "'test_value'"
        elif 'count' in param_name.lower() or 'number' in param_name.lower():
            return "10"
        elif 'flag' in param_name.lower() or 'is_' in param_name.lower():
            return "True"
        elif 'list' in param_name.lower() or 'items' in param_name.lower():
            return "[]"
        elif 'dict' in param_name.lower() or 'data' in param_name.lower():
            return "{}"
        else:
            return "None  # TODO: Provide test value"
    
    def _generate_assertions(self, func: ast.FunctionDef) -> List[str]:
        """Generate assertions for function test"""
        assertions = []
        
        # Basic assertion
        assertions.append("assert result is not None  # TODO: Add specific assertion")
        
        # Type assertion based on return annotation
        if func.returns:
            if isinstance(func.returns, ast.Name):
                type_name = func.returns.id
                assertions.append(f"assert isinstance(result, {type_name})")
        
        # Additional assertions based on function name
        if 'calculate' in func.name.lower() or 'compute' in func.name.lower():
            assertions.append("assert isinstance(result, (int, float))")
        elif 'validate' in func.name.lower() or 'check' in func.name.lower():
            assertions.append("assert isinstance(result, bool)")
        elif 'get' in func.name.lower() or 'fetch' in func.name.lower():
            assertions.append("assert result is not None")
        
        return assertions
    
    def _edge_case_applies(self, func: ast.FunctionDef, case_name: str) -> bool:
        """Check if edge case applies to function"""
        # Simple heuristic based on parameter types
        has_params = len(func.args.args) > 0
        
        if case_name in ['empty_input', 'none_input']:
            return has_params
        elif case_name in ['zero_input', 'negative_input']:
            # Check if function might handle numbers
            return any('num' in arg.arg.lower() or 'count' in arg.arg.lower() 
                      for arg in func.args.args)
        elif case_name == 'large_input':
            return has_params
        
        return False
    
    def _generate_edge_case_parameters(self, func: ast.FunctionDef, 
                                      values: Tuple[str, ...]) -> List[str]:
        """Generate edge case parameters"""
        params = []
        
        for i, arg in enumerate(func.args.args):
            if i < len(values):
                params.append(values[i])
            else:
                params.append(self._generate_value_for_name(arg.arg))
        
        return params
    
    def _generate_invalid_parameters(self, func: ast.FunctionDef) -> List[str]:
        """Generate invalid parameters for exception testing"""
        params = []
        
        for arg in func.args.args:
            # Generate invalid value based on expected type
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    type_name = arg.annotation.id
                    if type_name == 'str':
                        params.append("123")  # Number instead of string
                    elif type_name in ['int', 'float']:
                        params.append("'not_a_number'")
                    else:
                        params.append("'invalid'")
                else:
                    params.append("None")
            else:
                params.append("None")
        
        return params
    
    def _may_raise_exceptions(self, func: ast.FunctionDef) -> bool:
        """Check if function may raise exceptions"""
        # Check for operations that might raise exceptions
        for node in ast.walk(func):
            if isinstance(node, (ast.Subscript, ast.Attribute)):
                return True  # May raise AttributeError or KeyError
            elif isinstance(node, ast.BinOp):
                if isinstance(node.op, ast.Div):
                    return True  # May raise ZeroDivisionError
        
        return False
    
    def generate_from_modification(self, original_code: str, 
                                  modified_code: str) -> TestSuite:
        """Generate tests specifically for code modification"""
        # Generate tests for modified code
        suite = self.generate_tests(modified_code)
        
        # Add regression tests
        regression_tests = self._generate_regression_tests(original_code, modified_code)
        suite.test_cases.extend(regression_tests)
        
        return suite
    
    def _generate_regression_tests(self, original_code: str, 
                                  modified_code: str) -> List[TestCase]:
        """Generate regression tests to ensure modifications don't break existing functionality"""
        test_cases = []
        
        # Parse both versions
        try:
            original_tree = ast.parse(original_code)
            modified_tree = ast.parse(modified_code)
        except SyntaxError:
            return test_cases
        
        # Find functions that exist in both versions
        original_funcs = {node.name: node for node in ast.walk(original_tree) 
                         if isinstance(node, ast.FunctionDef)}
        modified_funcs = {node.name: node for node in ast.walk(modified_tree) 
                         if isinstance(node, ast.FunctionDef)}
        
        common_funcs = set(original_funcs.keys()) & set(modified_funcs.keys())
        
        for func_name in common_funcs:
            # Generate regression test
            test_case = TestCase(
                name=f"{func_name}_regression",
                test_code=f"# TODO: Add regression test for {func_name}",
                target_function=func_name,
                test_type="regression",
                description=f"Regression test to ensure {func_name} still works after modification",
                assertions=["assert True  # TODO: Add regression assertions"],
                tags=['regression', 'modification']
            )
            
            test_cases.append(test_case)
        
        return test_cases