import pytest
from backend.models import (
    UserRole,
    User,
    Project,
    TaskStatus,
    Task,
    Dependency,
    Comment,
    File,
    TimeEntry,
    AuditLog,
)
from datetime import datetime


def test_user_role_enum_contains_expected_roles():
    roles = [role.name for role in UserRole]
    assert "ADMIN" in roles
    assert "USER" in roles


def test_user_model_default_values_and_repr():
    user = User(
        id="123",
        email="test@example.com",
        hashed_password="hashedpass",
        role=UserRole.USER,
    )
    assert user.role == UserRole.USER
    assert str(user).startswith("User")


def test_project_model_requires_name_and_defaults():
    project = Project(id="proj1", name="Project One", owner_id="123")
    assert project.name == "Project One"
    assert hasattr(project, "created_at")


def test_task_and_status_field_behavior():
    task = Task(
        id="task1", project_id="proj1", title="Test Task", status=TaskStatus.PENDING
    )
    assert task.status == TaskStatus.PENDING
    assert task.title == "Test Task"


def test_dependency_and_comment_creation():
    dep = Dependency(id="dep1", task_id="task1", depends_on_task_id="task2")
    comment = Comment(
        id="comm1", task_id="task1", user_id="user1", content="This is a comment"
    )
    assert dep.task_id == "task1"
    assert comment.content == "This is a comment"


def test_file_and_time_entry_models():
    file = File(id="file1", filename="doc.txt", task_id="task1", uploaded_by="user1")
    time_entry = TimeEntry(
        id="te1",
        task_id="task1",
        user_id="user1",
        start_time=datetime.utcnow(),
        end_time=None,
    )
    assert file.filename == "doc.txt"
    assert time_entry.end_time is None


def test_audit_log_contains_action_and_meta():
    log = AuditLog(
        id="log1",
        action="create_task",
        user_id="user1",
        entity="task",
        entity_id="task1",
        meta={"foo": "bar"},
    )
    assert log.action == "create_task"
    assert log.meta["foo"] == "bar"
