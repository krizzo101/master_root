"""opsvi-fs - Core opsvi-fs functionality.

Comprehensive opsvi-fs library for the OPSVI ecosystem
"""

from __future__ import annotations

from typing import Any, List, Optional, Union
import asyncio
import logging
import os
from pathlib import Path
import shutil

from opsvi_foundation import BaseComponent, ComponentError
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class OpsviFsManagerError(ComponentError):
    """Base exception for opsvi-fs errors."""
    pass


class OpsviFsManagerConfigurationError(OpsviFsManagerError):
    """Configuration-related errors in opsvi-fs."""
    pass


class OpsviFsManagerInitializationError(OpsviFsManagerError):
    """Initialization-related errors in opsvi-fs."""
    pass


class OpsviFsManagerConfig(BaseSettings):
    """Configuration for opsvi-fs."""

    # Core configuration
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    # Filesystem configuration
    root_dir: Optional[str] = None
    create_root: bool = True
    allow_path_outside_root: bool = False
    concurrency_limit: int = 64

    class Config:
        env_prefix = "OPSVI_OPSVI_FS__"


class OpsviFsManager(BaseComponent):
    """Base class for opsvi-fs components.

    Provides async file system helpers rooted at a configured directory.
    """

    def __init__(
        self,
        config: Optional[OpsviFsManagerConfig] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize OpsviFsManager."""
        super().__init__("opsvi-fs", config.dict() if config else {})
        self.config = config or OpsviFsManagerConfig(**kwargs)
        self._initialized = False
        self._logger = logging.getLogger(f"{__name__}.opsvi-fs")
        self._sem: Optional[asyncio.Semaphore] = None
        self._lock: Optional[asyncio.Lock] = None
        self.root: Path = Path(self.config.root_dir or os.getcwd()).resolve()

    async def initialize(self) -> None:
        """Initialize the component."""
        try:
            # Configure logging level
            level = getattr(logging, (self.config.log_level or "INFO").upper(), logging.INFO)
            logging.getLogger().setLevel(level)
            if self.config.debug:
                self._logger.setLevel(logging.DEBUG)

            self._logger.info("Initializing opsvi-fs")
            if not self.config.enabled:
                self._logger.warning("opsvi-fs is disabled by configuration")

            if self.config.create_root:
                self.root.mkdir(parents=True, exist_ok=True)

            if not self.root.exists() or not self.root.is_dir():
                raise OpsviFsManagerInitializationError(
                    f"Root directory does not exist or is not a directory: {self.root}"
                )

            self._sem = asyncio.Semaphore(max(1, int(self.config.concurrency_limit)))
            self._lock = asyncio.Lock()

            self._initialized = True
            self._logger.info("opsvi-fs initialized successfully")
        except Exception as e:  # pragma: no cover - defensive logging
            self._logger.error(f"Failed to initialize opsvi-fs: {e}")
            raise OpsviFsManagerInitializationError(f"Initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown the component."""
        try:
            self._logger.info("Shutting down opsvi-fs")
            self._initialized = False
            self._sem = None
            self._lock = None
            self._logger.info("opsvi-fs shut down successfully")
        except Exception as e:  # pragma: no cover - defensive logging
            self._logger.error(f"Failed to shutdown opsvi-fs: {e}")
            raise OpsviFsManagerError(f"Shutdown failed: {e}") from e

    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            if not self._initialized or not self.config.enabled:
                return False
            if not self.root.exists() or not self.root.is_dir():
                return False
            # Basic access checks
            return os.access(self.root, os.R_OK) and os.access(self.root, os.W_OK)
        except Exception as e:  # pragma: no cover - defensive logging
            self._logger.error(f"Health check failed: {e}")
            return False

    # Internal helpers
    def _require_initialized(self) -> None:
        if not self._initialized:
            raise OpsviFsManagerInitializationError("opsvi-fs is not initialized")

    def _resolve_path(self, path: Union[str, Path]) -> Path:
        base = self.root
        candidate = Path(path)
        resolved = (candidate if candidate.is_absolute() else (base / candidate)).resolve()
        if self.config.allow_path_outside_root:
            return resolved
        try:
            resolved.relative_to(base)
        except Exception:  # ValueError on outside path
            raise OpsviFsManagerError(
                f"Access outside root directory is not allowed: {resolved}"
            )
        return resolved

    async def _to_thread(self, func, *args, **kwargs):
        self._require_initialized()
        if self._sem is None:
            raise OpsviFsManagerInitializationError("Semaphore not initialized")
        async with self._sem:
            return await asyncio.to_thread(func, *args, **kwargs)

    # Public async filesystem API
    async def exists(self, path: Union[str, Path]) -> bool:
        """Check if path exists."""
        p = self._resolve_path(path)
        return await self._to_thread(p.exists)

    async def read_text(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """Read text from file."""
        p = self._resolve_path(path)
        def _read() -> str:
            with p.open("r", encoding=encoding) as f:
                return f.read()
        try:
            return await self._to_thread(_read)
        except Exception as e:
            raise OpsviFsManagerError(f"Failed to read text: {p}: {e}") from e

    async def read_bytes(self, path: Union[str, Path]) -> bytes:
        """Read bytes from file."""
        p = self._resolve_path(path)
        def _read() -> bytes:
            return p.read_bytes()
        try:
            return await self._to_thread(_read)
        except Exception as e:
            raise OpsviFsManagerError(f"Failed to read bytes: {p}: {e}") from e

    async def write_text(
        self,
        path: Union[str, Path],
        data: str,
        *,
        encoding: str = "utf-8",
        create_dirs: bool = True,
    ) -> None:
        """Write text to file."""
        p = self._resolve_path(path)
        def _write() -> None:
            if create_dirs:
                p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("w", encoding=encoding) as f:
                f.write(data)
        try:
            await self._to_thread(_write)
        except Exception as e:
            raise OpsviFsManagerError(f"Failed to write text: {p}: {e}") from e

    async def write_bytes(
        self,
        path: Union[str, Path],
        data: bytes,
        *,
        create_dirs: bool = True,
    ) -> None:
        """Write bytes to file."""
        p = self._resolve_path(path)
        def _write() -> None:
            if create_dirs:
                p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        try:
            await self._to_thread(_write)
        except Exception as e:
            raise OpsviFsManagerError(f"Failed to write bytes: {p}: {e}") from e

    async def list_dir(
        self,
        path: Union[str, Path] = ".",
        *,
        recursive: bool = False,
        pattern: Optional[str] = None,
        include_dirs: bool = False,
        absolute: bool = True,
    ) -> List[str]:
        """List files under a directory."""
        p = self._resolve_path(path)
        def _list() -> List[str]:
            results: List[Path] = []
            if recursive:
                for root, dirs, files in os.walk(p):
                    root_path = Path(root)
                    if include_dirs:
                        for d in dirs:
                            results.append(root_path / d)
                    for f in files:
                        results.append(root_path / f)
            else:
                for entry in p.iterdir():
                    if entry.is_file() or (include_dirs and entry.is_dir()):
                        results.append(entry)
            if pattern:
                results = [r for r in results if r.match(pattern)]
            return [str(r.resolve() if absolute else r.relative_to(self.root)) for r in results]
        try:
            return await self._to_thread(_list)
        except Exception as e:
            raise OpsviFsManagerError(f"Failed to list directory: {p}: {e}") from e

    async def remove(self, path: Union[str, Path], *, recursive: bool = True) -> None:
        """Remove a file or directory."""
        p = self._resolve_path(path)
        def _remove() -> None:
            if p.is_dir():
                if recursive:
                    shutil.rmtree(p)
                else:
                    p.rmdir()
            else:
                if p.exists():
                    p.unlink()
        try:
            await self._to_thread(_remove)
        except Exception as e:
            raise OpsviFsManagerError(f"Failed to remove: {p}: {e}") from e

    async def copy(self, src: Union[str, Path], dst: Union[str, Path], *, overwrite: bool = True) -> None:
        """Copy a file or directory."""
        p_src = self._resolve_path(src)
        p_dst = self._resolve_path(dst)
        def _copy() -> None:
            if p_src.is_dir():
                if p_dst.exists() and overwrite:
                    shutil.rmtree(p_dst)
                shutil.copytree(p_src, p_dst)
            else:
                p_dst.parent.mkdir(parents=True, exist_ok=True)
                if p_dst.exists() and not overwrite:
                    raise FileExistsError(f"Destination exists: {p_dst}")
                shutil.copy2(p_src, p_dst)
        try:
            await self._to_thread(_copy)
        except Exception as e:
            raise OpsviFsManagerError(f"Failed to copy {p_src} -> {p_dst}: {e}") from e

    async def move(self, src: Union[str, Path], dst: Union[str, Path], *, overwrite: bool = True) -> None:
        """Move a file or directory."""
        p_src = self._resolve_path(src)
        p_dst = self._resolve_path(dst)
        def _move() -> None:
            p_dst.parent.mkdir(parents=True, exist_ok=True)
            if p_dst.exists():
                if overwrite:
                    if p_dst.is_dir():
                        shutil.rmtree(p_dst)
                    else:
                        p_dst.unlink()
                else:
                    raise FileExistsError(f"Destination exists: {p_dst}")
            shutil.move(str(p_src), str(p_dst))
        try:
            await self._to_thread(_move)
        except Exception as e:
            raise OpsviFsManagerError(f"Failed to move {p_src} -> {p_dst}: {e}") from e

    async def stat(self, path: Union[str, Path]) -> dict:
        """Get basic file stats."""
        p = self._resolve_path(path)
        def _stat() -> dict:
            st = p.stat()
            return {
                "path": str(p),
                "is_dir": p.is_dir(),
                "size": st.st_size,
                "mtime": st.st_mtime,
                "ctime": st.st_ctime,
                "mode": st.st_mode,
            }
        try:
            return await self._to_thread(_stat)
        except Exception as e:
            raise OpsviFsManagerError(f"Failed to stat {p}: {e}") from e
