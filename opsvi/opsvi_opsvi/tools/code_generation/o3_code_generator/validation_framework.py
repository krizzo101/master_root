"""
Validation Framework for O3 Code Generator Tools

This script provides comprehensive validation for all aspects of the O3 code generator
system including configuration, schemas, prompts, and generated outputs.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml

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


class ValidationFramework:
    """Comprehensive validation framework for O3 code generator tools."""

    def __init__(self, config_path: str | None = None) -> None:
        """Initialize the validation framework.

        Args:
            config_path: Path to configuration file
        """
        self.config_manager = ConfigManager(config_path)
        log_config = self.config_manager.get_logging_config()
        self.logger = setup_logger(log_config)
        self.validation_results: dict[str, Any] = {
            "total_checks": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "errors": [],
            "warnings_list": [],
            "timestamp": "",
            "overall_success": False,
        }

    def run_full_validation(self) -> dict[str, Any]:
        """Run full validation of the O3 code generator system.

        Returns:
            Dictionary containing validation results
        """
        self.logger.log_info("Starting comprehensive validation")
        validation_checks = [
            self._validate_project_structure,
            self._validate_configuration,
            self._validate_schemas,
            self._validate_prompts,
            self._validate_dependencies,
            self._validate_security,
            self._validate_performance,
            self._validate_documentation,
        ]
        for check_func in validation_checks:
            try:
                check_func()
                self.validation_results["passed"] += 1
            except Exception as e:
                self.validation_results["failed"] += 1
                self.validation_results["errors"].append(f"{check_func.__name__}: {e}")
                self.logger.log_error(f"❌ Validation check failed: {e}")
            else:
                pass
            finally:
                pass
            self.validation_results["total_checks"] += 1
        else:
            pass
        self.validation_results["timestamp"] = self._get_current_timestamp()
        self.validation_results["overall_success"] = (
            self.validation_results["failed"] == 0
        )
        self.logger.log_info("Validation completed")
        return self.validation_results

    def _validate_project_structure(self) -> None:
        """Validate project structure and organization."""
        self.logger.log_info("Validating project structure")
        required_directories = [
            "config",
            "schemas",
            "prompts",
            "o3_logger",
            "generated_files",
            "docs",
        ]
        required_files = [
            "README.md",
            "requirements_o3_generator.txt",
            "Makefile",
            "config/config.yaml",
        ]
        for directory in required_directories:
            dir_path = Path(script_dir) / directory
            if not dir_path.exists():
                raise FileNotFoundError(f"Required directory not found: {directory}")
            else:
                pass
            if not dir_path.is_dir():
                raise NotADirectoryError(f"Path is not a directory: {directory}")
            else:
                pass
        else:
            pass
        for file_path in required_files:
            file_obj = Path(script_dir) / file_path
            if not file_obj.exists():
                raise FileNotFoundError(f"Required file not found: {file_path}")
            else:
                pass
            if not file_obj.is_file():
                raise FileNotFoundError(f"Path is not a file: {file_path}")
            else:
                pass
        else:
            pass

    def _validate_configuration(self) -> None:
        """Validate configuration files and settings."""
        self.logger.log_info("Validating configuration")
        config_file = Path(script_dir) / "config" / "config.yaml"
        if not config_file.exists():
            raise FileNotFoundError("config.yaml not found")
        else:
            pass
        try:
            with open(config_file, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            required_sections = [
                "api",
                "output",
                "logging",
                "security",
                "performance",
                "code_generation",
                "docker",
                "testing",
                "documentation",
            ]
            for section in required_sections:
                if section not in config_data:
                    raise ValueError(f"Missing configuration section: {section}")
                else:
                    pass
                if not isinstance(config_data[section], dict):
                    raise ValueError(
                        f"Configuration section {section} must be a dictionary"
                    )
                else:
                    pass
            else:
                pass
            api_config = config_data.get("api", {})
            if "model_name" not in api_config:
                raise ValueError("Missing model_name in API configuration")
            else:
                pass
            output_config = config_data.get("output", {})
            if "output_dir" not in output_config:
                raise ValueError("Missing output_dir in output configuration")
            else:
                pass
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config.yaml: {e}")
        else:
            pass
        finally:
            pass

    def _validate_schemas(self) -> None:
        """Validate schema files and structure."""
        self.logger.log_info("Validating schemas")
        schema_dir = Path(script_dir) / "schemas"
        if not schema_dir.exists():
            raise FileNotFoundError("Schemas directory not found")
        else:
            pass
        required_schemas = [
            "docker_schemas.py",
            "requirements_schemas.py",
            "security_schemas.py",
            "code_reviewer_input_schema.py",
            "code_reviewer_output_schema.py",
            "dependency_analyzer_input_schema.py",
            "dependency_analyzer_output_schema.py",
            "project_initializer_input_schema.py",
            "project_initializer_output_schema.py",
        ]
        for schema_file in required_schemas:
            schema_path = schema_dir / schema_file
            if not schema_path.exists():
                raise FileNotFoundError(f"Required schema not found: {schema_file}")
            else:
                pass
            self._validate_schema_file(schema_path)
        else:
            pass

    def _validate_schema_file(self, schema_path: Path) -> None:
        """Validate individual schema file.

        Args:
            schema_path: Path to the schema file
        """
        try:
            with open(schema_path, encoding="utf-8") as f:
                content = f.read()
            compile(content, str(schema_path), "exec")
            if "from pydantic import" not in content:
                self.validation_results["warnings"] += 1
                self.validation_results["warnings_list"].append(
                    f"Schema file {schema_path.name} may not use Pydantic"
                )
            else:
                pass
            if "BaseModel" not in content:
                self.validation_results["warnings"] += 1
                self.validation_results["warnings_list"].append(
                    f"Schema file {schema_path.name} may not define Pydantic models"
                )
            else:
                pass
        except SyntaxError as e:
            raise ValueError(f"Syntax error in schema file {schema_path.name}: {e}")
        else:
            pass
        finally:
            pass

    def _validate_prompts(self) -> None:
        """Validate prompt files and content."""
        self.logger.log_info("Validating prompts")
        prompts_dir = Path(script_dir) / "prompts"
        if not prompts_dir.exists():
            raise FileNotFoundError("Prompts directory not found")
        else:
            pass
        required_prompts = [
            "docker_prompts.py",
            "requirements_prompts.py",
            "security_prompts.py",
        ]
        for prompt_file in required_prompts:
            prompt_path = prompts_dir / prompt_file
            if not prompt_path.exists():
                raise FileNotFoundError(f"Required prompt not found: {prompt_file}")
            else:
                pass
            self._validate_prompt_file(prompt_path)
        else:
            pass

    def _validate_prompt_file(self, prompt_path: Path) -> None:
        """Validate individual prompt file.

        Args:
            prompt_path: Path to the prompt file
        """
        try:
            with open(prompt_path, encoding="utf-8") as f:
                content = f.read()
            compile(content, str(prompt_path), "exec")
            if "_SYSTEM_PROMPT" not in content:
                self.validation_results["warnings"] += 1
                self.validation_results["warnings_list"].append(
                    f"Prompt file {prompt_path.name} may not define system prompt"
                )
            else:
                pass
            if '"""' not in content and "'''" not in content:
                self.validation_results["warnings"] += 1
                self.validation_results["warnings_list"].append(
                    f"Prompt file {prompt_path.name} may not contain proper docstrings"
                )
            else:
                pass
        except SyntaxError as e:
            raise ValueError(f"Syntax error in prompt file {prompt_path.name}: {e}")
        else:
            pass
        finally:
            pass

    def _validate_dependencies(self) -> None:
        """Validate dependencies and requirements."""
        self.logger.log_info("Validating dependencies")
        requirements_file = Path(script_dir) / "requirements_o3_generator.txt"
        if not requirements_file.exists():
            raise FileNotFoundError("requirements_o3_generator.txt not found")
        else:
            pass
        try:
            with open(requirements_file, encoding="utf-8") as f:
                requirements = f.read()
            required_deps = [
                "openai",
                "pydantic",
                "pyyaml",
                "pytest",
                "ruff",
                "mypy",
                "bandit",
            ]
            for dep in required_deps:
                if dep not in requirements:
                    self.validation_results["warnings"] += 1
                    self.validation_results["warnings_list"].append(
                        f"Required dependency {dep} not found in requirements"
                    )
                else:
                    pass
            else:
                pass
            lines = requirements.splitlines()
            for line in lines:
                line = line.strip()
                if line and (not line.startswith("#")):
                    if "==" not in line and ">=" not in line and ("~=" not in line):
                        self.validation_results["warnings"] += 1
                        self.validation_results["warnings_list"].append(
                            f"Dependency {line} may not have version specification"
                        )
                    else:
                        pass
                else:
                    pass
            else:
                pass
        except Exception as e:
            raise ValueError(f"Error reading requirements file: {e}")
        else:
            pass
        finally:
            pass

    def _validate_security(self) -> None:
        """Validate security aspects of the codebase."""
        self.logger.log_info("Validating security")
        secret_patterns = [
            "password\\s*=\\s*[\"\\'][^\"\\']+[\"\\']",
            "api_key\\s*=\\s*[\"\\'][^\"\\']+[\"\\']",
            "secret\\s*=\\s*[\"\\'][^\"\\']+[\"\\']",
            "token\\s*=\\s*[\"\\'][^\"\\']+[\"\\']",
        ]
        python_files = list(Path(script_dir).rglob("*.py"))
        for py_file in python_files:
            if "test_" in py_file.name or "backup" in py_file.name:
                continue
            else:
                pass
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()
                for pattern in secret_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        self.validation_results["warnings"] += 1
                        self.validation_results["warnings_list"].append(
                            f"Potential hardcoded secret found in {py_file.name}"
                        )
                    else:
                        pass
                else:
                    pass
            except Exception as e:
                self.logger.log_warning(f"Could not read file {py_file}: {e}")
            else:
                pass
            finally:
                pass
        else:
            pass

    def _validate_performance(self) -> None:
        """Validate performance aspects of the codebase."""
        self.logger.log_info("Validating performance")
        performance_patterns = [
            "for\\s+.*\\s+in\\s+.*:\\s*\\n\\s*for\\s+.*\\s+in\\s+.*:",
            "\\.read\\(\\)",
            "\\.listdir\\(\\)",
        ]
        python_files = list(Path(script_dir).rglob("*.py"))
        for py_file in python_files:
            if "test_" in py_file.name or "backup" in py_file.name:
                continue
            else:
                pass
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()
                for pattern in performance_patterns:
                    matches = re.findall(pattern, content, re.MULTILINE)
                    if matches:
                        self.validation_results["warnings"] += 1
                        self.validation_results["warnings_list"].append(
                            f"Potential performance issue found in {py_file.name}"
                        )
                    else:
                        pass
                else:
                    pass
            except Exception as e:
                self.logger.log_warning(f"Could not read file {py_file}: {e}")
            else:
                pass
            finally:
                pass
        else:
            pass

    def _validate_documentation(self) -> None:
        """Validate documentation and docstrings."""
        self.logger.log_info("Validating documentation")
        readme_file = Path(script_dir) / "README.md"
        if not readme_file.exists():
            raise FileNotFoundError("README.md not found")
        else:
            pass
        try:
            with open(readme_file, encoding="utf-8") as f:
                readme_content = f.read()
            required_sections = [
                "# O3 Code Generator",
                "## Installation",
                "## Usage",
                "## Features",
            ]
            for section in required_sections:
                if section not in readme_content:
                    self.validation_results["warnings"] += 1
                    self.validation_results["warnings_list"].append(
                        f"README may be missing section: {section}"
                    )
                else:
                    pass
            else:
                pass
        except Exception as e:
            raise ValueError(f"Error reading README: {e}")
        else:
            pass
        finally:
            pass
        python_files = list(Path(script_dir).rglob("*.py"))
        for py_file in python_files:
            if "test_" in py_file.name or "backup" in py_file.name:
                continue
            else:
                pass
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()
                if not content.strip().startswith('"""') and (
                    not content.strip().startswith("'''")
                ):
                    self.validation_results["warnings"] += 1
                    self.validation_results["warnings_list"].append(
                        f"Python file {py_file.name} may be missing module docstring"
                    )
                else:
                    pass
            except Exception as e:
                self.logger.log_warning(f"Could not read file {py_file}: {e}")
            else:
                pass
            finally:
                pass
        else:
            pass

    def _get_current_timestamp(self) -> str:
        """Get current timestamp string.

        Returns:
            Current timestamp as string
        """
        import datetime

        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def save_validation_results(self, output_file: str) -> None:
        """Save validation results to a file.

        Args:
            output_file: Path to save the validation results
        """
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.validation_results, f, indent=2)
            self.logger.log_info(f"Validation results saved to: {output_file}")
        except Exception as e:
            self.logger.log_error(f"Error saving validation results: {e}")
        else:
            pass
        finally:
            pass

    def print_summary(self) -> None:
        """Print validation summary."""
        if self.validation_results["errors"]:
            for error in self.validation_results["errors"]:
                pass
            else:
                pass
        else:
            pass
        if self.validation_results["warnings_list"]:
            for warning in self.validation_results["warnings_list"]:
                pass
            else:
                pass
        else:
            pass


def main() -> None:
    """Main function to run the validation framework."""
    parser = argparse.ArgumentParser(
        description="O3 Code Generator Validation Framework"
    )
    parser.add_argument("--config", "-c", help="Path to configuration file")
    parser.add_argument("--output", "-o", help="Output file for validation results")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    try:
        validator = ValidationFramework(args.config)
        results = validator.run_full_validation()
        if args.output:
            validator.save_validation_results(args.output)
        else:
            pass
        validator.print_summary()
        if results["failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
    except Exception:
        sys.exit(1)
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass
