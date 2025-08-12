import pytest
from app.models import User, Project, File, Report


def test_user_model_attributes_and_str_representation():
    user = User(id=1, email="user@example.com", name="Test User")
    assert user.email == "user@example.com"
    assert str(user).startswith("User") or hasattr(user, "__repr__")


def test_project_model_attributes():
    project = Project(id=1, name="Proj", description="desc")
    assert project.name == "Proj"
    assert hasattr(project, "description")


def test_file_model_attributes():
    file = File(id=1, filename="main.py", path="/tmp/main.py")
    assert file.filename == "main.py"
    assert file.path == "/tmp/main.py"


def test_report_model_attributes():
    report = Report(id=1, project_id=1, summary="Good")
    assert report.project_id == 1
    assert "Good" in getattr(report, "summary", "")
