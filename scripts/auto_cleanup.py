#!/usr/bin/env python3
"""
Automatic Project Cleanup Script
Run this automatically before tasks and on schedule
"""

import os
import shutil
import json
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple

class ProjectCleaner:
    def __init__(self, root_path: str = "/home/opsvi/master_root"):
        self.root = Path(root_path)
        self.violations = []
        self.actions_taken = []
        
    def check_root_documentation(self) -> List[str]:
        """Check for excess .md files in root directory"""
        allowed_root_docs = {'README.md', 'CLAUDE.md', 'QUICK_START.md', 'LICENSE.md', 'CONTRIBUTING.md'}
        md_files = list(self.root.glob('*.md'))
        violations = []
        
        for md_file in md_files:
            if md_file.name not in allowed_root_docs:
                violations.append(str(md_file))
                
        if violations:
            self.violations.append(f"Found {len(violations)} unauthorized .md files in root")
            
        return violations
    
    def check_version_suffixes(self) -> List[str]:
        """Find files with version suffixes"""
        bad_patterns = ['*_V[0-9]*', '*_v[0-9]*', '*_final*', '*_updated*', '*_new*', '*_old*']
        violations = []
        
        for pattern in bad_patterns:
            violations.extend([str(f) for f in self.root.rglob(pattern)])
            
        if violations:
            self.violations.append(f"Found {len(violations)} files with version suffixes")
            
        return violations
    
    def clean_temp_files(self) -> int:
        """Remove temporary files older than 24 hours"""
        temp_dir = self.root / '.tmp'
        if not temp_dir.exists():
            temp_dir.mkdir(exist_ok=True)
            
        count = 0
        cutoff = datetime.now() - timedelta(hours=24)
        
        for temp_file in temp_dir.iterdir():
            if temp_file.is_file():
                mtime = datetime.fromtimestamp(temp_file.stat().st_mtime)
                if mtime < cutoff:
                    temp_file.unlink()
                    count += 1
                    
        # Also clean root temp files
        for pattern in ['*.tmp', '*.log', '*.bak', 'temp.*']:
            for temp_file in self.root.glob(pattern):
                if temp_file.is_file():
                    mtime = datetime.fromtimestamp(temp_file.stat().st_mtime)
                    if mtime < cutoff:
                        temp_file.unlink()
                        count += 1
                        
        if count:
            self.actions_taken.append(f"Deleted {count} temporary files")
            
        return count
    
    def organize_documentation(self) -> Dict[str, List[str]]:
        """Move documentation to proper directories"""
        docs_dir = self.root / 'docs'
        docs_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        subdirs = ['architecture', 'analysis', 'guides', 'migration', 'archive']
        for subdir in subdirs:
            (docs_dir / subdir).mkdir(exist_ok=True)
            
        moved = {
            'architecture': [],
            'analysis': [],
            'guides': [],
            'migration': [],
            'archive': []
        }
        
        # Categorize and move files
        categorization = {
            'architecture': ['*ARCHITECTURE*.md', '*DESIGN*.md', '*ORCHESTRAT*.md'],
            'analysis': ['*ANALYSIS*.md', '*REPORT*.md', '*STATUS*.md'],
            'guides': ['*GUIDE*.md', '*INTEGRATION*.md', '*TUTORIAL*.md'],
            'migration': ['*MIGRATION*.md', '*ROADMAP*.md', '*UPGRADE*.md'],
        }
        
        for category, patterns in categorization.items():
            for pattern in patterns:
                for file in self.root.glob(pattern):
                    if file.is_file() and file.name not in ['README.md', 'CLAUDE.md', 'QUICK_START.md']:
                        target = docs_dir / category / file.name
                        if not target.exists():
                            shutil.move(str(file), str(target))
                            moved[category].append(file.name)
                            
        # Archive old versioned files
        for pattern in ['V[0-9]_*.md', '*_V[0-9].md']:
            for file in self.root.glob(pattern):
                if file.is_file():
                    target = docs_dir / 'archive' / file.name
                    if not target.exists():
                        shutil.move(str(file), str(target))
                        moved['archive'].append(file.name)
                        
        total_moved = sum(len(files) for files in moved.values())
        if total_moved:
            self.actions_taken.append(f"Organized {total_moved} documentation files")
            
        return moved
    
    def archive_old_documents(self, days: int = 30) -> int:
        """Archive ONLY temporary documents (date-prefixed) older than specified days
        Core documentation in architecture/ and guides/ NEVER expires"""
        docs_dir = self.root / 'docs'
        archive_dir = docs_dir / 'archive'
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        count = 0
        cutoff = datetime.now() - timedelta(days=days)
        
        # Only archive from temporary directories (analysis, migration)
        # NEVER archive from architecture or guides (permanent documentation)
        for subdir in ['analysis', 'migration']:
            source_dir = docs_dir / subdir
            if source_dir.exists():
                for doc in source_dir.glob('*.md'):
                    # Only archive if file has date prefix (YYYY-MM-DD format)
                    if doc.name[:10].replace('-', '').isdigit() and len(doc.name) > 10 and doc.name[10] == '_':
                        mtime = datetime.fromtimestamp(doc.stat().st_mtime)
                        if mtime < cutoff:
                            target = archive_dir / doc.name
                            shutil.move(str(doc), str(target))
                            count += 1
                        
        if count:
            self.actions_taken.append(f"Archived {count} old documents")
            
        return count
    
    def check_size_limits(self) -> List[Tuple[str, int]]:
        """Check for files and directories exceeding size limits"""
        violations = []
        
        # Check file sizes (10MB warning)
        for file in self.root.rglob('*'):
            if file.is_file() and not str(file).startswith(str(self.root / '.git')):
                size_mb = file.stat().st_size / (1024 * 1024)
                if size_mb > 10:
                    violations.append((str(file), size_mb))
                    
        # Check directory sizes (100MB warning)
        for dir_path in self.root.iterdir():
            if dir_path.is_dir() and dir_path.name not in ['.git', '.venv', 'node_modules']:
                size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                size_mb = size / (1024 * 1024)
                if size_mb > 100:
                    violations.append((str(dir_path), size_mb))
                    
        if violations:
            self.violations.append(f"Found {len(violations)} size limit violations")
            
        return violations
    
    def generate_report(self) -> str:
        """Generate cleanup report"""
        report = []
        report.append("=" * 50)
        report.append("PROJECT CLEANUP REPORT")
        report.append(f"Timestamp: {datetime.now().isoformat()}")
        report.append("=" * 50)
        
        if self.violations:
            report.append("\n⚠️  VIOLATIONS FOUND:")
            for violation in self.violations:
                report.append(f"  - {violation}")
        else:
            report.append("\n✅ No violations found")
            
        if self.actions_taken:
            report.append("\n🔧 ACTIONS TAKEN:")
            for action in self.actions_taken:
                report.append(f"  - {action}")
        else:
            report.append("\n📋 No actions needed")
            
        report.append("\n" + "=" * 50)
        return "\n".join(report)
    
    def run_cleanup(self, fix: bool = False) -> str:
        """Run all cleanup checks and optionally fix issues"""
        # Check for violations
        self.check_root_documentation()
        self.check_version_suffixes()
        size_violations = self.check_size_limits()
        
        if fix:
            # Perform cleanup actions
            self.clean_temp_files()
            self.organize_documentation()
            self.archive_old_documents()
            
        return self.generate_report()


if __name__ == "__main__":
    import sys
    
    # Check if --fix flag is provided
    fix_mode = '--fix' in sys.argv
    
    cleaner = ProjectCleaner()
    report = cleaner.run_cleanup(fix=fix_mode)
    print(report)
    
    # Exit with error code if violations found
    sys.exit(1 if cleaner.violations else 0)