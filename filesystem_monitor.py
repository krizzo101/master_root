#!/usr/bin/env python3
import json
import os
import subprocess
import time
from collections import defaultdict
from datetime import datetime


class FileSystemMonitor:
    def __init__(self, root_path="/home/opsvi/master_root"):
        self.root_path = root_path
        self.baseline = {}
        self.activity_log = []
        self.directory_stats = defaultdict(int)

    def get_current_state(self):
        """Get current filesystem state"""
        state = {}
        for root, dirs, files in os.walk(self.root_path):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    stat = os.stat(filepath)
                    state[filepath] = {
                        "mtime": stat.st_mtime,
                        "size": stat.st_size,
                        "directory": root,
                    }
                except (OSError, FileNotFoundError):
                    continue
        return state

    def count_files_dirs(self):
        """Count files and directories in each subdirectory"""
        counts = {}
        for item in os.listdir(self.root_path):
            item_path = os.path.join(self.root_path, item)
            if os.path.isdir(item_path):
                try:
                    files = 0
                    dirs = 0
                    for root, dirnames, filenames in os.walk(item_path):
                        files += len(filenames)
                        dirs += len(dirnames)
                    counts[item] = {"files": files, "dirs": dirs}
                except PermissionError:
                    counts[item] = {"files": "N/A", "dirs": "N/A"}
        return counts

    def detect_changes(self, old_state, new_state):
        """Detect changes between two states"""
        changes = {
            "new_files": [],
            "modified_files": [],
            "deleted_files": [],
            "active_directories": set(),
        }

        # New files
        for filepath in new_state:
            if filepath not in old_state:
                changes["new_files"].append(filepath)
                changes["active_directories"].add(new_state[filepath]["directory"])

        # Modified files
        for filepath in new_state:
            if filepath in old_state:
                if new_state[filepath]["mtime"] > old_state[filepath]["mtime"]:
                    changes["modified_files"].append(filepath)
                    changes["active_directories"].add(new_state[filepath]["directory"])

        # Deleted files
        for filepath in old_state:
            if filepath not in new_state:
                changes["deleted_files"].append(filepath)

        return changes

    def run_monitoring_cycle(self, cycle_num):
        """Run a single monitoring cycle"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        current_state = self.get_current_state()

        if self.baseline:
            changes = self.detect_changes(self.baseline, current_state)

            # Count directory activity
            for directory in changes["active_directories"]:
                self.directory_stats[directory] += 1

            cycle_data = {
                "cycle": cycle_num,
                "timestamp": timestamp,
                "new_files_count": len(changes["new_files"]),
                "modified_files_count": len(changes["modified_files"]),
                "deleted_files_count": len(changes["deleted_files"]),
                "active_directories_count": len(changes["active_directories"]),
                "new_files": changes["new_files"][:5],  # Sample first 5
                "modified_files": changes["modified_files"][:5],  # Sample first 5
                "active_directories": list(changes["active_directories"]),
            }

            self.activity_log.append(cycle_data)

            print(f"\n=== Cycle {cycle_num} - {timestamp} ===")
            print(f"New files: {len(changes['new_files'])}")
            print(f"Modified files: {len(changes['modified_files'])}")
            print(f"Deleted files: {len(changes['deleted_files'])}")
            print(f"Active directories: {len(changes['active_directories'])}")

            if changes["new_files"]:
                print("Sample new files:")
                for f in changes["new_files"][:3]:
                    print(f"  + {f}")

            if changes["modified_files"]:
                print("Sample modified files:")
                for f in changes["modified_files"][:3]:
                    print(f"  ~ {f}")

            if changes["active_directories"]:
                print("Active directories:")
                for d in list(changes["active_directories"])[:3]:
                    print(f"  📁 {d}")

        self.baseline = current_state
        return len(current_state)


if __name__ == "__main__":
    monitor = FileSystemMonitor()

    print("🔍 Starting 5-minute filesystem monitoring...")
    print("📊 Will check every 30 seconds for 10 iterations")

    # Initial file/directory count
    initial_counts = monitor.count_files_dirs()
    print("\n📈 Initial directory statistics:")
    for dirname, counts in sorted(initial_counts.items())[:10]:
        print(f"  {dirname}: {counts['files']} files, {counts['dirs']} directories")

    # Run monitoring cycles
    for i in range(1, 11):
        total_files = monitor.run_monitoring_cycle(i)
        print(f"Total files tracked: {total_files}")

        if i < 10:
            print("⏳ Sleeping 30 seconds...")
            time.sleep(30)

    # Final summary
    print("\n" + "=" * 50)
    print("📋 FINAL SUMMARY")
    print("=" * 50)

    total_new = sum(cycle["new_files_count"] for cycle in monitor.activity_log)
    total_modified = sum(
        cycle["modified_files_count"] for cycle in monitor.activity_log
    )
    total_deleted = sum(cycle["deleted_files_count"] for cycle in monitor.activity_log)

    print(f"Total new files: {total_new}")
    print(f"Total modified files: {total_modified}")
    print(f"Total deleted files: {total_deleted}")

    print("\n🏆 Most active directories:")
    sorted_dirs = sorted(
        monitor.directory_stats.items(), key=lambda x: x[1], reverse=True
    )
    for directory, activity_count in sorted_dirs[:5]:
        print(f"  {activity_count} changes: {directory}")

    # Activity patterns
    if monitor.activity_log:
        avg_new_per_cycle = total_new / len(monitor.activity_log)
        avg_modified_per_cycle = total_modified / len(monitor.activity_log)

        print(f"\n📊 Activity patterns:")
        print(f"  Average new files per cycle: {avg_new_per_cycle:.1f}")
        print(f"  Average modified files per cycle: {avg_modified_per_cycle:.1f}")

    print("\n✅ Monitoring complete!")
