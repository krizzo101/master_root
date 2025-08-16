import os
from io import BytesIO

import pytest
from app.storage import (
    cleanup_upload_folder,
    delete_file,
    save_upload_file,
    secure_filename,
)


@pytest.fixture
def temp_upload_dir(tmp_path):
    return tmp_path


def test_secure_filename_removes_unsafe_characters():
    unsafe_name = "../some*file?.py"
    safe_name = secure_filename(unsafe_name)
    assert "/" not in safe_name
    assert "\\" not in safe_name
    assert "*" not in safe_name
    assert "?" not in safe_name
    assert safe_name.endswith(".py")


def test_save_upload_file_creates_file_in_subdir(temp_upload_dir):
    filename = "test_file.py"
    file_content = b"print('hello world')"
    upload_file = BytesIO(file_content)
    upload_file.filename = filename
    path = save_upload_file(upload_file, subdir=str(temp_upload_dir))
    full_path = os.path.join(temp_upload_dir, filename)
    assert path == full_path
    assert os.path.exists(path)
    with open(path, "rb") as f:
        assert f.read() == file_content


def test_delete_file_removes_existing_file(temp_upload_dir):
    file_path = temp_upload_dir / "todelete.py"
    file_path.write_text("test")
    assert file_path.exists()
    delete_file(str(file_path))
    assert not file_path.exists()


def test_delete_file_handles_nonexistent_path_gracefully(temp_upload_dir):
    non_existent_file = temp_upload_dir / "nonexistent.py"
    # Should not raise
    delete_file(str(non_existent_file))


def test_cleanup_upload_folder_removes_all_contents(tmp_path):
    # Setup directory with files/folders
    subdir = tmp_path / "upload"
    subdir.mkdir()
    f1 = subdir / "file1.py"
    f1.write_text("content")
    dir1 = subdir / "dir1"
    dir1.mkdir()
    f2 = dir1 / "file2.py"
    f2.write_text("content2")
    # Patch upload folder path to our temp dir
    import app.storage as storage

    storage.UPLOAD_DIR = str(subdir)
    cleanup_upload_folder()
    assert not any(subdir.iterdir())
