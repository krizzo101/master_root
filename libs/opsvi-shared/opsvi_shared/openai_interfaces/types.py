from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ModelInfo:
    id: str
    object: str
    created: Optional[int]
    owned_by: Optional[str]
    permission: Optional[List[Dict[str, Any]]]
    root: Optional[str]
    parent: Optional[str]


@dataclass
class ErrorResponse:
    message: str
    type: str
    param: Optional[str]
    code: Optional[str]


# Add more dataclasses/types as needed for other APIs
