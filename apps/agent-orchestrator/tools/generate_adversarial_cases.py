#!/usr/bin/env python3
"""
Adversarial Case Generator: Turn real failures into test cases for system hardening
"""
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List


def get_output_dir() -> Path:
    """Get the output directory from environment or use default"""
    return Path(os.environ.get("ORCH_OUT", "./outputs/analysis")).resolve()


def find_latest_analysis_dir() -> Path:
    """Find the most recent analysis directory"""
    out_dir = get_output_dir()
    analysis_dirs = list(out_dir.glob("system_analysis_*"))
    if not analysis_dirs:
        raise FileNotFoundError("No analysis directories found")
    return max(analysis_dirs, key=lambda p: p.stat().st_mtime)


def load_improvement_report() -> Dict:
    """Load the self-improvement report"""
    analysis_dir = find_latest_analysis_dir()
    report_file = analysis_dir / "self_improve_report.json"

    if not report_file.exists():
        raise FileNotFoundError(f"No improvement report found at {report_file}")

    with open(report_file) as f:
        return json.load(f)


def generate_json_parse_cases(hint_data: List[Dict]) -> List[Dict]:
    """Generate test cases for JSON parsing failures"""
    cases = []

    for i, hint in enumerate(
        [h for h in hint_data if h["error_code"] == "json_parse_failed"]
    ):
        cases.extend(
            [
                {
                    "task_id": f"adversarial_json_fence_{i+1}",
                    "task_type": "analysis",
                    "description": "Test JSON parsing with markdown fences",
                    "prompt": 'Respond with: ```json\n{"status": "completed", "message": "fenced response"}\n```',
                    "expected_behavior": "Should parse correctly with UNIFIED_STRIP_FENCES=1",
                    "failure_source": hint["task"],
                },
                {
                    "task_id": f"adversarial_json_malformed_{i+1}",
                    "task_type": "analysis",
                    "description": "Test malformed JSON handling",
                    "prompt": "Respond with: {status: completed, message: missing quotes}",
                    "expected_behavior": "Should fail gracefully or be fixed by prompt improvement",
                    "failure_source": hint["task"],
                },
                {
                    "task_id": f"adversarial_json_text_{i+1}",
                    "task_type": "analysis",
                    "description": "Test plain text response",
                    "prompt": "Respond with only: Task completed successfully",
                    "expected_behavior": "Should wrap in JSON structure when UNIFIED_REQUIRE_JSON=0",
                    "failure_source": hint["task"],
                },
            ]
        )

    return cases


def generate_schema_validation_cases(hint_data: List[Dict]) -> List[Dict]:
    """Generate test cases for schema validation failures"""
    cases = []

    for i, hint in enumerate(
        [h for h in hint_data if h["error_code"] == "schema_task_id_mismatch"]
    ):
        cases.extend(
            [
                {
                    "task_id": f"adversarial_schema_wrong_id_{i+1}",
                    "task_type": "analysis",
                    "description": "Test task_id mismatch handling",
                    "prompt": f'Respond with: {{"status": "completed", "task_id": "wrong_id"}}',
                    "expected_behavior": "Should fail validation when UNIFIED_VALIDATE_SCHEMA=1",
                    "failure_source": hint["task"],
                },
                {
                    "task_id": f"adversarial_schema_missing_status_{i+1}",
                    "task_type": "analysis",
                    "description": "Test missing required status field",
                    "prompt": 'Respond with: {"message": "completed but no status field"}',
                    "expected_behavior": "Should fail schema validation",
                    "failure_source": hint["task"],
                },
            ]
        )

    return cases


def generate_dependency_cases(hint_data: List[Dict]) -> List[Dict]:
    """Generate test cases for dependency failures"""
    cases = []

    for i, hint in enumerate(
        [h for h in hint_data if h["error_code"] == "dependencies_not_met"]
    ):
        cases.extend(
            [
                {
                    "task_id": f"adversarial_dep_missing_{i+1}",
                    "task_type": "analysis",
                    "description": "Test missing dependency handling",
                    "dependencies": ["nonexistent_task"],
                    "prompt": "This should not execute due to missing dependency",
                    "expected_behavior": "Should remain pending until dependency resolved",
                    "failure_source": hint["task"],
                },
                {
                    "task_id": f"adversarial_dep_circular_{i+1}",
                    "task_type": "analysis",
                    "description": "Test circular dependency detection",
                    "dependencies": [f"adversarial_dep_circular_{i+2}"],
                    "prompt": "This creates a circular dependency",
                    "expected_behavior": "Should detect and fail gracefully",
                    "failure_source": hint["task"],
                },
                {
                    "task_id": f"adversarial_dep_circular_{i+2}",
                    "task_type": "analysis",
                    "description": "Test circular dependency detection (part 2)",
                    "dependencies": [f"adversarial_dep_circular_{i+1}"],
                    "prompt": "This completes the circular dependency",
                    "expected_behavior": "Should detect and fail gracefully",
                    "failure_source": hint["task"],
                },
            ]
        )

    return cases


def generate_timeout_cases(hint_data: List[Dict]) -> List[Dict]:
    """Generate test cases for timeout scenarios"""
    cases = []

    timeout_hints = [h for h in hint_data if "timeout" in h["error_code"].lower()]
    for i, hint in enumerate(timeout_hints):
        cases.extend(
            [
                {
                    "task_id": f"adversarial_timeout_long_{i+1}",
                    "task_type": "analysis",
                    "description": "Test long-running task handling",
                    "prompt": "Think step by step through a very complex problem. Take your time and be thorough. Repeat this analysis 10 times with different approaches.",
                    "expected_behavior": "Should timeout gracefully and allow recovery",
                    "failure_source": hint["task"],
                }
            ]
        )

    return cases


def generate_rate_limit_cases(hint_data: List[Dict]) -> List[Dict]:
    """Generate test cases for rate limiting scenarios"""
    cases = []

    rate_hints = [h for h in hint_data if "rate_limit" in h["error_code"].lower()]
    for i, hint in enumerate(rate_hints):
        cases.extend(
            [
                {
                    "task_id": f"adversarial_rate_burst_{i+1}",
                    "task_type": "analysis",
                    "description": "Test burst rate limiting",
                    "prompt": "Quick response to test rate limiting",
                    "expected_behavior": "Should handle rate limits with backoff",
                    "failure_source": hint["task"],
                    "config": {"burst_test": True, "expect_rate_limit": True},
                }
            ]
        )

    return cases


def main():
    """Generate adversarial test cases from recent failures"""
    print("🧪 Generating adversarial test cases from failures...")

    try:
        report = load_improvement_report()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return

    hint_data = report.get("improvement_hints", [])

    if not hint_data:
        print("✅ No failure patterns found - no adversarial cases needed")
        return

    print(f"🔍 Found {len(hint_data)} failure patterns to harden against")

    # Generate different types of adversarial cases
    cases = []
    cases.extend(generate_json_parse_cases(hint_data))
    cases.extend(generate_schema_validation_cases(hint_data))
    cases.extend(generate_dependency_cases(hint_data))
    cases.extend(generate_timeout_cases(hint_data))
    cases.extend(generate_rate_limit_cases(hint_data))

    if not cases:
        print("🤷 No adversarial cases generated from current failure patterns")
        return

    # Create adversarial test suite
    adversarial_suite = {
        "suite_name": "Adversarial Hardening Cases",
        "generated_from": report["analysis_dir"],
        "timestamp": time.time(),
        "description": "Auto-generated test cases from real system failures",
        "source_failures": len(hint_data),
        "tasks": cases,
    }

    # Save to output directory
    analysis_dir = Path(report["analysis_dir"])
    adversarial_file = analysis_dir / "adversarial_tasks.json"

    with open(adversarial_file, "w") as f:
        json.dump(adversarial_suite, f, indent=2)

    print(f"📝 Generated {len(cases)} adversarial test cases")
    print(f"💾 Saved to: {adversarial_file}")

    # Show breakdown
    case_types = {}
    for case in cases:
        task_type = case["task_id"].split("_")[1]
        case_types[task_type] = case_types.get(task_type, 0) + 1

    print("📊 Case breakdown:")
    for case_type, count in sorted(case_types.items()):
        print(f"   {case_type}: {count} cases")

    # Create integration instructions
    instructions = f"""
# Integrating Adversarial Test Cases

To add these hardening cases to your next orchestrator run:

1. **Manual Integration:**
   ```bash
   # Copy adversarial cases to your task file
   python -c "
   import json
   with open('{adversarial_file}') as f: adv = json.load(f)
   with open('your_tasks.json') as f: existing = json.load(f)
   existing['tasks'].extend(adv['tasks'])
   with open('your_tasks_hardened.json', 'w') as f: json.dump(existing, f, indent=2)
   "
   ```

2. **Validation Flags for Testing:**
   ```bash
   export UNIFIED_STRIP_FENCES=1
   export UNIFIED_REQUIRE_JSON=1
   export UNIFIED_VALIDATE_SCHEMA=1
   ```

3. **Expected Behavior:**
   - Some cases should PASS (after fixes)
   - Some cases should FAIL gracefully (expected failures)
   - System should remain stable throughout

Generated from: {len(hint_data)} real failure patterns
Test cases: {len(cases)} adversarial scenarios
"""

    readme_file = analysis_dir / "ADVERSARIAL_INTEGRATION.md"
    with open(readme_file, "w") as f:
        f.write(instructions)

    print(f"📖 Integration guide: {readme_file}")


if __name__ == "__main__":
    main()
