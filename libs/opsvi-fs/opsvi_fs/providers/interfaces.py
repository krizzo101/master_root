#!/usr/bin/env python3
"""Storage provider interfaces (ABCs)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import BinaryIO, Dict, Iterable, Iterator, List, Optional

from ..schemas.models import FileLocation, FileStat, ListEntry


class StorageProvider(ABC):
    """Abstract storage provider contract."""

    @abstractmethod
    def health_check(self) -> bool: ...

    @abstractmethod
    def exists(self, loc: FileLocation) -> bool: ...

    @abstractmethod
    def stat(self, loc: FileLocation) -> FileStat: ...

    @abstractmethod
    def list(self, loc: FileLocation) -> Iterator[ListEntry]: ...

    @abstractmethod
    def makedirs(self, loc: FileLocation, exist_ok: bool = True) -> None: ...

    @abstractmethod
    def delete(self, loc: FileLocation, recursive: bool = False) -> None: ...

    @abstractmethod
    def open_read(self, loc: FileLocation) -> BinaryIO: ...

    @abstractmethod
    def open_write(self, loc: FileLocation, overwrite: bool = True) -> BinaryIO: ...

    @abstractmethod
    def copy(self, src: FileLocation, dst: FileLocation, overwrite: bool = True) -> None: ...

    @abstractmethod
    def move(self, src: FileLocation, dst: FileLocation, overwrite: bool = True) -> None: ...
