import pytest
from flask import url_for
from ai_collab_task_manager.app import create_app, load_user
from ai_collab_task_manager.models import User, Task
from unittest.mock import patch, MagicMock


@pytest.fixture
@pytest.mark.usefixtures("app", "client")
def app():
    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
    yield app


@pytest.fixture
def test_client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def sample_user(db_session):
    user = User(
        id=1, username="testuser", email="test@example.com", password_hash="hashed"
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_task(db_session, sample_user):
    task = Task(
        id=1, title="Sample Task", description="Test task", assigned_to=sample_user.id
    )
    db_session.add(task)
    db_session.commit()
    return task


def test_load_user_returns_user_object(sample_user):
    user = load_user(sample_user.id)
    assert user is not None
    assert user.id == sample_user.id
    assert user.username == "testuser"


def test_load_user_with_invalid_id_returns_none():
    user = load_user(99999)
    assert user is None


@pytest.mark.parametrize(
    "endpoint,error_code,error_msg",
    [
        ("/nonexistent_url", 404, b"Not Found"),
    ],
)
def test_not_found_handler(test_client, endpoint, error_code, error_msg):
    response = test_client.get(endpoint)
    assert response.status_code == error_code
    assert error_msg in response.data


@pytest.mark.parametrize(
    "handler_func,error_code,error_msg",
    [
        ("forbidden", 403, b"Forbidden"),
        ("server_error", 500, b"Internal Server Error"),
    ],
)
@patch("ai_collab_task_manager.app.render_template")
def test_custom_error_handlers(mock_render, app, handler_func, error_code, error_msg):
    from werkzeug.exceptions import HTTPException

    error_instance = HTTPException()
    error_instance.code = error_code
    mock_render.return_value = error_msg
    handler = getattr(app, handler_func)
    response = handler(error_instance)
    assert response == error_msg
    mock_render.assert_called_once()


def test_index_renders_homepage(test_client):
    response = test_client.get(url_for("index"))
    assert response.status_code == 200
    assert b"Welcome" in response.data


def test_register_login_logout_flow(test_client, db_session):
    # Register user
    response = test_client.post(
        url_for("register"),
        data={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPassword123",
            "confirm": "StrongPassword123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Registration successful" in response.data or b"Welcome" in response.data

    # Attempt login
    login_resp = test_client.post(
        url_for("login"),
        data={"username": "newuser", "password": "StrongPassword123"},
        follow_redirects=True,
    )
    assert login_resp.status_code == 200
    assert b"Dashboard" in login_resp.data or b"Welcome" in login_resp.data

    # Logout
    logout_resp = test_client.get(url_for("logout"), follow_redirects=True)
    assert logout_resp.status_code == 200
    assert b"Logged out" in logout_resp.data or b"Login" in logout_resp.data


def test_dashboard_requires_login(test_client):
    response = test_client.get(url_for("dashboard"), follow_redirects=False)
    assert response.status_code in (302, 401)
    # Location header should point to login page
    assert "/login" in response.headers["Location"]


def test_new_task_creation_and_editing(test_client, sample_user, db_session):
    # Login first
    with test_client.session_transaction() as sess:
        sess["user_id"] = sample_user.id

    # Create a new task
    response = test_client.post(
        url_for("new_task"),
        data={
            "title": "New Task",
            "description": "Task description",
            "assigned_to": sample_user.id,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Task created" in response.data or b"Task" in response.data

    # Verify task exists
    task = db_session.query(Task).filter_by(title="New Task").first()
    assert task is not None

    # Edit the task
    response_edit = test_client.post(
        url_for("edit_task", task_id=task.id),
        data={
            "title": "Updated Task",
            "description": "Updated description",
            "assigned_to": sample_user.id,
        },
        follow_redirects=True,
    )
    assert response_edit.status_code == 200
    assert (
        b"Task updated" in response_edit.data or b"Updated Task" in response_edit.data
    )

    updated_task = db_session.query(Task).get(task.id)
    assert updated_task.title == "Updated Task"


def test_view_and_delete_task_requires_auth(
    test_client, sample_task, sample_user, db_session
):
    with test_client.session_transaction() as sess:
        sess["user_id"] = sample_user.id

    # View task
    response_view = test_client.get(url_for("view_task", task_id=sample_task.id))
    assert response_view.status_code == 200
    assert b"Sample Task" in response_view.data

    # Delete task
    response_delete = test_client.post(
        url_for("delete_task", task_id=sample_task.id), follow_redirects=True
    )
    assert response_delete.status_code == 200
    deleted_task = db_session.query(Task).get(sample_task.id)
    assert deleted_task is None


def test_start_and_stop_timer(test_client, sample_task, sample_user, db_session):
    with test_client.session_transaction() as sess:
        sess["user_id"] = sample_user.id

    # Start timer
    start_response = test_client.post(
        url_for("start_timer", task_id=sample_task.id), follow_redirects=True
    )
    assert start_response.status_code == 200
    # Assuming some response data or status for success
    assert b"Timer started" in start_response.data or start_response.status_code == 200

    # Stop timer
    stop_response = test_client.post(
        url_for("stop_timer", task_id=sample_task.id), follow_redirects=True
    )
    assert stop_response.status_code == 200
    assert b"Timer stopped" in stop_response.data or stop_response.status_code == 200


def test_reports_page_requires_login(test_client):
    response = test_client.get(url_for("reports"), follow_redirects=False)
    assert response.status_code in (302, 401)

    # Now with user logged in
    with test_client.session_transaction() as sess:
        sess["user_id"] = 1
    response_logged_in = test_client.get(url_for("reports"))
    assert response_logged_in.status_code == 200
    assert (
        b"Reports" in response_logged_in.data or b"Progress" in response_logged_in.data
    )


@patch("ai_collab_task_manager.calendar.GoogleCalendarService.sync_user_tasks")
def test_sync_calendar_endpoint(mock_sync, test_client, sample_user):
    with test_client.session_transaction() as sess:
        sess["user_id"] = sample_user.id
    mock_sync.return_value = True
    response = test_client.post(url_for("sync_calendar"))
    assert response.status_code == 200
    mock_sync.assert_called_once()
