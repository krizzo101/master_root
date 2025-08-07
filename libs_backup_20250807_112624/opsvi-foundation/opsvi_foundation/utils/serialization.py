"""
Serialization utilities for OPSVI Foundation.

Provides comprehensive serialization and deserialization functions.
"""

import base64
import json
import logging
import pickle
import zlib
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar
from uuid import UUID

import msgpack
import orjson
import yaml

logger = logging.getLogger(__name__)


class SerializationFormat(Enum):
    """Supported serialization formats."""

    JSON = "json"
    ORJSON = "orjson"
    MSGPACK = "msgpack"
    YAML = "yaml"
    PICKLE = "pickle"
    BASE64 = "base64"
    COMPRESSED_JSON = "compressed_json"


class SerializationError(Exception):
    """Exception raised when serialization fails."""


class DeserializationError(Exception):
    """Exception raised when deserialization fails."""


T = TypeVar("T")


class Serializer:
    """Base serializer class."""

    def __init__(self, format_type: SerializationFormat) -> None:
        self.format_type = format_type

    def serialize(self, data: Any) -> str | bytes:
        """Serialize data to the specified format."""
        raise NotImplementedError

    def deserialize(self, data: str | bytes) -> Any:
        """Deserialize data from the specified format."""
        raise NotImplementedError


class JSONSerializer(Serializer):
    """JSON serializer implementation."""

    def __init__(
        self,
        indent: int | None = None,
        ensure_ascii: bool = False,
    ) -> None:
        super().__init__(SerializationFormat.JSON)
        self.indent = indent
        self.ensure_ascii = ensure_ascii

    def serialize(self, data: Any) -> str:
        """Serialize data to JSON string."""
        try:
            return json.dumps(
                data,
                indent=self.indent,
                ensure_ascii=self.ensure_ascii,
                default=self._json_serializer,
            )
        except Exception as e:
            raise SerializationError(f"JSON serialization failed: {e}")

    def deserialize(self, data: str | bytes) -> Any:
        """Deserialize data from JSON string."""
        try:
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            return json.loads(data, object_hook=self._json_deserializer)
        except Exception as e:
            raise DeserializationError(f"JSON deserialization failed: {e}")

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for special types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Enum):
            return obj.value
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def _json_deserializer(self, obj: dict[str, Any]) -> Any:
        """Custom JSON deserializer for special types."""
        # Add custom deserialization logic here if needed
        return obj


class ORJSONSerializer(Serializer):
    """ORJSON serializer implementation (faster than standard JSON)."""

    def __init__(self, option: int | None = None) -> None:
        super().__init__(SerializationFormat.ORJSON)
        self.option = option or (orjson.OPT_NAIVE_UTC | orjson.OPT_SERIALIZE_NUMPY)

    def serialize(self, data: Any) -> bytes:
        """Serialize data to ORJSON bytes."""
        try:
            return orjson.dumps(data, option=self.option)
        except Exception as e:
            raise SerializationError(f"ORJSON serialization failed: {e}")

    def deserialize(self, data: str | bytes) -> Any:
        """Deserialize data from ORJSON bytes."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            return orjson.loads(data)
        except Exception as e:
            raise DeserializationError(f"ORJSON deserialization failed: {e}")


class MessagePackSerializer(Serializer):
    """MessagePack serializer implementation."""

    def __init__(self, use_bin_type: bool = True) -> None:
        super().__init__(SerializationFormat.MSGPACK)
        self.use_bin_type = use_bin_type

    def serialize(self, data: Any) -> bytes:
        """Serialize data to MessagePack bytes."""
        try:
            return msgpack.packb(
                data,
                use_bin_type=self.use_bin_type,
                default=self._msgpack_serializer,
            )
        except Exception as e:
            raise SerializationError(f"MessagePack serialization failed: {e}")

    def deserialize(self, data: str | bytes) -> Any:
        """Deserialize data from MessagePack bytes."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            return msgpack.unpackb(data, raw=False)
        except Exception as e:
            raise DeserializationError(f"MessagePack deserialization failed: {e}")

    def _msgpack_serializer(self, obj: Any) -> Any:
        """Custom MessagePack serializer for special types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Enum):
            return obj.value
        raise TypeError(f"Object of type {type(obj)} is not MessagePack serializable")


class YAMLSerializer(Serializer):
    """YAML serializer implementation."""

    def __init__(self, default_flow_style: bool = False, indent: int = 2) -> None:
        super().__init__(SerializationFormat.YAML)
        self.default_flow_style = default_flow_style
        self.indent = indent

    def serialize(self, data: Any) -> str:
        """Serialize data to YAML string."""
        try:
            return yaml.dump(
                data,
                default_flow_style=self.default_flow_style,
                indent=self.indent,
                default_representer=self._yaml_representer,
            )
        except Exception as e:
            raise SerializationError(f"YAML serialization failed: {e}")

    def deserialize(self, data: str | bytes) -> Any:
        """Deserialize data from YAML string."""
        try:
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            return yaml.safe_load(data)
        except Exception as e:
            raise DeserializationError(f"YAML deserialization failed: {e}")

    def _yaml_representer(self, representer: Any, data: Any) -> Any:
        """Custom YAML representer for special types."""
        if isinstance(data, datetime):
            return representer.represent_str(data.isoformat())
        if isinstance(data, UUID):
            return representer.represent_str(str(data))
        if isinstance(data, Enum):
            return representer.represent_str(data.value)
        return representer.represent_str(str(data))


class PickleSerializer(Serializer):
    """Pickle serializer implementation."""

    def __init__(self, protocol: int = pickle.HIGHEST_PROTOCOL) -> None:
        super().__init__(SerializationFormat.PICKLE)
        self.protocol = protocol

    def serialize(self, data: Any) -> bytes:
        """Serialize data to pickle bytes."""
        try:
            return pickle.dumps(data, protocol=self.protocol)
        except Exception as e:
            raise SerializationError(f"Pickle serialization failed: {e}")

    def deserialize(self, data: str | bytes) -> Any:
        """Deserialize data from pickle bytes."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            return pickle.loads(data)
        except Exception as e:
            raise DeserializationError(f"Pickle deserialization failed: {e}")


class Base64Serializer(Serializer):
    """Base64 serializer implementation."""

    def __init__(self, encoding: str = "utf-8") -> None:
        super().__init__(SerializationFormat.BASE64)
        self.encoding = encoding

    def serialize(self, data: Any) -> str:
        """Serialize data to base64 string."""
        try:
            if isinstance(data, str):
                data = data.encode(self.encoding)
            elif not isinstance(data, bytes):
                data = str(data).encode(self.encoding)
            return base64.b64encode(data).decode("ascii")
        except Exception as e:
            raise SerializationError(f"Base64 serialization failed: {e}")

    def deserialize(self, data: str | bytes) -> bytes:
        """Deserialize data from base64 string."""
        try:
            if isinstance(data, bytes):
                data = data.decode("ascii")
            return base64.b64decode(data)
        except Exception as e:
            raise DeserializationError(f"Base64 deserialization failed: {e}")


class CompressedJSONSerializer(Serializer):
    """Compressed JSON serializer implementation."""

    def __init__(self, compression_level: int = 6) -> None:
        super().__init__(SerializationFormat.COMPRESSED_JSON)
        self.compression_level = compression_level
        self.json_serializer = JSONSerializer()

    def serialize(self, data: Any) -> bytes:
        """Serialize data to compressed JSON bytes."""
        try:
            json_str = self.json_serializer.serialize(data)
            json_bytes = json_str.encode("utf-8")
            compressed = zlib.compress(json_bytes, level=self.compression_level)
            return compressed
        except Exception as e:
            raise SerializationError(f"Compressed JSON serialization failed: {e}")

    def deserialize(self, data: str | bytes) -> Any:
        """Deserialize data from compressed JSON bytes."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            decompressed = zlib.decompress(data)
            json_str = decompressed.decode("utf-8")
            return self.json_serializer.deserialize(json_str)
        except Exception as e:
            raise DeserializationError(f"Compressed JSON deserialization failed: {e}")


class SerializationManager:
    """Manager for handling multiple serialization formats."""

    def __init__(self) -> None:
        self.serializers: dict[SerializationFormat, Serializer] = {
            SerializationFormat.JSON: JSONSerializer(),
            SerializationFormat.ORJSON: ORJSONSerializer(),
            SerializationFormat.MSGPACK: MessagePackSerializer(),
            SerializationFormat.YAML: YAMLSerializer(),
            SerializationFormat.PICKLE: PickleSerializer(),
            SerializationFormat.BASE64: Base64Serializer(),
            SerializationFormat.COMPRESSED_JSON: CompressedJSONSerializer(),
        }

    def get_serializer(self, format_type: SerializationFormat) -> Serializer:
        """Get a serializer for the specified format."""
        if format_type not in self.serializers:
            raise ValueError(f"Unsupported serialization format: {format_type}")
        return self.serializers[format_type]

    def register_serializer(
        self,
        format_type: SerializationFormat,
        serializer: Serializer,
    ) -> None:
        """Register a custom serializer."""
        self.serializers[format_type] = serializer
        logger.info(f"Registered custom serializer for format: {format_type}")

    def serialize(
        self,
        data: Any,
        format_type: SerializationFormat,
    ) -> str | bytes:
        """Serialize data using the specified format."""
        serializer = self.get_serializer(format_type)
        return serializer.serialize(data)

    def deserialize(
        self,
        data: str | bytes,
        format_type: SerializationFormat,
    ) -> Any:
        """Deserialize data using the specified format."""
        serializer = self.get_serializer(format_type)
        return serializer.deserialize(data)

    def auto_detect_format(
        self,
        data: str | bytes,
    ) -> SerializationFormat | None:
        """Auto-detect the format of serialized data."""
        if isinstance(data, bytes):
            # Try to detect format from bytes
            if data.startswith(b"\x80"):  # MessagePack
                return SerializationFormat.MSGPACK
            if data.startswith(b"\x1f\x8b"):  # Gzip
                return SerializationFormat.COMPRESSED_JSON
            # Try to decode as string and detect
            try:
                data_str = data.decode("utf-8")
                return self._detect_string_format(data_str)
            except UnicodeDecodeError:
                return SerializationFormat.PICKLE
        else:
            return self._detect_string_format(data)

    def _detect_string_format(self, data: str) -> SerializationFormat | None:
        """Detect format from string data."""
        data = data.strip()

        if (data.startswith("{") and data.endswith("}")) or (
            data.startswith("[") and data.endswith("]")
        ):
            return SerializationFormat.JSON
        if data.startswith("-") or data.startswith("---"):
            return SerializationFormat.YAML
        # Try to decode as base64
        try:
            import base64

            base64.b64decode(data)
            return SerializationFormat.BASE64
        except Exception:
            return None


# Global serialization manager
serialization_manager = SerializationManager()


# Convenience functions


def serialize(
    data: Any,
    format_type: SerializationFormat = SerializationFormat.JSON,
) -> str | bytes:
    """Serialize data using the global serialization manager."""
    return serialization_manager.serialize(data, format_type)


def deserialize(
    data: str | bytes,
    format_type: SerializationFormat | None = None,
) -> Any:
    """Deserialize data using the global serialization manager."""
    if format_type is None:
        format_type = serialization_manager.auto_detect_format(data)
        if format_type is None:
            raise DeserializationError("Could not auto-detect serialization format")

    return serialization_manager.deserialize(data, format_type)


def to_json(data: Any, indent: int | None = None) -> str:
    """Serialize data to JSON string."""
    serializer = JSONSerializer(indent=indent)
    return serializer.serialize(data)


def from_json(data: str | bytes) -> Any:
    """Deserialize data from JSON string."""
    serializer = JSONSerializer()
    return serializer.deserialize(data)


def to_yaml(data: Any, indent: int = 2) -> str:
    """Serialize data to YAML string."""
    serializer = YAMLSerializer(indent=indent)
    return serializer.serialize(data)


def from_yaml(data: str | bytes) -> Any:
    """Deserialize data from YAML string."""
    serializer = YAMLSerializer()
    return serializer.deserialize(data)


def to_msgpack(data: Any) -> bytes:
    """Serialize data to MessagePack bytes."""
    serializer = MessagePackSerializer()
    return serializer.serialize(data)


def from_msgpack(data: str | bytes) -> Any:
    """Deserialize data from MessagePack bytes."""
    serializer = MessagePackSerializer()
    return serializer.deserialize(data)


def to_pickle(data: Any) -> bytes:
    """Serialize data to pickle bytes."""
    serializer = PickleSerializer()
    return serializer.serialize(data)


def from_pickle(data: str | bytes) -> Any:
    """Deserialize data from pickle bytes."""
    serializer = PickleSerializer()
    return serializer.deserialize(data)


def to_base64(data: Any) -> str:
    """Serialize data to base64 string."""
    serializer = Base64Serializer()
    return serializer.serialize(data)


def from_base64(data: str | bytes) -> bytes:
    """Deserialize data from base64 string."""
    serializer = Base64Serializer()
    return serializer.deserialize(data)


def to_compressed_json(data: Any) -> bytes:
    """Serialize data to compressed JSON bytes."""
    serializer = CompressedJSONSerializer()
    return serializer.serialize(data)


def from_compressed_json(data: str | bytes) -> Any:
    """Deserialize data from compressed JSON bytes."""
    serializer = CompressedJSONSerializer()
    return serializer.deserialize(data)


# Type-safe serialization


def serialize_typed(
    data: T,
    format_type: SerializationFormat = SerializationFormat.JSON,
) -> str | bytes:
    """Type-safe serialization."""
    return serialize(data, format_type)


def deserialize_typed(
    data: str | bytes,
    target_type: type[T],
    format_type: SerializationFormat | None = None,
) -> T:
    """Type-safe deserialization."""
    result = deserialize(data, format_type)
    if not isinstance(result, target_type):
        raise DeserializationError(
            f"Deserialized data is not of type {target_type.__name__}",
        )
    return result
