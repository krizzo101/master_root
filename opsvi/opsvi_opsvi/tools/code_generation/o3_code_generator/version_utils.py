"""O3 Code Generator Version Utility

Provides a single utility function to retrieve the current version number
of the O3 Code Generator.
"""

from __future__ import annotations

__all__: list[str] = ["get_o3_generator_version"]
_O3_GENERATOR_VERSION: str = "1.0.0"


def get_o3_generator_version() -> str:
    """Return the current version of the O3 Code Generator."""
    return _O3_GENERATOR_VERSION
