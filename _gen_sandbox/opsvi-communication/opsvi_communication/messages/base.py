"""Message base for opsvi-communication.

Provides a small, typed Message dataclass with helpers for basic
validation and (de)serialization. No external dependencies.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple, Type, Union


class MessageError(Exception):
    """Base exception for message-related errors."""


class MessageValidationError(MessageError):
    """Raised when payload validation fails."""


class MessageParseError(MessageError):
    """Raised when parsing/serialization fails."""


TypeLike = Union[Type, Tuple[Type, ...]]


@dataclass
class Message:
    """A simple typed message container.

    Attributes:
        type: a short string describing the message type.
        payload: a mapping with message contents (must be a dict).
    """

    type: str
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Basic type enforcement
        if not isinstance(self.type, str):
            raise MessageParseError("Message.type must be a string")
        if not isinstance(self.payload, dict):
            raise MessageParseError("Message.payload must be a dict")

    def validate_payload(
        self,
        schema: Optional[Mapping[str, TypeLike]] = None,
        allow_extra: bool = True,
    ) -> None:
        """Validate payload against a simple schema.

        The schema is a mapping of key -> type (or tuple of types). All keys
        in the schema are required to be present in the payload. If
        allow_extra is False, payload is not allowed to contain keys not in
        the schema.

        Raises:
            MessageValidationError: when validation fails.
        """
        if schema is None:
            return

        # Check required keys and types
        for key, expected in schema.items():
            if key not in self.payload:
                raise MessageValidationError(f"Missing required payload key: {key}")
            value = self.payload[key]
            if not isinstance(value, expected):
                # Provide readable type names
                exp_names = (
                    expected.__name__
                    if isinstance(expected, type)
                    else ", ".join(t.__name__ for t in expected)
                )
                raise MessageValidationError(
                    f"Payload key '{key}' expected type {exp_names}, got {type(value).__name__}"
                )

        if not allow_extra:
            extra = set(self.payload) - set(schema)
            if extra:
                raise MessageValidationError(f"Payload contains unexpected keys: {sorted(extra)}")

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict representation of the message.

        The returned dict is safe to JSON-serialize.
        """
        return {"type": self.type, "payload": dict(self.payload)}

    def to_json(self) -> str:
        """Serialize message to a JSON string.

        This is synchronous and deterministic (sorts keys).
        """
        try:
            return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError) as exc:
            raise MessageParseError(f"Failed to serialize message to JSON: {exc}") from exc

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Message":
        """Construct a Message from a mapping.

        Expects keys 'type' and 'payload'.
        """
        if not isinstance(data, Mapping):
            raise MessageParseError("Input must be a mapping")
        if "type" not in data:
            raise MessageParseError("Missing 'type' in message dict")
        if "payload" not in data:
            raise MessageParseError("Missing 'payload' in message dict")

        mtype = data["type"]
        payload = data["payload"]

        if not isinstance(mtype, str):
            raise MessageParseError("'type' must be a string")
        if not isinstance(payload, Mapping):
            raise MessageParseError("'payload' must be a mapping/dict")

        # copy payload into a plain dict
        return cls(type=mtype, payload=dict(payload))

    @classmethod
    def from_json(cls, raw: str) -> "Message":
        """Parse a JSON string into a Message.

        Raises MessageParseError on malformed input.
        """
        try:
            data = json.loads(raw)
        except (TypeError, ValueError) as exc:
            raise MessageParseError(f"Invalid JSON: {exc}") from exc
        return cls.from_dict(data)

    async def to_json_async(self) -> str:
        """Asynchronous wrapper for to_json.

        This yields control to the event loop briefly; useful when used from
        async code to avoid blocking the loop for large payloads.
        """
        await asyncio.sleep(0)
        return self.to_json()

    @classmethod
    async def from_json_async(cls, raw: str) -> "Message":
        """Asynchronous wrapper for from_json."""
        await asyncio.sleep(0)
        return cls.from_json(raw)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"Message(type={self.type!r}, payload_keys={list(self.payload.keys())!r})"
