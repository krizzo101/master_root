"""
Testing Framework Generator - AI-powered test generation and framework setup using OpenAI's O3 models.

This script generates comprehensive test suites, test frameworks, and testing configurations
for various programming languages and frameworks.
"""

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Optional

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)
else:
    pass
try:
    from openai import OpenAI
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass
try:
    from src.tools.code_generation.o3_code_generator.config.core.config_manager import (
        ConfigManager,
    )
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass
try:
    from o3_logger.logger import setup_logger
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass
try:
    from schemas.testing_framework_generator_input_schema import (
        TestingFrameworkGeneratorInput,
    )
    from schemas.testing_framework_generator_output_schema import (
        TestingFrameworkGeneratorOutput,
    )
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass
try:
    from src.tools.code_generation.o3_code_generator.config.self_improvement.validation_framework import (
        validate_code_quality,
        validate_documentation,
        validate_imports,
        validate_syntax,
    )
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass


class ProjectAnalyzer:
    """Analyzes project structure and requirements for testing configuration."""

    def __init__(self, logger: Any) -> None:
        self.logger = logger

    def analyze_project(self, project_path: Path) -> dict[str, Any]:
        """
        Analyze project for testing requirements.

        Args:
            project_path: Path to the project directory

        Returns:
            Dictionary containing project analysis
        """
        self.logger.log_info(
            f"Analyzing project for testing configuration: {project_path}"
        )
        analysis = {
            "project_type": self._detect_project_type(project_path),
            "existing_tests": self._find_existing_tests(project_path),
            "testable_components": self._identify_testable_components(project_path),
            "dependencies": self._analyze_dependencies(project_path),
            "framework_preferences": self._detect_framework_preferences(project_path),
            "testing_needs": self._assess_testing_needs(project_path),
        }
        self.logger.log_info(f"Project analysis completed: {analysis['project_type']}")
        return analysis

    def _detect_project_type(self, project_path: Path) -> str:
        """Detect the type of project."""
        if (project_path / "requirements.txt").exists():
            return "python"
        elif (project_path / "package.json").exists():
            return "nodejs"
        elif (project_path / "pom.xml").exists():
            return "java"
        elif (project_path / "Cargo.toml").exists():
            return "rust"
        elif (project_path / "go.mod").exists():
            return "go"
        else:
            return "unknown"

    def _find_existing_tests(self, project_path: Path) -> list[str]:
        """Find existing test files in the project."""
        test_files = []
        test_patterns = [
            "test_*.py",
            "*_test.py",
            "tests.py",
            "*.test.js",
            "*.spec.js",
            "*.test.ts",
            "*.spec.ts",
            "*Test.java",
            "*Tests.java",
            "*_test.rs",
            "*_tests.rs",
            "*_test.go",
            "*_tests.go",
        ]
        for pattern in test_patterns:
            test_files.extend([str(f) for f in project_path.rglob(pattern)])
        else:
            pass
        return test_files

    def _identify_testable_components(self, project_path: Path) -> list[dict[str, Any]]:
        """Identify components that need testing."""
        components = []
        for py_file in project_path.rglob("*.py"):
            if not any(
                skip in str(py_file) for skip in ["__pycache__", "tests", "test_"]
            ):
                components.append(
                    {
                        "file": str(py_file),
                        "type": "python_module",
                        "priority": "high"
                        if "main" in py_file.name or "app" in py_file.name
                        else "medium",
                    }
                )
            else:
                pass
        else:
            pass
        for js_file in project_path.rglob("*.js"):
            if not any(
                skip in str(js_file) for skip in ["node_modules", "tests", "test_"]
            ):
                components.append(
                    {
                        "file": str(js_file),
                        "type": "javascript_module",
                        "priority": "high"
                        if "main" in js_file.name or "app" in js_file.name
                        else "medium",
                    }
                )
            else:
                pass
        else:
            pass
        return components

    def _analyze_dependencies(self, project_path: Path) -> dict[str, Any]:
        """Analyze project dependencies for testing."""
        deps = {"runtime": [], "dev": [], "testing": []}
        if (project_path / "requirements.txt").exists():
            with open(project_path / "requirements.txt") as f:
                deps["runtime"] = [
                    line.strip()
                    for line in f
                    if line.strip() and (not line.startswith("#"))
                ]
        else:
            pass
        if (project_path / "package.json").exists():
            with open(project_path / "package.json") as f:
                pkg_data = json.load(f)
                deps["runtime"].extend(list(pkg_data.get("dependencies", {}).keys()))
                deps["dev"].extend(list(pkg_data.get("devDependencies", {}).keys()))
        else:
            pass
        return deps

    def _detect_framework_preferences(self, project_path: Path) -> list[str]:
        """Detect testing framework preferences."""
        frameworks = []
        if (project_path / "pytest.ini").exists() or (
            project_path / "pyproject.toml"
        ).exists():
            frameworks.append("pytest")
        else:
            pass
        if (project_path / "tox.ini").exists():
            frameworks.append("tox")
        else:
            pass
        if (project_path / "package.json").exists():
            with open(project_path / "package.json") as f:
                pkg_data = json.load(f)
                dev_deps = pkg_data.get("devDependencies", {})
                if "jest" in dev_deps:
                    frameworks.append("jest")
                else:
                    pass
                if "mocha" in dev_deps:
                    frameworks.append("mocha")
                else:
                    pass
                if "cypress" in dev_deps:
                    frameworks.append("cypress")
                else:
                    pass
        else:
            pass
        return frameworks

    def _assess_testing_needs(self, project_path: Path) -> dict[str, Any]:
        """Assess testing needs for the project."""
        needs = {
            "unit_tests": True,
            "integration_tests": True,
            "e2e_tests": False,
            "performance_tests": False,
            "security_tests": False,
            "api_tests": False,
        }
        api_indicators = ["fastapi", "flask", "django", "express", "koa"]
        for indicator in api_indicators:
            if any(indicator in str(f) for f in project_path.rglob("*")):
                needs["api_tests"] = True
                needs["e2e_tests"] = True
                break
            else:
                pass
        else:
            pass
        web_indicators = ["react", "vue", "angular", "html", "css"]
        for indicator in web_indicators:
            if any(indicator in str(f) for f in project_path.rglob("*")):
                needs["e2e_tests"] = True
                break
            else:
                pass
        else:
            pass
        return needs


class TestGenerator:
    """Generates test files using AI."""

    def __init__(self, client: OpenAI, logger: Any) -> None:
        self.client = client
        self.logger = logger

    def generate_tests(
        self,
        project_name: str,
        components: list[dict[str, Any]],
        framework: str,
        config: dict[str, Any],
    ) -> dict[str, str]:
        """
        Generate test files for project components.

        Args:
            project_name: Name of the project
            components: Components to test
            framework: Testing framework to use
            config: Test generation configuration

        Returns:
            Dictionary containing generated test files
        """
        self.logger.log_info(f"Generating tests for {project_name} using {framework}")
        test_files = {}
        for component in components[: config.get("max_components", 10)]:
            test_content = self._generate_component_tests(component, framework, config)
            if test_content:
                test_filename = self._generate_test_filename(
                    component["file"], framework
                )
                test_files[test_filename] = test_content
            else:
                pass
        else:
            pass
        return test_files

    def _generate_component_tests(
        self, component: dict[str, Any], framework: str, config: dict[str, Any]
    ) -> Optional[str]:
        """Generate tests for a specific component."""
        try:
            with open(component["file"]) as f:
                content = f.read()
        except Exception as e:
            self.logger.log_warning(
                f"Failed to read component {component['file']}: {e}"
            )
            return None
        else:
            pass
        finally:
            pass
        prompt = f"\nGenerate comprehensive tests for the following component using {framework}.\n\nComponent: {component['file']}\nType: {component['type']}\nPriority: {component['priority']}\n\nCode:\n{content[:1500]}  # Limit content to avoid token limits\n\nRequirements:\n1. Include unit tests for all functions/methods\n2. Include edge cases and error conditions\n3. Use proper test naming conventions\n4. Include setup and teardown if needed\n5. Mock external dependencies\n6. Include assertions for expected behavior\n7. Follow {framework} best practices\n8. Include test documentation\n\nConfiguration:\n{json.dumps(config, indent=2)}\n\nGenerate only the test file content, no additional text.\n"
        try:
            response = self.client.chat.completions.create(
                model="o3-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a testing expert. Generate comprehensive tests using {framework}.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=16000,
                temperature=0.2,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.log_error(
                f"Failed to generate tests for {component['file']} with O3: {e}"
            )
            return self._generate_fallback_tests(component, framework)
        else:
            pass
        finally:
            pass

    def _generate_test_filename(self, component_file: str, framework: str) -> str:
        """Generate test filename based on component and framework."""
        component_path = Path(component_file)
        if framework == "pytest":
            return f"test_{component_path.stem}.py"
        elif framework == "jest":
            return f"{component_path.stem}.test.js"
        elif framework == "mocha":
            return f"{component_path.stem}.spec.js"
        else:
            return f"test_{component_path.stem}.py"

    def _generate_fallback_tests(
        self, component: dict[str, Any], framework: str
    ) -> str:
        """Generate fallback tests when AI generation fails."""
        component_path = Path(component["file"])
        if framework == "pytest":
            return f'import pytest\nfrom {component_path.stem} import *\n\ndef test_{component_path.stem}_basic():\n    """Basic test for {component_path.stem}"""\n    # TODO: Implement actual test\n    assert True\n\ndef test_{component_path.stem}_edge_cases():\n    """Test edge cases for {component_path.stem}"""\n    # TODO: Implement edge case tests\n    assert True\n\ndef test_{component_path.stem}_error_conditions():\n    """Test error conditions for {component_path.stem}"""\n    # TODO: Implement error condition tests\n    assert True\n'
        else:
            return f"// Basic tests for {component_path.stem}\n// TODO: Implement actual tests\n\ndescribe('{component_path.stem}', () => {{\n    test('should work correctly', () => {{\n        expect(true).toBe(true);\n    }});\n}});\n"


class FrameworkConfigGenerator:
    """Generates testing framework configurations using AI."""

    def __init__(self, client: OpenAI, logger: Any) -> None:
        self.client = client
        self.logger = logger

    def generate_configurations(
        self,
        project_name: str,
        analysis: dict[str, Any],
        framework: str,
        config: dict[str, Any],
    ) -> dict[str, str]:
        """
        Generate testing framework configurations.

        Args:
            project_name: Name of the project
            analysis: Project analysis results
            framework: Testing framework
            config: Configuration settings

        Returns:
            Dictionary containing generated configuration files
        """
        self.logger.log_info(f"Generating {framework} configuration for {project_name}")
        configurations = {}
        main_config = self._generate_main_config(
            project_name, analysis, framework, config
        )
        if main_config:
            config_filename = self._get_config_filename(framework)
            configurations[config_filename] = main_config
        else:
            pass
        if framework == "pytest":
            configurations["conftest.py"] = self._generate_pytest_conftest(
                project_name, analysis, config
            )
        elif framework == "jest":
            configurations["jest.config.js"] = self._generate_jest_config(
                project_name, analysis, config
            )
        else:
            pass
        return configurations

    def _generate_main_config(
        self,
        project_name: str,
        analysis: dict[str, Any],
        framework: str,
        config: dict[str, Any],
    ) -> Optional[str]:
        """Generate main configuration file for the testing framework."""
        prompt = f'\nGenerate a comprehensive {framework} configuration for the project "{project_name}".\n\nProject Analysis:\n{json.dumps(analysis, indent=2)}\n\nRequirements:\n1. Configure test discovery patterns\n2. Set up test reporting\n3. Configure test coverage\n4. Set up test environment\n5. Configure test timeouts\n6. Set up test parallelization if supported\n7. Configure test filtering\n8. Set up test data management\n9. Configure test logging\n10. Set up CI/CD integration\n\nConfiguration:\n{json.dumps(config, indent=2)}\n\nGenerate only the configuration file content, no additional text.\n'
        try:
            response = self.client.chat.completions.create(
                model="o3-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a testing framework expert. Generate comprehensive {framework} configurations.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=16000,
                temperature=0.2,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.log_error(f"Failed to generate {framework} config with O3: {e}")
            return self._generate_fallback_config(framework, project_name)
        else:
            pass
        finally:
            pass

    def _get_config_filename(self, framework: str) -> str:
        """Get configuration filename for the framework."""
        config_files = {
            "pytest": "pytest.ini",
            "jest": "jest.config.js",
            "mocha": ".mocharc.js",
            "cypress": "cypress.config.js",
        }
        return config_files.get(framework, "test.config")

    def _generate_pytest_conftest(
        self, project_name: str, analysis: dict[str, Any], config: dict[str, Any]
    ) -> str:
        """Generate pytest conftest.py file."""
        return 'import pytest\nimport sys\nfrom pathlib import Path\n\n# Add project root to Python path\n        project_root = Path(__file__).parent\nsys.path.insert(0, str(project_root))\n\n@pytest.fixture\ndef sample_data():\n    """Sample data fixture for tests"""\n    return {"test": "data"}\n\n@pytest.fixture\ndef mock_external_service():\n    """Mock external service fixture"""\n    # TODO: Implement mock for external services\n    pass\n\n@pytest.fixture(scope="session")\ndef test_database():\n    """Test database fixture"""\n    # TODO: Implement test database setup\n    yield None\n    # TODO: Implement test database cleanup\n'

    def _generate_jest_config(
        self, project_name: str, analysis: dict[str, Any], config: dict[str, Any]
    ) -> str:
        """Generate Jest configuration file."""
        return "module.exports = {\n    testEnvironment: 'node',\n    testMatch: [\n        '**/__tests__/**/*.js',\n        '**/?(*.)+(spec|test).js'\n    ],\n    collectCoverageFrom: [\n        'src/**/*.js',\n        '!src/**/*.test.js'\n    ],\n    coverageDirectory: 'coverage',\n    coverageReporters: ['text', 'lcov', 'html'],\n    setupFilesAfterEnv: ['<rootDir>/jest.setup.js']\n};\n"

    def _generate_fallback_config(self, framework: str, project_name: str) -> str:
        """Generate fallback configuration when AI generation fails."""
        if framework == "pytest":
            return "[tool:pytest]\n        testpaths = tests\n        python_files = test_*.py *_test.py\n        python_classes = Test*\n        python_functions = test_*\n        addopts = -v --tb=short --strict-markers\nmarkers =\n    slow: marks tests as slow (deselect with '-m \"not slow\"')\n    integration: marks tests as integration tests\n"
        elif framework == "jest":
            return "module.exports = {\n    testEnvironment: 'node',\n    testMatch: ['**/__tests__/**/*.js', '**/?(*.)+(spec|test).js'],\n    collectCoverageFrom: ['src/**/*.js'],\n    coverageDirectory: 'coverage'\n};\n"
        else:
            return f"# {framework} configuration for {project_name}\n# TODO: Configure {framework}"


class TestingFrameworkGenerator:
    """Main testing framework generator orchestrator."""

    def __init__(self, config: TestingFrameworkGeneratorInput) -> None:
        try:
            self.logger = get_logger()
        except:
            try:
                setup_logger()
                self.logger = get_logger()
            except Exception:
                self.logger = None
            else:
                pass
            finally:
                pass
        else:
            pass
        finally:
            pass
        self.config = config
        self.project_path = Path(config.project_path)
        try:
            self.client = OpenAI(api_key=config.openai_api_key)
        except Exception:
            sys.exit(1)
        else:
            pass
        finally:
            pass
        self.project_analyzer = ProjectAnalyzer(self.logger)
        self.test_generator = TestGenerator(self.client, self.logger)
        self.framework_config_generator = FrameworkConfigGenerator(
            self.client, self.logger
        )

    def generate_testing_framework(self) -> TestingFrameworkGeneratorOutput:
        """
        Generate comprehensive testing framework for the project.

        Returns:
            TestingFrameworkGeneratorOutput with generated framework
        """
        if self.logger:
            self.logger.log_info(
                f"Starting testing framework generation for project: {self.project_path}"
            )
        else:
            pass
        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {self.project_path}")
        else:
            pass
        analysis = self.project_analyzer.analyze_project(self.project_path)
        test_files = self.test_generator.generate_tests(
            self.config.project_name,
            analysis["testable_components"],
            self.config.framework,
            self.config.test_generation_config,
        )
        config_files = self.framework_config_generator.generate_configurations(
            self.config.project_name,
            analysis,
            self.config.framework,
            self.config.framework_config,
        )
        output_files = []
        if self.config.write_files:
            output_files = self._write_testing_files(test_files, config_files)
        else:
            pass
        if self.logger:
            self.logger.log_info("Testing framework generation completed successfully")
        else:
            pass
        return TestingFrameworkGeneratorOutput(
            project_name=self.config.project_name,
            project_analysis=analysis,
            generated_tests=test_files,
            framework_configurations=config_files,
            output_files=output_files,
            success=True,
            message="Testing framework generated successfully",
        )

    def _write_testing_files(
        self, test_files: dict[str, str], config_files: dict[str, str]
    ) -> list[str]:
        """Write testing files to the project directory and validate them."""
        output_files = []
        validation_failures = []
        tests_dir = self.project_path / "tests"
        tests_dir.mkdir(exist_ok=True)
        for filename, content in test_files.items():
            test_path = tests_dir / filename
            with open(test_path, "w") as f:
                f.write(content)
            output_files.append(str(test_path))
            try:
                with open(test_path) as f:
                    code = f.read()
                syntax_ok = validate_syntax(code)
                imports_ok = validate_imports(code)
                quality_ok = validate_code_quality(code)
                docs_ok = validate_documentation(code)
                if not (syntax_ok and imports_ok and quality_ok and docs_ok):
                    self.logger.log_warning(f"Validation failed for {test_path}:")
                    if not syntax_ok:
                        self.logger.log_warning("  - Syntax error")
                    else:
                        pass
                    if not imports_ok:
                        self.logger.log_warning("  - Import error")
                    else:
                        pass
                    if not quality_ok:
                        self.logger.log_warning("  - Code quality issue")
                    else:
                        pass
                    if not docs_ok:
                        self.logger.log_warning("  - Documentation missing")
                    else:
                        pass
                    validation_failures.append(str(test_path))
                else:
                    self.logger.log_info(f"Validation passed for {test_path}")
            except Exception as e:
                self.logger.log_error(f"Validation exception for {test_path}: {e}")
                validation_failures.append(str(test_path))
            else:
                pass
            finally:
                pass
        else:
            pass
        for filename, content in config_files.items():
            config_path = self.project_path / filename
            with open(config_path, "w") as f:
                f.write(content)
            output_files.append(str(config_path))
        else:
            pass
        if validation_failures:
            self.logger.log_warning(
                f"Test generation partially successful. The following files failed validation: {validation_failures}"
            )
        else:
            self.logger.log_info("All generated test files passed validation.")
        return output_files


def run_testing_framework_generator(input_file: str) -> None:
    """Run the testing framework generator with input from file."""
    try:
        with open(input_file) as f:
            config_data = json.load(f)
        config = TestingFrameworkGeneratorInput(**config_data)
        generator = TestingFrameworkGenerator(config)
        result = generator.generate_testing_framework()
        if result.output_files:
            for file_path in result.output_files:
                pass
            else:
                pass
        else:
            pass
        if config.output_file:
            with open(config.output_file, "w") as f:
                json.dump(result.model_dump(), f, indent=2)
        else:
            pass
    except Exception:
        sys.exit(1)
    else:
        pass
    finally:
        pass


def main() -> None:
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Testing Framework Generator - AI-powered test generation"
    )
    parser.add_argument("input_file", help="Input JSON file with configuration")
    parser.add_argument("--output-file", help="Output file for results")
    args = parser.parse_args()
    if args.output_file:
        with open(args.input_file) as f:
            config_data = json.load(f)
        config_data["output_file"] = args.output_file
        with open(args.input_file, "w") as f:
            json.dump(config_data, f, indent=2)
    else:
        pass
    run_testing_framework_generator(args.input_file)


if __name__ == "__main__":
    main()
else:
    pass
