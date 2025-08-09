#!/usr/bin/env python3
"""
ACCF Log Monitor

This script monitors ACCF log files in real-time, showing the latest logs
and highlighting errors and warnings.
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Default log directory
LOG_DIR = Path("/tmp/accf_logs")

def get_latest_log_file():
    """Get the most recent log file."""
    if not LOG_DIR.exists():
        print(f"Log directory {LOG_DIR} does not exist")
        return None

    log_files = list(LOG_DIR.glob("*.log"))
    if not log_files:
        print(f"No log files found in {LOG_DIR}")
        return None

    # Sort by modification time, newest first
    latest = max(log_files, key=lambda f: f.stat().st_mtime)
    return latest

def monitor_logs(log_file: Path, lines: int = 50):
    """Monitor a log file in real-time."""
    print(f"Monitoring: {log_file}")
    print(f"Last {lines} lines:")
    print("-" * 80)

    try:
        # Show last N lines
        with open(log_file, 'r') as f:
            lines_list = f.readlines()
            for line in lines_list[-lines:]:
                print(line.rstrip())

        # Monitor for new lines
        print("\n" + "=" * 80)
        print("Monitoring for new log entries... (Ctrl+C to stop)")
        print("=" * 80)

        with open(log_file, 'r') as f:
            # Seek to end
            f.seek(0, 2)

            while True:
                line = f.readline()
                if line:
                    # Highlight errors and warnings
                    if "ERROR" in line:
                        print(f"\033[91m{line.rstrip()}\033[0m")  # Red
                    elif "WARNING" in line:
                        print(f"\033[93m{line.rstrip()}\033[0m")  # Yellow
                    else:
                        print(line.rstrip())
                else:
                    time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
    except Exception as e:
        print(f"Error monitoring logs: {e}")

def list_log_files():
    """List all available log files."""
    if not LOG_DIR.exists():
        print(f"Log directory {LOG_DIR} does not exist")
        return

    log_files = list(LOG_DIR.glob("*.log"))
    if not log_files:
        print(f"No log files found in {LOG_DIR}")
        return

    print(f"Available log files in {LOG_DIR}:")
    print("-" * 80)

    for log_file in sorted(log_files, key=lambda f: f.stat().st_mtime, reverse=True):
        stat = log_file.stat()
        size = stat.st_size
        mtime = datetime.fromtimestamp(stat.st_mtime)
        print(f"{log_file.name:<40} {size:>10} bytes  {mtime.strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main function."""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "list":
            list_log_files()
            return
        elif command == "monitor":
            log_file = get_latest_log_file()
            if log_file:
                lines = int(sys.argv[2]) if len(sys.argv) > 2 else 50
                monitor_logs(log_file, lines)
            return
        elif command == "tail":
            log_file = get_latest_log_file()
            if log_file:
                # Use system tail command for better performance
                subprocess.run(["tail", "-f", str(log_file)])
            return
        else:
            print(f"Unknown command: {command}")

    # Default: show latest log file
    log_file = get_latest_log_file()
    if log_file:
        print(f"Latest log file: {log_file}")
        print(f"Size: {log_file.stat().st_size} bytes")
        print(f"Modified: {datetime.fromtimestamp(log_file.stat().st_mtime)}")
        print()

        # Show last 20 lines
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-20:]:
                print(line.rstrip())

if __name__ == "__main__":
    main()
