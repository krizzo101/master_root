"Common type aliases and protocols to avoid import cycles."

from __future__ import annotations
from typing import Protocol, TypeAlias

JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
JsonDict: TypeAlias = dict[str, JsonValue]


class SupportsToDict(Protocol):
    """Objects that can be converted to a dictionary."""

    def to_dict(self) -> JsonDict: ...

