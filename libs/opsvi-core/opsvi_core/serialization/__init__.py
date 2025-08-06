"""
Serialization module for opsvi-core.

Provides data serialization and format conversion capabilities.
"""

from opsvi_foundation import (
    DeserializationError,
    SerializationError,
    deserialize_json,
    deserialize_msgpack,
    deserialize_pickle,
    serialize_json,
    serialize_msgpack,
    serialize_pickle,
)

__all__ = [
    "SerializationError",
    "DeserializationError",
    "serialize_json",
    "deserialize_json",
    "serialize_pickle",
    "deserialize_pickle",
    "serialize_msgpack",
    "deserialize_msgpack",
]

__version__ = "1.0.0"
