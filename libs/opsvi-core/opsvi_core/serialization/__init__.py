"""
Serialization module for opsvi-core.

Provides data serialization and format conversion capabilities.
"""

from opsvi_foundation import (
    BaseComponent,
    ComponentError,
    get_logger,
)

# Base serialization infrastructure
from .base import (
    BaseSerializer,
    DeserializationError,
    JSONSerializer,
    MessagePackSerializer,
    PickleSerializer,
    SerializationError,
    SerializationFormat,
    SerializationManager,
    SerializerConfig,
    YAMLSerializer,
)

__all__ = [
    # Base classes
    "BaseSerializer",
    "DeserializationError",
    "JSONSerializer",
    "MessagePackSerializer",
    "PickleSerializer",
    "SerializationError",
    "SerializationFormat",
    "SerializationManager",
    "SerializerConfig",
    "YAMLSerializer",
]

__version__ = "1.0.0"
