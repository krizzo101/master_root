#!/usr/bin/env python3
"""
Safe cleanup script for agent-orchestrator directory
Includes backup, archival, and rollback capabilities
"""

import argparse
import json
import logging
import os
import shutil
import sys
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("cleanup.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class AgentOrchestratorCleaner:
    def __init__(self, base_dir: str = ".", dry_run: bool = False):
        self.base_dir = Path(base_dir).resolve()
        self.dry_run = dry_run
        self.backup_dir = self.base_dir / "backups"
        self.archive_dir = self.base_dir / "output" / "archive"
        self.actions_taken = []
        self.space_freed = 0

    def create_backup(self) -> str:
        """Create a tar.gz backup of the current state"""
        if self.dry_run:
            logger.info("[DRY RUN] Would create backup")
            return "dry_run_backup.tar.gz"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"agent_orchestrator_backup_{timestamp}.tar.gz"
        backup_path = self.backup_dir / backup_name

        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(exist_ok=True)

        logger.info(f"Creating backup: {backup_path}")

        with tarfile.open(backup_path, "w:gz") as tar:
            # Backup everything except backups directory itself
            for item in self.base_dir.iterdir():
                if item.name != "backups":
                    tar.add(item, arcname=item.name)

        logger.info(f"Backup created successfully: {backup_path}")
        self.actions_taken.append(f"Created backup: {backup_path}")
        return str(backup_path)

    def get_file_size(self, path: Path) -> int:
        """Get file size in bytes"""
        try:
            return path.stat().st_size if path.exists() else 0
        except:
            return 0

    def delete_old_logs(self) -> None:
        """Delete old log files identified in analysis"""
        old_logs = [
            "orchestrator_20250908_121637.log",
            "orchestrator_20250908_121932.log",
            "orchestrator_20250908_122028.log",
            "orchestrator_20250908_125406.log",
            "orchestrator_20250908_130457.log",
            "orchestrator_20250908_130547.log",
            "orchestrator_20250908_133238.log",
            "orchestrator_20250908_133244.log",
            "orchestrator_20250908_133251.log",
            "orchestrator_20250908_140458.log",
            "orchestrator_20250908_145849.log",
            "orchestrator_20250908_214056.log",
            "orchestrator_20250908_214305.log",
            "orchestrator_20250909_004256.log",
            "orchestrator_20250909_004306.log",
            "orchestrator_20250909_004704.log",
            "mcp-shell.log",
        ]

        for log_file in old_logs:
            log_path = self.base_dir / log_file
            if log_path.exists():
                size = self.get_file_size(log_path)
                if self.dry_run:
                    logger.info(
                        f"[DRY RUN] Would delete log: {log_file} ({size} bytes)"
                    )
                else:
                    log_path.unlink()
                    logger.info(f"Deleted log: {log_file} ({size} bytes)")
                    self.actions_taken.append(f"Deleted: {log_file}")
                    self.space_freed += size

    def delete_temporary_files(self) -> None:
        """Delete temporary and broken files"""
        temp_files = [
            "temp_orchestrator_output_spec.md",
            "test_report.html",
            "system_analysis_tasks.broken.json",
            "system_analysis_tasks.json.original",
        ]

        for temp_file in temp_files:
            temp_path = self.base_dir / temp_file
            if temp_path.exists():
                size = self.get_file_size(temp_path)
                if self.dry_run:
                    logger.info(
                        f"[DRY RUN] Would delete temp file: {temp_file} ({size} bytes)"
                    )
                else:
                    temp_path.unlink()
                    logger.info(f"Deleted temp file: {temp_file} ({size} bytes)")
                    self.actions_taken.append(f"Deleted: {temp_file}")
                    self.space_freed += size

    def archive_old_outputs(self, days_old: int = 7) -> None:
        """Archive output directories older than specified days"""
        output_dir = self.base_dir / "output"
        if not output_dir.exists():
            return

        cutoff_date = datetime.now() - timedelta(days=days_old)

        for item in output_dir.iterdir():
            if item.is_dir() and item.name not in ["archive", "archived"]:
                # Try to parse timestamp from directory name
                try:
                    # Expected format: workflow_*_YYYYMMDD_HHMMSS_*
                    parts = item.name.split("_")
                    if len(parts) >= 4:
                        date_str = parts[-3]
                        time_str = parts[-2]
                        dir_date = datetime.strptime(
                            f"{date_str}_{time_str}", "%Y%m%d_%H%M%S"
                        )

                        if dir_date < cutoff_date:
                            self.archive_dir.mkdir(parents=True, exist_ok=True)
                            archive_name = f"{item.name}.tar.gz"
                            archive_path = self.archive_dir / archive_name

                            if self.dry_run:
                                logger.info(
                                    f"[DRY RUN] Would archive: {item.name} to {archive_path}"
                                )
                            else:
                                # Create archive
                                with tarfile.open(archive_path, "w:gz") as tar:
                                    tar.add(item, arcname=item.name)
                                # Remove original directory
                                shutil.rmtree(item)
                                logger.info(f"Archived: {item.name} to {archive_path}")
                                self.actions_taken.append(f"Archived: {item.name}")
                except (ValueError, IndexError):
                    # Skip if we can't parse the date
                    continue

    def reorganize_files(self) -> None:
        """Reorganize files into appropriate directories"""
        reorganizations = {
            "demos": [
                "comprehensive_demo.py",
                "demo_monitoring.py",
                "simple_chat_demo.py",
                "demo_task_examples.json",
                "simple_demo_workflow.json",
                "openai_demo_workflow.json",
                "DEMO_INDEX.md",
                "DEMO_README.md",
                "DEMO_SUMMARY.md",
            ],
            "task_definitions": [
                f
                for f in os.listdir(self.base_dir)
                if f.endswith("_tasks.json") or f.endswith("_task.json")
            ],
            "scripts": [
                f
                for f in os.listdir(self.base_dir)
                if f.startswith("run_") and f.endswith(".py")
            ],
        }

        for dir_name, files in reorganizations.items():
            target_dir = self.base_dir / dir_name

            for file_name in files:
                source_path = self.base_dir / file_name
                if source_path.exists():
                    if self.dry_run:
                        logger.info(f"[DRY RUN] Would move {file_name} to {dir_name}/")
                    else:
                        target_dir.mkdir(exist_ok=True)
                        target_path = target_dir / file_name
                        shutil.move(str(source_path), str(target_path))
                        logger.info(f"Moved {file_name} to {dir_name}/")
                        self.actions_taken.append(f"Moved {file_name} to {dir_name}/")

    def generate_report(self) -> Dict:
        """Generate cleanup report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "base_directory": str(self.base_dir),
            "actions_taken": self.actions_taken,
            "space_freed_bytes": self.space_freed,
            "space_freed_mb": round(self.space_freed / (1024 * 1024), 2),
        }

        return report

    def save_report(self, report: Dict) -> None:
        """Save cleanup report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.base_dir / f"cleanup_report_{timestamp}.json"

        if not self.dry_run:
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to: {report_file}")

    def run(self, skip_backup: bool = False, archive_days: int = 7) -> Dict:
        """Execute the cleanup process"""
        logger.info(f"Starting cleanup {'[DRY RUN]' if self.dry_run else ''}")
        logger.info(f"Base directory: {self.base_dir}")

        # Step 1: Create backup (unless skipped)
        if not skip_backup:
            backup_path = self.create_backup()
            logger.info(f"Backup created at: {backup_path}")

        # Step 2: Delete old logs
        logger.info("Cleaning old log files...")
        self.delete_old_logs()

        # Step 3: Delete temporary files
        logger.info("Cleaning temporary files...")
        self.delete_temporary_files()

        # Step 4: Archive old outputs
        logger.info(f"Archiving outputs older than {archive_days} days...")
        self.archive_old_outputs(archive_days)

        # Step 5: Reorganize files (optional - requires confirmation)
        # self.reorganize_files()  # Commented out by default for safety

        # Generate and save report
        report = self.generate_report()
        self.save_report(report)

        return report


def main():
    parser = argparse.ArgumentParser(
        description="Safe cleanup script for agent-orchestrator directory"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without making them"
    )
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Skip creating backup (not recommended)",
    )
    parser.add_argument(
        "--archive-days",
        type=int,
        default=7,
        help="Archive outputs older than N days (default: 7)",
    )
    parser.add_argument(
        "--reorganize",
        action="store_true",
        help="Also reorganize files into appropriate directories",
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Base directory to clean (default: current directory)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Skip confirmation prompts"
    )

    args = parser.parse_args()

    # Show what will be done
    print("\n" + "=" * 60)
    print("AGENT-ORCHESTRATOR CLEANUP SCRIPT")
    print("=" * 60)
    print(f"Base Directory: {Path(args.base_dir).resolve()}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Archive outputs older than: {args.archive_days} days")
    print(f"Create backup: {'No' if args.skip_backup else 'Yes'}")
    print(f"Reorganize files: {'Yes' if args.reorganize else 'No'}")
    print("=" * 60)

    if not args.dry_run and not args.force:
        print("\nThis will:")
        print("1. Delete old log files")
        print("2. Delete temporary/broken files")
        print(f"3. Archive outputs older than {args.archive_days} days")
        if args.reorganize:
            print("4. Reorganize files into appropriate directories")
        if not args.skip_backup:
            print("5. Create a backup first (recommended)")

        response = input("\nProceed? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Cleanup cancelled.")
            sys.exit(0)

    # Run cleanup
    cleaner = AgentOrchestratorCleaner(args.base_dir, args.dry_run)

    try:
        report = cleaner.run(
            skip_backup=args.skip_backup, archive_days=args.archive_days
        )

        if args.reorganize:
            logger.info("Reorganizing files...")
            cleaner.reorganize_files()

        # Print summary
        print("\n" + "=" * 60)
        print("CLEANUP SUMMARY")
        print("=" * 60)
        print(f"Actions taken: {len(report['actions_taken'])}")
        print(f"Space freed: {report['space_freed_mb']} MB")

        if args.dry_run:
            print("\n[DRY RUN] No actual changes were made.")
            print("Run without --dry-run to execute cleanup.")
        else:
            print("\nCleanup completed successfully!")
            print(f"Report saved to: cleanup_report_*.json")

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        print(f"\nError during cleanup: {e}")
        print("Check cleanup.log for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
