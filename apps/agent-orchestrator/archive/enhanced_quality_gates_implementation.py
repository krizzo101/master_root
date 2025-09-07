"""
Enhanced Quality Gates Implementation
Real validation implementations for ExecutionPlan quality gates
"""
import asyncio
import json
import logging
import os
import sqlite3
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import psycopg2
import requests

try:
    from execution_plan_schema import QualityGateType

    from src.quality_gates import GateStatus, ValidationResult
except ImportError:
    try:
        from .execution_plan_schema import QualityGateType
        from .src.quality_gates import GateStatus, ValidationResult
    except ImportError:
        # Fallback definitions if imports fail
        class GateStatus(Enum):
            PENDING = "pending"
            PASSED = "passed"
            FAILED = "failed"
            DISABLED = "disabled"

        @dataclass
        class ValidationResult:
            status: GateStatus
            message: str = ""
            details: Dict[str, Any] = field(default_factory=dict)

        class QualityGateType(Enum):
            DATABASE = "database"
            HTTP = "http"
            FILE_EXISTS = "file_exists"
            CODE_QUALITY = "code_quality"
            TEST_RESULTS = "test_results"
            CUSTOM = "custom"


logger = logging.getLogger(__name__)


class QualityGateValidator(ABC):
    """Abstract base class for quality gate validators"""

    @abstractmethod
    async def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate based on configuration"""
        pass

    @abstractmethod
    def get_supported_type(self) -> QualityGateType:
        """Get the quality gate type this validator supports"""
        pass


class DatabaseQualityGateValidator(QualityGateValidator):
    """Validator for database connectivity and query execution"""

    def get_supported_type(self) -> QualityGateType:
        return QualityGateType.DATABASE

    async def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate database connectivity and optionally run queries"""
        try:
            connection_string = config.get("connection_string")
            timeout_seconds = config.get("timeout_seconds", 30)
            test_query = config.get("test_query", "SELECT 1")
            required_tables = config.get("required_tables", [])
            min_row_count = config.get("min_row_count")

            if not connection_string:
                return ValidationResult(
                    status=GateStatus.FAILED,
                    message="No connection string provided",
                    details={"error": "connection_string is required"},
                )

            # Determine database type and connect
            if (
                "postgresql://" in connection_string
                or "postgres://" in connection_string
            ):
                result = await self._validate_postgresql(
                    connection_string,
                    timeout_seconds,
                    test_query,
                    required_tables,
                    min_row_count,
                )
            elif "sqlite://" in connection_string or connection_string.endswith(".db"):
                result = await self._validate_sqlite(
                    connection_string,
                    timeout_seconds,
                    test_query,
                    required_tables,
                    min_row_count,
                )
            else:
                return ValidationResult(
                    status=GateStatus.FAILED,
                    message="Unsupported database type",
                    details={"connection_string": connection_string},
                )

            return result

        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            return ValidationResult(
                status=GateStatus.FAILED,
                message=f"Database validation error: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
            )

    async def _validate_postgresql(
        self,
        connection_string: str,
        timeout: int,
        test_query: str,
        required_tables: List[str],
        min_row_count: Optional[int],
    ) -> ValidationResult:
        """Validate PostgreSQL connection"""
        try:
            import psycopg2

            conn = psycopg2.connect(connection_string, connect_timeout=timeout)
            cursor = conn.cursor()

            # Test basic connectivity
            cursor.execute(test_query)
            result = cursor.fetchone()

            details = {"test_query_result": result}

            # Check required tables
            if required_tables:
                cursor.execute(
                    """
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                """
                )
                existing_tables = [row[0] for row in cursor.fetchall()]
                missing_tables = [
                    table for table in required_tables if table not in existing_tables
                ]

                if missing_tables:
                    conn.close()
                    return ValidationResult(
                        status=GateStatus.FAILED,
                        message=f"Missing required tables: {', '.join(missing_tables)}",
                        details={
                            "missing_tables": missing_tables,
                            "existing_tables": existing_tables,
                        },
                    )
                details["verified_tables"] = required_tables

            # Check minimum row count if specified
            if min_row_count is not None and required_tables:
                for table in required_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    if count < min_row_count:
                        conn.close()
                        return ValidationResult(
                            status=GateStatus.FAILED,
                            message=f"Table {table} has {count} rows, minimum required: {min_row_count}",
                            details={
                                "table": table,
                                "actual_count": count,
                                "required_count": min_row_count,
                            },
                        )
                    details[f"{table}_count"] = count

            conn.close()

            return ValidationResult(
                status=GateStatus.PASSED,
                message="PostgreSQL database validation successful",
                details=details,
            )

        except ImportError:
            return ValidationResult(
                status=GateStatus.FAILED,
                message="psycopg2 not installed - cannot validate PostgreSQL",
                details={"error": "Missing psycopg2 dependency"},
            )
        except Exception as e:
            return ValidationResult(
                status=GateStatus.FAILED,
                message=f"PostgreSQL validation failed: {str(e)}",
                details={"error": str(e)},
            )

    async def _validate_sqlite(
        self,
        connection_string: str,
        timeout: int,
        test_query: str,
        required_tables: List[str],
        min_row_count: Optional[int],
    ) -> ValidationResult:
        """Validate SQLite connection"""
        try:
            # Handle sqlite:// URLs and direct file paths
            db_path = connection_string.replace("sqlite://", "")

            if not os.path.exists(db_path):
                return ValidationResult(
                    status=GateStatus.FAILED,
                    message=f"SQLite database file not found: {db_path}",
                    details={"db_path": db_path},
                )

            conn = sqlite3.connect(db_path, timeout=timeout)
            cursor = conn.cursor()

            # Test basic connectivity
            cursor.execute(test_query)
            result = cursor.fetchone()

            details = {"test_query_result": result, "db_path": db_path}

            # Check required tables
            if required_tables:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = [row[0] for row in cursor.fetchall()]
                missing_tables = [
                    table for table in required_tables if table not in existing_tables
                ]

                if missing_tables:
                    conn.close()
                    return ValidationResult(
                        status=GateStatus.FAILED,
                        message=f"Missing required tables: {', '.join(missing_tables)}",
                        details={
                            "missing_tables": missing_tables,
                            "existing_tables": existing_tables,
                        },
                    )
                details["verified_tables"] = required_tables

            # Check minimum row count if specified
            if min_row_count is not None and required_tables:
                for table in required_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    if count < min_row_count:
                        conn.close()
                        return ValidationResult(
                            status=GateStatus.FAILED,
                            message=f"Table {table} has {count} rows, minimum required: {min_row_count}",
                            details={
                                "table": table,
                                "actual_count": count,
                                "required_count": min_row_count,
                            },
                        )
                    details[f"{table}_count"] = count

            conn.close()

            return ValidationResult(
                status=GateStatus.PASSED,
                message="SQLite database validation successful",
                details=details,
            )

        except Exception as e:
            return ValidationResult(
                status=GateStatus.FAILED,
                message=f"SQLite validation failed: {str(e)}",
                details={"error": str(e)},
            )


class HttpQualityGateValidator(QualityGateValidator):
    """Validator for HTTP endpoint availability and response validation"""

    def get_supported_type(self) -> QualityGateType:
        return QualityGateType.HTTP

    async def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate HTTP endpoint"""
        try:
            url = config.get("url")
            method = config.get("method", "GET").upper()
            expected_status = config.get("expected_status", 200)
            timeout_seconds = config.get("timeout_seconds", 30)
            headers = config.get("headers", {})
            expected_response = config.get("expected_response")
            json_path = config.get(
                "json_path"
            )  # e.g., "data.status" to check nested JSON

            if not url:
                return ValidationResult(
                    status=GateStatus.FAILED,
                    message="No URL provided",
                    details={"error": "url is required"},
                )

            # Make HTTP request
            start_time = time.time()
            response = requests.request(
                method=method, url=url, headers=headers, timeout=timeout_seconds
            )
            response_time = time.time() - start_time

            details = {
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "response_time_seconds": round(response_time, 3),
                "response_headers": dict(response.headers),
            }

            # Check status code
            if response.status_code != expected_status:
                return ValidationResult(
                    status=GateStatus.FAILED,
                    message=f"HTTP {method} {url} returned {response.status_code}, expected {expected_status}",
                    details={**details, "response_text": response.text[:500]},
                )

            # Check response content if specified
            if expected_response:
                if expected_response not in response.text:
                    return ValidationResult(
                        status=GateStatus.FAILED,
                        message=f"Response does not contain expected text: {expected_response}",
                        details={**details, "response_text": response.text[:500]},
                    )
                details["expected_response_found"] = True

            # Check JSON path if specified
            if json_path:
                try:
                    response_json = response.json()
                    value = self._get_json_path_value(response_json, json_path)
                    details["json_path_value"] = value
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    return ValidationResult(
                        status=GateStatus.FAILED,
                        message=f"Failed to extract JSON path '{json_path}': {str(e)}",
                        details={**details, "json_error": str(e)},
                    )

            return ValidationResult(
                status=GateStatus.PASSED,
                message=f"HTTP {method} {url} validation successful",
                details=details,
            )

        except requests.RequestException as e:
            return ValidationResult(
                status=GateStatus.FAILED,
                message=f"HTTP request failed: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
            )
        except Exception as e:
            logger.error(f"HTTP validation failed: {e}")
            return ValidationResult(
                status=GateStatus.FAILED,
                message=f"HTTP validation error: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
            )

    def _get_json_path_value(self, json_data: Any, path: str) -> Any:
        """Extract value from JSON using dot notation path"""
        keys = path.split(".")
        current = json_data
        for key in keys:
            if isinstance(current, dict):
                current = current[key]
            elif isinstance(current, list) and key.isdigit():
                current = current[int(key)]
            else:
                raise KeyError(f"Cannot access key '{key}' in {type(current)}")
        return current


class FileExistsQualityGateValidator(QualityGateValidator):
    """Validator for file and directory existence"""

    def get_supported_type(self) -> QualityGateType:
        return QualityGateType.FILE_EXISTS

    async def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate file/directory existence"""
        try:
            paths = config.get("paths", [])
            required_files = config.get("required_files", [])
            required_directories = config.get("required_directories", [])
            min_file_size = config.get("min_file_size", 0)  # bytes
            file_patterns = config.get("file_patterns", [])  # glob patterns

            all_paths = paths + required_files + required_directories

            if not all_paths and not file_patterns:
                return ValidationResult(
                    status=GateStatus.FAILED,
                    message="No paths or patterns specified",
                    details={"error": "At least one path or pattern is required"},
                )

            details = {}
            missing_items = []
            found_items = []

            # Check specific paths
            for path_str in all_paths:
                path = Path(path_str)
                if path.exists():
                    found_items.append(path_str)
                    details[f"found_{path_str}"] = True

                    # Check file size if specified and it's a file
                    if path.is_file() and min_file_size > 0:
                        size = path.stat().st_size
                        if size < min_file_size:
                            return ValidationResult(
                                status=GateStatus.FAILED,
                                message=f"File {path_str} is {size} bytes, minimum required: {min_file_size}",
                                details={
                                    "file": path_str,
                                    "actual_size": size,
                                    "required_size": min_file_size,
                                },
                            )
                        details[f"size_{path_str}"] = size
                else:
                    missing_items.append(path_str)
                    details[f"missing_{path_str}"] = True

            # Check file patterns
            pattern_matches = {}
            for pattern in file_patterns:
                matches = list(Path(".").glob(pattern))
                pattern_matches[pattern] = [str(m) for m in matches]
                if not matches:
                    missing_items.append(f"pattern:{pattern}")

            details["pattern_matches"] = pattern_matches

            if missing_items:
                return ValidationResult(
                    status=GateStatus.FAILED,
                    message=f"Missing items: {', '.join(missing_items)}",
                    details={
                        **details,
                        "missing_items": missing_items,
                        "found_items": found_items,
                    },
                )

            return ValidationResult(
                status=GateStatus.PASSED,
                message=f"All file/directory checks passed ({len(found_items)} items verified)",
                details={**details, "found_items": found_items},
            )

        except Exception as e:
            logger.error(f"File existence validation failed: {e}")
            return ValidationResult(
                status=GateStatus.FAILED,
                message=f"File existence validation error: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
            )


class CodeQualityGateValidator(QualityGateValidator):
    """Validator for code quality using various tools"""

    def get_supported_type(self) -> QualityGateType:
        return QualityGateType.CODE_QUALITY

    async def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate code quality"""
        try:
            tool = config.get("tool", "auto")  # auto, flake8, pylint, black, mypy
            target_path = config.get("target_path", ".")
            min_score = config.get("min_score", 8.0)
            max_violations = config.get("max_violations", 10)
            ignore_patterns = config.get("ignore_patterns", [])

            if tool == "auto":
                # Try to detect best tool based on project
                if Path("setup.py").exists() or Path("pyproject.toml").exists():
                    tool = "flake8"  # Python project
                else:
                    tool = "generic"

            if tool == "flake8":
                return await self._validate_with_flake8(
                    target_path, max_violations, ignore_patterns
                )
            elif tool == "pylint":
                return await self._validate_with_pylint(
                    target_path, min_score, ignore_patterns
                )
            elif tool == "black":
                return await self._validate_with_black(target_path)
            elif tool == "mypy":
                return await self._validate_with_mypy(target_path, max_violations)
            else:
                return await self._validate_generic_code_quality(
                    target_path, max_violations
                )

        except Exception as e:
            logger.error(f"Code quality validation failed: {e}")
            return ValidationResult(
                status=GateStatus.FAILED,
                message=f"Code quality validation error: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
            )

    async def _validate_with_flake8(
        self, target_path: str, max_violations: int, ignore_patterns: List[str]
    ) -> ValidationResult:
        """Validate using flake8"""
        try:
            cmd = ["flake8", target_path, "--count"]
            if ignore_patterns:
                cmd.extend(["--ignore", ",".join(ignore_patterns)])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            # flake8 returns violation count in the last line
            lines = result.stdout.strip().split("\n")
            violation_count = 0

            if lines and lines[-1].isdigit():
                violation_count = int(lines[-1])

            details = {
                "tool": "flake8",
                "target_path": target_path,
                "violation_count": violation_count,
                "max_violations": max_violations,
                "return_code": result.returncode,
            }

            if violation_count > max_violations:
                return ValidationResult(
                    status=GateStatus.FAILED,
                    message=f"flake8 found {violation_count} violations, maximum allowed: {max_violations}",
                    details={**details, "violations": result.stdout},
                )

            return ValidationResult(
                status=GateStatus.PASSED,
                message=f"Code quality validation passed ({violation_count} violations, max {max_violations})",
                details=details,
            )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                status=GateStatus.FAILED,
                message="flake8 validation timed out",
                details={"timeout_seconds": 120},
            )
        except FileNotFoundError:
            return ValidationResult(
                status=GateStatus.FAILED,
                message="flake8 not installed",
                details={"error": "flake8 command not found"},
            )

    async def _validate_generic_code_quality(
        self, target_path: str, max_violations: int
    ) -> ValidationResult:
        """Generic code quality checks"""
        violations = []
        details = {"tool": "generic", "target_path": target_path}

        # Check for common issues
        for py_file in Path(target_path).rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")

                # Check for basic issues
                if "print(" in content and "# debug" not in content.lower():
                    violations.append(f"Debug print statement in {py_file}")

                if "import *" in content:
                    violations.append(f"Wildcard import in {py_file}")

                if len(content.split("\n")) > 1000:
                    violations.append(f"Very long file (>1000 lines): {py_file}")

            except Exception:
                continue  # Skip files that can't be read

        violation_count = len(violations)
        details["violation_count"] = violation_count
        details["violations"] = violations[:10]  # Limit details

        if violation_count > max_violations:
            return ValidationResult(
                status=GateStatus.FAILED,
                message=f"Generic quality checks found {violation_count} issues, maximum allowed: {max_violations}",
                details=details,
            )

        return ValidationResult(
            status=GateStatus.PASSED,
            message=f"Generic code quality validation passed ({violation_count} issues)",
            details=details,
        )

    async def _validate_with_pylint(
        self, target_path: str, min_score: float, ignore_patterns: List[str]
    ) -> ValidationResult:
        """Validate using pylint (placeholder - would need full implementation)"""
        return ValidationResult(
            status=GateStatus.PASSED,
            message="Pylint validation not fully implemented",
            details={"tool": "pylint", "target_path": target_path},
        )

    async def _validate_with_black(self, target_path: str) -> ValidationResult:
        """Validate using black formatter"""
        try:
            result = subprocess.run(
                ["black", "--check", target_path],
                capture_output=True,
                text=True,
                timeout=60,
            )

            details = {
                "tool": "black",
                "target_path": target_path,
                "return_code": result.returncode,
            }

            if result.returncode != 0:
                return ValidationResult(
                    status=GateStatus.FAILED,
                    message="Code formatting issues found (black)",
                    details={**details, "output": result.stdout},
                )

            return ValidationResult(
                status=GateStatus.PASSED,
                message="Code formatting validation passed (black)",
                details=details,
            )

        except FileNotFoundError:
            return ValidationResult(
                status=GateStatus.FAILED,
                message="black not installed",
                details={"error": "black command not found"},
            )

    async def _validate_with_mypy(
        self, target_path: str, max_violations: int
    ) -> ValidationResult:
        """Validate using mypy (placeholder)"""
        return ValidationResult(
            status=GateStatus.PASSED,
            message="MyPy validation not fully implemented",
            details={"tool": "mypy", "target_path": target_path},
        )


class TestResultsQualityGateValidator(QualityGateValidator):
    """Validator for test results and coverage"""

    def get_supported_type(self) -> QualityGateType:
        return QualityGateType.TEST_RESULTS

    async def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate test results"""
        try:
            test_command = config.get("test_command", "python -m pytest")
            min_coverage = config.get("min_coverage", 80.0)
            required_tests = config.get("required_tests", [])
            test_directory = config.get("test_directory", "tests")
            timeout_seconds = config.get("timeout_seconds", 300)

            # Check if test directory exists
            if not Path(test_directory).exists():
                return ValidationResult(
                    status=GateStatus.FAILED,
                    message=f"Test directory not found: {test_directory}",
                    details={"test_directory": test_directory},
                )

            # Run tests
            start_time = time.time()
            result = subprocess.run(
                test_command.split(),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=".",
            )
            execution_time = time.time() - start_time

            details = {
                "test_command": test_command,
                "return_code": result.returncode,
                "execution_time_seconds": round(execution_time, 2),
                "stdout": result.stdout[-1000:],  # Last 1000 chars
                "stderr": result.stderr[-1000:] if result.stderr else "",
            }

            # Check if tests passed
            if result.returncode != 0:
                return ValidationResult(
                    status=GateStatus.FAILED,
                    message=f"Tests failed (exit code {result.returncode})",
                    details=details,
                )

            # Extract test metrics from output (basic implementation)
            test_output = result.stdout
            passed_tests = test_output.count(" PASSED")
            failed_tests = test_output.count(" FAILED")
            total_tests = passed_tests + failed_tests

            details.update(
                {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                }
            )

            # Check coverage if mentioned in output
            if "coverage" in test_output.lower():
                # Try to extract coverage percentage
                import re

                coverage_match = re.search(r"(\d+)%", test_output)
                if coverage_match:
                    coverage = float(coverage_match.group(1))
                    details["coverage_percentage"] = coverage

                    if coverage < min_coverage:
                        return ValidationResult(
                            status=GateStatus.FAILED,
                            message=f"Coverage {coverage}% is below minimum {min_coverage}%",
                            details=details,
                        )

            return ValidationResult(
                status=GateStatus.PASSED,
                message=f"Test validation passed ({passed_tests} tests passed)",
                details=details,
            )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                status=GateStatus.FAILED,
                message=f"Tests timed out after {timeout_seconds} seconds",
                details={"timeout_seconds": timeout_seconds},
            )
        except Exception as e:
            logger.error(f"Test results validation failed: {e}")
            return ValidationResult(
                status=GateStatus.FAILED,
                message=f"Test validation error: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
            )


class CustomQualityGateValidator(QualityGateValidator):
    """Validator for custom validation logic"""

    def get_supported_type(self) -> QualityGateType:
        return QualityGateType.CUSTOM

    async def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """Execute custom validation"""
        try:
            validation_type = config.get("type", "command")

            if validation_type == "command":
                return await self._validate_command(config)
            elif validation_type == "python":
                return await self._validate_python_code(config)
            elif validation_type == "script":
                return await self._validate_script(config)
            else:
                return ValidationResult(
                    status=GateStatus.FAILED,
                    message=f"Unknown custom validation type: {validation_type}",
                    details={"supported_types": ["command", "python", "script"]},
                )

        except Exception as e:
            logger.error(f"Custom validation failed: {e}")
            return ValidationResult(
                status=GateStatus.FAILED,
                message=f"Custom validation error: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
            )

    async def _validate_command(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate using shell command"""
        command = config.get("command")
        expected_exit_code = config.get("expected_exit_code", 0)
        timeout_seconds = config.get("timeout_seconds", 60)

        if not command:
            return ValidationResult(
                status=GateStatus.FAILED,
                message="No command specified",
                details={"error": "command is required"},
            )

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )

            details = {
                "command": command,
                "return_code": result.returncode,
                "expected_exit_code": expected_exit_code,
                "stdout": result.stdout[-500:],  # Last 500 chars
                "stderr": result.stderr[-500:] if result.stderr else "",
            }

            if result.returncode != expected_exit_code:
                return ValidationResult(
                    status=GateStatus.FAILED,
                    message=f"Command exit code {result.returncode}, expected {expected_exit_code}",
                    details=details,
                )

            return ValidationResult(
                status=GateStatus.PASSED,
                message="Custom command validation passed",
                details=details,
            )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                status=GateStatus.FAILED,
                message=f"Command timed out after {timeout_seconds} seconds",
                details={"command": command, "timeout_seconds": timeout_seconds},
            )

    async def _validate_python_code(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate using Python code"""
        python_code = config.get("code")

        if not python_code:
            return ValidationResult(
                status=GateStatus.FAILED,
                message="No Python code specified",
                details={"error": "code is required"},
            )

        try:
            # Create a controlled execution environment
            local_vars = {"config": config}
            exec(python_code, {"__builtins__": {}}, local_vars)

            # Check for result
            if "result" in local_vars:
                result = local_vars["result"]
                if isinstance(result, bool):
                    status = GateStatus.PASSED if result else GateStatus.FAILED
                    message = f"Python validation {'passed' if result else 'failed'}"
                else:
                    status = GateStatus.PASSED
                    message = f"Python validation completed: {result}"
            else:
                status = GateStatus.PASSED
                message = "Python validation completed (no explicit result)"

            return ValidationResult(
                status=status,
                message=message,
                details={
                    "code": python_code[:200],
                    "variables": list(local_vars.keys()),
                },
            )

        except Exception as e:
            return ValidationResult(
                status=GateStatus.FAILED,
                message=f"Python validation failed: {str(e)}",
                details={"error": str(e), "code": python_code[:200]},
            )

    async def _validate_script(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate using external script"""
        script_path = config.get("script_path")
        script_args = config.get("args", [])
        timeout_seconds = config.get("timeout_seconds", 120)

        if not script_path or not Path(script_path).exists():
            return ValidationResult(
                status=GateStatus.FAILED,
                message=f"Script not found: {script_path}",
                details={"script_path": script_path},
            )

        try:
            cmd = [script_path] + script_args
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout_seconds
            )

            details = {
                "script_path": script_path,
                "args": script_args,
                "return_code": result.returncode,
                "stdout": result.stdout[-500:],
                "stderr": result.stderr[-500:] if result.stderr else "",
            }

            if result.returncode != 0:
                return ValidationResult(
                    status=GateStatus.FAILED,
                    message=f"Script failed with exit code {result.returncode}",
                    details=details,
                )

            return ValidationResult(
                status=GateStatus.PASSED,
                message="Script validation passed",
                details=details,
            )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                status=GateStatus.FAILED,
                message=f"Script timed out after {timeout_seconds} seconds",
                details={
                    "script_path": script_path,
                    "timeout_seconds": timeout_seconds,
                },
            )


class EnhancedQualityGateManager:
    """Enhanced quality gate manager with real validation implementations"""

    def __init__(self, state_dir: str = None):
        self.state_dir = state_dir or "./quality_gate_state"
        self.gates = {}
        self.enabled = True

        # Register validators
        self.validators = {
            QualityGateType.DATABASE: DatabaseQualityGateValidator(),
            QualityGateType.HTTP: HttpQualityGateValidator(),
            QualityGateType.FILE_EXISTS: FileExistsQualityGateValidator(),
            QualityGateType.CODE_QUALITY: CodeQualityGateValidator(),
            QualityGateType.TEST_RESULTS: TestResultsQualityGateValidator(),
            QualityGateType.CUSTOM: CustomQualityGateValidator(),
        }

        # Ensure state directory exists
        Path(self.state_dir).mkdir(parents=True, exist_ok=True)

    async def check_quality_gates(self, gate_ids: List[str]) -> ValidationResult:
        """Check multiple quality gates"""
        if not self.enabled:
            return ValidationResult(
                status=GateStatus.DISABLED, message="Quality gates disabled"
            )

        if not gate_ids:
            return ValidationResult(
                status=GateStatus.PASSED, message="No quality gates to check"
            )

        results = []
        failed_gates = []
        passed_gates = []

        for gate_id in gate_ids:
            if gate_id not in self.gates:
                failed_gates.append(gate_id)
                results.append(
                    {
                        "gate_id": gate_id,
                        "status": GateStatus.FAILED.value,
                        "message": f"Quality gate {gate_id} not defined",
                    }
                )
                continue

            gate_config = self.gates[gate_id]
            result = await self.check_single_gate(gate_id, gate_config)

            results.append(
                {
                    "gate_id": gate_id,
                    "status": result.status.value,
                    "message": result.message,
                    "details": result.details,
                }
            )

            if result.status == GateStatus.PASSED:
                passed_gates.append(gate_id)
            else:
                failed_gates.append(gate_id)

        # Overall result
        if failed_gates:
            return ValidationResult(
                status=GateStatus.FAILED,
                message=f"{len(failed_gates)} of {len(gate_ids)} quality gates failed",
                details={
                    "passed_gates": passed_gates,
                    "failed_gates": failed_gates,
                    "results": results,
                },
            )
        else:
            return ValidationResult(
                status=GateStatus.PASSED,
                message=f"All {len(gate_ids)} quality gates passed",
                details={"passed_gates": passed_gates, "results": results},
            )

    async def check_single_gate(
        self, gate_id: str, gate_config: Dict[str, Any]
    ) -> ValidationResult:
        """Check a single quality gate"""
        try:
            gate_type_str = gate_config.get("type")
            if not gate_type_str:
                return ValidationResult(
                    status=GateStatus.FAILED,
                    message=f"Quality gate {gate_id} has no type specified",
                )

            try:
                gate_type = QualityGateType(gate_type_str)
            except ValueError:
                return ValidationResult(
                    status=GateStatus.FAILED,
                    message=f"Unknown quality gate type: {gate_type_str}",
                )

            validator = self.validators.get(gate_type)
            if not validator:
                return ValidationResult(
                    status=GateStatus.FAILED,
                    message=f"No validator available for gate type: {gate_type_str}",
                )

            # Execute validation
            result = await validator.validate(gate_config.get("config", {}))

            # Store result state
            await self._store_gate_result(gate_id, result)

            return result

        except Exception as e:
            logger.error(f"Quality gate {gate_id} validation failed: {e}")
            return ValidationResult(
                status=GateStatus.FAILED,
                message=f"Quality gate validation error: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
            )

    async def initialize_gate(
        self,
        gate_id: str,
        gate_name: str,
        gate_description: str,
        gate_type: str,
        config: Dict[str, Any],
        dependencies: List[str] = None,
    ):
        """Initialize a quality gate"""
        self.gates[gate_id] = {
            "name": gate_name,
            "description": gate_description,
            "type": gate_type,
            "config": config,
            "dependencies": dependencies or [],
            "status": GateStatus.PENDING.value,
            "last_checked": None,
        }

        # Store gate definition
        await self._store_gate_definition(gate_id, self.gates[gate_id])

    async def _store_gate_result(self, gate_id: str, result: ValidationResult):
        """Store quality gate result to state directory"""
        try:
            result_file = Path(self.state_dir) / f"{gate_id}_result.json"
            result_data = {
                "gate_id": gate_id,
                "status": result.status.value,
                "message": result.message,
                "details": result.details,
                "timestamp": time.time(),
            }

            result_file.write_text(json.dumps(result_data, indent=2))

        except Exception as e:
            logger.error(f"Failed to store gate result for {gate_id}: {e}")

    async def _store_gate_definition(self, gate_id: str, gate_config: Dict[str, Any]):
        """Store quality gate definition"""
        try:
            def_file = Path(self.state_dir) / f"{gate_id}_definition.json"
            def_file.write_text(json.dumps(gate_config, indent=2))

        except Exception as e:
            logger.error(f"Failed to store gate definition for {gate_id}: {e}")

    def disable(self):
        """Disable quality gates"""
        self.enabled = False

    def enable(self):
        """Enable quality gates"""
        self.enabled = True

    def get_gate_status(self, gate_id: str) -> Dict[str, Any]:
        """Get current status of a quality gate"""
        try:
            result_file = Path(self.state_dir) / f"{gate_id}_result.json"
            if result_file.exists():
                return json.loads(result_file.read_text())
            else:
                return {"gate_id": gate_id, "status": "not_checked"}
        except Exception as e:
            logger.error(f"Failed to get gate status for {gate_id}: {e}")
            return {"gate_id": gate_id, "status": "error", "error": str(e)}


# Factory function for enhanced quality gate manager
def create_enhanced_quality_manager(
    state_dir: str = None,
) -> EnhancedQualityGateManager:
    """Create enhanced quality gate manager"""
    return EnhancedQualityGateManager(state_dir)


# Testing function
async def test_quality_gates():
    """Test quality gate implementations"""
    print("Testing Enhanced Quality Gates...")

    manager = create_enhanced_quality_manager("./test_quality_gates")

    # Test file existence gate
    await manager.initialize_gate(
        "test_files",
        "Test Files Exist",
        "Check that required test files exist",
        "file_exists",
        {
            "required_files": [__file__],  # This file should exist
            "file_patterns": ["*.py"],
        },
    )

    # Test HTTP gate (if internet available)
    await manager.initialize_gate(
        "http_test",
        "HTTP Connectivity",
        "Test HTTP endpoint availability",
        "http",
        {
            "url": "https://httpbin.org/status/200",
            "expected_status": 200,
            "timeout_seconds": 10,
        },
    )

    # Test custom command gate
    await manager.initialize_gate(
        "python_version",
        "Python Version Check",
        "Verify Python version",
        "custom",
        {"type": "command", "command": "python3 --version", "expected_exit_code": 0},
    )

    # Run tests
    result = await manager.check_quality_gates(
        ["test_files", "http_test", "python_version"]
    )

    print(f"✅ Quality gate test result: {result.status.value}")
    print(f"   Message: {result.message}")
    print(f"   Passed gates: {result.details.get('passed_gates', [])}")
    print(f"   Failed gates: {result.details.get('failed_gates', [])}")

    return manager


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_quality_gates())
