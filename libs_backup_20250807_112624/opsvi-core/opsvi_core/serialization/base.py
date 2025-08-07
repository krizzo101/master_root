"""
Base serialization infrastructure for OPSVI Core.

Provides data serialization and deserialization with support for multiple formats.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from opsvi_foundation import BaseComponent, ComponentError, get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)


class SerializationError(ComponentError):
    """Raised when serialization operations fail."""

    pass


class DeserializationError(ComponentError):
    """Raised when deserialization operations fail."""

    pass


class SerializationFormat(str, Enum):
    """Supported serialization formats."""

    JSON = "json"
    YAML = "yaml"
    MSGPACK = "msgpack"
    PICKLE = "pickle"
    PROTOBUF = "protobuf"


class SerializerConfig(BaseModel):
    """Configuration for serializers."""

    format: SerializationFormat = Field(
        default=SerializationFormat.JSON, description="Serialization format"
    )
    pretty_print: bool = Field(default=False, description="Pretty print output")
    ensure_ascii: bool = Field(default=False, description="Ensure ASCII encoding")
    compression: bool = Field(default=False, description="Enable compression")


class BaseSerializer(BaseComponent, ABC):
    """Abstract serializer interface."""

    def __init__(self, config: SerializerConfig):
        super().__init__()
        self.config = config

    @abstractmethod
    def serialize(self, data: Any) -> str | bytes:
        """Serialize data to string or bytes."""
        pass

    @abstractmethod
    def deserialize(self, data: str | bytes) -> Any:
        """Deserialize string or bytes to data."""
        pass

    @property
    @abstractmethod
    def format(self) -> SerializationFormat:
        """Get serialization format."""
        pass

    @property
    @abstractmethod
    def binary_output(self) -> bool:
        """Whether serializer produces binary output."""
        pass


class JSONSerializer(BaseSerializer):
    """JSON serializer implementation."""

    def __init__(self, config: SerializerConfig | None = None):
        config = config or SerializerConfig(format=SerializationFormat.JSON)
        super().__init__(config)

    def serialize(self, data: Any) -> str:
        """Serialize data to JSON string."""
        try:
            return json.dumps(
                data,
                indent=2 if self.config.pretty_print else None,
                ensure_ascii=self.config.ensure_ascii,
                default=self._json_serializer,
            )
        except Exception as e:
            raise SerializationError(f"JSON serialization failed: {e}") from e

    def deserialize(self, data: str | bytes) -> Any:
        """Deserialize JSON string to data."""
        try:
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            return json.loads(data)
        except Exception as e:
            raise DeserializationError(f"JSON deserialization failed: {e}") from e

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for complex objects."""
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        elif hasattr(obj, "isoformat"):  # datetime objects
            return obj.isoformat()
        else:
            return str(obj)

    @property
    def format(self) -> SerializationFormat:
        """Get serialization format."""
        return SerializationFormat.JSON

    @property
    def binary_output(self) -> bool:
        """Whether serializer produces binary output."""
        return False


class YAMLSerializer(BaseSerializer):
    """YAML serializer implementation."""

    def __init__(self, config: SerializerConfig | None = None):
        config = config or SerializerConfig(format=SerializationFormat.YAML)
        super().__init__(config)

    def serialize(self, data: Any) -> str:
        """Serialize data to YAML string."""
        try:
            import yaml

            return yaml.safe_dump(
                data,
                default_flow_style=not self.config.pretty_print,
                allow_unicode=not self.config.ensure_ascii,
            )
        except ImportError:
            raise SerializationError(
                "PyYAML not installed. Install with: pip install pyyaml"
            ) from None
        except Exception as e:
            raise SerializationError(f"YAML serialization failed: {e}") from e

    def deserialize(self, data: str | bytes) -> Any:
        """Deserialize YAML string to data."""
        try:
            import yaml

            if isinstance(data, bytes):
                data = data.decode("utf-8")
            return yaml.safe_load(data)
        except ImportError:
            raise DeserializationError(
                "PyYAML not installed. Install with: pip install pyyaml"
            ) from None
        except Exception as e:
            raise DeserializationError(f"YAML deserialization failed: {e}") from e

    @property
    def format(self) -> SerializationFormat:
        """Get serialization format."""
        return SerializationFormat.YAML

    @property
    def binary_output(self) -> bool:
        """Whether serializer produces binary output."""
        return False


class MessagePackSerializer(BaseSerializer):
    """MessagePack serializer implementation."""

    def __init__(self, config: SerializerConfig | None = None):
        config = config or SerializerConfig(format=SerializationFormat.MSGPACK)
        super().__init__(config)

    def serialize(self, data: Any) -> bytes:
        """Serialize data to MessagePack bytes."""
        try:
            import msgpack

            return msgpack.packb(data, use_bin_type=True)
        except ImportError:
            raise SerializationError(
                "msgpack not installed. Install with: pip install msgpack"
            ) from None
        except Exception as e:
            raise SerializationError(f"MessagePack serialization failed: {e}") from e

    def deserialize(self, data: str | bytes) -> Any:
        """Deserialize MessagePack bytes to data."""
        try:
            import msgpack

            if isinstance(data, str):
                data = data.encode("utf-8")
            return msgpack.unpackb(data, raw=False)
        except ImportError:
            raise DeserializationError(
                "msgpack not installed. Install with: pip install msgpack"
            ) from None
        except Exception as e:
            raise DeserializationError(
                f"MessagePack deserialization failed: {e}"
            ) from e

    @property
    def format(self) -> SerializationFormat:
        """Get serialization format."""
        return SerializationFormat.MSGPACK

    @property
    def binary_output(self) -> bool:
        """Whether serializer produces binary output."""
        return True


class PickleSerializer(BaseSerializer):
    """Pickle serializer implementation (use with caution)."""

    def __init__(self, config: SerializerConfig | None = None):
        config = config or SerializerConfig(format=SerializationFormat.PICKLE)
        super().__init__(config)
        logger.warning(
            "Pickle serializer is insecure and should not be used with untrusted data"
        )

    def serialize(self, data: Any) -> bytes:
        """Serialize data to pickle bytes."""
        try:
            import pickle

            return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            raise SerializationError(f"Pickle serialization failed: {e}") from e

    def deserialize(self, data: str | bytes) -> Any:
        """Deserialize pickle bytes to data."""
        try:
            import pickle

            if isinstance(data, str):
                data = data.encode("utf-8")
            return pickle.loads(data)
        except Exception as e:
            raise DeserializationError(f"Pickle deserialization failed: {e}") from e

    @property
    def format(self) -> SerializationFormat:
        """Get serialization format."""
        return SerializationFormat.PICKLE

    @property
    def binary_output(self) -> bool:
        """Whether serializer produces binary output."""
        return True


class SerializationManager(BaseComponent):
    """Serialization manager with multiple format support."""

    def __init__(self, default_format: SerializationFormat = SerializationFormat.JSON):
        super().__init__()
        self.default_format = default_format
        self._serializers: dict[SerializationFormat, BaseSerializer] = {}
        self._register_default_serializers()

    def _register_default_serializers(self) -> None:
        """Register default serializers."""
        self._serializers[SerializationFormat.JSON] = JSONSerializer()
        self._serializers[SerializationFormat.YAML] = YAMLSerializer()
        self._serializers[SerializationFormat.MSGPACK] = MessagePackSerializer()
        self._serializers[SerializationFormat.PICKLE] = PickleSerializer()

    def register_serializer(
        self, format: SerializationFormat, serializer: BaseSerializer
    ) -> None:
        """Register a custom serializer."""
        self._serializers[format] = serializer
        logger.info("Registered serializer for format: %s", format)

    def get_serializer(
        self, format: SerializationFormat | None = None
    ) -> BaseSerializer:
        """Get serializer for format."""
        format = format or self.default_format
        if format not in self._serializers:
            raise SerializationError(f"Unsupported serialization format: {format}")
        return self._serializers[format]

    def serialize(
        self, data: Any, format: SerializationFormat | None = None
    ) -> str | bytes:
        """Serialize data using specified format."""
        serializer = self.get_serializer(format)
        return serializer.serialize(data)

    def deserialize(
        self, data: str | bytes, format: SerializationFormat | None = None
    ) -> Any:
        """Deserialize data using specified format."""
        serializer = self.get_serializer(format)
        return serializer.deserialize(data)

    def set_default_format(self, format: SerializationFormat) -> None:
        """Set default serialization format."""
        if format not in self._serializers:
            raise SerializationError(f"Unsupported serialization format: {format}")
        self.default_format = format
        logger.info("Set default serialization format: %s", format)

    def get_supported_formats(self) -> list[SerializationFormat]:
        """Get list of supported formats."""
        return list(self._serializers.keys())

    def detect_format(self, data: str | bytes) -> SerializationFormat | None:
        """Attempt to detect serialization format from data."""
        if isinstance(data, bytes):
            # Check for MessagePack magic bytes
            if (
                data.startswith(b"\x81")
                or data.startswith(b"\x82")
                or data.startswith(b"\x83")
            ):
                return SerializationFormat.MSGPACK
            # Check for pickle magic bytes
            if data.startswith(b"\x80"):
                return SerializationFormat.PICKLE
            # Try to decode as string for text formats
            try:
                data = data.decode("utf-8")
            except UnicodeDecodeError:
                return None

        if isinstance(data, str):
            data = data.strip()
            # Check for JSON
            if (data.startswith("{") and data.endswith("}")) or (
                data.startswith("[") and data.endswith("]")
            ):
                return SerializationFormat.JSON
            # Check for YAML
            if ":" in data and not data.startswith("{"):
                return SerializationFormat.YAML

        return None
