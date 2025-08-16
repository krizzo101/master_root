import pytest
from app.schemas import (
    GitHubAnalyzeRequest,
    GitHubRepo,
    Msg,
    ProjectCreate,
    ProjectUpdate,
    Token,
    TokenData,
    UserCreate,
    UserLogin,
)
from pydantic import ValidationError


def test_user_create_validation_and_fields():
    data = {"email": "user@example.com", "password": "pass123", "name": "User"}
    user = UserCreate(**data)
    assert user.email == "user@example.com"
    # Missing required fields should raise
    with pytest.raises(ValidationError):
        UserCreate(email="user@example.com")


def test_user_login_accepts_valid_fields_and_fails_invalid():
    valid_data = {"email": "login@example.com", "password": "pass123"}
    login_obj = UserLogin(**valid_data)
    assert login_obj.email == "login@example.com"

    with pytest.raises(ValidationError):
        UserLogin(email="bademail")  # Missing password


def test_project_create_and_update_fields_validation():
    create_data = {"name": "My Project", "description": "desc"}
    project_create = ProjectCreate(**create_data)
    assert project_create.name == "My Project"

    update_data = {"name": "Updated", "description": "updated desc"}
    project_update = ProjectUpdate(**update_data)
    assert project_update.name == "Updated"


def test_token_and_token_data_schemas():
    token_data = {"access_token": "token", "token_type": "bearer"}
    token = Token(**token_data)
    assert token.access_token == "token"

    token_sub = {"sub": "user@example.com"}
    tokendata = TokenData(**token_sub)
    assert tokendata.sub == "user@example.com"


def test_msg_schema_accepts_message_field():
    msg = Msg(message="Hello")
    assert msg.message == "Hello"


def test_githubrepo_and_analyze_request_schemas():
    repo_data = {"id": 1, "name": "repo"}
    repo = GitHubRepo(**repo_data)
    assert repo.name == "repo"

    req_data = {"repo_full_name": "user/repo"}
    req = GitHubAnalyzeRequest(**req_data)
    assert req.repo_full_name == "user/repo"
