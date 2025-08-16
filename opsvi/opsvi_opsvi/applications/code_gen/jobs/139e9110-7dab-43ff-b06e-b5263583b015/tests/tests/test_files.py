import pytest
from backend.files import upload_file, download_file

import io
from unittest.mock import AsyncMock


@pytest.mark.asyncio
def test_upload_file_adds_file_record():
    file_like = io.BytesIO(b"Test file content")
    file_like.filename = "test.txt"
    fake_db = AsyncMock()
    user = MagicMock()

    file_obj = await upload_file(file_like, fake_db, user)
    assert file_obj.filename == "test.txt"


@pytest.mark.asyncio
def test_download_file_returns_file_content_or_none():
    fake_db = AsyncMock()
    user = MagicMock()
    # Mock DB call returning a file-like
    fake_db.get_file_content = AsyncMock(return_value=b"content")
    file_id = "file123"
    content = await download_file(file_id, fake_db, user)
    assert isinstance(content, bytes)
