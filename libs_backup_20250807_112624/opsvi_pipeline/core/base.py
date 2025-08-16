"Base classes and mixins used across the library."

from __future__ import annotations


class BaseModel:
    """A minimal base class – extend as required."""

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.__class__.__name__}()"

