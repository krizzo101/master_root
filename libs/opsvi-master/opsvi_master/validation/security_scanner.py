"""
Security Vulnerability Scanner

Performs static security analysis using bandit and returns metrics.
"""

import subprocess
from typing import Dict


def scan_security(target_path: str = "src/") -> Dict[str, int]:
    try:
        result = subprocess.run(
            ["bandit", "-r", target_path, "-f", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout[:1000]  # Truncate to 1000 chars
        import json

        try:
            data = json.loads(result.stdout)
            issues = len(data.get("results", []))
        except Exception:
            issues = -1
        print(f"[Validator] bandit completed, issues: {issues}", flush=True)
        return {
            "bandit_issues": issues,
            "returncode": result.returncode,
            "output": output,
        }
    except subprocess.TimeoutExpired:
        print("[Validator] bandit timed out!", flush=True)
        return {"bandit_issues": -1, "returncode": -1, "output": "[timeout]"}
