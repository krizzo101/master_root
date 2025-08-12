"""Code generation utility package initializer."""

import sys as _sys
from pathlib import Path

pkg_dir = Path(__file__).parent
if str(pkg_dir) not in _sys.path:
    _sys.path.insert(0, str(pkg_dir))

__all__ = ["__version__"]
__version__: str = "0.1.0"
