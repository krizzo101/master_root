#!/usr/bin/env python3
"""
Code Generation Utility - Stop All Script (Python Version)
This script stops all code generation processes and related services
"""

import os
import subprocess
import time
import signal
import psutil


def is_running(pattern):
    """Check if a process is running using pgrep."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", pattern], capture_output=True, text=True
        )
        return result.returncode == 0
    except:
        return False


def kill_processes(pattern, name):
    """Kill processes with a pattern."""
    if is_running(pattern):
        print(f"  Stopping {name}...")
        try:
            subprocess.run(["pkill", "-f", pattern], capture_output=True, text=True)
            time.sleep(1)

            # Force kill if still running
            if is_running(pattern):
                print(f"  Force stopping {name}...")
                subprocess.run(
                    ["pkill", "-9", "-f", pattern], capture_output=True, text=True
                )
        except:
            pass
    else:
        print(f"  {name} is not running")


def check_port(port):
    """Check if a port is in use."""
    try:
        result = subprocess.run(
            ["lsof", "-i", f":{port}"], capture_output=True, text=True
        )
        return result.returncode == 0
    except:
        return False


def free_port(port):
    """Free a port by killing processes using it."""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"], capture_output=True, text=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                if pid:
                    subprocess.run(["kill", "-9", pid], capture_output=True, text=True)
    except:
        pass


def main():
    print("🛑 Stopping Code Generation Utility and all related processes...")

    # Stop main application processes
    print("📱 Stopping main application processes...")
    kill_processes("applications.code_gen.main", "Code Generation Main")
    kill_processes("start_with_logs.py", "Start Script")
    kill_processes("uvicorn.*applications.code_gen", "Uvicorn Server")

    # Stop Celery workers
    print("🐛 Stopping Celery workers...")
    kill_processes("celery.*applications.code_gen", "Celery Workers")
    kill_processes("celery.*task_queue", "Celery Task Queue")

    # Stop any Python processes related to code_gen
    print("🐍 Stopping Python processes...")
    kill_processes("python.*code_gen", "Python Code Gen")

    # Check for processes on common ports
    print("🔌 Checking for processes on common ports...")
    for port in [8010, 8000, 8001, 8002, 8003, 8004, 8005]:
        if check_port(port):
            print(f"  Port {port} is in use, attempting to free it...")
            free_port(port)

    # Final check
    print("🔍 Final status check...")
    time.sleep(2)

    # Check if any processes are still running
    if (
        is_running("applications.code_gen")
        or is_running("celery.*code_gen")
        or is_running("start_with_logs")
    ):
        print("⚠️  Some processes may still be running. You can manually check with:")
        print(
            "   ps aux | grep -E '(applications.code_gen|celery.*code_gen|start_with_logs)' | grep -v grep"
        )
    else:
        print("✅ All Code Generation processes have been stopped successfully!")

    # Show current status
    print("")
    print("📊 Current status:")
    print(
        f"  - Main app: {'RUNNING' if is_running('applications.code_gen.main') else 'STOPPED'}"
    )
    print(f"  - Celery: {'RUNNING' if is_running('celery.*code_gen') else 'STOPPED'}")
    print(f"  - Port 8010: {'IN USE' if check_port(8010) else 'FREE'}")

    print("")
    print("🎯 To restart the application, run:")
    print(
        "   cd /home/opsvi/agent_world && python src/applications/code_gen/start_with_logs.py"
    )
    print("")
    print("🌐 Available themes:")
    print("   - Default (Cyberpunk): http://localhost:8010")
    print("   - Original: http://localhost:8010/original")
    print("   - Holographic: http://localhost:8010/holographic")


if __name__ == "__main__":
    main()
