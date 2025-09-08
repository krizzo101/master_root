#!/usr/bin/env python3
"""
Self-Improvement Suite: Analyze orchestrator runs and generate improvement hints
"""
import glob
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_output_dir() -> Path:
    """Get the output directory from environment or use default"""
    return Path(os.environ.get("ORCH_OUT", "./outputs/analysis")).resolve()


def find_latest_analysis_dir() -> Optional[Path]:
    """Find the most recent analysis directory"""
    out_dir = get_output_dir()
    analysis_dirs = list(out_dir.glob("system_analysis_*"))
    if not analysis_dirs:
        return None
    return max(analysis_dirs, key=lambda p: p.stat().st_mtime)


def load_task_statuses(analysis_dir: Path) -> Dict[str, Dict]:
    """Load all task statuses from JSON files"""
    tasks = {}
    tasks_dir = analysis_dir / "tasks"

    if not tasks_dir.exists():
        return tasks

    for task_file in tasks_dir.glob("*.json"):
        try:
            with open(task_file) as f:
                task_data = json.load(f)

            task_id = task_data.get("task_id", task_file.stem)
            tasks[task_id] = {
                "status": task_data.get("status", task_data.get("state", "unknown")),
                "error_details": task_data.get("error_details", ""),
                "execution_time": task_data.get("execution_time", 0),
                "file_path": str(task_file),
            }
        except Exception as e:
            print(f"Warning: Could not load {task_file}: {e}")

    return tasks


def load_validation_suite() -> Dict:
    """Load validation suite configuration"""
    suite_file = Path("validation_suite.json")
    if not suite_file.exists():
        # Create minimal default suite
        return {
            "suite_id": "default",
            "expectations": {},
            "hints": {
                "json_parse_failed": "Enable UNIFIED_STRIP_FENCES=1 or improve agent prompts",
                "dependencies_not_met": "Check for upstream task failures",
            },
        }

    with open(suite_file) as f:
        return json.load(f)


def analyze_failures(tasks: Dict[str, Dict], expectations: Dict[str, str]) -> Dict:
    """Analyze task failures against expectations"""
    failures = {}

    for task_id, expected_status in expectations.items():
        actual_status = tasks.get(task_id, {}).get("status", "missing")

        if actual_status != expected_status:
            failures[task_id] = {
                "expected": expected_status,
                "actual": actual_status,
                "error_details": tasks.get(task_id, {}).get("error_details", ""),
                "execution_time": tasks.get(task_id, {}).get("execution_time", 0),
            }

    return failures


def generate_improvement_hints(failures: Dict, hints: Dict) -> List[Dict]:
    """Generate specific improvement hints based on failures"""
    improvement_hints = []

    for task_id, failure_info in failures.items():
        error_details = failure_info.get("error_details", "")

        # Map error patterns to hints
        for error_pattern, hint in hints.items():
            if error_pattern.lower() in error_details.lower():
                improvement_hints.append(
                    {
                        "task": task_id,
                        "error_code": error_pattern,
                        "hint": hint,
                        "error_details": error_details[
                            :200
                        ],  # Truncate for readability
                    }
                )
                break
        else:
            # Generic hint for unmapped errors
            if error_details:
                improvement_hints.append(
                    {
                        "task": task_id,
                        "error_code": "unknown_error",
                        "hint": f"Review error: {error_details[:100]}...",
                        "error_details": error_details[:200],
                    }
                )

    return improvement_hints


def calculate_performance_metrics(tasks: Dict[str, Dict]) -> Dict:
    """Calculate performance metrics"""
    if not tasks:
        return {}

    completed_tasks = [t for t in tasks.values() if t["status"] == "completed"]
    total_tasks = len(tasks)
    success_rate = len(completed_tasks) / total_tasks if total_tasks > 0 else 0

    execution_times = [
        t["execution_time"] for t in tasks.values() if t["execution_time"] > 0
    ]
    avg_execution_time = (
        sum(execution_times) / len(execution_times) if execution_times else 0
    )

    return {
        "total_tasks": total_tasks,
        "completed_tasks": len(completed_tasks),
        "success_rate": success_rate,
        "avg_execution_time_seconds": avg_execution_time,
        "failed_tasks": total_tasks - len(completed_tasks),
    }


def generate_auto_tune_recommendations(metrics: Dict, suite: Dict) -> List[Dict]:
    """Generate auto-tuning recommendations"""
    recommendations = []

    auto_tune_config = suite.get("auto_tune_config", {})
    targets = suite.get("performance_targets", {})

    success_rate = metrics.get("success_rate", 0)
    avg_time = metrics.get("avg_execution_time_seconds", 0)

    # Success rate recommendations
    min_success = targets.get("min_success_rate", 0.95)
    if success_rate < min_success:
        recommendations.append(
            {
                "type": "reliability",
                "issue": f"Success rate {success_rate:.2%} below target {min_success:.2%}",
                "recommendation": "Consider reducing parallelism or adding retry logic",
            }
        )

    # Latency recommendations
    max_latency = targets.get("max_avg_task_latency_seconds", 60)
    if avg_time > max_latency:
        recommendations.append(
            {
                "type": "performance",
                "issue": f"Average task time {avg_time:.1f}s exceeds target {max_latency}s",
                "recommendation": "Consider increasing parallelism or optimizing prompts",
            }
        )

    return recommendations


def main():
    """Main validation and improvement analysis"""
    print("🔍 Analyzing orchestrator run for improvements...")

    # Find latest analysis
    analysis_dir = find_latest_analysis_dir()
    if not analysis_dir:
        print("❌ No analysis directories found")
        sys.exit(1)

    print(f"📁 Analyzing: {analysis_dir}")

    # Load data
    tasks = load_task_statuses(analysis_dir)
    suite = load_validation_suite()

    if not tasks:
        print("⚠️  No task files found")
        sys.exit(1)

    print(f"📊 Found {len(tasks)} tasks")

    # Analyze against expectations
    expectations = suite.get("expectations", {})
    failures = analyze_failures(tasks, expectations)

    # Calculate metrics
    metrics = calculate_performance_metrics(tasks)

    # Generate improvements
    hints = generate_improvement_hints(failures, suite.get("hints", {}))
    recommendations = generate_auto_tune_recommendations(metrics, suite)

    # Create report
    report = {
        "suite_id": suite.get("suite_id", "unknown"),
        "analysis_dir": str(analysis_dir),
        "timestamp": time.time(),
        "pass": len(failures) == 0,
        "summary": {
            "total_tasks": len(tasks),
            "failed_tasks": len(failures),
            "success_rate": metrics.get("success_rate", 0),
        },
        "performance_metrics": metrics,
        "failures": failures,
        "improvement_hints": hints,
        "auto_tune_recommendations": recommendations,
    }

    # Save report
    report_file = analysis_dir / "self_improve_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"📝 Report written to: {report_file}")

    # Print summary
    if report["pass"]:
        print("✅ All tasks completed successfully!")
    else:
        print(f"❌ {len(failures)} tasks failed")
        for hint in hints[:3]:  # Show first 3 hints
            print(f"   💡 {hint['task']}: {hint['hint']}")

    print(f"📈 Success rate: {metrics.get('success_rate', 0):.1%}")

    if not report["pass"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
