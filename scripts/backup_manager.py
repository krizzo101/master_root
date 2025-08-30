#!/usr/bin/env python3
"""
Project Backup Manager - Intelligent incremental backup system with retention policies
"""

import argparse
import fnmatch
import hashlib
import json
import logging
import os
import subprocess
import sys
import tarfile
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class BackupMetadata:
    """Metadata for a backup"""

    backup_id: str
    backup_type: str  # 'full', 'incremental', 'snapshot'
    timestamp: str
    base_backup_id: Optional[str]  # For incrementals, reference to base
    files_count: int
    total_size: int
    hash_manifest: str  # Path to hash manifest file
    exclude_patterns: List[str]
    project_path: str
    git_commit: Optional[str]
    git_branch: Optional[str]


class BackupManager:
    """Manages project backups with intelligent retention and incremental strategies"""

    # Default exclude patterns for development projects
    DEFAULT_EXCLUDES = [
        # Python
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".Python",
        "pip-log.txt",
        "pip-delete-this-directory.txt",
        ".venv",
        "venv/",
        "ENV/",
        "env/",
        ".env",
        "*.egg-info",
        "dist/",
        "build/",
        ".pytest_cache/",
        ".mypy_cache/",
        ".ruff_cache/",
        # JavaScript/Node
        "node_modules/",
        "npm-debug.log",
        "yarn-error.log",
        ".npm",
        ".yarn",
        ".pnp.js",
        ".pnp/",
        # Version Control
        ".git/",
        ".svn/",
        ".hg/",
        # IDE
        ".idea/",
        ".vscode/",
        "*.swp",
        "*.swo",
        "*~",
        ".DS_Store",
        # Build outputs
        "target/",
        "out/",
        "bin/",
        "obj/",
        # Large files
        "*.log",
        "*.sqlite",
        "*.db",
        # Temporary
        "tmp/",
        "temp/",
        "*.tmp",
        ".cache/",
        # Project specific
        ".proj-intel/",  # Can be regenerated
        "workspace/",
        "razer_workspace/",
        "*.tar.gz",
        "*.zip",
        "*.bak",
    ]

    def __init__(
        self, project_path: str, backup_dir: str, config_file: Optional[str] = None
    ):
        self.project_path = Path(project_path).resolve()
        self.backup_dir = Path(backup_dir).resolve()
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Setup directories
        self.full_backups_dir = self.backup_dir / "full"
        self.incremental_dir = self.backup_dir / "incremental"
        self.snapshots_dir = self.backup_dir / "snapshots"
        self.metadata_dir = self.backup_dir / "metadata"
        self.manifests_dir = self.backup_dir / "manifests"

        for dir in [
            self.full_backups_dir,
            self.incremental_dir,
            self.snapshots_dir,
            self.metadata_dir,
            self.manifests_dir,
        ]:
            dir.mkdir(exist_ok=True)

        # Load or create config
        self.config_file = (
            Path(config_file) if config_file else self.backup_dir / "backup_config.json"
        )
        self.config = self.load_config()

        # Setup logging
        self.setup_logging()

    def load_config(self) -> Dict:
        """Load or create backup configuration"""
        default_config = {
            "exclude_patterns": self.DEFAULT_EXCLUDES,
            "retention": {
                "full_backups_keep": 2,  # Number of full backups to keep
                "full_backup_interval_days": 7,  # Days between full backups
                "incremental_keep_days": 7,  # Keep incrementals for N days
                "snapshot_keep_hours": 48,  # Keep snapshots for N hours
                "monthly_archives_keep": 3,  # Keep N monthly archives
            },
            "compression": {
                "algorithm": "gzip",  # gzip, bz2, or xz
                "level": 6,  # 1-9, higher = better compression but slower
            },
            "deduplication": {
                "enabled": True,
                "block_size": 4096,  # Bytes for content hashing
            },
            "auto_backup": {
                "enabled": False,
                "snapshot_interval_minutes": 60,
                "incremental_time": "02:00",  # Daily at 2 AM
                "full_backup_day": "sunday",  # Weekly full backup day
            },
        }

        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                loaded_config = json.load(f)
                # Merge with defaults
                for key in default_config:
                    if key not in loaded_config:
                        loaded_config[key] = default_config[key]
                return loaded_config
        else:
            with open(self.config_file, "w") as f:
                json.dump(default_config, f, indent=2)
            return default_config

    def setup_logging(self):
        """Setup logging configuration"""
        log_file = self.backup_dir / "backup.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    def should_exclude(self, file_path: Path) -> bool:
        """Check if file should be excluded from backup"""
        relative_path = file_path.relative_to(self.project_path)
        path_str = str(relative_path)

        for pattern in self.config["exclude_patterns"]:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(
                f"{path_str}/", pattern
            ):
                return True
            # Check if any parent directory matches
            for parent in relative_path.parents:
                if fnmatch.fnmatch(str(parent), pattern.rstrip("/")):
                    return True
        return False

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except (IOError, OSError) as e:
            self.logger.warning(f"Could not hash {file_path}: {e}")
            return ""

    def create_manifest(self, backup_id: str) -> Tuple[Dict[str, str], str]:
        """Create a manifest of all files with their hashes"""
        manifest = {}
        manifest_path = self.manifests_dir / f"{backup_id}_manifest.json"

        self.logger.info("Creating file manifest...")
        for root, dirs, files in os.walk(self.project_path):
            root_path = Path(root)

            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not self.should_exclude(root_path / d)]

            for file in files:
                file_path = root_path / file
                if not self.should_exclude(file_path):
                    relative_path = file_path.relative_to(self.project_path)
                    file_hash = self.calculate_file_hash(file_path)
                    if file_hash:
                        manifest[str(relative_path)] = {
                            "hash": file_hash,
                            "size": file_path.stat().st_size,
                            "mtime": file_path.stat().st_mtime,
                        }

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        return manifest, str(manifest_path)

    def get_git_info(self) -> Tuple[Optional[str], Optional[str]]:
        """Get current git commit and branch"""
        try:
            commit = (
                subprocess.check_output(
                    ["git", "rev-parse", "HEAD"],
                    cwd=self.project_path,
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )

            branch = (
                subprocess.check_output(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=self.project_path,
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )

            return commit, branch
        except subprocess.CalledProcessError:
            return None, None

    def create_full_backup(self) -> BackupMetadata:
        """Create a full backup of the project"""
        timestamp = datetime.now()
        backup_id = f"full_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        backup_file = self.full_backups_dir / f"{backup_id}.tar.gz"

        self.logger.info(f"Creating full backup: {backup_id}")

        # Create manifest
        manifest, manifest_path = self.create_manifest(backup_id)

        # Get git info
        git_commit, git_branch = self.get_git_info()

        # Create tar archive
        with tarfile.open(backup_file, "w:gz") as tar:
            for file_path in manifest:
                full_path = self.project_path / file_path
                tar.add(full_path, arcname=file_path)

        # Calculate total size
        total_size = sum(info["size"] for info in manifest.values())

        # Create metadata
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type="full",
            timestamp=timestamp.isoformat(),
            base_backup_id=None,
            files_count=len(manifest),
            total_size=total_size,
            hash_manifest=manifest_path,
            exclude_patterns=self.config["exclude_patterns"],
            project_path=str(self.project_path),
            git_commit=git_commit,
            git_branch=git_branch,
        )

        # Save metadata
        metadata_file = self.metadata_dir / f"{backup_id}_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(asdict(metadata), f, indent=2)

        self.logger.info(
            f"Full backup completed: {len(manifest)} files, {total_size / 1024 / 1024:.2f} MB"
        )

        # Clean old backups
        self.cleanup_old_backups()

        return metadata

    def create_incremental_backup(
        self, base_backup_id: Optional[str] = None
    ) -> Optional[BackupMetadata]:
        """Create an incremental backup based on the last full backup"""
        # Find base backup
        if not base_backup_id:
            base_backup_id = self.get_latest_full_backup_id()

        if not base_backup_id:
            self.logger.warning("No base backup found, creating full backup instead")
            return self.create_full_backup()

        # Load base manifest
        base_manifest_path = self.manifests_dir / f"{base_backup_id}_manifest.json"
        if not base_manifest_path.exists():
            self.logger.error(f"Base manifest not found: {base_manifest_path}")
            return None

        with open(base_manifest_path, "r") as f:
            base_manifest = json.load(f)

        # Create current manifest
        timestamp = datetime.now()
        backup_id = f"incr_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        current_manifest, manifest_path = self.create_manifest(backup_id)

        # Find changed files
        changed_files = []
        new_files = []
        deleted_files = []

        for file_path, info in current_manifest.items():
            if file_path not in base_manifest:
                new_files.append(file_path)
            elif info["hash"] != base_manifest[file_path]["hash"]:
                changed_files.append(file_path)

        for file_path in base_manifest:
            if file_path not in current_manifest:
                deleted_files.append(file_path)

        total_changes = len(changed_files) + len(new_files) + len(deleted_files)

        if total_changes == 0:
            self.logger.info("No changes detected since last backup")
            return None

        self.logger.info(
            f"Creating incremental backup: {len(new_files)} new, "
            f"{len(changed_files)} modified, {len(deleted_files)} deleted"
        )

        # Create incremental backup
        backup_file = self.incremental_dir / f"{backup_id}.tar.gz"

        with tarfile.open(backup_file, "w:gz") as tar:
            # Add changed and new files
            for file_path in changed_files + new_files:
                full_path = self.project_path / file_path
                if full_path.exists():
                    tar.add(full_path, arcname=file_path)

        # Save change list
        changes_file = self.incremental_dir / f"{backup_id}_changes.json"
        with open(changes_file, "w") as f:
            json.dump(
                {
                    "new_files": new_files,
                    "changed_files": changed_files,
                    "deleted_files": deleted_files,
                },
                f,
                indent=2,
            )

        # Get git info
        git_commit, git_branch = self.get_git_info()

        # Calculate size of changed files
        total_size = sum(
            current_manifest[f]["size"]
            for f in changed_files + new_files
            if f in current_manifest
        )

        # Create metadata
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type="incremental",
            timestamp=timestamp.isoformat(),
            base_backup_id=base_backup_id,
            files_count=total_changes,
            total_size=total_size,
            hash_manifest=manifest_path,
            exclude_patterns=self.config["exclude_patterns"],
            project_path=str(self.project_path),
            git_commit=git_commit,
            git_branch=git_branch,
        )

        # Save metadata
        metadata_file = self.metadata_dir / f"{backup_id}_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(asdict(metadata), f, indent=2)

        self.logger.info(
            f"Incremental backup completed: {total_changes} changes, "
            f"{total_size / 1024 / 1024:.2f} MB"
        )

        # Clean old backups
        self.cleanup_old_backups()

        return metadata

    def create_snapshot(self) -> BackupMetadata:
        """Create a lightweight snapshot (similar to incremental but with shorter retention)"""
        # timestamp = datetime.now()
        # backup_id = f"snap_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        # Currently unused - using incremental instead

        # Find the most recent backup (full or incremental)
        latest_backup = self.get_latest_backup_id()

        if not latest_backup:
            self.logger.info("No previous backup found, creating full backup instead")
            return self.create_full_backup()

        # Create as incremental with snapshot prefix
        return self.create_incremental_backup(latest_backup)

    def get_latest_full_backup_id(self) -> Optional[str]:
        """Get the ID of the most recent full backup"""
        full_backups = sorted(
            [f.stem for f in self.full_backups_dir.glob("full_*.tar.gz")], reverse=True
        )

        return full_backups[0] if full_backups else None

    def get_latest_backup_id(self) -> Optional[str]:
        """Get the ID of the most recent backup of any type"""
        all_backups = []

        # Collect all backup IDs with timestamps
        for backup_dir, prefix in [
            (self.full_backups_dir, "full_"),
            (self.incremental_dir, "incr_"),
            (self.snapshots_dir, "snap_"),
        ]:
            for f in backup_dir.glob(f"{prefix}*.tar.gz"):
                all_backups.append(f.stem)

        all_backups.sort(reverse=True)
        return all_backups[0] if all_backups else None

    def cleanup_old_backups(self):
        """Remove old backups according to retention policy"""
        retention = self.config["retention"]
        now = datetime.now()

        # Clean old full backups (keep N most recent)
        full_backups = sorted(
            [f for f in self.full_backups_dir.glob("full_*.tar.gz")],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        for backup in full_backups[retention["full_backups_keep"] :]:
            self.logger.info(f"Removing old full backup: {backup.name}")
            backup.unlink()
            # Also remove associated metadata and manifest
            backup_id = backup.stem
            (self.metadata_dir / f"{backup_id}_metadata.json").unlink(missing_ok=True)
            (self.manifests_dir / f"{backup_id}_manifest.json").unlink(missing_ok=True)

        # Clean old incrementals
        incremental_cutoff = now - timedelta(days=retention["incremental_keep_days"])
        for backup in self.incremental_dir.glob("incr_*.tar.gz"):
            if backup.stat().st_mtime < incremental_cutoff.timestamp():
                self.logger.info(f"Removing old incremental: {backup.name}")
                backup.unlink()
                backup_id = backup.stem
                (self.metadata_dir / f"{backup_id}_metadata.json").unlink(
                    missing_ok=True
                )
                (self.manifests_dir / f"{backup_id}_manifest.json").unlink(
                    missing_ok=True
                )
                (self.incremental_dir / f"{backup_id}_changes.json").unlink(
                    missing_ok=True
                )

        # Clean old snapshots
        snapshot_cutoff = now - timedelta(hours=retention["snapshot_keep_hours"])
        for backup in self.snapshots_dir.glob("snap_*.tar.gz"):
            if backup.stat().st_mtime < snapshot_cutoff.timestamp():
                self.logger.info(f"Removing old snapshot: {backup.name}")
                backup.unlink()
                backup_id = backup.stem
                (self.metadata_dir / f"{backup_id}_metadata.json").unlink(
                    missing_ok=True
                )
                (self.manifests_dir / f"{backup_id}_manifest.json").unlink(
                    missing_ok=True
                )

    def restore_backup(self, backup_id: str, restore_path: Optional[str] = None):
        """Restore a backup to specified path or original location"""
        if not restore_path:
            restore_path = (
                self.project_path.parent
                / f"{self.project_path.name}_restored_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

        restore_path = Path(restore_path)
        restore_path.mkdir(parents=True, exist_ok=True)

        # Load metadata
        metadata_file = self.metadata_dir / f"{backup_id}_metadata.json"
        if not metadata_file.exists():
            self.logger.error(f"Metadata not found for backup: {backup_id}")
            return False

        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        self.logger.info(f"Restoring backup {backup_id} to {restore_path}")

        if metadata["backup_type"] == "full":
            # Simple full restore
            backup_file = self.full_backups_dir / f"{backup_id}.tar.gz"
            with tarfile.open(backup_file, "r:gz") as tar:
                # Security fix: validate members before extraction
                for member in tar.getmembers():
                    if member.name.startswith(("/", "..")) or ".." in member.name:
                        raise ValueError(f"Unsafe path: {member.name}")
                tar.extractall(restore_path)  # nosec B202 - validated above
        else:
            # Incremental restore - need to restore base first
            base_backup_id = metadata["base_backup_id"]
            if base_backup_id:
                self.logger.info(f"Restoring base backup first: {base_backup_id}")
                self.restore_backup(base_backup_id, restore_path)

            # Apply incremental changes
            backup_file = self.incremental_dir / f"{backup_id}.tar.gz"
            if backup_file.exists():
                with tarfile.open(backup_file, "r:gz") as tar:
                    # Security fix: validate members before extraction
                    for member in tar.getmembers():
                        if member.name.startswith(("/", "..")) or ".." in member.name:
                            raise ValueError(f"Unsafe path: {member.name}")
                    tar.extractall(restore_path)  # nosec B202 - validated above

            # Handle deleted files
            changes_file = self.incremental_dir / f"{backup_id}_changes.json"
            if changes_file.exists():
                with open(changes_file, "r") as f:
                    changes = json.load(f)
                    for deleted_file in changes.get("deleted_files", []):
                        file_to_delete = restore_path / deleted_file
                        if file_to_delete.exists():
                            file_to_delete.unlink()
                            self.logger.info(f"Removed deleted file: {deleted_file}")

        self.logger.info(f"Restore completed to {restore_path}")
        return True

    def list_backups(self) -> List[Dict]:
        """List all available backups with their metadata"""
        backups = []

        for metadata_file in sorted(
            self.metadata_dir.glob("*_metadata.json"), reverse=True
        ):
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
                backups.append(metadata)

        return backups

    def verify_backup(self, backup_id: str) -> bool:
        """Verify integrity of a backup"""
        self.logger.info(f"Verifying backup: {backup_id}")

        # Load manifest
        manifest_file = self.manifests_dir / f"{backup_id}_manifest.json"
        if not manifest_file.exists():
            self.logger.error(f"Manifest not found: {manifest_file}")
            return False

        # Check if backup file exists
        for backup_dir in [
            self.full_backups_dir,
            self.incremental_dir,
            self.snapshots_dir,
        ]:
            backup_file = backup_dir / f"{backup_id}.tar.gz"
            if backup_file.exists():
                try:
                    with tarfile.open(backup_file, "r:gz") as tar:
                        tar.getmembers()  # Test read
                    self.logger.info(f"Backup {backup_id} verified successfully")
                    return True
                except tarfile.TarError as e:
                    self.logger.error(f"Backup {backup_id} is corrupted: {e}")
                    return False

        self.logger.error(f"Backup file not found for {backup_id}")
        return False

    def auto_backup(self):
        """Determine and execute appropriate backup based on schedule"""
        now = datetime.now()

        # Check if it's time for a full backup
        latest_full = self.get_latest_full_backup_id()
        if latest_full:
            # Parse timestamp from backup ID
            timestamp_str = latest_full.replace("full_", "")
            last_full_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            days_since_full = (now - last_full_date).days

            if days_since_full >= self.config["retention"]["full_backup_interval_days"]:
                self.create_full_backup()
            else:
                self.create_incremental_backup()
        else:
            # No full backup exists, create one
            self.create_full_backup()


def main():
    parser = argparse.ArgumentParser(description="Project Backup Manager")
    parser.add_argument("project_path", help="Path to project to backup")
    parser.add_argument(
        "--backup-dir", default="./backups", help="Directory to store backups"
    )
    parser.add_argument("--config", help="Path to config file")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Backup commands
    backup_parser = subparsers.add_parser("backup", help="Create backup")
    backup_parser.add_argument(
        "--type",
        choices=["auto", "full", "incremental", "snapshot"],
        default="auto",
        help="Backup type",
    )

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore backup")
    restore_parser.add_argument("backup_id", help="Backup ID to restore")
    restore_parser.add_argument("--to", help="Path to restore to")

    # List command
    list_parser = subparsers.add_parser("list", help="List backups")
    list_parser.add_argument(
        "--detailed", action="store_true", help="Show detailed info"
    )

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify backup integrity")
    verify_parser.add_argument("backup_id", help="Backup ID to verify")

    # Clean command
    subparsers.add_parser("clean", help="Clean old backups")

    args = parser.parse_args()

    # Initialize backup manager
    manager = BackupManager(args.project_path, args.backup_dir, args.config)

    if args.command == "backup":
        if args.type == "auto":
            manager.auto_backup()
        elif args.type == "full":
            manager.create_full_backup()
        elif args.type == "incremental":
            manager.create_incremental_backup()
        elif args.type == "snapshot":
            manager.create_snapshot()

    elif args.command == "restore":
        manager.restore_backup(args.backup_id, args.to)

    elif args.command == "list":
        backups = manager.list_backups()
        for backup in backups:
            if args.detailed:
                print(json.dumps(backup, indent=2))
            else:
                print(
                    f"{backup['backup_id']} - {backup['backup_type']} - "
                    f"{backup['timestamp']} - {backup['files_count']} files"
                )

    elif args.command == "verify":
        if manager.verify_backup(args.backup_id):
            print(f"Backup {args.backup_id} is valid")
        else:
            print(f"Backup {args.backup_id} is corrupted or missing")
            sys.exit(1)

    elif args.command == "clean":
        manager.cleanup_old_backups()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
