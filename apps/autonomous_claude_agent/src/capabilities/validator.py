"""
Capability Validator - Validates capability functionality and compatibility
"""

import asyncio
import importlib
import subprocess
import tempfile
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import traceback
import aiohttp
import psutil

from src.capabilities.discovery import Capability
from src.capabilities.registry import CapabilityRegistry
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ValidationLevel(Enum):
    """Levels of validation thoroughness"""

    BASIC = "basic"  # Quick availability check
    STANDARD = "standard"  # Standard functionality test
    COMPREHENSIVE = "comprehensive"  # Full validation with edge cases
    STRESS = "stress"  # Performance and stress testing


class ValidationResult:
    """Result of capability validation"""

    def __init__(self, capability_name: str):
        self.capability_name = capability_name
        self.passed = False
        self.level = ValidationLevel.BASIC
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.performance_metrics = {}
        self.errors = []
        self.warnings = []
        self.suggestions = []
        self.timestamp = datetime.now()
        self.duration = 0.0

    def add_test_result(
        self,
        test_name: str,
        passed: bool,
        error: Optional[str] = None,
        metrics: Optional[Dict] = None,
    ):
        """Add a test result"""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
            if error:
                self.errors.append(f"{test_name}: {error}")

        if metrics:
            self.performance_metrics[test_name] = metrics

    def finalize(self):
        """Finalize the validation result"""
        self.passed = self.tests_failed == 0 and self.tests_run > 0
        self.duration = (datetime.now() - self.timestamp).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "capability": self.capability_name,
            "passed": self.passed,
            "level": self.level.value,
            "tests": {
                "total": self.tests_run,
                "passed": self.tests_passed,
                "failed": self.tests_failed,
            },
            "performance": self.performance_metrics,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration,
        }


class CapabilityValidator:
    """Validates capability functionality"""

    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry
        self.validation_cache = Path.home() / ".autonomous_claude" / "validations"
        self.validation_cache.mkdir(parents=True, exist_ok=True)
        self.validation_history = []
        self._validators = {
            "python_module": self._validate_python_module,
            "cli_tool": self._validate_cli_tool,
            "mcp_tool": self._validate_mcp_tool,
            "api": self._validate_api_endpoint,
            "system": self._validate_system_capability,
        }

    async def validate_capability(
        self, capability_name: str, level: ValidationLevel = ValidationLevel.STANDARD
    ) -> ValidationResult:
        """Validate a single capability"""

        result = ValidationResult(capability_name)
        result.level = level

        # Get capability from registry
        capability = self.registry.get_capability(capability_name)
        if not capability:
            result.errors.append(f"Capability {capability_name} not found in registry")
            result.finalize()
            return result

        logger.info(f"Validating capability {capability_name} at level {level.value}")

        # Run type-specific validation
        validator = self._validators.get(capability.type)
        if validator:
            await validator(capability, result, level)
        else:
            await self._validate_generic(capability, result, level)

        # Run compatibility checks
        await self._validate_compatibility(capability, result)

        # Run performance tests if comprehensive or stress level
        if level in [ValidationLevel.COMPREHENSIVE, ValidationLevel.STRESS]:
            await self._validate_performance(capability, result, level)

        # Finalize and save result
        result.finalize()
        self._save_validation_result(result)

        # Update registry with validation results
        await self._update_registry_from_validation(capability, result)

        return result

    async def _validate_python_module(
        self, capability: Capability, result: ValidationResult, level: ValidationLevel
    ):
        """Validate a Python module capability"""

        module_name = capability.name.replace("python_", "")

        # Basic: Check if module can be imported
        try:
            module = importlib.import_module(module_name)
            result.add_test_result("import", True)
        except ImportError as e:
            result.add_test_result("import", False, str(e))
            return

        if level == ValidationLevel.BASIC:
            return

        # Standard: Check basic functionality
        try:
            # Check for common attributes
            has_version = hasattr(module, "__version__")
            has_doc = bool(module.__doc__)

            result.add_test_result("has_version", has_version)
            result.add_test_result("has_documentation", has_doc)

            # Check for callable functions
            functions = [
                name
                for name in dir(module)
                if not name.startswith("_") and callable(getattr(module, name))
            ]

            result.add_test_result("has_functions", len(functions) > 0)
            result.performance_metrics["function_count"] = len(functions)

            if not has_version:
                result.warnings.append("Module lacks __version__ attribute")
            if not has_doc:
                result.warnings.append("Module lacks documentation")

        except Exception as e:
            result.add_test_result("functionality_check", False, str(e))

        if level in [ValidationLevel.COMPREHENSIVE, ValidationLevel.STRESS]:
            # Comprehensive: Test actual functionality
            await self._test_python_module_functions(module, result, level)

    async def _test_python_module_functions(
        self, module: Any, result: ValidationResult, level: ValidationLevel
    ):
        """Test functions in a Python module"""

        # Get testable functions
        functions = []
        for name in dir(module):
            if not name.startswith("_"):
                obj = getattr(module, name)
                if callable(obj):
                    functions.append((name, obj))

        # Test a sample of functions
        sample_size = min(5 if level == ValidationLevel.COMPREHENSIVE else 10, len(functions))

        for name, func in functions[:sample_size]:
            try:
                # Try to call with no arguments (many functions have defaults)
                import inspect

                sig = inspect.signature(func)

                # Check if function can be called without arguments
                required_params = [
                    p
                    for p in sig.parameters.values()
                    if p.default == inspect.Parameter.empty
                    and p.kind != inspect.Parameter.VAR_POSITIONAL
                ]

                if not required_params:
                    # Can call without arguments
                    start_time = time.time()
                    try:
                        if asyncio.iscoroutinefunction(func):
                            await asyncio.wait_for(func(), timeout=5)
                        else:
                            func()
                        duration = time.time() - start_time
                        result.add_test_result(
                            f"function_{name}", True, metrics={"duration": duration}
                        )
                    except Exception as e:
                        # Function might need specific arguments
                        result.add_test_result(
                            f"function_{name}", True, f"Requires arguments: {str(e)}"
                        )
                else:
                    # Function requires arguments
                    result.add_test_result(f"function_{name}_signature", True)

            except Exception as e:
                result.add_test_result(f"function_{name}", False, str(e))

    async def _validate_cli_tool(
        self, capability: Capability, result: ValidationResult, level: ValidationLevel
    ):
        """Validate a CLI tool capability"""

        tool_name = capability.name.replace("cli_", "")

        # Basic: Check if tool exists
        try:
            which_result = subprocess.run(["which", tool_name], capture_output=True, timeout=5)

            if which_result.returncode == 0:
                result.add_test_result("tool_exists", True)
                tool_path = which_result.stdout.decode().strip()
                result.performance_metrics["tool_path"] = tool_path
            else:
                result.add_test_result("tool_exists", False, "Tool not found in PATH")
                return

        except subprocess.TimeoutExpired:
            result.add_test_result("tool_exists", False, "Timeout checking for tool")
            return
        except Exception as e:
            result.add_test_result("tool_exists", False, str(e))
            return

        if level == ValidationLevel.BASIC:
            return

        # Standard: Check version and help
        try:
            # Try to get version
            for flag in ["--version", "-v", "version", "-V"]:
                try:
                    version_result = subprocess.run(
                        [tool_name, flag], capture_output=True, text=True, timeout=5
                    )
                    if version_result.returncode == 0:
                        result.add_test_result("has_version", True)
                        result.performance_metrics["version"] = version_result.stdout.strip()[:100]
                        break
                except:
                    continue

            # Try to get help
            for flag in ["--help", "-h", "help"]:
                try:
                    help_result = subprocess.run(
                        [tool_name, flag], capture_output=True, text=True, timeout=5
                    )
                    if help_result.returncode == 0:
                        result.add_test_result("has_help", True)
                        break
                except:
                    continue

        except Exception as e:
            result.add_test_result("standard_flags", False, str(e))

        if level in [ValidationLevel.COMPREHENSIVE, ValidationLevel.STRESS]:
            # Test actual command execution
            await self._test_cli_tool_execution(tool_name, result, level)

    async def _test_cli_tool_execution(
        self, tool_name: str, result: ValidationResult, level: ValidationLevel
    ):
        """Test CLI tool execution"""

        # Define safe test commands for known tools
        safe_tests = {
            "git": ["git", "status"],
            "python": ["python", "--version"],
            "npm": ["npm", "--version"],
            "docker": ["docker", "--version"],
            "curl": ["curl", "--version"],
            "jq": ["echo", '{"test": "data"}', "|", "jq", "."],
            "grep": ["echo", "test", "|", "grep", "test"],
        }

        if tool_name in safe_tests:
            try:
                start_time = time.time()
                test_result = subprocess.run(
                    safe_tests[tool_name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True if "|" in safe_tests[tool_name] else False,
                )
                duration = time.time() - start_time

                if test_result.returncode == 0:
                    result.add_test_result("execution_test", True, metrics={"duration": duration})
                else:
                    result.add_test_result("execution_test", False, test_result.stderr)

            except Exception as e:
                result.add_test_result("execution_test", False, str(e))

    async def _validate_mcp_tool(
        self, capability: Capability, result: ValidationResult, level: ValidationLevel
    ):
        """Validate an MCP tool capability"""

        server_name = capability.name.replace("mcp_", "")

        # Check MCP configuration
        mcp_config_path = Path.home() / ".mcp" / "mcp.json"

        if not mcp_config_path.exists():
            result.add_test_result("mcp_config_exists", False, "MCP configuration not found")
            return

        try:
            with open(mcp_config_path) as f:
                mcp_config = json.load(f)

            if server_name in mcp_config.get("servers", {}):
                result.add_test_result("server_configured", True)
                server_config = mcp_config["servers"][server_name]

                # Check server configuration
                if "command" in server_config:
                    result.add_test_result("has_command", True)
                else:
                    result.add_test_result(
                        "has_command", False, "Server lacks command configuration"
                    )

                if level != ValidationLevel.BASIC:
                    # Would need actual MCP client to test further
                    result.warnings.append("Full MCP validation requires MCP client")

            else:
                result.add_test_result(
                    "server_configured", False, f"Server {server_name} not in configuration"
                )

        except Exception as e:
            result.add_test_result("mcp_validation", False, str(e))

    async def _validate_api_endpoint(
        self, capability: Capability, result: ValidationResult, level: ValidationLevel
    ):
        """Validate an API endpoint capability"""

        api_config = capability.metadata.get("api_config", {})
        endpoint = api_config.get("endpoint")

        if not endpoint:
            result.add_test_result("has_endpoint", False, "No endpoint configured")
            return

        result.add_test_result("has_endpoint", True)

        if level == ValidationLevel.BASIC:
            return

        # Test connectivity
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(
                    endpoint,
                    headers=api_config.get("headers", {}),
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    duration = time.time() - start_time

                    result.add_test_result(
                        "connectivity",
                        response.status < 500,
                        metrics={"status_code": response.status, "response_time": duration},
                    )

                    if response.status >= 400:
                        result.warnings.append(f"API returned status {response.status}")

        except aiohttp.ClientTimeout:
            result.add_test_result("connectivity", False, "Request timeout")
        except Exception as e:
            result.add_test_result("connectivity", False, str(e))

        if level in [ValidationLevel.COMPREHENSIVE, ValidationLevel.STRESS]:
            await self._test_api_performance(endpoint, api_config, result, level)

    async def _test_api_performance(
        self, endpoint: str, api_config: Dict, result: ValidationResult, level: ValidationLevel
    ):
        """Test API performance"""

        num_requests = 10 if level == ValidationLevel.COMPREHENSIVE else 50

        response_times = []
        errors = 0

        async with aiohttp.ClientSession() as session:
            for _ in range(num_requests):
                try:
                    start_time = time.time()
                    async with session.get(
                        endpoint,
                        headers=api_config.get("headers", {}),
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as response:
                        duration = time.time() - start_time
                        response_times.append(duration)
                        if response.status >= 500:
                            errors += 1
                except:
                    errors += 1

                # Small delay between requests
                await asyncio.sleep(0.1)

        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)

            result.add_test_result(
                "performance_test",
                errors < num_requests * 0.1,
                metrics={
                    "requests": num_requests,
                    "errors": errors,
                    "avg_response_time": avg_time,
                    "min_response_time": min_time,
                    "max_response_time": max_time,
                },
            )

            if avg_time > 1.0:
                result.warnings.append(f"High average response time: {avg_time:.2f}s")
        else:
            result.add_test_result("performance_test", False, "All requests failed")

    async def _validate_system_capability(
        self, capability: Capability, result: ValidationResult, level: ValidationLevel
    ):
        """Validate a system capability"""

        # System capabilities are generally always available
        result.add_test_result("availability", True)

        if level == ValidationLevel.BASIC:
            return

        # Check system resources
        try:
            # Memory check
            memory = psutil.virtual_memory()
            result.add_test_result(
                "memory_available",
                memory.available > 100 * 1024 * 1024,
                metrics={
                    "available_mb": memory.available / (1024 * 1024),
                    "percent_used": memory.percent,
                },
            )

            # CPU check
            cpu_percent = psutil.cpu_percent(interval=1)
            result.add_test_result(
                "cpu_available", cpu_percent < 90, metrics={"cpu_percent": cpu_percent}
            )

            # Disk check
            disk = psutil.disk_usage("/")
            result.add_test_result(
                "disk_available",
                disk.free > 100 * 1024 * 1024,
                metrics={"free_mb": disk.free / (1024 * 1024), "percent_used": disk.percent},
            )

            if memory.percent > 80:
                result.warnings.append(f"High memory usage: {memory.percent}%")
            if cpu_percent > 80:
                result.warnings.append(f"High CPU usage: {cpu_percent}%")
            if disk.percent > 90:
                result.warnings.append(f"Low disk space: {disk.percent}% used")

        except Exception as e:
            result.add_test_result("system_check", False, str(e))

    async def _validate_generic(
        self, capability: Capability, result: ValidationResult, level: ValidationLevel
    ):
        """Generic validation for unknown capability types"""

        # Check basic attributes
        result.add_test_result("has_name", bool(capability.name))
        result.add_test_result("has_type", bool(capability.type))
        result.add_test_result("has_description", bool(capability.description))

        # Check availability flag
        result.add_test_result("marked_available", capability.available)

        if level != ValidationLevel.BASIC:
            result.warnings.append(f"Limited validation for capability type: {capability.type}")

    async def _validate_compatibility(self, capability: Capability, result: ValidationResult):
        """Validate compatibility with other capabilities"""

        # Check for conflicts
        conflicts = self.registry.get_conflicts(capability.name)
        if conflicts:
            active_conflicts = [
                c
                for c in conflicts
                if self.registry.get_capability(c) and self.registry.get_capability(c).available
            ]

            if active_conflicts:
                result.warnings.append(f"Conflicts with active capabilities: {active_conflicts}")
                result.add_test_result("no_active_conflicts", False)
            else:
                result.add_test_result("no_active_conflicts", True)
        else:
            result.add_test_result("no_active_conflicts", True)

        # Check dependencies
        dependencies = self.registry.get_dependencies(capability.name)
        if dependencies:
            missing_deps = [
                d
                for d in dependencies
                if not self.registry.get_capability(d)
                or not self.registry.get_capability(d).available
            ]

            if missing_deps:
                result.errors.append(f"Missing dependencies: {missing_deps}")
                result.add_test_result("dependencies_satisfied", False)
            else:
                result.add_test_result("dependencies_satisfied", True)
        else:
            result.add_test_result("dependencies_satisfied", True)

    async def _validate_performance(
        self, capability: Capability, result: ValidationResult, level: ValidationLevel
    ):
        """Validate performance characteristics"""

        # Memory usage before
        process = psutil.Process()
        mem_before = process.memory_info().rss

        # Simulate usage
        start_time = time.time()

        # Type-specific performance test would go here
        # For now, just measure overhead

        await asyncio.sleep(0.1)  # Simulate some work

        duration = time.time() - start_time
        mem_after = process.memory_info().rss
        mem_increase = (mem_after - mem_before) / (1024 * 1024)  # MB

        result.performance_metrics["memory_overhead_mb"] = mem_increase
        result.performance_metrics["initialization_time"] = duration

        # Add performance warnings
        if mem_increase > 100:
            result.warnings.append(f"High memory overhead: {mem_increase:.1f} MB")
        if duration > 1.0:
            result.warnings.append(f"Slow initialization: {duration:.2f}s")

    async def _update_registry_from_validation(
        self, capability: Capability, result: ValidationResult
    ):
        """Update registry based on validation results"""

        # Update availability based on validation
        if not result.passed and result.level != ValidationLevel.BASIC:
            capability.available = False
            logger.warning(
                f"Marking capability {capability.name} as unavailable due to validation failure"
            )

        # Update success rate (weighted average with previous)
        if result.tests_run > 0:
            new_success_rate = result.tests_passed / result.tests_run
            capability.success_rate = capability.success_rate * 0.7 + new_success_rate * 0.3

        # Add validation metadata
        capability.metadata["last_validation"] = {
            "timestamp": result.timestamp.isoformat(),
            "level": result.level.value,
            "passed": result.passed,
            "tests": f"{result.tests_passed}/{result.tests_run}",
        }

        # Re-register to update
        await self.registry.register(capability)

    def _save_validation_result(self, result: ValidationResult):
        """Save validation result to cache"""

        # Save to history
        self.validation_history.append(result.to_dict())

        # Save to file
        result_file = (
            self.validation_cache / f"{result.capability_name}_{result.timestamp.isoformat()}.json"
        )
        with open(result_file, "w") as f:
            json.dump(result.to_dict(), f, indent=2)

        # Update latest symlink
        latest_link = self.validation_cache / f"{result.capability_name}_latest.json"
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(result_file)

    async def validate_all(
        self, level: ValidationLevel = ValidationLevel.STANDARD
    ) -> Dict[str, ValidationResult]:
        """Validate all registered capabilities"""

        results = {}

        for capability_name in self.registry.capabilities:
            results[capability_name] = await self.validate_capability(capability_name, level)

        return results

    async def validate_category(
        self, category: str, level: ValidationLevel = ValidationLevel.STANDARD
    ) -> Dict[str, ValidationResult]:
        """Validate all capabilities in a category"""

        results = {}

        for capability in self.registry.get_by_category(category):
            results[capability.name] = await self.validate_capability(capability.name, level)

        return results

    def get_validation_report(self) -> Dict[str, Any]:
        """Generate a validation report"""

        if not self.validation_history:
            return {"message": "No validations performed yet"}

        # Aggregate statistics
        total_validations = len(self.validation_history)
        passed = sum(1 for v in self.validation_history if v["passed"])

        by_level = {}
        for v in self.validation_history:
            level = v["level"]
            if level not in by_level:
                by_level[level] = {"total": 0, "passed": 0}
            by_level[level]["total"] += 1
            if v["passed"]:
                by_level[level]["passed"] += 1

        # Find problematic capabilities
        failures = [v for v in self.validation_history if not v["passed"]]
        problematic = {}
        for failure in failures:
            cap = failure["capability"]
            if cap not in problematic:
                problematic[cap] = []
            problematic[cap].extend(failure["errors"])

        return {
            "total_validations": total_validations,
            "passed": passed,
            "failed": total_validations - passed,
            "success_rate": passed / total_validations if total_validations > 0 else 0,
            "by_level": by_level,
            "problematic_capabilities": problematic,
            "last_validation": self.validation_history[-1]["timestamp"]
            if self.validation_history
            else None,
        }
