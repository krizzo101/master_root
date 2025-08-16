"""Top-level package for opsvi-orchestration."""

from importlib.metadata import version as _v

__all__: list[str] = ["__version__"]

try:
    __version__: str = _v("opsvi-orchestration")
except Exception:  # pragma: no cover
    __version__ = "0.0.0.dev0"
