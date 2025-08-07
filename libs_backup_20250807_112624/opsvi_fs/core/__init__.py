"""Top-level package for opsvi_fs."""

from importlib.metadata import version as _version

__all__ = ("__version__",)
__version__: str = _version(__name__)

