"""Critic agent for evaluating code generation outputs."""

import ast
import hashlib
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PolicyScore(BaseModel):
    """Score for a specific policy."""
    name: str
    score: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0, le=1.0)
    reasons: List[str] = Field(default_factory=list)


class PatchPlan(BaseModel):
    """Plan for fixing issues."""
    file: str
    line: Optional[int] = None
    change: str
    priority: str = "medium"  # low, medium, high, critical


class CriticResult(BaseModel):
    """Result of critic evaluation."""
    pass: bool
    score: float = Field(ge=0.0, le=1.0)
    policy_scores: Dict[str, float] = Field(default_factory=dict)
    reasons: List[str] = Field(default_factory=list)
    patch_plan: List[Dict[str, Any]] = Field(default_factory=list)


class CriticAgent:
    """Agent for evaluating code generation outputs."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the critic agent."""
        self.config = config or {}
        self.policies = {
            "spec": self._evaluate_spec,
            "arch": self._evaluate_architecture,
            "compile": self._evaluate_compile,
            "tests": self._evaluate_tests,
            "compliance": self._evaluate_compliance,
            "perf": self._evaluate_performance,
        }
        self.threshold = self.config.get("threshold", 0.95)

    def evaluate(self, input_data: Dict[str, Any]) -> CriticResult:
        """Evaluate the input data and return a critic result."""
        try:
            # Extract evaluation context
            task_type = input_data.get("task_type", "unknown")
            artifacts = input_data.get("artifacts", [])
            code_path = input_data.get("code_path")
            test_path = input_data.get("test_path")
            spec_data = input_data.get("spec", {})
            arch_data = input_data.get("architecture", {})

            # Initialize scores
            policy_scores = {}
            all_reasons = []
            patch_plan = []

            # Evaluate each policy
            for policy_name, policy_func in self.policies.items():
                try:
                    score, reasons, patches = policy_func(
                        task_type, artifacts, code_path, test_path, spec_data, arch_data
                    )
                    policy_scores[policy_name] = score
                    all_reasons.extend(reasons)
                    patch_plan.extend(patches)
                except Exception as e:
                    logger.error(f"Failed to evaluate policy {policy_name}: {e}")
                    policy_scores[policy_name] = 0.0
                    all_reasons.append(f"Policy {policy_name} evaluation failed: {e}")

            # Calculate overall score (weighted average)
            overall_score = self._calculate_overall_score(policy_scores)

            # Determine if it passes
            passes = overall_score >= self.threshold

            return CriticResult(
                pass=passes,
                score=overall_score,
                policy_scores=policy_scores,
                reasons=all_reasons,
                patch_plan=patch_plan
            )

        except Exception as e:
            logger.error(f"Critic evaluation failed: {e}")
            return CriticResult(
                pass=False,
                score=0.0,
                policy_scores={},
                reasons=[f"Critic evaluation failed: {e}"],
                patch_plan=[]
            )

    def _calculate_overall_score(self, policy_scores: Dict[str, float]) -> float:
        """Calculate weighted overall score."""
        if not policy_scores:
            return 0.0

        # Default weights (can be configured)
        weights = {
            "spec": 0.15,
            "arch": 0.15,
            "compile": 0.20,
            "tests": 0.20,
            "compliance": 0.15,
            "perf": 0.15,
        }

        total_weight = 0.0
        weighted_sum = 0.0

        for policy, score in policy_scores.items():
            weight = weights.get(policy, 0.1)
            weighted_sum += score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _evaluate_spec(
        self,
        task_type: str,
        artifacts: List[Dict[str, Any]],
        code_path: Optional[str],
        test_path: Optional[str],
        spec_data: Dict[str, Any],
        arch_data: Dict[str, Any]
    ) -> Tuple[float, List[str], List[Dict[str, Any]]]:
        """Evaluate specification quality."""
        reasons = []
        patches = []
        score = 1.0

        # Check if spec exists and is complete
        if not spec_data:
            score = 0.0
            reasons.append("No specification data provided")
            patches.append({
                "file": "specification.md",
                "change": "Create comprehensive specification document",
                "priority": "critical"
            })
            return score, reasons, patches

        # Check for required spec components
        required_fields = ["title", "description", "functional_requirements", "non_functional_requirements"]
        missing_fields = [field for field in required_fields if not spec_data.get(field)]

        if missing_fields:
            score -= 0.2 * len(missing_fields)
            reasons.append(f"Missing specification fields: {', '.join(missing_fields)}")
            for field in missing_fields:
                patches.append({
                    "file": "specification.md",
                    "change": f"Add {field} section to specification",
                    "priority": "high"
                })

        # Check for detailed requirements
        func_reqs = spec_data.get("functional_requirements", [])
        if len(func_reqs) < 3:
            score -= 0.1
            reasons.append("Insufficient functional requirements")
            patches.append({
                "file": "specification.md",
                "change": "Add more detailed functional requirements",
                "priority": "medium"
            })

        return max(0.0, score), reasons, patches

    def _evaluate_architecture(
        self,
        task_type: str,
        artifacts: List[Dict[str, Any]],
        code_path: Optional[str],
        test_path: Optional[str],
        spec_data: Dict[str, Any],
        arch_data: Dict[str, Any]
    ) -> Tuple[float, List[str], List[Dict[str, Any]]]:
        """Evaluate architecture quality."""
        reasons = []
        patches = []
        score = 1.0

        # Check if architecture exists
        if not arch_data:
            score = 0.0
            reasons.append("No architecture data provided")
            patches.append({
                "file": "architecture.md",
                "change": "Create architecture documentation",
                "priority": "critical"
            })
            return score, reasons, patches

        # Check for required architecture components
        required_components = ["components", "interfaces", "data_flow"]
        missing_components = [comp for comp in required_components if not arch_data.get(comp)]

        if missing_components:
            score -= 0.15 * len(missing_components)
            reasons.append(f"Missing architecture components: {', '.join(missing_components)}")
            for comp in missing_components:
                patches.append({
                    "file": "architecture.md",
                    "change": f"Add {comp} section to architecture",
                    "priority": "high"
                })

        # Check for design patterns and best practices
        if not arch_data.get("design_patterns"):
            score -= 0.1
            reasons.append("No design patterns specified")
            patches.append({
                "file": "architecture.md",
                "change": "Document design patterns used",
                "priority": "medium"
            })

        return max(0.0, score), reasons, patches

    def _evaluate_compile(
        self,
        task_type: str,
        artifacts: List[Dict[str, Any]],
        code_path: Optional[str],
        test_path: Optional[str],
        spec_data: Dict[str, Any],
        arch_data: Dict[str, Any]
    ) -> Tuple[float, List[str], List[Dict[str, Any]]]:
        """Evaluate compilation and static analysis."""
        reasons = []
        patches = []
        score = 1.0

        if not code_path or not Path(code_path).exists():
            score = 0.0
            reasons.append("Code path does not exist")
            return score, reasons, patches

        # Check for Python syntax errors
        python_files = list(Path(code_path).rglob("*.py"))
        if not python_files:
            score = 0.0
            reasons.append("No Python files found")
            return score, reasons, patches

        syntax_errors = []
        for py_file in python_files:
            try:
                with open(py_file, 'r') as f:
                    ast.parse(f.read())
            except SyntaxError as e:
                syntax_errors.append(f"{py_file}: {e}")

        if syntax_errors:
            score -= 0.3
            reasons.append(f"Syntax errors found: {len(syntax_errors)}")
            for error in syntax_errors[:3]:  # Limit to first 3 errors
                file_path, line_info = error.split(": ", 1)
                patches.append({
                    "file": str(file_path),
                    "change": f"Fix syntax error: {line_info}",
                    "priority": "critical"
                })

        # Check for basic code quality (simple heuristics)
        for py_file in python_files[:5]:  # Check first 5 files
            try:
                with open(py_file, 'r') as f:
                    content = f.read()

                # Check for docstrings
                if '"""' not in content and "'''" not in content:
                    score -= 0.05
                    reasons.append(f"Missing docstrings in {py_file.name}")
                    patches.append({
                        "file": str(py_file),
                        "change": "Add module and function docstrings",
                        "priority": "medium"
                    })

                # Check for imports
                if not any(line.strip().startswith('import ') or line.strip().startswith('from ')
                          for line in content.split('\n')):
                    score -= 0.05
                    reasons.append(f"No imports found in {py_file.name}")

            except Exception as e:
                logger.warning(f"Error analyzing {py_file}: {e}")

        return max(0.0, score), reasons, patches

    def _evaluate_tests(
        self,
        task_type: str,
        artifacts: List[Dict[str, Any]],
        code_path: Optional[str],
        test_path: Optional[str],
        spec_data: Dict[str, Any],
        arch_data: Dict[str, Any]
    ) -> Tuple[float, List[str], List[Dict[str, Any]]]:
        """Evaluate test coverage and quality."""
        reasons = []
        patches = []
        score = 1.0

        if not test_path or not Path(test_path).exists():
            score = 0.0
            reasons.append("Test path does not exist")
            patches.append({
                "file": "tests/",
                "change": "Create test directory and test files",
                "priority": "critical"
            })
            return score, reasons, patches

        # Check for test files
        test_files = list(Path(test_path).rglob("test_*.py")) + list(Path(test_path).rglob("*_test.py"))
        if not test_files:
            score = 0.0
            reasons.append("No test files found")
            patches.append({
                "file": "tests/",
                "change": "Create test files with test_ prefix",
                "priority": "critical"
            })
            return score, reasons, patches

        # Check test file quality
        for test_file in test_files:
            try:
                with open(test_file, 'r') as f:
                    content = f.read()

                # Check for test functions
                if 'def test_' not in content:
                    score -= 0.1
                    reasons.append(f"No test functions in {test_file.name}")
                    patches.append({
                        "file": str(test_file),
                        "change": "Add test functions with test_ prefix",
                        "priority": "high"
                    })

                # Check for assertions
                if 'assert ' not in content and 'self.assert' not in content:
                    score -= 0.1
                    reasons.append(f"No assertions in {test_file.name}")
                    patches.append({
                        "file": str(test_file),
                        "change": "Add assertions to test functions",
                        "priority": "high"
                    })

            except Exception as e:
                logger.warning(f"Error analyzing test file {test_file}: {e}")

        # Try to run tests if possible
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", test_path, "--tb=short", "-q"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                score -= 0.2
                reasons.append("Tests failed to run")
                patches.append({
                    "file": "tests/",
                    "change": "Fix failing tests",
                    "priority": "high"
                })

        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("Could not run tests (pytest not available)")

        return max(0.0, score), reasons, patches

    def _evaluate_compliance(
        self,
        task_type: str,
        artifacts: List[Dict[str, Any]],
        code_path: Optional[str],
        test_path: Optional[str],
        spec_data: Dict[str, Any],
        arch_data: Dict[str, Any]
    ) -> Tuple[float, List[str], List[Dict[str, Any]]]:
        """Evaluate security and compliance."""
        reasons = []
        patches = []
        score = 1.0

        if not code_path:
            return score, reasons, patches

        # Check for security issues (basic checks)
        python_files = list(Path(code_path).rglob("*.py"))
        security_issues = []

        for py_file in python_files:
            try:
                with open(py_file, 'r') as f:
                    content = f.read()

                # Check for hardcoded secrets
                if any(secret in content.lower() for secret in ['password', 'secret', 'key', 'token']):
                    if any(line.strip().startswith(('password =', 'secret =', 'key =', 'token ='))
                          for line in content.split('\n')):
                        security_issues.append(f"Hardcoded secrets in {py_file.name}")
                        score -= 0.2
                        patches.append({
                            "file": str(py_file),
                            "change": "Move secrets to environment variables",
                            "priority": "critical"
                        })

                # Check for SQL injection vulnerabilities
                if 'execute(' in content and any(op in content for op in ['%s', 'format(', 'f"']):
                    security_issues.append(f"Potential SQL injection in {py_file.name}")
                    score -= 0.15
                    patches.append({
                        "file": str(py_file),
                        "change": "Use parameterized queries to prevent SQL injection",
                        "priority": "critical"
                    })

            except Exception as e:
                logger.warning(f"Error analyzing {py_file} for security: {e}")

        if security_issues:
            reasons.extend(security_issues)

        # Check for proper error handling
        for py_file in python_files[:3]:  # Check first 3 files
            try:
                with open(py_file, 'r') as f:
                    content = f.read()

                if 'try:' in content and 'except:' in content:
                    if 'except:' in content and 'except Exception:' not in content:
                        score -= 0.05
                        reasons.append(f"Bare except clause in {py_file.name}")
                        patches.append({
                            "file": str(py_file),
                            "change": "Replace bare except with specific exception handling",
                            "priority": "medium"
                        })

            except Exception as e:
                logger.warning(f"Error analyzing {py_file} for error handling: {e}")

        return max(0.0, score), reasons, patches

    def _evaluate_performance(
        self,
        task_type: str,
        artifacts: List[Dict[str, Any]],
        code_path: Optional[str],
        test_path: Optional[str],
        spec_data: Dict[str, Any],
        arch_data: Dict[str, Any]
    ) -> Tuple[float, List[str], List[Dict[str, Any]]]:
        """Evaluate performance characteristics."""
        reasons = []
        patches = []
        score = 1.0

        if not code_path:
            return score, reasons, patches

        # Basic performance checks
        python_files = list(Path(code_path).rglob("*.py"))

        for py_file in python_files:
            try:
                with open(py_file, 'r') as f:
                    content = f.read()

                # Check for potential performance issues
                if 'for ' in content and ' in ' in content:
                    # Check for nested loops
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'for ' in line and ' in ' in line:
                            # Look for nested loops
                            for j in range(i + 1, min(i + 10, len(lines))):
                                if 'for ' in lines[j] and ' in ' in lines[j]:
                                    score -= 0.1
                                    reasons.append(f"Nested loops detected in {py_file.name}")
                                    patches.append({
                                        "file": str(py_file),
                                        "line": i + 1,
                                        "change": "Consider optimizing nested loops",
                                        "priority": "medium"
                                    })
                                    break

                # Check for large data structures in memory
                if any(pattern in content for pattern in ['list(', 'dict(', 'set(']):
                    if len(content) > 10000:  # Large file
                        score -= 0.05
                        reasons.append(f"Large file {py_file.name} may have memory issues")
                        patches.append({
                            "file": str(py_file),
                            "change": "Consider breaking into smaller modules",
                            "priority": "low"
                        })

            except Exception as e:
                logger.warning(f"Error analyzing {py_file} for performance: {e}")

        return max(0.0, score), reasons, patches


# Global critic agent instance
critic_agent = CriticAgent()


def evaluate_code_generation(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate code generation output and return critic result."""
    result = critic_agent.evaluate(input_data)
    return result.dict()