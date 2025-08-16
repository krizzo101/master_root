from ai_collab_task_manager.models import (
    AuditLog,
    Comment,
    Notification,
    Task,
    TaskAssignment,
    Team,
    TeamMembers,
    TimeEntry,
    User,
)


def test_user_model_creation():
    user = User(username="testuser", email="test@example.com")
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert str(user) is not None


def test_team_and_teammembers():
    team = Team(name="Dev Team")
    member = TeamMembers(user_id=1, team_id=1, role="member")
    team.members = [member]
    assert team.name == "Dev Team"
    assert team.members[0].role == "member"


def test_task_and_taskassignment_association():
    task = Task(title="Task 1", description="Desc")
    assignment = TaskAssignment(task_id=1, user_id=2)
    task.assignments = [assignment]
    assert task.title == "Task 1"
    assert task.assignments[0].user_id == 2


def test_auxiliary_models():
    comment = Comment(content="Nice work")
    time_entry = TimeEntry(task_id=1, user_id=1, duration=30)
    notification = Notification(user_id=1, message="Assigned to task")
    audit_log = AuditLog(event="Created", user_id=1)
    assert str(comment) != ""
    assert time_entry.duration == 30
    assert notification.message == "Assigned to task"
    assert audit_log.event == "Created"
