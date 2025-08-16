"""
Code analysis logic using Bandit (security), Pylint (quality), Radon (complexity), flake8 (style), custom perf.
Each runs as a Python subprocess; results are parsed and aggregated.
"""
import json
import logging
import shlex
import subprocess
from typing import Any

logger = logging.getLogger("code_analysis")


class AnalysisError(Exception):
    pass


def run_subprocess(cmd: str, cwd: str = None, timeout: int = 45) -> str:
    """Run a shell command, return stdout, raise if nonzero or exception."""
    try:
        logger.debug(f"Running command: {cmd}")
        result = subprocess.run(
            shlex.split(cmd),
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        output = result.stdout.decode()
        if result.returncode != 0:
            raise AnalysisError(
                f"Command failed: {cmd}\nSTDERR: {result.stderr.decode()}"
            )
        return output
    except subprocess.TimeoutExpired:
        raise AnalysisError(f"Timeout running: {cmd}")
    except Exception as e:
        logger.error(f"Subprocess error for {cmd}: {e}")
        raise AnalysisError(str(e))


# --- Security: Bandit ---
def run_bandit(path: str) -> list[dict[str, Any]]:
    """Run Bandit security analyzer."""
    bandit_cmd = f"bandit -r -f json {path}"
    out = run_subprocess(bandit_cmd)
    results = json.loads(out)
    issues = results.get("results", [])
    return issues


# --- Quality: pylint ---
def run_pylint(path: str) -> dict[str, Any]:
    """Run pylint for code quality and errors."""
    pylint_cmd = f"pylint --output-format=json {path}"
    try:
        out = run_subprocess(pylint_cmd)
        issues = json.loads(out)
        return {"issues": issues}
    except AnalysisError as exc:
        if "No module named" in str(exc):
            # Sometimes occurs for isolated files; report as warning
            return {"issues": [], "warning": str(exc)}
        raise


# --- Complexity: Radon ---
def run_radon_cc(path: str) -> list[dict[str, Any]]:
    """Run Radon for cyclomatic complexity."""
    cc_cmd = f"radon cc -j {path}"
    out = run_subprocess(cc_cmd)
    results = json.loads(out)
    return results


def run_radon_mi(path: str) -> dict[str, Any]:
    """Run Radon for maintainability index."""
    mi_cmd = f"radon mi -j {path}"
    out = run_subprocess(mi_cmd)
    results = json.loads(out)
    return results


# --- Style: flake8 ---
def run_flake8(path: str) -> list[dict[str, str]]:
    """Run flake8 for style violations."""
    flake8_cmd = f"flake8 --format=json {path}"
    try:
        out = run_subprocess(flake8_cmd)
        # flake8 output is not always JSON, handle both
        try:
            results = json.loads(out)
            return results
        except json.JSONDecodeError:
            # Fallback: parse plain text
            lines = out.splitlines()
            parsed = [l for l in lines if l.strip()]
            return [{"violation": l} for l in parsed]
    except AnalysisError as exc:
        if "No module named" in str(exc):
            return []
        raise


# --- Performance: Heuristic ---
def run_performance_heuristic(path: str) -> list[dict[str, Any]]:
    """
    Inspect for performance anti-patterns (e.g., unbounded loops, builtins misuse). Basic regexes.
    """
    issues = []
    try:
        with open(path, encoding="utf-8") as file:
            lines = file.readlines()
        for idx, line in enumerate(lines):
            lstr = line.strip()
            if (
                "for" in lstr
                and "range(" in lstr
                and ("1000000" in lstr or "10**6" in lstr)
            ):
                issues.append(
                    {
                        "type": "large_range_loop",
                        "line": idx + 1,
                        "code": lstr,
                        "suggestion": "Check for large loops - consider batching or limiting size.",
                    }
                )
            if "open(" in lstr and ", 'r'" not in lstr:
                issues.append(
                    {
                        "type": "file_open_no_context",
                        "line": idx + 1,
                        "code": lstr,
                        "suggestion": "Use 'with open(...) as f:' context manager for file ops.",
                    }
                )
    except Exception as e:
        logger.error(f"Performance heuristic scan failed: {e}")
    return issues


# --- Aggregation/Entry Point ---
def analyze_code(path: str) -> dict[str, Any]:
    """
    Analyze a single code file/directory and return structured results.
    """
    results = {}
    try:
        results["security"] = run_bandit(path)
    except Exception as e:
        logger.error(f"Bandit analysis failed: {e}")
        results["security"] = [{"error": str(e)}]
    try:
        results["quality"] = run_pylint(path)
    except Exception as e:
        logger.error(f"Pylint analysis failed: {e}")
        results["quality"] = {"error": str(e)}
    try:
        results["complexity"] = run_radon_cc(path)
    except Exception as e:
        logger.error(f"Radon CC failed: {e}")
        results["complexity"] = [{"error": str(e)}]
    try:
        results["maintainability"] = run_radon_mi(path)
    except Exception as e:
        logger.error(f"Radon MI failed: {e}")
        results["maintainability"] = {"error": str(e)}
    try:
        results["style"] = run_flake8(path)
    except Exception as e:
        logger.error(f"Flake8 failed: {e}")
        results["style"] = [{"error": str(e)}]
    try:
        results["performance"] = run_performance_heuristic(path)
    except Exception as e:
        logger.error(f"Custom performance check failed: {e}")
        results["performance"] = [{"error": str(e)}]
    return results
