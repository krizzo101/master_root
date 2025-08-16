"""
Code Quality Validator

Performs static code analysis using flake8 and returns quality metrics.
"""
import subprocess
from typing import Dict


def validate_code_quality(target_path: str = "src/") -> Dict[str, int]:
    try:
        result = subprocess.run(
            ["flake8", target_path], capture_output=True, text=True, timeout=10
        )
        output = result.stdout[:1000]  # Truncate to 1000 chars
        errors = output.count("\n") if result.returncode != 0 else 0
        print(f"[Validator] flake8 completed, errors: {errors}", flush=True)
        return {
            "flake8_errors": errors,
            "returncode": result.returncode,
            "output": output,
        }
    except subprocess.TimeoutExpired:
        print("[Validator] flake8 timed out!", flush=True)
        return {"flake8_errors": -1, "returncode": -1, "output": "[timeout]"}
