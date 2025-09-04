"""Project intelligence reader."""

from pathlib import Path
from typing import Optional


class ProjectIntelReader:
    """Project intelligence reader for .proj-intel directories."""

    def __init__(self, intel_dir: Optional[str] = None):
        """Initialize reader with intel directory path."""
        self.intel_dir = Path(intel_dir) if intel_dir else Path.cwd() / ".proj-intel"

        # Ensure the directory exists
        if not self.intel_dir.exists():
            self.intel_dir.mkdir(parents=True, exist_ok=True)

    def get_project_root(self) -> Path:
        """Get the project root directory."""
        return self.intel_dir.parent

    def get_intel_dir(self) -> Path:
        """Get the intelligence directory path."""
        return self.intel_dir
