#!/usr/bin/env python3
"""
Monitor Sleuth Intel Implementation Progress
"""

import json
import time
from pathlib import Path


def monitor_progress():
    """Monitor the orchestrator implementation progress"""

    impl_dir = Path("sleuth_intel_implementation")
    if not impl_dir.exists():
        print("❌ Implementation directory not found")
        return

    print("🕵️  Sleuth Intel Implementation Monitor")
    print("=" * 50)

    # Check for completion metrics
    metrics_file = impl_dir / "metrics.json"
    if metrics_file.exists():
        with open(metrics_file) as f:
            metrics = json.load(f)

        print(
            f"📊 Progress: {metrics.get('completed', 0)}/{metrics.get('total', 0)} tasks"
        )
        print(f"⏱️  Duration: {metrics.get('total_duration', 'In progress...')}")
        print(f"✅ Success Rate: {metrics.get('success_rate', 0):.1f}%")

        if metrics.get("completed") == metrics.get("total"):
            print("\n🎉 IMPLEMENTATION COMPLETE!")
            return True

    # Check task progress
    tasks_dir = impl_dir / "tasks"
    if tasks_dir.exists():
        completed_tasks = list(tasks_dir.glob("*.json"))
        print(f"📋 Task Files Created: {len(completed_tasks)}")

        # Show recent completions
        if completed_tasks:
            print("\n📁 Recent Task Completions:")
            for task_file in sorted(completed_tasks, key=lambda x: x.stat().st_mtime)[
                -5:
            ]:
                task_name = task_file.stem
                mtime = task_file.stat().st_mtime
                print(f"   ✓ {task_name} ({time.ctime(mtime)})")

    # Check logs
    log_dir = impl_dir / "logs"
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        if log_files:
            latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
            print(f"\n📝 Latest Log: {latest_log.name}")

            # Show last few lines
            with open(latest_log, "r") as f:
                lines = f.readlines()
                if lines:
                    print("   Recent activity:")
                    for line in lines[-3:]:
                        if line.strip():
                            print(f"   {line.strip()}")

    print()
    return False


def show_created_structure():
    """Show the project structure being created"""

    print("🏗️  Project Structure Being Created:")
    print("-" * 40)

    # Check main source directory
    src_dir = Path("src")
    if src_dir.exists():
        print("📂 src/")
        for item in sorted(src_dir.rglob("*")):
            if item.is_file():
                rel_path = str(item.relative_to(Path(".")))
                size = item.stat().st_size
                print(f"   📄 {rel_path} ({size:,} bytes)")
            elif item.is_dir() and item != src_dir:
                rel_path = str(item.relative_to(Path(".")))
                print(f"   📁 {rel_path}/")

    # Check other directories
    for dir_name in ["tests", "examples", "config", "docs"]:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"📂 {dir_name}/")
            files = list(dir_path.glob("*"))
            print(f"   ({len(files)} files)")


if __name__ == "__main__":
    while True:
        try:
            complete = monitor_progress()
            show_created_structure()

            if complete:
                break

            print("⏳ Monitoring continues... (Ctrl+C to stop)")
            time.sleep(30)  # Check every 30 seconds

        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")
            break
        except Exception as e:
            print(f"❌ Monitor error: {e}")
            time.sleep(5)
