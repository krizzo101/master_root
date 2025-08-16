from dataclasses import dataclass
from typing import Any


@dataclass
class ModelInfo:
    id: str
    object: str
    created: int | None
    owned_by: str | None
    permission: list[dict[str, Any]] | None
    root: str | None
    parent: str | None


@dataclass
class ErrorResponse:
    message: str
    type: str
    param: str | None
    code: str | None


# Add more dataclasses/types as needed for other APIs
