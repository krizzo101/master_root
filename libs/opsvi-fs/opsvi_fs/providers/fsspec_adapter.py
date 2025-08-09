#!/usr/bin/env python3
from __future__ import annotations

from typing import BinaryIO, Iterator
from dataclasses import dataclass
import os

try:
    import fsspec  # type: ignore
except Exception:  # pragma: no cover - optional dep
    fsspec = None  # type: ignore

from .interfaces import StorageProvider
from ..schemas.models import FileLocation, FileStat, ListEntry
from ..config.settings import LibrarySettings
from ..exceptions.base import ProviderError


@dataclass(slots=True)
class _FsContext:
    fs: any
    root_url: str  # like s3://bucket/prefix or local path prefix for file


class FsspecStorageProvider(StorageProvider):
    """Generic fsspec-backed provider.

    Uses OPSVI_FS_FS_PROVIDER and OPSVI_FS_FS_ROOT. If fs_root includes a scheme
    (e.g., s3://bucket/prefix), that scheme and path are honored.
    """

    def __init__(self, settings: LibrarySettings) -> None:
        if fsspec is None:
            raise ProviderError("fsspec is not installed. Install opsvi-fs[fsspec] or a backend like s3fs/gcsfs")
        self.settings = settings
        self.ctx = self._init_fs(settings)

    def _init_fs(self, settings: LibrarySettings) -> _FsContext:
        root = settings.fs_root or "."
        if "://" in root:
            protocol, rest = root.split("://", 1)
            fs = fsspec.filesystem(protocol)
            root_url = f"{protocol}://{rest.strip(/)}"
            return _FsContext(fs=fs, root_url=root_url)
        # default local
        fs = fsspec.filesystem("file")
        return _FsContext(fs=fs, root_url=os.path.abspath(root))

    def _full_url(self, loc: FileLocation) -> str:
        # If root_url has scheme://, join as URL; otherwise, join local path
        base = self.ctx.root_url.rstrip("/")
        path = (loc.path or "").lstrip("/")
        if base.startswith("file:"):
            base = base.replace("file://", "")
        return f"{base}/{path}" if base else path

    def health_check(self) -> bool:
        try:
            # Attempt simple listing/stat on root
            if self.ctx.root_url.startswith("file:"):
                path = self.ctx.root_url.replace("file://", "")
            else:
                path = self.ctx.root_url
            # Some filesystems require try/except
            _ = list(self.list(FileLocation(path=".")))
            return True
        except Exception:
            return False

    def exists(self, loc: FileLocation) -> bool:
        return self.ctx.fs.exists(self._full_url(loc))

    def stat(self, loc: FileLocation) -> FileStat:
        url = self._full_url(loc)
        if not self.ctx.fs.exists(url):
            raise ProviderError(f"Not found: {url}")
        info = self.ctx.fs.info(url)
        size = int(info.get("size", 0))
        is_dir = info.get("type") == "directory"
        return FileStat(path=url, size=size, is_dir=is_dir)

    def list(self, loc: FileLocation) -> Iterator[ListEntry]:
        url = self._full_url(loc)
        if not self.ctx.fs.exists(url):
            return iter(())
        for info in self.ctx.fs.ls(url, detail=True):
            yield ListEntry(path=info.get("name", ""), is_dir=info.get("type") == "directory")

    def makedirs(self, loc: FileLocation, exist_ok: bool = True) -> None:
        url = self._full_url(loc)
        self.ctx.fs.makedirs(url, exist_ok=exist_ok)

    def delete(self, loc: FileLocation, recursive: bool = False) -> None:
        url = self._full_url(loc)
        self.ctx.fs.rm(url, recursive=recursive)

    def open_read(self, loc: FileLocation) -> BinaryIO:
        return self.ctx.fs.open(self._full_url(loc), mode="rb")

    def open_write(self, loc: FileLocation, overwrite: bool = True) -> BinaryIO:
        url = self._full_url(loc)
        if not overwrite and self.ctx.fs.exists(url):
            raise ProviderError(f"Refusing to overwrite: {url}")
        # Ensure parent dirs for local
        if "://" not in url:
            os.makedirs(os.path.dirname(url), exist_ok=True)
        return self.ctx.fs.open(url, mode="wb")

    def copy(self, src: FileLocation, dst: FileLocation, overwrite: bool = True) -> None:
        data = self.open_read(src).read()
        with self.open_write(dst, overwrite=overwrite) as w:
            w.write(data)

    def move(self, src: FileLocation, dst: FileLocation, overwrite: bool = True) -> None:
        self.copy(src, dst, overwrite=overwrite)
        self.delete(src, recursive=False)
