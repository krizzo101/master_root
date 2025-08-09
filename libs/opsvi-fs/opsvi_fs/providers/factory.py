#!/usr/bin/env python3
"""Factory to build storage providers from settings."""
from __future__ import annotations

from typing import Final

from ..config.settings import LibrarySettings
from .interfaces import StorageProvider
from .local_adapter import LocalStorageProvider

_PROVIDER_LOCAL: Final[str] = "local"
_PROVIDER_S3: Final[str] = "s3"
_PROVIDER_GCS: Final[str] = "gcs"
_PROVIDER_AZURE: Final[str] = "azure"
_PROVIDER_MINIO: Final[str] = "minio"
_PROVIDER_FSSPEC: Final[str] = "fsspec"


def build_provider(settings: LibrarySettings | None = None) -> StorageProvider:
    cfg = settings or LibrarySettings()
    provider = (cfg.fs_provider or _PROVIDER_LOCAL).lower()

    if provider == _PROVIDER_LOCAL:
        return LocalStorageProvider(root=cfg.fs_root)

    if provider == _PROVIDER_S3:
        from .s3_adapter import S3StorageProvider

        return S3StorageProvider(settings=cfg)

    if provider == _PROVIDER_GCS:
        from .gcs_adapter import GCSStorageProvider

        return GCSStorageProvider(settings=cfg)

    if provider == _PROVIDER_AZURE:
        from .azure_adapter import AzureBlobStorageProvider

        return AzureBlobStorageProvider(settings=cfg)

    if provider == _PROVIDER_MINIO:
        from .minio_adapter import MinioStorageProvider

        return MinioStorageProvider(settings=cfg)

    if provider == _PROVIDER_FSSPEC:
        from .fsspec_adapter import FsspecStorageProvider

        return FsspecStorageProvider(settings=cfg)

    # Fallback
    return LocalStorageProvider(root=cfg.fs_root)
