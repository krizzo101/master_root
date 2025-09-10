#!/usr/bin/env python3
"""
Comprehensive Orchestrator Monitoring System
Tracks: task progress, token usage, submissions, results, and performance metrics
"""

import json
import re
import subprocess
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import psutil


class OrchestratorMonitor:
    def __init__(self, output_dir: str = "./output/self_improvement_continued"):
        self.output_dir = Path(output_dir)
        self.log_file = self.output_dir / "orchestrator.log"
        self.checkpoint_dir = self.output_dir / "checkpoints"
        self.tasks_dir = self.output_dir / "tasks"
        self.metrics = defaultdict(dict)
        self.token_usage = defaultdict(int)

    def parse_log_for_metrics(self) -> Dict[str, Any]:
        """Extract metrics from orchestrator log"""
        metrics = {
            "tasks": {},
            "token_usage": {},
            "memory_usage": [],
            "errors": [],
            "warnings": [],
            "audit_trail": [],
        }

        if not self.log_file.exists():
            return metrics

        with open(self.log_file, "r") as f:
            for line in f:
                # Task status
                if "task_started" in line:
                    match = re.search(r"'task_id': '([^']+)'", line)
                    if match:
                        task_id = match.group(1)
                        metrics["tasks"][task_id] = {
                            "status": "started",
                            "timestamp": self._extract_timestamp(line),
                        }

                # Task completion
                if "task_completed" in line:
                    match = re.search(
                        r"'task_id': '([^']+)'.*'duration': ([0-9.]+)", line
                    )
                    if match:
                        task_id = match.group(1)
                        duration = float(match.group(2))
                        if task_id in metrics["tasks"]:
                            metrics["tasks"][task_id]["status"] = "completed"
                            metrics["tasks"][task_id]["duration"] = duration

                # Token usage (estimate from prompts)
                if "prompt_tokens" in line or "completion_tokens" in line:
                    match = re.search(r"'([^']+)': (\d+)", line)
                    if match:
                        token_type = match.group(1)
                        count = int(match.group(2))
                        metrics["token_usage"][token_type] = (
                            metrics["token_usage"].get(token_type, 0) + count
                        )

                # Memory usage
                if "Memory usage" in line:
                    match = re.search(r"(\d+\.?\d*)%", line)
                    if match:
                        metrics["memory_usage"].append(
                            {
                                "timestamp": self._extract_timestamp(line),
                                "usage": float(match.group(1)),
                            }
                        )

                # Errors and warnings
                if "ERROR" in line:
                    metrics["errors"].append(line.strip())
                if "WARNING" in line:
                    metrics["warnings"].append(line.strip())

                # Audit trail
                if "AUDIT:" in line:
                    metrics["audit_trail"].append(line.strip())

        return metrics

    def _extract_timestamp(self, line: str) -> str:
        """Extract timestamp from log line"""
        match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
        return match.group(1) if match else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def analyze_checkpoint(self) -> Dict[str, Any]:
        """Analyze latest checkpoint for progress"""
        latest_checkpoint = self.checkpoint_dir / "latest_checkpoint.json"
        if not latest_checkpoint.exists():
            checkpoints = sorted(self.checkpoint_dir.glob("checkpoint_*.json"))
            if checkpoints:
                latest_checkpoint = checkpoints[-1]
            else:
                return {"error": "No checkpoints found"}

        with open(latest_checkpoint, "r") as f:
            checkpoint = json.load(f)

        return {
            "workflow_id": checkpoint.get("workflow_id"),
            "progress": {
                "total": checkpoint.get("metrics", {}).get("total", 0),
                "completed": checkpoint.get("metrics", {}).get("completed", 0),
                "failed": checkpoint.get("metrics", {}).get("failed", 0),
                "percentage": (
                    checkpoint.get("metrics", {}).get("completed", 0)
                    / max(checkpoint.get("metrics", {}).get("total", 1), 1)
                )
                * 100,
            },
            "completed_tasks": checkpoint.get("completed_tasks", []),
            "failed_tasks": checkpoint.get("failed_tasks", []),
            "running_tasks": checkpoint.get("running_tasks", []),
            "duration": checkpoint.get("metrics", {}).get("total_duration", 0),
        }

    def analyze_task_results(self) -> Dict[str, Any]:
        """Analyze individual task results"""
        results = {}
        if not self.tasks_dir.exists():
            return results

        for task_file in self.tasks_dir.glob("*.json"):
            with open(task_file, "r") as f:
                task_data = json.load(f)

            task_id = task_file.stem
            results[task_id] = {
                "status": task_data.get("status", "unknown"),
                "duration": task_data.get("execution_time", 0),
                "token_estimate": self._estimate_tokens(task_data),
                "output_size": len(json.dumps(task_data.get("result", {}))),
                "error": task_data.get("error"),
            }

        return results

    def _estimate_tokens(self, task_data: Dict) -> int:
        """Estimate token usage from task data"""
        # Rough estimation: ~4 chars per token
        prompt = task_data.get("prompt", "")
        result = json.dumps(task_data.get("result", {}))
        return (len(prompt) + len(result)) // 4

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_mb": psutil.virtual_memory().available / (1024 * 1024),
            "disk_usage_percent": psutil.disk_usage("/").percent,
        }

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "system_metrics": self.get_system_metrics(),
            "checkpoint_analysis": self.analyze_checkpoint(),
            "log_metrics": self.parse_log_for_metrics(),
            "task_results": self.analyze_task_results(),
        }

        # Calculate totals
        if report["log_metrics"]["token_usage"]:
            report["token_totals"] = {
                "total_tokens": sum(report["log_metrics"]["token_usage"].values()),
                "estimated_cost": sum(report["log_metrics"]["token_usage"].values())
                * 0.00002,  # Rough estimate
            }

        # Task summary
        checkpoint = report["checkpoint_analysis"]
        report["summary"] = {
            "workflow_progress": f"{checkpoint.get('progress', {}).get('percentage', 0):.1f}%",
            "tasks_completed": len(checkpoint.get("completed_tasks", [])),
            "tasks_failed": len(checkpoint.get("failed_tasks", [])),
            "tasks_running": len(checkpoint.get("running_tasks", [])),
            "total_duration_minutes": checkpoint.get("duration", 0) / 60,
            "warnings_count": len(report["log_metrics"]["warnings"]),
            "errors_count": len(report["log_metrics"]["errors"]),
        }

        return report

    def print_dashboard(self, report: Dict[str, Any]):
        """Print formatted dashboard"""
        print("\n" + "=" * 80)
        print("ORCHESTRATOR MONITORING DASHBOARD")
        print("=" * 80)
        print(f"Timestamp: {report['timestamp']}")

        # System Status
        print("\n📊 SYSTEM STATUS")
        sys = report["system_metrics"]
        print(
            f"  CPU: {sys['cpu_percent']}% | Memory: {sys['memory_percent']}% | Available: {sys['memory_available_mb']:.0f}MB"
        )

        # Workflow Progress
        print("\n⚙️ WORKFLOW PROGRESS")
        summary = report["summary"]
        print(
            f"  Progress: {summary['workflow_progress']} | Completed: {summary['tasks_completed']} | Failed: {summary['tasks_failed']} | Running: {summary['tasks_running']}"
        )
        print(f"  Duration: {summary['total_duration_minutes']:.1f} minutes")

        # Token Usage
        if "token_totals" in report:
            print("\n💰 TOKEN USAGE")
            print(f"  Total Tokens: {report['token_totals']['total_tokens']:,}")
            print(f"  Estimated Cost: ${report['token_totals']['estimated_cost']:.4f}")

        # Current Tasks
        checkpoint = report["checkpoint_analysis"]
        if checkpoint.get("running_tasks"):
            print("\n🔄 CURRENTLY RUNNING")
            for task in checkpoint["running_tasks"]:
                print(f"  • {task}")

        # Recent Completions
        if checkpoint.get("completed_tasks"):
            print("\n✅ RECENT COMPLETIONS")
            for task in checkpoint["completed_tasks"][-5:]:
                print(f"  • {task}")

        # Alerts
        if summary["errors_count"] > 0:
            print(f"\n⚠️ ERRORS: {summary['errors_count']} errors detected")
        if summary["warnings_count"] > 0:
            print(f"\n⚠️ WARNINGS: {summary['warnings_count']} warnings detected")

        print("\n" + "=" * 80)

    def save_report(self, report: Dict[str, Any]):
        """Save report to file"""
        report_file = (
            self.output_dir
            / f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        return report_file


def main():
    """Run monitoring in continuous mode"""
    import argparse

    parser = argparse.ArgumentParser(description="Monitor orchestrator workflow")
    parser.add_argument(
        "--output-dir",
        default="./output/self_improvement_continued",
        help="Orchestrator output directory",
    )
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument(
        "--interval", type=int, default=10, help="Update interval in seconds"
    )
    parser.add_argument("--save", action="store_true", help="Save reports to file")

    args = parser.parse_args()

    monitor = OrchestratorMonitor(args.output_dir)

    try:
        while True:
            report = monitor.generate_report()

            # Clear screen for dashboard effect
            print("\033[2J\033[H")  # Clear screen and move cursor to top

            monitor.print_dashboard(report)

            if args.save:
                report_file = monitor.save_report(report)
                print(f"\nReport saved to: {report_file}")

            if args.once:
                break

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")

        # Save final report
        if args.save:
            final_report = monitor.generate_report()
            report_file = monitor.save_report(final_report)
            print(f"Final report saved to: {report_file}")


if __name__ == "__main__":
    main()
