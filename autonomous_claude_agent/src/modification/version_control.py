"""
Version Control Integration for Self-Modification System

Provides Git integration for versioning code modifications
with rollback capabilities and change tracking.

Created: 2025-08-15
"""

import os
import subprocess
import tempfile
import shutil
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
import difflib


@dataclass
class ModificationVersion:
    """Version of a code modification"""
    version_id: str
    timestamp: datetime
    description: str
    files_modified: List[str]
    commit_hash: Optional[str] = None
    parent_version: Optional[str] = None
    changes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    rollback_point: bool = False
    
    def get_summary(self) -> str:
        """Get summary of version"""
        return (f"Version {self.version_id[:8]} - {self.description}\n"
                f"Modified: {len(self.files_modified)} files\n"
                f"Timestamp: {self.timestamp.isoformat()}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModificationVersion':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ChangeTracker:
    """Track changes between versions"""
    added_lines: int = 0
    removed_lines: int = 0
    modified_files: List[str] = field(default_factory=list)
    added_files: List[str] = field(default_factory=list)
    removed_files: List[str] = field(default_factory=list)
    change_summary: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    def add_file_changes(self, filepath: str, added: int, removed: int):
        """Add changes for a file"""
        self.added_lines += added
        self.removed_lines += removed
        
        if filepath not in self.change_summary:
            self.change_summary[filepath] = {'added': 0, 'removed': 0}
        
        self.change_summary[filepath]['added'] += added
        self.change_summary[filepath]['removed'] += removed
    
    def get_stats(self) -> Dict[str, Any]:
        """Get change statistics"""
        return {
            'total_added': self.added_lines,
            'total_removed': self.removed_lines,
            'net_change': self.added_lines - self.removed_lines,
            'files_modified': len(self.modified_files),
            'files_added': len(self.added_files),
            'files_removed': len(self.removed_files),
            'change_summary': self.change_summary
        }


class RollbackManager:
    """Manage rollback operations"""
    
    def __init__(self, repo_path: Path):
        """Initialize rollback manager"""
        self.repo_path = repo_path
        self.rollback_points: List[ModificationVersion] = []
        self.rollback_history: List[Dict[str, Any]] = []
    
    def create_rollback_point(self, version: ModificationVersion, 
                             force: bool = False) -> bool:
        """Create a rollback point"""
        version.rollback_point = True
        self.rollback_points.append(version)
        
        # Create git tag for rollback point
        if version.commit_hash:
            try:
                subprocess.run(
                    ['git', 'tag', f'rollback_{version.version_id[:8]}', version.commit_hash],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True
                )
                return True
            except subprocess.CalledProcessError:
                if force:
                    # Force create tag
                    subprocess.run(
                        ['git', 'tag', '-f', f'rollback_{version.version_id[:8]}', version.commit_hash],
                        cwd=self.repo_path,
                        check=True,
                        capture_output=True
                    )
                    return True
                return False
        return False
    
    def rollback_to_version(self, version_id: str, 
                           create_backup: bool = True) -> Tuple[bool, str]:
        """Rollback to a specific version"""
        # Find version
        version = None
        for v in self.rollback_points:
            if v.version_id.startswith(version_id):
                version = v
                break
        
        if not version:
            return False, f"Version {version_id} not found in rollback points"
        
        # Create backup if requested
        if create_backup:
            backup_result = self._create_backup()
            if not backup_result[0]:
                return False, f"Failed to create backup: {backup_result[1]}"
        
        # Perform rollback
        try:
            # Check current status
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                # Stash current changes
                subprocess.run(
                    ['git', 'stash', 'push', '-m', f'Rollback stash {datetime.now().isoformat()}'],
                    cwd=self.repo_path,
                    check=True
                )
            
            # Checkout version
            if version.commit_hash:
                subprocess.run(
                    ['git', 'checkout', version.commit_hash],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True
                )
            else:
                # Use tag
                subprocess.run(
                    ['git', 'checkout', f'rollback_{version.version_id[:8]}'],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True
                )
            
            # Record rollback
            self.rollback_history.append({
                'timestamp': datetime.now().isoformat(),
                'rolled_back_to': version.version_id,
                'description': f"Rolled back to: {version.description}"
            })
            
            return True, f"Successfully rolled back to version {version.version_id[:8]}"
            
        except subprocess.CalledProcessError as e:
            return False, f"Rollback failed: {str(e)}"
    
    def _create_backup(self) -> Tuple[bool, str]:
        """Create backup of current state"""
        try:
            # Create backup branch
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            subprocess.run(
                ['git', 'checkout', '-b', backup_name],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            # Commit current state
            subprocess.run(
                ['git', 'add', '-A'],
                cwd=self.repo_path,
                check=True
            )
            
            subprocess.run(
                ['git', 'commit', '-m', f'Backup before rollback'],
                cwd=self.repo_path,
                capture_output=True
            )
            
            # Return to previous branch
            subprocess.run(
                ['git', 'checkout', '-'],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            return True, backup_name
            
        except subprocess.CalledProcessError as e:
            return False, str(e)
    
    def list_rollback_points(self) -> List[Dict[str, Any]]:
        """List available rollback points"""
        points = []
        for version in self.rollback_points:
            points.append({
                'version_id': version.version_id[:8],
                'description': version.description,
                'timestamp': version.timestamp.isoformat(),
                'files_modified': len(version.files_modified),
                'commit': version.commit_hash[:8] if version.commit_hash else None
            })
        return points


class VersionController:
    """Main version control system for code modifications"""
    
    def __init__(self, repo_path: Optional[Path] = None,
                 auto_commit: bool = True,
                 branch_name: Optional[str] = None):
        """Initialize version controller"""
        self.repo_path = repo_path or Path.cwd()
        self.auto_commit = auto_commit
        self.branch_name = branch_name or "auto_modifications"
        
        self.versions: List[ModificationVersion] = []
        self.current_version: Optional[ModificationVersion] = None
        self.change_tracker = ChangeTracker()
        self.rollback_manager = RollbackManager(self.repo_path)
        
        # Initialize or verify git repo
        self._initialize_git()
        
        # Load version history
        self._load_version_history()
    
    def _initialize_git(self):
        """Initialize git repository if needed"""
        if not (self.repo_path / '.git').exists():
            subprocess.run(
                ['git', 'init'],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            # Initial commit
            gitignore_path = self.repo_path / '.gitignore'
            if not gitignore_path.exists():
                gitignore_path.write_text('*.pyc\n__pycache__/\n.pytest_cache/\n')
            
            subprocess.run(
                ['git', 'add', '.gitignore'],
                cwd=self.repo_path,
                check=True
            )
            
            subprocess.run(
                ['git', 'commit', '-m', 'Initial commit'],
                cwd=self.repo_path,
                capture_output=True
            )
    
    def _load_version_history(self):
        """Load version history from git log and metadata"""
        versions_file = self.repo_path / '.modification_versions.json'
        
        if versions_file.exists():
            with open(versions_file, 'r') as f:
                data = json.load(f)
                for version_data in data:
                    version = ModificationVersion.from_dict(version_data)
                    self.versions.append(version)
                    if version.rollback_point:
                        self.rollback_manager.rollback_points.append(version)
    
    def _save_version_history(self):
        """Save version history to file"""
        versions_file = self.repo_path / '.modification_versions.json'
        
        data = [v.to_dict() for v in self.versions]
        
        with open(versions_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_version(self, description: str,
                      files_modified: List[str],
                      changes: Optional[Dict[str, Any]] = None,
                      auto_commit: Optional[bool] = None) -> ModificationVersion:
        """Create a new version for modifications"""
        # Generate version ID
        version_id = hashlib.sha256(
            f"{description}{datetime.now().isoformat()}".encode()
        ).hexdigest()
        
        # Create version
        version = ModificationVersion(
            version_id=version_id,
            timestamp=datetime.now(),
            description=description,
            files_modified=files_modified,
            parent_version=self.current_version.version_id if self.current_version else None,
            changes=changes or {},
            metadata={
                'branch': self._get_current_branch(),
                'author': self._get_git_config('user.name', 'autonomous_agent')
            }
        )
        
        # Auto-commit if enabled
        if auto_commit if auto_commit is not None else self.auto_commit:
            commit_hash = self._commit_version(version)
            version.commit_hash = commit_hash
        
        # Update tracking
        self.versions.append(version)
        self.current_version = version
        
        # Save history
        self._save_version_history()
        
        return version
    
    def _commit_version(self, version: ModificationVersion) -> Optional[str]:
        """Commit version to git"""
        try:
            # Check if on correct branch
            current_branch = self._get_current_branch()
            if current_branch != self.branch_name:
                # Create or checkout branch
                try:
                    subprocess.run(
                        ['git', 'checkout', '-b', self.branch_name],
                        cwd=self.repo_path,
                        check=True,
                        capture_output=True
                    )
                except subprocess.CalledProcessError:
                    # Branch exists, just checkout
                    subprocess.run(
                        ['git', 'checkout', self.branch_name],
                        cwd=self.repo_path,
                        check=True,
                        capture_output=True
                    )
            
            # Stage modified files
            for filepath in version.files_modified:
                file_path = self.repo_path / filepath
                if file_path.exists():
                    subprocess.run(
                        ['git', 'add', filepath],
                        cwd=self.repo_path,
                        check=True
                    )
            
            # Create commit message
            commit_message = f"[Auto-Modification] {version.description}\n\n"
            commit_message += f"Version: {version.version_id[:8]}\n"
            commit_message += f"Files modified: {', '.join(version.files_modified)}\n"
            
            if version.changes:
                commit_message += f"\nChanges:\n"
                for key, value in version.changes.items():
                    commit_message += f"  - {key}: {value}\n"
            
            # Commit
            result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Get commit hash
                result = subprocess.run(
                    ['git', 'rev-parse', 'HEAD'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                return result.stdout.strip()
            
        except subprocess.CalledProcessError:
            pass
        
        return None
    
    def _get_current_branch(self) -> str:
        """Get current git branch"""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "main"
    
    def _get_git_config(self, key: str, default: str = "") -> str:
        """Get git configuration value"""
        try:
            result = subprocess.run(
                ['git', 'config', key],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.stdout.strip() or default
        except subprocess.CalledProcessError:
            return default
    
    def track_file_changes(self, filepath: str, 
                          original_content: str,
                          modified_content: str):
        """Track changes to a file"""
        # Calculate diff
        original_lines = original_content.splitlines(keepends=True)
        modified_lines = modified_content.splitlines(keepends=True)
        
        diff = list(difflib.unified_diff(
            original_lines,
            modified_lines,
            lineterm=''
        ))
        
        # Count changes
        added = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        removed = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
        
        # Update tracker
        self.change_tracker.add_file_changes(filepath, added, removed)
        
        if filepath not in self.change_tracker.modified_files:
            self.change_tracker.modified_files.append(filepath)
    
    def get_version_diff(self, version_id: str) -> Optional[str]:
        """Get diff for a specific version"""
        version = None
        for v in self.versions:
            if v.version_id.startswith(version_id):
                version = v
                break
        
        if not version or not version.commit_hash:
            return None
        
        try:
            result = subprocess.run(
                ['git', 'show', version.commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return None
    
    def create_rollback_point(self, description: str = "Rollback point") -> bool:
        """Create a rollback point at current state"""
        if self.current_version:
            return self.rollback_manager.create_rollback_point(
                self.current_version,
                force=True
            )
        return False
    
    def rollback(self, version_id: str) -> Tuple[bool, str]:
        """Rollback to a specific version"""
        return self.rollback_manager.rollback_to_version(version_id)
    
    def get_version_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get version history"""
        history = []
        for version in self.versions[-limit:]:
            history.append({
                'version_id': version.version_id[:8],
                'timestamp': version.timestamp.isoformat(),
                'description': version.description,
                'files_modified': version.files_modified,
                'commit': version.commit_hash[:8] if version.commit_hash else None,
                'rollback_point': version.rollback_point
            })
        return history
    
    def export_version(self, version_id: str, 
                      export_path: Path) -> Tuple[bool, str]:
        """Export a specific version to a directory"""
        version = None
        for v in self.versions:
            if v.version_id.startswith(version_id):
                version = v
                break
        
        if not version:
            return False, f"Version {version_id} not found"
        
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Export version using git archive
                if version.commit_hash:
                    subprocess.run(
                        ['git', 'archive', version.commit_hash, '-o', temp_path / 'archive.tar'],
                        cwd=self.repo_path,
                        check=True
                    )
                    
                    # Extract to export path
                    export_path.mkdir(parents=True, exist_ok=True)
                    subprocess.run(
                        ['tar', '-xf', temp_path / 'archive.tar'],
                        cwd=export_path,
                        check=True
                    )
                    
                    return True, f"Version exported to {export_path}"
                else:
                    return False, "Version has no commit hash"
                    
        except subprocess.CalledProcessError as e:
            return False, f"Export failed: {str(e)}"
    
    @contextmanager
    def temporary_version(self, description: str = "Temporary version"):
        """Context manager for temporary version (auto-rollback on exit)"""
        # Create version
        temp_version = self.create_version(
            description=description,
            files_modified=[],
            auto_commit=False
        )
        
        try:
            yield temp_version
        finally:
            # Rollback to previous version
            if temp_version.parent_version:
                self.rollback(temp_version.parent_version)
            
            # Remove temporary version from history
            self.versions = [v for v in self.versions if v.version_id != temp_version.version_id]
            self._save_version_history()