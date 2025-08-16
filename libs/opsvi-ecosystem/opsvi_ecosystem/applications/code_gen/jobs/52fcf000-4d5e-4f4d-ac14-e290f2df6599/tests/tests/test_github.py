from unittest.mock import MagicMock

import pytest
from app.github import (
    github_analyze,
    github_list_repos,
    github_oauth_callback,
    github_oauth_login,
)


def test_github_oauth_login_redirects_to_github():
    resp = github_oauth_login()
    # Assuming it returns a RedirectResponse or url string
    # Check string or attribute 'location' in response
    if hasattr(resp, "headers"):
        location = resp.headers.get("location")
        assert location and "github" in location
    else:
        assert isinstance(resp, str)
        assert "github" in resp


def test_github_oauth_callback_success_and_error(monkeypatch):
    dummy_db = MagicMock()
    dummy_user = MagicMock()

    # Success case
    monkeypatch.setattr("app.github.exchange_code_for_token", lambda code: "faketoken")
    monkeypatch.setattr(
        "app.github.get_user_from_github", lambda token: {"login": "user"}
    )

    result = github_oauth_callback("code", dummy_db, dummy_user)
    assert result is not None

    # Simulate error by patching exchange to raise
    def raise_exc(code):
        raise Exception("OAuth failed")

    monkeypatch.setattr("app.github.exchange_code_for_token", raise_exc)
    with pytest.raises(Exception):
        github_oauth_callback("code", dummy_db, dummy_user)


def test_github_list_repos_returns_list(monkeypatch):
    dummy_db = MagicMock()
    dummy_user = MagicMock()
    monkeypatch.setattr(
        "app.github.get_repos_for_user", lambda db, user: [{"id": 1, "name": "repo1"}]
    )
    repos = github_list_repos(dummy_db, dummy_user)
    assert isinstance(repos, list)
    assert "id" in repos[0]
    assert "name" in repos[0]


def test_github_analyze_triggers_analysis(monkeypatch):
    dummy_db = MagicMock()
    dummy_user = MagicMock()
    req = MagicMock()
    req.repo_full_name = "user/repo"

    monkeypatch.setattr(
        "app.github.clone_and_analyze_repo", lambda req, db, user: {"score": 90}
    )

    result = github_analyze(req, dummy_db, dummy_user)
    assert "score" in result
