"""
File upload/storage logic. Supports S3 or secure local filesystem.
Handles uploads, secure filename, retention.
"""
import os
import shutil
from pathlib import Path
import uuid
from typing import Optional
from fastapi import UploadFile, HTTPException
from app.config import settings
import logging

logger = logging.getLogger("storage")


def secure_filename(filename: str) -> str:
    """Produce a secure, unique, sanitized file name."""
    # Remove potentially dangerous chars
    base = os.path.basename(filename)
    base = base.replace("..", "").replace("/", "")
    fname, ext = os.path.splitext(base)
    fname = fname[:64].replace(" ", "_")
    return f"{uuid.uuid4().hex}_{fname}{ext}"


def save_upload_file(upload_file: UploadFile, subdir: Optional[str] = None) -> str:
    """Store upload to configured storage, return absolute file path. Only stores on local filesystem in this implementation."""
    upload_dir = Path(settings.UPLOAD_DIR)
    if subdir:
        upload_dir = upload_dir / subdir
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = secure_filename(upload_file.filename)
    file_path = upload_dir / filename
    # Limit upload size
    file_size = 0
    with file_path.open("wb") as buffer:
        while chunk := upload_file.file.read(1024 * 1024):
            file_size += len(chunk)
            if file_size > settings.MAX_UPLOAD_SIZE:
                buffer.close()
                file_path.unlink(missing_ok=True)
                raise HTTPException(413, detail="Uploaded file too large (max 1MB)")
            buffer.write(chunk)
    logger.info(f"Saved upload: {file_path} ({file_size} bytes)")
    return str(file_path)


def delete_file(path: str):
    """Delete file from storage."""
    try:
        file = Path(path)
        if file.exists():
            file.unlink()
            logger.info(f"Deleted file: {file}")
    except Exception as e:
        logger.warning(f"File remove error [{path}]: {e}")


def cleanup_upload_folder():
    """Purge files older than retention window from uploads folder."""
    cutoff_sec = settings.RETAIN_HOURS * 3600
    root = Path(settings.UPLOAD_DIR)
    for child in root.glob("**/*"):
        try:
            if child.is_file() and (
                os.stat(child).st_mtime < (os.stat(child).st_mtime - cutoff_sec)
            ):
                child.unlink()
        except Exception as e:
            logger.warning(f"cleanup_upload_folder error: {e}")
