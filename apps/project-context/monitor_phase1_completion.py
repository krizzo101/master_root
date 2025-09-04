#!/usr/bin/env python3
"""
Phase 1 Completion Monitor - Updated for New Execution Files

Monitors:
- execute_phase1_generic.py (GenericOrchestrator with 18 parallel)
- execute_phase1_practical.py (PracticalOrchestrator with deterministic UUIDs)
- Up to 18 parallel task execution
- Real-time progress tracking
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.append("/home/opsvi/master_root/apps/chat-search")


class Phase1CompletionMonitor:
    """Monitor Phase 1 completion execution with support for multiple orchestrators"""

    def __init__(self):
        self.base_dir = Path("/home/opsvi/master_root/apps/project-context")

        # Output directories for different execution methods
        self.output_dirs = {
            "generic": self.base_dir / "phase1_completion_generic_output",
            "practical": self.base_dir / "phase1_completion_practical_output",
            "enhanced": self.base_dir / "phase1_completion_output",
            "original": self.base_dir / "phase1_execution_output",
        }

        # Claude session logs
        self.claude_logs_dir = Path.home() / ".claude" / "projects"

        # Phase 1 completion tasks
        self.completion_tasks = [
            "implement_chat_adapter",
            "implement_code_adapter",
            "integrate_with_mcp",
            "comprehensive_testing",
            "create_documentation",
        ]

    def generate_deterministic_uuid(
        self, task_id: str, plan_id: str = "practical"
    ) -> str:
        """Generate deterministic UUID for PracticalOrchestrator tasks"""
        import hashlib

        seed_string = f"{plan_id}-{task_id}-development-specialist"
        hash_obj = hashlib.md5(seed_string.encode())
        hex_str = hash_obj.hexdigest()
        return f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"

    def find_active_execution(self) -> Optional[Dict]:
        """Find currently running Phase 1 completion execution"""

        # Check for running processes
        import subprocess

        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)

            for line in result.stdout.split("\n"):
                if any(
                    script in line
                    for script in [
                        "execute_phase1_generic.py",
                        "execute_phase1_practical.py",
                        "execute_phase1_completion.py",
                    ]
                ):
                    parts = line.split()
                    if len(parts) >= 11:
                        return {
                            "pid": parts[1],
                            "script": parts[10],
                            "start_time": parts[8],
                            "status": "running",
                        }
        except Exception as e:
            print(f"⚠️  Could not check running processes: {e}")

        return None

    def get_task_status(self) -> Dict:
        """Get status of all Phase 1 completion tasks"""

        task_status = {}

        # Check all output directories
        for method, output_dir in self.output_dirs.items():
            if not output_dir.exists():
                continue

            tasks_dir = output_dir / "tasks"
            if not tasks_dir.exists():
                continue

            method_tasks = {}
            for task_id in self.completion_tasks:
                task_file = tasks_dir / f"{task_id}.json"

                if task_file.exists():
                    try:
                        with open(task_file) as f:
                            task_data = json.load(f)

                        method_tasks[task_id] = {
                            "status": task_data.get("status", "unknown"),
                            "start_time": task_data.get("start_time"),
                            "end_time": task_data.get("end_time"),
                            "duration": self._calculate_duration(
                                task_data.get("start_time"), task_data.get("end_time")
                            ),
                            "session_id": task_data.get("session_id"),
                            "error": task_data.get("error"),
                        }
                    except Exception as e:
                        method_tasks[task_id] = {"status": "error", "error": str(e)}
                else:
                    method_tasks[task_id] = {"status": "not_started"}

            if method_tasks:
                task_status[method] = method_tasks

        return task_status

    def _calculate_duration(self, start_time, end_time):
        """Calculate task duration in seconds"""
        if start_time and end_time:
            return end_time - start_time
        return None

    def get_session_activity(self, task_id: str) -> Dict:
        """Get recent activity for a task's session"""

        session_id = self.generate_deterministic_uuid(task_id)

        # Find session log file
        for project_dir in self.claude_logs_dir.glob("*"):
            if project_dir.is_dir():
                session_file = project_dir / f"{session_id}.jsonl"
                if session_file.exists():
                    try:
                        # Get file stats
                        stat = session_file.stat()
                        file_size = stat.st_size
                        last_modified = datetime.fromtimestamp(stat.st_mtime)

                        # Check if actively being written to
                        now = datetime.now()
                        active = (
                            now - last_modified
                        ).total_seconds() < 60  # Active if modified in last minute

                        # Get recent content
                        recent_lines = []
                        with open(session_file, "r") as f:
                            lines = f.readlines()
                            recent_lines = lines[-5:] if len(lines) >= 5 else lines

                        return {
                            "session_id": session_id,
                            "log_path": str(session_file),
                            "file_size": file_size,
                            "last_modified": last_modified.strftime("%H:%M:%S"),
                            "active": active,
                            "recent_activity": len(recent_lines) > 0,
                        }
                    except Exception as e:
                        return {"session_id": session_id, "error": str(e)}

        return {
            "session_id": session_id,
            "log_path": f"~/.claude/projects/.../{session_id}.jsonl",
            "status": "not_found",
        }

    def print_status_dashboard(self):
        """Print comprehensive status dashboard"""

        print("🔍 PHASE 1 COMPLETION MONITORING DASHBOARD")
        print("=" * 60)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Check for active execution
        active_execution = self.find_active_execution()
        if active_execution:
            print("🚀 ACTIVE EXECUTION DETECTED")
            print("-" * 30)
            print(f"   PID: {active_execution['pid']}")
            print(f"   Script: {active_execution['script']}")
            print(f"   Status: {active_execution['status']}")
            print()
        else:
            print("⏸️  NO ACTIVE EXECUTION DETECTED")
            print()

        # Task status across all methods
        task_status = self.get_task_status()

        if not task_status:
            print("📋 NO TASK RESULTS FOUND")
            print("   Run one of these to start execution:")
            print("   • python execute_phase1_generic.py")
            print("   • python execute_phase1_practical.py")
            return

        # Summary by execution method
        print("📊 TASK STATUS BY EXECUTION METHOD")
        print("-" * 40)

        for method, tasks in task_status.items():
            completed = len(
                [t for t in tasks.values() if t.get("status") == "completed"]
            )
            failed = len([t for t in tasks.values() if t.get("status") == "failed"])
            running = len([t for t in tasks.values() if t.get("status") == "running"])
            total = len(tasks)

            print(f"\n🔧 {method.upper()} METHOD:")
            print(f"   ✅ Completed: {completed}/{total}")
            print(f"   ❌ Failed: {failed}")
            print(f"   🔄 Running: {running}")

            if completed > 0 or failed > 0 or running > 0:
                print(f"   📁 Output: {self.output_dirs[method]}")

        # Detailed task breakdown
        print(f"\n📋 DETAILED TASK STATUS")
        print("-" * 30)

        for task_id in self.completion_tasks:
            print(f"\n📌 {task_id}")

            # Show status across methods
            task_found = False
            for method, tasks in task_status.items():
                if task_id in tasks:
                    task_info = tasks[task_id]
                    status = task_info.get("status", "unknown")
                    duration = task_info.get("duration")

                    status_icon = {
                        "completed": "✅",
                        "failed": "❌",
                        "running": "🔄",
                        "not_started": "⏸️",
                        "error": "💥",
                    }.get(status, "❓")

                    duration_str = f" ({duration:.1f}s)" if duration else ""
                    print(f"   {status_icon} {method}: {status}{duration_str}")

                    if task_info.get("error"):
                        print(f"      Error: {task_info['error'][:100]}...")

                    task_found = True

            if not task_found:
                print(f"   ⏸️  Not started")

            # Show session monitoring for PracticalOrchestrator
            session_info = self.get_session_activity(task_id)
            if session_info.get("session_id"):
                active_indicator = " 🔥" if session_info.get("active") else ""
                print(f"   📍 Session: {session_info['session_id']}{active_indicator}")
                print(f"   📂 Monitor: tail -f {session_info['log_path']}")

        print(f"\n💡 MONITORING COMMANDS")
        print("-" * 25)
        print("   Monitor all sessions:")
        for task_id in self.completion_tasks:
            session_id = self.generate_deterministic_uuid(task_id)
            print(f"   tail -f ~/.claude/projects/*/{session_id}.jsonl  # {task_id}")

    def watch_mode(self, refresh_seconds: int = 10):
        """Continuous monitoring mode"""
        print(f"👁️  WATCH MODE - Refreshing every {refresh_seconds} seconds")
        print("   Press Ctrl+C to exit")
        print()

        try:
            while True:
                # Clear screen
                os.system("clear" if os.name == "posix" else "cls")

                self.print_status_dashboard()

                print(f"\n🔄 Auto-refresh in {refresh_seconds}s... (Ctrl+C to exit)")
                time.sleep(refresh_seconds)

        except KeyboardInterrupt:
            print(f"\n👋 Monitoring stopped")


def main():
    """Main monitoring interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Phase 1 Completion Monitor")
    parser.add_argument(
        "--watch", action="store_true", help="Continuous monitoring mode"
    )
    parser.add_argument(
        "--refresh",
        type=int,
        default=10,
        help="Refresh interval in seconds (default: 10)",
    )
    parser.add_argument(
        "--status", action="store_true", help="Show current status once"
    )

    args = parser.parse_args()

    monitor = Phase1CompletionMonitor()

    if args.watch:
        monitor.watch_mode(args.refresh)
    else:
        monitor.print_status_dashboard()


if __name__ == "__main__":
    main()
