import pytest
from backend.auth import (
    verify_password,
    hash_password,
    get_user,
    authenticate,
    create_access_token,
    decode_access_token,
    require_role,
    register_user,
    login,
    TokenData,
)
from unittest.mock import MagicMock
from datetime import timedelta


@pytest.fixture
async def fake_db():
    class FakeDB:
        users = {}

        async def get_user_by_email(self, email):
            return self.users.get(email)

        async def add_user(self, user):
            self.users[user["email"]] = user

    return FakeDB()


def test_hash_password_and_verify_password():
    password = "SecurePass123!"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPass", hashed) is False


@pytest.mark.asyncio
def test_get_user_returns_user_when_exists(fake_db):
    user_data = {"email": "user@example.com", "hashed_password": "hash", "role": "user"}
    fake_db.users[user_data["email"]] = user_data
    user = (
        pytest.run(asyncio.run(get_user(user_data["email"], fake_db)))
        if hasattr(pytest, "run")
        else None
    )
    import asyncio

    user = asyncio.run(get_user(user_data["email"], fake_db))
    assert user == user_data


@pytest.mark.asyncio
def test_authenticate_returns_user_on_valid_credentials(fake_db):
    password = "MySecretPass"
    hashed_pw = hash_password(password)
    user_data = {
        "email": "auth@example.com",
        "hashed_password": hashed_pw,
        "role": "user",
    }
    fake_db.users[user_data["email"]] = user_data
    import asyncio

    user = asyncio.run(authenticate(user_data["email"], password, fake_db))
    assert user == user_data

    # Wrong password
    user_none = asyncio.run(authenticate(user_data["email"], "wrongpass", fake_db))
    assert user_none is None


def test_create_and_decode_access_token_valid_and_expired():
    data = {"sub": "user123"}
    expires = timedelta(minutes=1)
    token = create_access_token(data, expires)
    decoded = decode_access_token(token)
    assert decoded["sub"] == data["sub"]

    import time

    time.sleep(65)  # Wait to expire
    with pytest.raises(Exception):
        decode_access_token(token)


def test_require_role_decorator_allows_required_role():
    user_mock = MagicMock()
    user_mock.role = "admin"

    required = "admin"
    decorator = require_role(required)

    @decorator
    def secured_function(user):
        return True

    assert secured_function(user_mock) == True


@pytest.mark.parametrize(
    "user_role,required_role",
    [
        ("user", "admin"),
        ("guest", "user"),
    ],
)
def test_require_role_decorator_blocks_unauthorized(user_role, required_role):
    user_mock = MagicMock()
    user_mock.role = user_role
    decorator = require_role(required_role)

    @decorator
    def secured_func(user):
        return True

    with pytest.raises(Exception):
        secured_func(user_mock)


@pytest.mark.asyncio
def test_register_user_creates_user_and_handles_duplicate(fake_db):
    payload = {"email": "newuser@example.com", "password": "pass1", "role": "user"}

    # Register new user
    user = await register_user(payload, fake_db)
    assert user["email"] == payload["email"]

    # Try duplicate
    with pytest.raises(Exception):
        await register_user(payload, fake_db)


@pytest.mark.asyncio
def test_login_returns_token_on_valid_credentials(fake_db):
    from backend.auth import LoginForm

    password = "ValidPass123"
    user_data = {
        "email": "login@example.com",
        "hashed_password": hash_password(password),
        "role": "user",
    }
    fake_db.users[user_data["email"]] = user_data

    form = LoginForm(email=user_data["email"], password=password)
    token = await login(form, fake_db)
    assert isinstance(token["access_token"], str)
    assert token["token_type"] == "bearer"

    # Invalid password raises
    form_bad = LoginForm(email=user_data["email"], password="wrongpass")
    with pytest.raises(Exception):
        await login(form_bad, fake_db)
