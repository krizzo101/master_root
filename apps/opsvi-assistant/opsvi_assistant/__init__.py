"""OPSVI Assistant - AI-powered CLI application.

Demonstrates integration of opsvi libraries for building
production-ready AI applications.
"""

__version__ = "1.0.0"
__author__ = "OPSVI Team"

from .cli import main
from .core import Assistant

__all__ = ["main", "Assistant", "__version__"]