#!/usr/bin/env python3
"""
High-performance File Compression with Multiprocessing
Supports multiple compression algorithms and batch processing
"""

import asyncio
import bz2
import gzip
import logging
import lzma
import shutil
import tarfile
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .multiprocess_executor import get_process_pool

logger = logging.getLogger(__name__)


@dataclass
class CompressionResult:
    """Result of compression operation"""

    original_file: str
    compressed_file: str
    original_size: int
    compressed_size: int
    compression_ratio: float
    algorithm: str
    time_elapsed: float = 0.0
    error: Optional[str] = None


class CompressionProcessor:
    """High-performance compression processor using multiprocessing"""

    ALGORITHMS = {
        "gzip": {"extension": ".gz", "levels": range(1, 10)},
        "bzip2": {"extension": ".bz2", "levels": range(1, 10)},
        "lzma": {"extension": ".xz", "levels": range(0, 10)},
        "zip": {
            "extension": ".zip",
            "levels": [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED],
        },
        "tar": {"extension": ".tar", "levels": [None]},
        "tar.gz": {"extension": ".tar.gz", "levels": range(1, 10)},
        "tar.bz2": {"extension": ".tar.bz2", "levels": range(1, 10)},
        "tar.xz": {"extension": ".tar.xz", "levels": range(0, 10)},
    }

    def __init__(self, use_multiprocessing: bool = True):
        self.use_multiprocessing = use_multiprocessing
        self.pool = None

    async def __aenter__(self):
        if self.use_multiprocessing:
            self.pool = await get_process_pool()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Pool is managed globally
        pass

    async def compress_file(
        self,
        file_path: Union[str, Path],
        algorithm: str = "gzip",
        level: Optional[int] = None,
        output_path: Optional[Union[str, Path]] = None,
        delete_original: bool = False,
    ) -> CompressionResult:
        """Compress a single file with specified algorithm"""
        import time

        start_time = time.time()

        path = Path(file_path)
        if not path.exists():
            return CompressionResult(
                original_file=str(file_path),
                compressed_file="",
                original_size=0,
                compressed_size=0,
                compression_ratio=0,
                algorithm=algorithm,
                error=f"File not found: {file_path}",
            )

        # Determine output path
        if output_path is None:
            ext = self.ALGORITHMS.get(algorithm, {}).get("extension", ".compressed")
            output_path = path.parent / f"{path.name}{ext}"
        else:
            output_path = Path(output_path)

        # Get default compression level
        if level is None:
            if algorithm in ["gzip", "bzip2"]:
                level = 6
            elif algorithm == "lzma":
                level = 6
            elif algorithm == "zip":
                level = zipfile.ZIP_DEFLATED

        original_size = path.stat().st_size

        try:
            if algorithm == "gzip":
                await self._compress_gzip(path, output_path, level)
            elif algorithm == "bzip2":
                await self._compress_bzip2(path, output_path, level)
            elif algorithm == "lzma":
                await self._compress_lzma(path, output_path, level)
            elif algorithm == "zip":
                await self._compress_zip(path, output_path, level)
            elif algorithm.startswith("tar"):
                await self._compress_tar(path, output_path, algorithm, level)
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")

            compressed_size = output_path.stat().st_size
            compression_ratio = (
                compressed_size / original_size if original_size > 0 else 0
            )

            # Delete original if requested
            if delete_original and output_path != path:
                path.unlink()

            return CompressionResult(
                original_file=str(file_path),
                compressed_file=str(output_path),
                original_size=original_size,
                compressed_size=compressed_size,
                compression_ratio=compression_ratio,
                algorithm=algorithm,
                time_elapsed=time.time() - start_time,
            )

        except Exception as e:
            return CompressionResult(
                original_file=str(file_path),
                compressed_file="",
                original_size=original_size,
                compressed_size=0,
                compression_ratio=0,
                algorithm=algorithm,
                time_elapsed=time.time() - start_time,
                error=str(e),
            )

    async def _compress_gzip(self, input_path: Path, output_path: Path, level: int):
        """Compress using gzip"""
        loop = asyncio.get_event_loop()

        def _compress():
            with open(input_path, "rb") as f_in:
                with gzip.open(output_path, "wb", compresslevel=level) as f_out:
                    shutil.copyfileobj(f_in, f_out, length=1024 * 1024)  # 1MB chunks

        await loop.run_in_executor(None, _compress)

    async def _compress_bzip2(self, input_path: Path, output_path: Path, level: int):
        """Compress using bzip2"""
        loop = asyncio.get_event_loop()

        def _compress():
            with open(input_path, "rb") as f_in:
                with bz2.open(output_path, "wb", compresslevel=level) as f_out:
                    shutil.copyfileobj(f_in, f_out, length=1024 * 1024)

        await loop.run_in_executor(None, _compress)

    async def _compress_lzma(self, input_path: Path, output_path: Path, level: int):
        """Compress using lzma"""
        loop = asyncio.get_event_loop()

        def _compress():
            with open(input_path, "rb") as f_in:
                with lzma.open(output_path, "wb", preset=level) as f_out:
                    shutil.copyfileobj(f_in, f_out, length=1024 * 1024)

        await loop.run_in_executor(None, _compress)

    async def _compress_zip(self, input_path: Path, output_path: Path, level: int):
        """Compress using zip"""
        loop = asyncio.get_event_loop()

        def _compress():
            with zipfile.ZipFile(output_path, "w", compression=level) as zf:
                zf.write(input_path, input_path.name)

        await loop.run_in_executor(None, _compress)

    async def _compress_tar(
        self, input_path: Path, output_path: Path, algorithm: str, level: int
    ):
        """Compress using tar with optional compression"""
        loop = asyncio.get_event_loop()

        def _compress():
            mode = "w"
            if algorithm == "tar.gz":
                mode = "w:gz"
            elif algorithm == "tar.bz2":
                mode = "w:bz2"
            elif algorithm == "tar.xz":
                mode = "w:xz"

            with tarfile.open(output_path, mode) as tar:
                tar.add(input_path, arcname=input_path.name)

        await loop.run_in_executor(None, _compress)

    async def compress_batch(
        self,
        file_paths: List[Union[str, Path]],
        algorithm: str = "gzip",
        level: Optional[int] = None,
        output_dir: Optional[Union[str, Path]] = None,
    ) -> List[CompressionResult]:
        """Compress multiple files using multiprocessing"""
        if not file_paths:
            return []

        # Use multiprocessing for large batches
        if self.use_multiprocessing and self.pool and len(file_paths) > 5:
            results = await self.pool.compress_files(file_paths, algorithm, level or 6)

            # Convert to CompressionResult objects
            compression_results = []
            for r in results:
                if "error" in r:
                    compression_results.append(
                        CompressionResult(
                            original_file=r["file"],
                            compressed_file="",
                            original_size=0,
                            compressed_size=0,
                            compression_ratio=0,
                            algorithm=algorithm,
                            error=r["error"],
                        )
                    )
                else:
                    compression_results.append(
                        CompressionResult(
                            original_file=r["file"],
                            compressed_file=r.get("compressed_file", ""),
                            original_size=r.get("original_size", 0),
                            compressed_size=r.get("compressed_size", 0),
                            compression_ratio=r.get("ratio", 0),
                            algorithm=algorithm,
                        )
                    )

            return compression_results

        # Process sequentially for small batches
        tasks = []
        for file_path in file_paths:
            output_path = None
            if output_dir:
                path = Path(file_path)
                ext = self.ALGORITHMS.get(algorithm, {}).get("extension", ".compressed")
                output_path = Path(output_dir) / f"{path.name}{ext}"

            tasks.append(self.compress_file(file_path, algorithm, level, output_path))

        return await asyncio.gather(*tasks)

    async def decompress_file(
        self,
        file_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        delete_compressed: bool = False,
    ) -> Dict:
        """Decompress a file based on its extension"""
        path = Path(file_path)

        # Detect compression type
        algorithm = None
        if path.suffix == ".gz":
            algorithm = "gzip"
        elif path.suffix == ".bz2":
            algorithm = "bzip2"
        elif path.suffix in [".xz", ".lzma"]:
            algorithm = "lzma"
        elif path.suffix == ".zip":
            algorithm = "zip"
        elif path.name.endswith(".tar.gz"):
            algorithm = "tar.gz"
        elif path.name.endswith(".tar.bz2"):
            algorithm = "tar.bz2"
        elif path.name.endswith(".tar.xz"):
            algorithm = "tar.xz"
        elif path.suffix == ".tar":
            algorithm = "tar"

        if not algorithm:
            return {"error": f"Unknown compression format: {path.suffix}"}

        # Determine output path
        if output_path is None:
            if algorithm == "gzip":
                output_path = path.with_suffix("")
            elif algorithm == "bzip2":
                output_path = path.with_suffix("")
            elif algorithm == "lzma":
                output_path = path.with_suffix("")
            else:
                output_path = path.parent / path.stem

        output_path = Path(output_path)

        try:
            loop = asyncio.get_event_loop()

            if algorithm == "gzip":

                def _decompress():
                    with gzip.open(path, "rb") as f_in:
                        with open(output_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out, length=1024 * 1024)

                await loop.run_in_executor(None, _decompress)

            elif algorithm == "bzip2":

                def _decompress():
                    with bz2.open(path, "rb") as f_in:
                        with open(output_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out, length=1024 * 1024)

                await loop.run_in_executor(None, _decompress)

            elif algorithm == "lzma":

                def _decompress():
                    with lzma.open(path, "rb") as f_in:
                        with open(output_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out, length=1024 * 1024)

                await loop.run_in_executor(None, _decompress)

            elif algorithm == "zip":

                def _decompress():
                    with zipfile.ZipFile(path, "r") as zf:
                        zf.extractall(output_path.parent)

                await loop.run_in_executor(None, _decompress)

            elif algorithm.startswith("tar"):

                def _decompress():
                    with tarfile.open(path, "r:*") as tar:
                        tar.extractall(output_path.parent)

                await loop.run_in_executor(None, _decompress)

            # Delete compressed file if requested
            if delete_compressed:
                path.unlink()

            return {
                "compressed_file": str(file_path),
                "output_file": str(output_path),
                "algorithm": algorithm,
                "success": True,
            }

        except Exception as e:
            return {
                "compressed_file": str(file_path),
                "algorithm": algorithm,
                "error": str(e),
            }

    async def find_best_compression(
        self, file_path: Union[str, Path], algorithms: Optional[List[str]] = None
    ) -> Dict:
        """Test multiple compression algorithms and find the best one"""
        if algorithms is None:
            algorithms = ["gzip", "bzip2", "lzma", "zip"]

        results = []
        for algo in algorithms:
            result = await self.compress_file(
                file_path, algo, output_path=Path(file_path).parent / f"test_{algo}"
            )
            results.append(
                {
                    "algorithm": algo,
                    "ratio": result.compression_ratio,
                    "size": result.compressed_size,
                    "time": result.time_elapsed,
                }
            )

            # Clean up test file
            if result.compressed_file:
                try:
                    Path(result.compressed_file).unlink()
                except:
                    pass

        # Find best by compression ratio
        best = min(results, key=lambda x: x["ratio"])

        return {
            "best_algorithm": best["algorithm"],
            "best_ratio": best["ratio"],
            "all_results": results,
        }


# Global instance
_global_compressor: Optional[CompressionProcessor] = None


async def get_compression_processor() -> CompressionProcessor:
    """Get or create global compression processor"""
    global _global_compressor
    if _global_compressor is None:
        _global_compressor = CompressionProcessor()
    return _global_compressor
