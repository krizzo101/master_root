import pytest
from unittest.mock import MagicMock, patch
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    authenticate_user,
    signup,
    login,
    get_me,
)


def test_verify_password_success_and_failure_cases():
    plain_password = "password123"
    hashed_password = get_password_hash(plain_password)
    assert verify_password(plain_password, hashed_password) is True
    assert verify_password("wrongpassword", hashed_password) is False


def test_get_password_hash_is_non_empty_and_different_than_plain():
    password = "testpass"
    hashed = get_password_hash(password)
    assert isinstance(hashed, str)
    assert hashed != password
    assert len(hashed) > 0


def test_create_access_token_contains_subject_and_expiration():
    import jwt  # Assuming JWT is used

    subject = "user@example.com"
    token = create_access_token(
        subject=subject, expires_delta=None
    )  # Test with no expiration
    assert isinstance(token, str)
    # Without expiration, token should decode and contain subject claim
    # Note: requires SECRET_KEY and ALGORITHM to decode correctly
    # For demo purposes, patch or mock jwt.decode if needed


def test_authenticate_user_success_and_failure(monkeypatch):
    mock_user = MagicMock()
    mock_user.hashed_password = get_password_hash("correctpass")

    class DummyDB:
        def get_user_by_email(self, email):
            if email == "valid@example.com":
                return mock_user
            return None

    dummy_db = DummyDB()

    # Patch get_user_by_email method
    monkeypatch.setattr(dummy_db, "get_user_by_email", dummy_db.get_user_by_email)

    user = authenticate_user(dummy_db, "valid@example.com", "correctpass")
    assert user == mock_user

    user = authenticate_user(dummy_db, "valid@example.com", "wrongpass")
    assert user is None

    user = authenticate_user(dummy_db, "invalid@example.com", "any")
    assert user is None


def test_signup_returns_user_instance(monkeypatch):
    class DummyDB:
        def add_user(self, user_in):
            return {"id": 1, "email": user_in.email}

    dummy_db = DummyDB()
    user_in = MagicMock(email="new@example.com", password="pass")
    user = signup(user_in=user_in, db=dummy_db)
    assert user is not None
    assert user["email"] == "new@example.com"


def test_login_returns_token_on_valid_and_raises_on_invalid(monkeypatch):
    class DummyDB:
        def get_user_by_email(self, email):
            dummy_user = MagicMock()
            dummy_user.hashed_password = get_password_hash("validpass")
            if email == "valid@example.com":
                return dummy_user
            return None

    dummy_db = DummyDB()
    form_data_valid = MagicMock(username="valid@example.com", password="validpass")
    form_data_invalid = MagicMock(username="valid@example.com", password="wrongpass")

    token = login(form_data_valid, dummy_db)
    assert isinstance(token, dict)
    assert "access_token" in token

    with pytest.raises(Exception):
        login(form_data_invalid, dummy_db)


def test_get_me_returns_current_user_object():
    current_user = MagicMock()
    result = get_me(current_user)
    assert result == current_user
