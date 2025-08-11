import pytest
from backend.auth import (
    verify_password,
    get_password_hash,
    authenticate_user,
    create_access_token,
)


def test_get_password_hash_and_verify_password():
    password = "testpass123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpass", hashed)


def test_authenticate_user_success_and_failure(mocker):
    # Mock DB and user model
    class DummyUser:
        def __init__(self, username, hashed_password):
            self.username = username
            self.hashed_password = hashed_password

    db = MagicMock()
    user_obj = DummyUser("user1", get_password_hash("pass1"))

    db.query().filter().first = MagicMock(return_value=user_obj)

    # Patch verify_password
    with patch("backend.auth.verify_password", return_value=True):
        user = authenticate_user(db, "user1", "pass1")
        assert user is not None

    with patch("backend.auth.verify_password", return_value=False):
        user = authenticate_user(db, "user1", "wrongpass")
        assert user is None

    # User not found
    db.query().filter().first = MagicMock(return_value=None)
    user = authenticate_user(db, "nouser", "pass")
    assert user is None


import datetime


def test_create_access_token_returns_token_string():
    data = {"sub": "user1"}
    token = create_access_token(data, expires_delta=datetime.timedelta(minutes=5))
    assert isinstance(token, str)
    assert len(token) > 0
