"""
Compression utilities for OPSVI Foundation.

Provides comprehensive compression and decompression functionality.
"""

import bz2
import gzip
import logging
import lzma
import zlib
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

import brotli

logger = logging.getLogger(__name__)


class CompressionFormat(Enum):
    """Supported compression formats."""

    GZIP = "gzip"
    BZIP2 = "bzip2"
    LZMA = "lzma"
    ZLIB = "zlib"
    BROTLI = "brotli"
    NONE = "none"


class CompressionError(Exception):
    """Exception raised when compression operations fail."""


class DecompressionError(Exception):
    """Exception raised when decompression operations fail."""


class Compressor(ABC):
    """Abstract base class for compressors."""

    def __init__(self, format_type: CompressionFormat) -> None:
        self.format_type = format_type

    @abstractmethod
    def compress(self, data: str | bytes, **kwargs) -> bytes:
        """Compress data."""

    @abstractmethod
    def decompress(self, data: bytes, **kwargs) -> str | bytes:
        """Decompress data."""

    @abstractmethod
    def get_compression_ratio(self, original_size: int, compressed_size: int) -> float:
        """Calculate compression ratio."""


class GzipCompressor(Compressor):
    """Gzip compressor implementation."""

    def __init__(self, compression_level: int = 6) -> None:
        super().__init__(CompressionFormat.GZIP)
        self.compression_level = compression_level

    def compress(self, data: str | bytes, **kwargs) -> bytes:
        """Compress data using gzip."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            level = kwargs.get("compression_level", self.compression_level)
            return gzip.compress(data, compresslevel=level)
        except Exception as e:
            raise CompressionError(f"Gzip compression failed: {e}")

    def decompress(self, data: bytes, **kwargs) -> str | bytes:
        """Decompress data using gzip."""
        try:
            decompressed = gzip.decompress(data)

            # Try to decode as string if possible
            try:
                return decompressed.decode("utf-8")
            except UnicodeDecodeError:
                return decompressed
        except Exception as e:
            raise DecompressionError(f"Gzip decompression failed: {e}")

    def get_compression_ratio(self, original_size: int, compressed_size: int) -> float:
        """Calculate compression ratio."""
        if original_size == 0:
            return 0.0
        return (1 - compressed_size / original_size) * 100


class Bzip2Compressor(Compressor):
    """Bzip2 compressor implementation."""

    def __init__(self, compression_level: int = 9) -> None:
        super().__init__(CompressionFormat.BZIP2)
        self.compression_level = compression_level

    def compress(self, data: str | bytes, **kwargs) -> bytes:
        """Compress data using bzip2."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            level = kwargs.get("compression_level", self.compression_level)
            return bz2.compress(data, compresslevel=level)
        except Exception as e:
            raise CompressionError(f"Bzip2 compression failed: {e}")

    def decompress(self, data: bytes, **kwargs) -> str | bytes:
        """Decompress data using bzip2."""
        try:
            decompressed = bz2.decompress(data)

            # Try to decode as string if possible
            try:
                return decompressed.decode("utf-8")
            except UnicodeDecodeError:
                return decompressed
        except Exception as e:
            raise DecompressionError(f"Bzip2 decompression failed: {e}")

    def get_compression_ratio(self, original_size: int, compressed_size: int) -> float:
        """Calculate compression ratio."""
        if original_size == 0:
            return 0.0
        return (1 - compressed_size / original_size) * 100


class LzmaCompressor(Compressor):
    """LZMA compressor implementation."""

    def __init__(self, compression_level: int = 6) -> None:
        super().__init__(CompressionFormat.LZMA)
        self.compression_level = compression_level

    def compress(self, data: str | bytes, **kwargs) -> bytes:
        """Compress data using LZMA."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            level = kwargs.get("compression_level", self.compression_level)
            return lzma.compress(data, preset=level)
        except Exception as e:
            raise CompressionError(f"LZMA compression failed: {e}")

    def decompress(self, data: bytes, **kwargs) -> str | bytes:
        """Decompress data using LZMA."""
        try:
            decompressed = lzma.decompress(data)

            # Try to decode as string if possible
            try:
                return decompressed.decode("utf-8")
            except UnicodeDecodeError:
                return decompressed
        except Exception as e:
            raise DecompressionError(f"LZMA decompression failed: {e}")

    def get_compression_ratio(self, original_size: int, compressed_size: int) -> float:
        """Calculate compression ratio."""
        if original_size == 0:
            return 0.0
        return (1 - compressed_size / original_size) * 100


class ZlibCompressor(Compressor):
    """Zlib compressor implementation."""

    def __init__(self, compression_level: int = 6) -> None:
        super().__init__(CompressionFormat.ZLIB)
        self.compression_level = compression_level

    def compress(self, data: str | bytes, **kwargs) -> bytes:
        """Compress data using zlib."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            level = kwargs.get("compression_level", self.compression_level)
            return zlib.compress(data, level=level)
        except Exception as e:
            raise CompressionError(f"Zlib compression failed: {e}")

    def decompress(self, data: bytes, **kwargs) -> str | bytes:
        """Decompress data using zlib."""
        try:
            decompressed = zlib.decompress(data)

            # Try to decode as string if possible
            try:
                return decompressed.decode("utf-8")
            except UnicodeDecodeError:
                return decompressed
        except Exception as e:
            raise DecompressionError(f"Zlib decompression failed: {e}")

    def get_compression_ratio(self, original_size: int, compressed_size: int) -> float:
        """Calculate compression ratio."""
        if original_size == 0:
            return 0.0
        return (1 - compressed_size / original_size) * 100


class BrotliCompressor(Compressor):
    """Brotli compressor implementation."""

    def __init__(self, quality: int = 11) -> None:
        super().__init__(CompressionFormat.BROTLI)
        self.quality = quality

    def compress(self, data: str | bytes, **kwargs) -> bytes:
        """Compress data using Brotli."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            quality = kwargs.get("quality", self.quality)
            return brotli.compress(data, quality=quality)
        except Exception as e:
            raise CompressionError(f"Brotli compression failed: {e}")

    def decompress(self, data: bytes, **kwargs) -> str | bytes:
        """Decompress data using Brotli."""
        try:
            decompressed = brotli.decompress(data)

            # Try to decode as string if possible
            try:
                return decompressed.decode("utf-8")
            except UnicodeDecodeError:
                return decompressed
        except Exception as e:
            raise DecompressionError(f"Brotli decompression failed: {e}")

    def get_compression_ratio(self, original_size: int, compressed_size: int) -> float:
        """Calculate compression ratio."""
        if original_size == 0:
            return 0.0
        return (1 - compressed_size / original_size) * 100


class NoCompressor(Compressor):
    """No compression implementation (pass-through)."""

    def __init__(self) -> None:
        super().__init__(CompressionFormat.NONE)

    def compress(self, data: str | bytes, **kwargs) -> bytes:
        """Return data as-is (no compression)."""
        if isinstance(data, str):
            return data.encode("utf-8")
        return data

    def decompress(self, data: bytes, **kwargs) -> str | bytes:
        """Return data as-is (no decompression)."""
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data

    def get_compression_ratio(self, original_size: int, compressed_size: int) -> float:
        """Calculate compression ratio (always 0 for no compression)."""
        return 0.0


class CompressionManager:
    """Manager for handling multiple compression formats."""

    def __init__(self) -> None:
        self.compressors: dict[CompressionFormat, Compressor] = {
            CompressionFormat.GZIP: GzipCompressor(),
            CompressionFormat.BZIP2: Bzip2Compressor(),
            CompressionFormat.LZMA: LzmaCompressor(),
            CompressionFormat.ZLIB: ZlibCompressor(),
            CompressionFormat.BROTLI: BrotliCompressor(),
            CompressionFormat.NONE: NoCompressor(),
        }
        self._default_format = CompressionFormat.GZIP

    def get_compressor(self, format_type: CompressionFormat) -> Compressor:
        """Get a compressor for the specified format."""
        if format_type not in self.compressors:
            raise ValueError(f"Unsupported compression format: {format_type}")
        return self.compressors[format_type]

    def register_compressor(
        self,
        format_type: CompressionFormat,
        compressor: Compressor,
    ) -> None:
        """Register a custom compressor."""
        self.compressors[format_type] = compressor
        logger.info(f"Registered custom compressor for format: {format_type}")

    def set_default_format(self, format_type: CompressionFormat) -> None:
        """Set the default compression format."""
        if format_type not in self.compressors:
            raise ValueError(f"Unsupported compression format: {format_type}")
        self._default_format = format_type
        logger.info(f"Set default compression format: {format_type}")

    def get_default_format(self) -> CompressionFormat:
        """Get the default compression format."""
        return self._default_format

    def compress(
        self,
        data: str | bytes,
        format_type: CompressionFormat | None = None,
        **kwargs,
    ) -> bytes:
        """Compress data using the specified format."""
        format_type = format_type or self._default_format
        compressor = self.get_compressor(format_type)
        return compressor.compress(data, **kwargs)

    def decompress(
        self,
        data: bytes,
        format_type: CompressionFormat | None = None,
        **kwargs,
    ) -> str | bytes:
        """Decompress data using the specified format."""
        format_type = format_type or self._default_format
        compressor = self.get_compressor(format_type)
        return compressor.decompress(data, **kwargs)

    def auto_detect_format(self, data: bytes) -> CompressionFormat | None:
        """Auto-detect the compression format of data."""
        if data.startswith(b"\x1f\x8b"):  # Gzip magic number
            return CompressionFormat.GZIP
        if data.startswith(b"BZ"):  # Bzip2 magic number
            return CompressionFormat.BZIP2
        if data.startswith(b"\xfd7zXZ"):  # LZMA magic number
            return CompressionFormat.LZMA
        if data.startswith(b"\x78"):  # Zlib magic number
            return CompressionFormat.ZLIB
        if data.startswith(b"\x0b"):  # Brotli magic number
            return CompressionFormat.BROTLI
        return None

    def benchmark_compression(
        self,
        data: str | bytes,
        formats: list | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Benchmark compression across different formats."""
        if formats is None:
            formats = list(CompressionFormat)

        results = {}
        original_size = len(data.encode("utf-8") if isinstance(data, str) else data)

        for format_type in formats:
            try:
                compressor = self.get_compressor(format_type)
                compressed = compressor.compress(data)
                compressed_size = len(compressed)
                ratio = compressor.get_compression_ratio(original_size, compressed_size)

                results[format_type.value] = {
                    "original_size": original_size,
                    "compressed_size": compressed_size,
                    "compression_ratio": ratio,
                    "compressed_data": compressed,
                }
            except Exception as e:
                logger.error(f"Benchmark failed for {format_type}: {e}")
                results[format_type.value] = {"error": str(e)}

        return results


# Global compression manager
compression_manager = CompressionManager()


# Convenience functions


def compress(
    data: str | bytes,
    format_type: CompressionFormat | None = None,
    **kwargs,
) -> bytes:
    """Compress data using the global compression manager."""
    return compression_manager.compress(data, format_type, **kwargs)


def decompress(
    data: bytes,
    format_type: CompressionFormat | None = None,
    **kwargs,
) -> str | bytes:
    """Decompress data using the global compression manager."""
    return compression_manager.decompress(data, format_type, **kwargs)


def compress_gzip(data: str | bytes, compression_level: int = 6) -> bytes:
    """Compress data using gzip."""
    compressor = GzipCompressor(compression_level)
    return compressor.compress(data)


def decompress_gzip(data: bytes) -> str | bytes:
    """Decompress data using gzip."""
    compressor = GzipCompressor()
    return compressor.decompress(data)


def compress_bzip2(data: str | bytes, compression_level: int = 9) -> bytes:
    """Compress data using bzip2."""
    compressor = Bzip2Compressor(compression_level)
    return compressor.compress(data)


def decompress_bzip2(data: bytes) -> str | bytes:
    """Decompress data using bzip2."""
    compressor = Bzip2Compressor()
    return compressor.decompress(data)


def compress_lzma(data: str | bytes, compression_level: int = 6) -> bytes:
    """Compress data using LZMA."""
    compressor = LzmaCompressor(compression_level)
    return compressor.compress(data)


def decompress_lzma(data: bytes) -> str | bytes:
    """Decompress data using LZMA."""
    compressor = LzmaCompressor()
    return compressor.decompress(data)


def compress_zlib(data: str | bytes, compression_level: int = 6) -> bytes:
    """Compress data using zlib."""
    compressor = ZlibCompressor(compression_level)
    return compressor.compress(data)


def decompress_zlib(data: bytes) -> str | bytes:
    """Decompress data using zlib."""
    compressor = ZlibCompressor()
    return compressor.decompress(data)


def compress_brotli(data: str | bytes, quality: int = 11) -> bytes:
    """Compress data using Brotli."""
    compressor = BrotliCompressor(quality)
    return compressor.compress(data)


def decompress_brotli(data: bytes) -> str | bytes:
    """Decompress data using Brotli."""
    compressor = BrotliCompressor()
    return compressor.decompress(data)


# File compression utilities


def compress_file(
    input_path: str,
    output_path: str,
    format_type: CompressionFormat = CompressionFormat.GZIP,
    **kwargs,
) -> None:
    """Compress a file."""
    try:
        with open(input_path, "rb") as input_file:
            data = input_file.read()

        compressed_data = compress(data, format_type, **kwargs)

        with open(output_path, "wb") as output_file:
            output_file.write(compressed_data)

        logger.info(f"Compressed {input_path} to {output_path}")
    except Exception as e:
        raise CompressionError(f"File compression failed: {e}")


def decompress_file(
    input_path: str,
    output_path: str,
    format_type: CompressionFormat | None = None,
    **kwargs,
) -> None:
    """Decompress a file."""
    try:
        with open(input_path, "rb") as input_file:
            compressed_data = input_file.read()

        if format_type is None:
            format_type = compression_manager.auto_detect_format(compressed_data)
            if format_type is None:
                raise DecompressionError("Could not auto-detect compression format")

        decompressed_data = decompress(compressed_data, format_type, **kwargs)

        if isinstance(decompressed_data, str):
            mode = "w"
            encoding = "utf-8"
        else:
            mode = "wb"
            encoding = None

        with open(output_path, mode, encoding=encoding) as output_file:
            output_file.write(decompressed_data)

        logger.info(f"Decompressed {input_path} to {output_path}")
    except Exception as e:
        raise DecompressionError(f"File decompression failed: {e}")


# Compression analysis utilities


def analyze_compression(data: str | bytes) -> dict[str, dict[str, Any]]:
    """Analyze compression effectiveness across different formats."""
    return compression_manager.benchmark_compression(data)


def get_best_compression(
    data: str | bytes,
) -> tuple[CompressionFormat, bytes, float]:
    """Get the best compression format for the given data."""
    results = analyze_compression(data)

    best_format = None
    best_ratio = -1
    best_compressed = None

    for format_name, result in results.items():
        if "error" not in result:
            ratio = result["compression_ratio"]
            if ratio > best_ratio:
                best_ratio = ratio
                best_format = CompressionFormat(format_name)
                best_compressed = result["compressed_data"]

    if best_format is None:
        raise CompressionError("No compression format worked")

    return best_format, best_compressed, best_ratio


def is_compressed(data: bytes) -> bool:
    """Check if data appears to be compressed."""
    return compression_manager.auto_detect_format(data) is not None


def get_compression_info(data: bytes) -> dict[str, Any] | None:
    """Get information about compressed data."""
    format_type = compression_manager.auto_detect_format(data)
    if format_type is None:
        return None

    try:
        compressor = compression_manager.get_compressor(format_type)
        decompressed = compressor.decompress(data)
        original_size = len(
            decompressed.encode("utf-8")
            if isinstance(decompressed, str)
            else decompressed,
        )
        compressed_size = len(data)
        ratio = compressor.get_compression_ratio(original_size, compressed_size)

        return {
            "format": format_type.value,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": ratio,
            "savings_percent": ratio,
        }
    except Exception as e:
        logger.error(f"Error getting compression info: {e}")
        return None
