"""
Encoding utilities for OPSVI Foundation.

Provides comprehensive encoding and decoding functionality.
"""

import base64
import json
import logging
import quopri
import urllib.parse
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EncodingFormat(Enum):
    """Supported encoding formats."""

    BASE64 = "base64"
    BASE32 = "base32"
    BASE16 = "base16"
    HEX = "hex"
    URL_ENCODE = "url_encode"
    QUOTED_PRINTABLE = "quoted_printable"
    JSON = "json"
    UTF8 = "utf8"
    ASCII = "ascii"
    LATIN1 = "latin1"


class EncodingError(Exception):
    """Exception raised when encoding operations fail."""


class DecodingError(Exception):
    """Exception raised when decoding operations fail."""


class Encoder(ABC):
    """Abstract base class for encoders."""

    def __init__(self, format_type: EncodingFormat) -> None:
        self.format_type = format_type

    @abstractmethod
    def encode(self, data: str | bytes, **kwargs) -> str:
        """Encode data."""

    @abstractmethod
    def decode(self, data: str, **kwargs) -> str | bytes:
        """Decode data."""


class Base64Encoder(Encoder):
    """Base64 encoder implementation."""

    def __init__(self) -> None:
        super().__init__(EncodingFormat.BASE64)

    def encode(self, data: str | bytes, **kwargs) -> str:
        """Encode data using base64."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            return base64.b64encode(data).decode("ascii")
        except Exception as e:
            raise EncodingError(f"Base64 encoding failed: {e}")

    def decode(self, data: str, **kwargs) -> str | bytes:
        """Decode data using base64."""
        try:
            decoded = base64.b64decode(data.encode("ascii"))

            # Try to decode as string if possible
            try:
                return decoded.decode("utf-8")
            except UnicodeDecodeError:
                return decoded
        except Exception as e:
            raise DecodingError(f"Base64 decoding failed: {e}")


class Base32Encoder(Encoder):
    """Base32 encoder implementation."""

    def __init__(self) -> None:
        super().__init__(EncodingFormat.BASE32)

    def encode(self, data: str | bytes, **kwargs) -> str:
        """Encode data using base32."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            return base64.b32encode(data).decode("ascii")
        except Exception as e:
            raise EncodingError(f"Base32 encoding failed: {e}")

    def decode(self, data: str, **kwargs) -> str | bytes:
        """Decode data using base32."""
        try:
            decoded = base64.b32decode(data.encode("ascii"))

            # Try to decode as string if possible
            try:
                return decoded.decode("utf-8")
            except UnicodeDecodeError:
                return decoded
        except Exception as e:
            raise DecodingError(f"Base32 decoding failed: {e}")


class Base16Encoder(Encoder):
    """Base16 encoder implementation."""

    def __init__(self) -> None:
        super().__init__(EncodingFormat.BASE16)

    def encode(self, data: str | bytes, **kwargs) -> str:
        """Encode data using base16."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            return base64.b16encode(data).decode("ascii")
        except Exception as e:
            raise EncodingError(f"Base16 encoding failed: {e}")

    def decode(self, data: str, **kwargs) -> str | bytes:
        """Decode data using base16."""
        try:
            decoded = base64.b16decode(data.encode("ascii"))

            # Try to decode as string if possible
            try:
                return decoded.decode("utf-8")
            except UnicodeDecodeError:
                return decoded
        except Exception as e:
            raise DecodingError(f"Base16 decoding failed: {e}")


class HexEncoder(Encoder):
    """Hex encoder implementation."""

    def __init__(self) -> None:
        super().__init__(EncodingFormat.HEX)

    def encode(self, data: str | bytes, **kwargs) -> str:
        """Encode data using hex."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            return data.hex()
        except Exception as e:
            raise EncodingError(f"Hex encoding failed: {e}")

    def decode(self, data: str, **kwargs) -> str | bytes:
        """Decode data using hex."""
        try:
            decoded = bytes.fromhex(data)

            # Try to decode as string if possible
            try:
                return decoded.decode("utf-8")
            except UnicodeDecodeError:
                return decoded
        except Exception as e:
            raise DecodingError(f"Hex decoding failed: {e}")


class URLEncoder(Encoder):
    """URL encoder implementation."""

    def __init__(self) -> None:
        super().__init__(EncodingFormat.URL_ENCODE)

    def encode(self, data: str | bytes, **kwargs) -> str:
        """Encode data using URL encoding."""
        try:
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            return urllib.parse.quote(data)
        except Exception as e:
            raise EncodingError(f"URL encoding failed: {e}")

    def decode(self, data: str, **kwargs) -> str | bytes:
        """Decode data using URL decoding."""
        try:
            decoded = urllib.parse.unquote(data)
            return decoded
        except Exception as e:
            raise DecodingError(f"URL decoding failed: {e}")


class QuotedPrintableEncoder(Encoder):
    """Quoted-printable encoder implementation."""

    def __init__(self) -> None:
        super().__init__(EncodingFormat.QUOTED_PRINTABLE)

    def encode(self, data: str | bytes, **kwargs) -> str:
        """Encode data using quoted-printable."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            return quopri.encodestring(data).decode("ascii")
        except Exception as e:
            raise EncodingError(f"Quoted-printable encoding failed: {e}")

    def decode(self, data: str, **kwargs) -> str | bytes:
        """Decode data using quoted-printable."""
        try:
            decoded = quopri.decodestring(data.encode("ascii"))

            # Try to decode as string if possible
            try:
                return decoded.decode("utf-8")
            except UnicodeDecodeError:
                return decoded
        except Exception as e:
            raise DecodingError(f"Quoted-printable decoding failed: {e}")


class JSONEncoder(Encoder):
    """JSON encoder implementation."""

    def __init__(self) -> None:
        super().__init__(EncodingFormat.JSON)

    def encode(self, data: str | bytes, **kwargs) -> str:
        """Encode data using JSON."""
        try:
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            return json.dumps(data, **kwargs)
        except Exception as e:
            raise EncodingError(f"JSON encoding failed: {e}")

    def decode(self, data: str, **kwargs) -> str | bytes:
        """Decode data using JSON."""
        try:
            decoded = json.loads(data, **kwargs)
            return decoded
        except Exception as e:
            raise DecodingError(f"JSON decoding failed: {e}")


class UTF8Encoder(Encoder):
    """UTF-8 encoder implementation."""

    def __init__(self) -> None:
        super().__init__(EncodingFormat.UTF8)

    def encode(self, data: str | bytes, **kwargs) -> str:
        """Encode data using UTF-8."""
        try:
            if isinstance(data, bytes):
                return data.decode("utf-8")
            return data
        except Exception as e:
            raise EncodingError(f"UTF-8 encoding failed: {e}")

    def decode(self, data: str, **kwargs) -> str | bytes:
        """Decode data using UTF-8."""
        try:
            return data.encode("utf-8")
        except Exception as e:
            raise DecodingError(f"UTF-8 decoding failed: {e}")


class ASCIIEncoder(Encoder):
    """ASCII encoder implementation."""

    def __init__(self) -> None:
        super().__init__(EncodingFormat.ASCII)

    def encode(self, data: str | bytes, **kwargs) -> str:
        """Encode data using ASCII."""
        try:
            if isinstance(data, bytes):
                return data.decode("ascii")
            return data
        except Exception as e:
            raise EncodingError(f"ASCII encoding failed: {e}")

    def decode(self, data: str, **kwargs) -> str | bytes:
        """Decode data using ASCII."""
        try:
            return data.encode("ascii")
        except Exception as e:
            raise DecodingError(f"ASCII decoding failed: {e}")


class Latin1Encoder(Encoder):
    """Latin-1 encoder implementation."""

    def __init__(self) -> None:
        super().__init__(EncodingFormat.LATIN1)

    def encode(self, data: str | bytes, **kwargs) -> str:
        """Encode data using Latin-1."""
        try:
            if isinstance(data, bytes):
                return data.decode("latin1")
            return data
        except Exception as e:
            raise EncodingError(f"Latin-1 encoding failed: {e}")

    def decode(self, data: str, **kwargs) -> str | bytes:
        """Decode data using Latin-1."""
        try:
            return data.encode("latin1")
        except Exception as e:
            raise DecodingError(f"Latin-1 decoding failed: {e}")


class EncodingManager:
    """Manager for handling multiple encoding formats."""

    def __init__(self) -> None:
        self.encoders: dict[EncodingFormat, Encoder] = {
            EncodingFormat.BASE64: Base64Encoder(),
            EncodingFormat.BASE32: Base32Encoder(),
            EncodingFormat.BASE16: Base16Encoder(),
            EncodingFormat.HEX: HexEncoder(),
            EncodingFormat.URL_ENCODE: URLEncoder(),
            EncodingFormat.QUOTED_PRINTABLE: QuotedPrintableEncoder(),
            EncodingFormat.JSON: JSONEncoder(),
            EncodingFormat.UTF8: UTF8Encoder(),
            EncodingFormat.ASCII: ASCIIEncoder(),
            EncodingFormat.LATIN1: Latin1Encoder(),
        }
        self._default_format = EncodingFormat.BASE64

    def get_encoder(self, format_type: EncodingFormat) -> Encoder:
        """Get an encoder for the specified format."""
        if format_type not in self.encoders:
            raise ValueError(f"Unsupported encoding format: {format_type}")
        return self.encoders[format_type]

    def register_encoder(self, format_type: EncodingFormat, encoder: Encoder) -> None:
        """Register a custom encoder."""
        self.encoders[format_type] = encoder
        logger.info(f"Registered custom encoder for format: {format_type}")

    def set_default_format(self, format_type: EncodingFormat) -> None:
        """Set the default encoding format."""
        if format_type not in self.encoders:
            raise ValueError(f"Unsupported encoding format: {format_type}")
        self._default_format = format_type
        logger.info(f"Set default encoding format: {format_type}")

    def get_default_format(self) -> EncodingFormat:
        """Get the default encoding format."""
        return self._default_format

    def encode(
        self,
        data: str | bytes,
        format_type: EncodingFormat | None = None,
        **kwargs,
    ) -> str:
        """Encode data using the specified format."""
        format_type = format_type or self._default_format
        encoder = self.get_encoder(format_type)
        return encoder.encode(data, **kwargs)

    def decode(
        self,
        data: str,
        format_type: EncodingFormat | None = None,
        **kwargs,
    ) -> str | bytes:
        """Decode data using the specified format."""
        format_type = format_type or self._default_format
        encoder = self.get_encoder(format_type)
        return encoder.decode(data, **kwargs)

    def auto_detect_format(self, data: str) -> EncodingFormat | None:
        """Auto-detect the encoding format of data."""
        # Try to detect base64
        try:
            base64.b64decode(data.encode("ascii"))
            return EncodingFormat.BASE64
        except Exception:
            pass

        # Try to detect base32
        try:
            base64.b32decode(data.encode("ascii"))
            return EncodingFormat.BASE32
        except Exception:
            pass

        # Try to detect base16
        try:
            base64.b16decode(data.encode("ascii"))
            return EncodingFormat.BASE16
        except Exception:
            pass

        # Try to detect hex
        try:
            bytes.fromhex(data)
            return EncodingFormat.HEX
        except Exception:
            pass

        # Try to detect JSON
        try:
            json.loads(data)
            return EncodingFormat.JSON
        except Exception:
            pass

        # Try to detect URL encoding
        if "%" in data:
            return EncodingFormat.URL_ENCODE

        # Try to detect quoted-printable
        if "=" in data and data.count("=") > len(data) * 0.1:
            return EncodingFormat.QUOTED_PRINTABLE

        return None


# Global encoding manager
encoding_manager = EncodingManager()


# Convenience functions


def encode_data(
    data: str | bytes,
    format_type: EncodingFormat | None = None,
    **kwargs,
) -> str:
    """Encode data using the global encoding manager."""
    return encoding_manager.encode(data, format_type, **kwargs)


def decode_data(
    data: str,
    format_type: EncodingFormat | None = None,
    **kwargs,
) -> str | bytes:
    """Decode data using the global encoding manager."""
    return encoding_manager.decode(data, format_type, **kwargs)


def encode_base64(data: str | bytes) -> str:
    """Encode data using base64."""
    encoder = Base64Encoder()
    return encoder.encode(data)


def decode_base64(data: str) -> str | bytes:
    """Decode data using base64."""
    encoder = Base64Encoder()
    return encoder.decode(data)


def encode_base32(data: str | bytes) -> str:
    """Encode data using base32."""
    encoder = Base32Encoder()
    return encoder.encode(data)


def decode_base32(data: str) -> str | bytes:
    """Decode data using base32."""
    encoder = Base32Encoder()
    return encoder.decode(data)


def encode_base16(data: str | bytes) -> str:
    """Encode data using base16."""
    encoder = Base16Encoder()
    return encoder.encode(data)


def decode_base16(data: str) -> str | bytes:
    """Decode data using base16."""
    encoder = Base16Encoder()
    return encoder.decode(data)


def encode_hex(data: str | bytes) -> str:
    """Encode data using hex."""
    encoder = HexEncoder()
    return encoder.encode(data)


def decode_hex(data: str) -> str | bytes:
    """Decode data using hex."""
    encoder = HexEncoder()
    return encoder.decode(data)


def encode_url(data: str | bytes) -> str:
    """Encode data using URL encoding."""
    encoder = URLEncoder()
    return encoder.encode(data)


def decode_url(data: str) -> str | bytes:
    """Decode data using URL decoding."""
    encoder = URLEncoder()
    return encoder.decode(data)


def encode_quoted_printable(data: str | bytes) -> str:
    """Encode data using quoted-printable."""
    encoder = QuotedPrintableEncoder()
    return encoder.encode(data)


def decode_quoted_printable(data: str) -> str | bytes:
    """Decode data using quoted-printable."""
    encoder = QuotedPrintableEncoder()
    return encoder.decode(data)


def encode_json(data: str | bytes, **kwargs) -> str:
    """Encode data using JSON."""
    encoder = JSONEncoder()
    return encoder.encode(data, **kwargs)


def decode_json(data: str, **kwargs) -> str | bytes:
    """Decode data using JSON."""
    encoder = JSONEncoder()
    return encoder.decode(data, **kwargs)


def encode_utf8(data: str | bytes) -> str:
    """Encode data using UTF-8."""
    encoder = UTF8Encoder()
    return encoder.encode(data)


def decode_utf8(data: str) -> str | bytes:
    """Decode data using UTF-8."""
    encoder = UTF8Encoder()
    return encoder.decode(data)


def encode_ascii(data: str | bytes) -> str:
    """Encode data using ASCII."""
    encoder = ASCIIEncoder()
    return encoder.encode(data)


def decode_ascii(data: str) -> str | bytes:
    """Decode data using ASCII."""
    encoder = ASCIIEncoder()
    return encoder.decode(data)


def encode_latin1(data: str | bytes) -> str:
    """Encode data using Latin-1."""
    encoder = Latin1Encoder()
    return encoder.encode(data)


def decode_latin1(data: str) -> str | bytes:
    """Decode data using Latin-1."""
    encoder = Latin1Encoder()
    return encoder.decode(data)


# Multi-format encoding utilities


def encode_multiple_formats(
    data: str | bytes,
    formats: list[EncodingFormat],
) -> dict[str, str]:
    """Encode data in multiple formats."""
    results = {}

    for format_type in formats:
        try:
            encoded = encode_data(data, format_type)
            results[format_type.value] = encoded
        except Exception as e:
            logger.error(f"Failed to encode in {format_type}: {e}")
            results[format_type.value] = f"ERROR: {e}"

    return results


def decode_multiple_formats(
    data: str,
    formats: list[EncodingFormat],
) -> dict[str, str | bytes]:
    """Try to decode data in multiple formats."""
    results = {}

    for format_type in formats:
        try:
            decoded = decode_data(data, format_type)
            results[format_type.value] = decoded
        except Exception as e:
            logger.error(f"Failed to decode in {format_type}: {e}")
            results[format_type.value] = f"ERROR: {e}"

    return results


# Format detection utilities


def detect_encoding_format(data: str) -> EncodingFormat | None:
    """Detect the encoding format of data."""
    return encoding_manager.auto_detect_format(data)


def is_valid_encoding(data: str, format_type: EncodingFormat) -> bool:
    """Check if data is valid for a specific encoding format."""
    try:
        encoding_manager.decode(data, format_type)
        return True
    except Exception:
        return False


def get_encoding_info(data: str) -> dict[str, Any]:
    """Get information about the encoding of data."""
    detected_format = detect_encoding_format(data)

    info = {
        "data_length": len(data),
        "detected_format": detected_format.value if detected_format else None,
        "valid_formats": [],
    }

    # Check all formats
    for format_type in EncodingFormat:
        if is_valid_encoding(data, format_type):
            info["valid_formats"].append(format_type.value)

    return info


# File encoding utilities


def encode_file(
    input_path: str,
    output_path: str,
    format_type: EncodingFormat = EncodingFormat.BASE64,
) -> None:
    """Encode a file."""
    try:
        with open(input_path, "rb") as input_file:
            data = input_file.read()

        encoded_data = encode_data(data, format_type)

        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(encoded_data)

        logger.info(f"Encoded {input_path} to {output_path}")
    except Exception as e:
        raise EncodingError(f"File encoding failed: {e}")


def decode_file(
    input_path: str,
    output_path: str,
    format_type: EncodingFormat | None = None,
) -> None:
    """Decode a file."""
    try:
        with open(input_path, encoding="utf-8") as input_file:
            encoded_data = input_file.read()

        if format_type is None:
            format_type = detect_encoding_format(encoded_data)
            if format_type is None:
                raise DecodingError("Could not auto-detect encoding format")

        decoded_data = decode_data(encoded_data, format_type)

        if isinstance(decoded_data, str):
            mode = "w"
            encoding = "utf-8"
        else:
            mode = "wb"
            encoding = None

        with open(output_path, mode, encoding=encoding) as output_file:
            output_file.write(decoded_data)

        logger.info(f"Decoded {input_path} to {output_path}")
    except Exception as e:
        raise DecodingError(f"File decoding failed: {e}")


# Specialized encoding utilities


def encode_for_transmission(data: str | bytes) -> str:
    """Encode data for safe transmission (base64)."""
    return encode_base64(data)


def decode_from_transmission(data: str) -> str | bytes:
    """Decode data from transmission (base64)."""
    return decode_base64(data)


def encode_for_url(data: str | bytes) -> str:
    """Encode data for URL usage."""
    return encode_url(data)


def decode_from_url(data: str) -> str | bytes:
    """Decode data from URL."""
    return decode_url(data)


def encode_for_json(data: str | bytes) -> str:
    """Encode data for JSON usage."""
    return encode_json(data)


def decode_from_json(data: str) -> str | bytes:
    """Decode data from JSON."""
    return decode_json(data)


def encode_for_storage(data: str | bytes) -> str:
    """Encode data for storage (base64)."""
    return encode_base64(data)


def decode_from_storage(data: str) -> str | bytes:
    """Decode data from storage (base64)."""
    return decode_base64(data)
