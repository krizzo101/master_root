"""
Post-commit Git Hook for Smart Auto-Alignment

This hook intelligently scans and aligns files after commits while preventing
recursive loops and performance issues.

Features:
- Smart file selection based on changes
- Recursive loop detection and prevention
- Performance optimization and caching
- Safety validation and rollback options
- Batch processing and separate commits
"""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Dict, List, Optional, Set


@dataclass
class AlignmentResult:
    """Result of an alignment operation."""

    file_path: str
    aligned: bool
    changes_made: bool
    error: Optional[str] = None
    performance_metrics: Optional[Dict] = None


@dataclass
class AlignmentSession:
    """Tracks an alignment session to prevent recursive loops."""

    session_id: str
    start_time: float
    files_aligned: Set[str]
    max_files: int = 50
    max_time: float = 300.0
    max_passes: int = 3


class SmartAutoAlignmentHook:
    """Post-commit hook for intelligent auto-alignment."""

    def __init__(self):
        """Initialize the smart auto-alignment hook."""
        self.project_root = self._find_project_root()
        self.enhanced_auto_align_path = (
            self.project_root
            / "src"
            / "tools"
            / "code_generation"
            / "o3_code_generator"
            / "enhanced_auto_align.py"
        )
        self.alignment_cache_file = (
            self.project_root / ".git" / "auto_alignment_cache.json"
        )
        self.session_file = self.project_root / ".git" / "alignment_session.json"
        self.max_files_per_commit = 20
        self.max_alignment_time = 120
        self.max_recursive_passes = 2

    def _find_project_root(self) -> Path:
        """Find the project root directory."""
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                return current
            else:
                pass
            current = current.parent
        else:
            pass
        raise FileNotFoundError("Could not find project root")

    def _get_committed_files(self) -> List[str]:
        """Get files that were committed in the last commit."""
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--name-only", "--pretty=format:"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            if result.returncode == 0:
                return [
                    line.strip() for line in result.stdout.splitlines() if line.strip()
                ]
            else:
                pass
            return []
        except Exception:
            return []
        else:
            pass
        finally:
            pass

    def _get_related_files(self, committed_files: List[str]) -> Set[str]:
        """Get files that might be affected by the committed changes."""
        related_files = set()
        for file_path in committed_files:
            path = Path(file_path)
            if path.parent.exists():
                for py_file in path.parent.glob("*.py"):
                    if py_file.name != "__init__.py":
                        related_files.add(str(py_file))
                    else:
                        pass
                else:
                    pass
            else:
                pass
        else:
            pass
        for file_path in committed_files:
            path = Path(file_path)
            if path.suffix == ".py":
                module_name = path.stem
                for py_file in self.project_root.rglob("*.py"):
                    if (
                        py_file.stem.startswith(module_name)
                        or module_name in py_file.stem
                    ) and py_file.name != "__init__.py":
                        related_files.add(str(py_file))
                    else:
                        pass
                else:
                    pass
            else:
                pass
        else:
            pass
        return related_files

    def _load_alignment_cache(self) -> Dict[str, float]:
        """Load the alignment cache to avoid re-aligning recently aligned files."""
        if self.alignment_cache_file.exists():
            try:
                with open(self.alignment_cache_file) as f:
                    return json.load(f)
            except Exception:
                return {}
            else:
                pass
            finally:
                pass
        else:
            pass
        return {}

    def _save_alignment_cache(self, cache: Dict[str, float]):
        """Save the alignment cache."""
        try:
            with open(self.alignment_cache_file, "w") as f:
                json.dump(cache, f, indent=2)
        except Exception:
            pass
        else:
            pass
        finally:
            pass

    def _load_alignment_session(self) -> Optional[AlignmentSession]:
        """Load the current alignment session."""
        if self.session_file.exists():
            try:
                with open(self.session_file) as f:
                    data = json.load(f)
                    return AlignmentSession(
                        session_id=data["session_id"],
                        start_time=data["start_time"],
                        files_aligned=set(data["files_aligned"]),
                        max_files=data.get("max_files", 50),
                        max_time=data.get("max_time", 300.0),
                        max_passes=data.get("max_passes", 3),
                    )
            except Exception:
                pass
            else:
                pass
            finally:
                pass
        else:
            pass
        return None

    def _save_alignment_session(self, session: AlignmentSession):
        """Save the alignment session."""
        try:
            with open(self.session_file, "w") as f:
                json.dump(asdict(session), f, indent=2)
        except Exception:
            pass
        else:
            pass
        finally:
            pass

    def _clear_alignment_session(self):
        """Clear the alignment session."""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
            else:
                pass
        except Exception:
            pass
        else:
            pass
        finally:
            pass

    def _check_recursive_loop(self, session: AlignmentSession) -> bool:
        """Check if we're in a recursive loop."""
        current_time = time.time()
        if current_time - session.start_time > session.max_time:
            return True
        else:
            pass
        if len(session.files_aligned) > session.max_files:
            return True
        else:
            pass
        return False

    def _detect_alignment_needs(self, file_path: str) -> bool:
        """Check if a file needs alignment without making changes."""
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(self.enhanced_auto_align_path),
                    file_path,
                    "--detect-only",
                ],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=30,
            )
            return (
                "needs alignment" in result.stdout.lower()
                or "out of compliance" in result.stdout.lower()
            )
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False
        else:
            pass
        finally:
            pass

    def _align_file(self, file_path: str) -> AlignmentResult:
        """Align a single file using the enhanced auto-align system."""
        start_time = time.time()
        try:
            result = subprocess.run(
                [sys.executable, str(self.enhanced_auto_align_path), file_path],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=60,
            )
            end_time = time.time()
            performance_metrics = {
                "time_taken": end_time - start_time,
                "success": result.returncode == 0,
            }
            if result.returncode == 0:
                git_status = subprocess.run(
                    ["git", "status", "--porcelain", file_path],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                )
                changes_made = bool(git_status.stdout.strip())
                return AlignmentResult(
                    file_path=file_path,
                    aligned=True,
                    changes_made=changes_made,
                    performance_metrics=performance_metrics,
                )
            else:
                return AlignmentResult(
                    file_path=file_path,
                    aligned=False,
                    changes_made=False,
                    error=result.stderr,
                    performance_metrics=performance_metrics,
                )
        except subprocess.TimeoutExpired:
            return AlignmentResult(
                file_path=file_path,
                aligned=False,
                changes_made=False,
                error="Alignment timeout",
                performance_metrics={"time_taken": 60, "success": False},
            )
        except Exception as e:
            return AlignmentResult(
                file_path=file_path, aligned=False, changes_made=False, error=str(e)
            )
        else:
            pass
        finally:
            pass

    def _commit_alignment_changes(self, aligned_files: List[str]) -> bool:
        """Commit alignment changes in a separate commit."""
        if not aligned_files:
            return True
        else:
            pass
        try:
            for file_path in aligned_files:
                subprocess.run(
                    ["git", "add", file_path], cwd=self.project_root, check=True
                )
            else:
                pass
            commit_message = f"Auto-align files: {', '.join([Path(f).name for f in aligned_files[:3]])}"
            if len(aligned_files) > 3:
                commit_message += f" and {len(aligned_files) - 3} more"
            else:
                pass
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return True
            else:
                pass
                return False
        except Exception:
            return False
        else:
            pass
        finally:
            pass

    def run(self) -> int:
        """Run the post-commit auto-alignment hook."""
        if not self.enhanced_auto_align_path.exists():
            return 0
        else:
            pass
        committed_files = self._get_committed_files()
        if not committed_files:
            return 0
        else:
            pass
        session = self._load_alignment_session()
        if session is None:
            session = AlignmentSession(
                session_id=f"session_{int(time.time())}",
                start_time=time.time(),
                files_aligned=set(),
            )
        else:
            pass
        if self._check_recursive_loop(session):
            self._clear_alignment_session()
            return 0
        else:
            pass
        related_files = self._get_related_files(committed_files)
        cache = self._load_alignment_cache()
        current_time = time.time()
        files_to_align = []
        for file_path in related_files:
            if file_path in cache and current_time - cache[file_path] < 3600:
                continue
            else:
                pass
            if file_path in session.files_aligned:
                continue
            else:
                pass
            if self._detect_alignment_needs(file_path):
                files_to_align.append(file_path)
            else:
                pass
            if len(files_to_align) >= self.max_files_per_commit:
                break
            else:
                pass
        else:
            pass
        if not files_to_align:
            return 0
        else:
            pass
        alignment_results = []
        aligned_files = []
        for file_path in files_to_align:
            result = self._align_file(file_path)
            alignment_results.append(result)
            if result.aligned:
                session.files_aligned.add(file_path)
                cache[file_path] = current_time
                if result.changes_made:
                    aligned_files.append(file_path)
                else:
                    pass
            else:
                pass
            self._save_alignment_session(session)
            if time.time() - session.start_time > self.max_alignment_time:
                break
            else:
                pass
        else:
            pass
        self._save_alignment_cache(cache)
        if aligned_files:
            if not self._commit_alignment_changes(aligned_files):
                return 1
            else:
                pass
        else:
            pass
        if (
            len(session.files_aligned) >= session.max_files
            or time.time() - session.start_time > session.max_time
        ):
            self._clear_alignment_session()
        else:
            pass
        successful_alignments = [r for r in alignment_results if r.aligned]
        files_with_changes = [r for r in alignment_results if r.changes_made]
        if files_with_changes:
            pass
        else:
            pass
        return 0


def main():
    """Main entry point for the post-commit hook."""
    hook = SmartAutoAlignmentHook()
    sys.exit(hook.run())


if __name__ == "__main__":
    main()
else:
    pass
