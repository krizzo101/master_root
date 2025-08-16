from unittest.mock import MagicMock, patch

import pytest
from app.api import (
    create_project,
    delete_project,
    download_report_html,
    get_project,
    get_report,
    list_project_reports,
    list_projects,
    update_project,
    upload_python_code,
)


def test_create_project_creates_and_returns_project_object(monkeypatch):
    dummy_db = MagicMock()
    current_user = MagicMock()
    project_in = MagicMock(name="Test Project")

    monkeypatch.setattr(dummy_db, "add", lambda proj: None)
    monkeypatch.setattr(dummy_db, "commit", lambda: None)
    monkeypatch.setattr(dummy_db, "refresh", lambda proj: None)

    project = create_project(project_in, dummy_db, current_user)
    assert project is not None
    assert hasattr(project, "name")


def test_list_projects_returns_user_projects(monkeypatch):
    dummy_db = MagicMock()
    current_user = MagicMock(id=1)
    projects = [MagicMock(name="Project1"), MagicMock(name="Project2")]

    dummy_db.query = MagicMock(return_value=dummy_db)
    dummy_db.filter_by = MagicMock(return_value=projects)

    with patch("app.api.list_projects", return_value=projects):
        result = list_projects(dummy_db, current_user)
        assert isinstance(result, list)


def test_get_project_returns_project_or_raises(monkeypatch):
    dummy_db = MagicMock()
    current_user = MagicMock()

    existing_project = MagicMock(name="Existing")
    dummy_db.query = MagicMock(return_value=dummy_db)
    dummy_db.filter_by = MagicMock(return_value=[existing_project])

    proj = get_project(1, dummy_db, current_user)
    assert proj == existing_project

    # When no project found, should raise
    dummy_db.filter_by = MagicMock(return_value=[])

    with pytest.raises(Exception):
        get_project(99, dummy_db, current_user)


def test_update_project_updates_attributes(monkeypatch):
    dummy_db = MagicMock()
    current_user = MagicMock()
    project_in = MagicMock(name="New Name")

    project = MagicMock(name="Old Name")
    monkeypatch.setattr("app.api.get_project", lambda project_id, db, user: project)

    updated_project = update_project(1, project_in, dummy_db, current_user)
    assert updated_project is project
    assert updated_project.name == "New Name"
    dummy_db.commit.assert_called()


def test_delete_project_removes_and_commits(monkeypatch):
    dummy_db = MagicMock()
    current_user = MagicMock()

    project = MagicMock()
    monkeypatch.setattr("app.api.get_project", lambda project_id, db, user: project)

    delete_project(1, dummy_db, current_user)
    dummy_db.delete.assert_called_with(project)
    dummy_db.commit.assert_called()


def test_upload_python_code_saves_file_and_returns_report(monkeypatch):
    dummy_db = MagicMock()
    current_user = MagicMock()
    project_id = 1

    file_mock = MagicMock()
    file_mock.filename = "test.py"

    monkeypatch.setattr(
        "app.storage.save_upload_file", lambda upload_file, subdir: "/path/to/test.py"
    )
    monkeypatch.setattr(
        "app.api.create_report", lambda db, project_id, path: {"id": 123}
    )

    report = upload_python_code(project_id, file_mock, dummy_db, current_user)
    assert report is not None
    assert "id" in report


def test_list_project_reports_returns_list(monkeypatch):
    dummy_db = MagicMock()
    current_user = MagicMock()
    dummy_reports = [MagicMock(id=1), MagicMock(id=2)]

    monkeypatch.setattr("app.api.get_project", lambda pid, db, user: MagicMock())
    monkeypatch.setattr(
        "app.api.fetch_reports_for_project", lambda db, project_id: dummy_reports
    )

    reports = list_project_reports(1, dummy_db, current_user)
    assert isinstance(reports, list)
    assert all(hasattr(r, "id") for r in reports)


def test_get_report_returns_report_or_404(monkeypatch):
    dummy_db = MagicMock()
    current_user = MagicMock()

    existing_report = MagicMock(id=1)
    monkeypatch.setattr(
        "app.api.get_report_by_id", lambda rid, db, user: existing_report
    )
    report = get_report(1, dummy_db, current_user)
    assert report == existing_report

    monkeypatch.setattr("app.api.get_report_by_id", lambda rid, db, user: None)
    with pytest.raises(Exception):
        get_report(99, dummy_db, current_user)


def test_download_report_html_returns_file_response(monkeypatch):
    dummy_db = MagicMock()
    current_user = MagicMock()

    report_path = "/tmp/report_1.html"

    monkeypatch.setattr(
        "app.api.get_report_by_id",
        lambda rid, db, user: MagicMock(file_path=report_path),
    )

    response = download_report_html(1, dummy_db, current_user)
    # Should return a FastAPI response or similar containing headers with content-disposition
    assert hasattr(response, "headers")
    content_disposition = response.headers.get("content-disposition", "")
    assert "attachment" in content_disposition
    assert ".html" in content_disposition
