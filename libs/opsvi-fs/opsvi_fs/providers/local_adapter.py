#!/usr/bin/env python3
"""Local filesystem provider using pathlib/os."""
from __future__ import annotations

import os
from pathlib import Path
from typing import BinaryIO, Iterator

from .interfaces import StorageProvider
from ..schemas.models import FileLocation, FileStat, ListEntry
from ..exceptions.base import ProviderError


class LocalStorageProvider(StorageProvider):
    def __init__(self, root: str = ".") -> None:
        self.root = Path(root).resolve()

    def _to_path(self, loc: FileLocation) -> Path:
        # Join root with the loc.path (ignore bucket)
        return (self.root / loc.path.lstrip("/"))

    def health_check(self) -> bool:
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    def exists(self, loc: FileLocation) -> bool:
        return self._to_path(loc).exists()

    def stat(self, loc: FileLocation) -> FileStat:
        p = self._to_path(loc)
        if not p.exists():
            raise ProviderError(f"Not found: {p}")
        st = p.stat()
        return FileStat(path=str(p), size=st.st_size, is_dir=p.is_dir())

    def list(self, loc: FileLocation) -> Iterator[ListEntry]:
        p = self._to_path(loc)
        if not p.exists():
            return iter(())
        for child in p.iterdir():
            yield ListEntry(path=str(child), is_dir=child.is_dir())

    def makedirs(self, loc: FileLocation, exist_ok: bool = True) -> None:
        self._to_path(loc).mkdir(parents=True, exist_ok=exist_ok)

    def delete(self, loc: FileLocation, recursive: bool = False) -> None:
        p = self._to_path(loc)
        if p.is_dir():
            if not recursive:
                os.rmdir(p)
            else:
                for root, dirs, files in os.walk(p, topdown=False):
                    for f in files:
                        Path(root, f).unlink(missing_ok=True)
                    for d in dirs:
                        Path(root, d).rmdir()
                p.rmdir()
        else:
            p.unlink(missing_ok=True)

    def open_read(self, loc: FileLocation) -> BinaryIO:
        return open(self._to_path(loc), "rb")

    def open_write(self, loc: FileLocation, overwrite: bool = True) -> BinaryIO:
        p = self._to_path(loc)
        p.parent.mkdir(parents=True, exist_ok=True)
        if not overwrite and p.exists():
            raise ProviderError(f"Refusing to overwrite: {p}")
        return open(p, "wb")

    def copy(self, src: FileLocation, dst: FileLocation, overwrite: bool = True) -> None:
        data = self.open_read(src).read()
        with self.open_write(dst, overwrite=overwrite) as w:
            w.write(data)

    def move(self, src: FileLocation, dst: FileLocation, overwrite: bool = True) -> None:
        self.copy(src, dst, overwrite=overwrite)
        self.delete(src, recursive=False)
