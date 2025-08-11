"""
GitHub OAuth and repo integration endpoints.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.auth import get_current_active_user
from app.db import get_db
from app.models import User
from app.schemas import GitHubRepo, GitHubAnalyzeRequest, Msg
from app.config import settings
import requests
from fastapi.responses import RedirectResponse
import os
from github import Github, GithubException
from typing import List

router = APIRouter()
logger = logging.getLogger("github.integration")

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
github_scope = "repo"


@router.get("/login")
def github_oauth_login():
    """Redirect user to GitHub OAuth authorization."""
    redirect_uri = os.environ.get(
        "GITHUB_CALLBACK_URL", "http://localhost:8000/github/callback"
    )
    url = (
        f"{GITHUB_AUTH_URL}?client_id={settings.GITHUB_CLIENT_ID}&scope={github_scope}"
        f"&redirect_uri={redirect_uri}"
    )
    return RedirectResponse(url)


@router.get("/callback")
def github_oauth_callback(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    GitHub OAuth callback: exchange code for token, store in user.
    """
    try:
        payload = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
        }
        headers = {"Accept": "application/json"}
        r = requests.post(GITHUB_TOKEN_URL, data=payload, headers=headers)
        r.raise_for_status()
        token = r.json().get("access_token")
        if not token:
            raise Exception("GitHub token missing")
        current_user.github_token = token
        db.commit()
        logger.info(f"GitHub token stored for user {current_user.id}")
        return RedirectResponse("/dashboard")
    except Exception as e:
        logger.error(f"GitHub OAuth failed: {e}")
        raise HTTPException(status_code=500, detail="GitHub OAuth failed")


@router.get("/repos", response_model=List[GitHubRepo])
def github_list_repos(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """List authenticated user's GitHub repos."""
    if not current_user.github_token:
        raise HTTPException(403, detail="GitHub not connected.")
    client = Github(current_user.github_token)
    try:
        repos = client.get_user().get_repos()
        repo_list = []
        for repo in repos:
            repo_list.append(
                GitHubRepo(
                    name=repo.name,
                    full_name=repo.full_name,
                    owner=repo.owner.login,
                    description=repo.description,
                    url=repo.html_url,
                )
            )
        return repo_list
    except GithubException as e:
        logger.error(f"Error fetching repos: {e}")
        raise HTTPException(500, detail="Failed to fetch repos")


@router.post("/analyze", response_model=Msg)
def github_analyze(
    req: GitHubAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Download repo code from GitHub, store as temp file/dir, create report, enqueue analysis task.
    """
    if not current_user.github_token:
        raise HTTPException(403, detail="GitHub not connected.")
    client = Github(current_user.github_token)
    try:
        repo = client.get_repo(req.repo_full_name)
        branch = req.branch or repo.default_branch
        temp_dir = f"{settings.UPLOAD_DIR}/github-{current_user.id}-{repo.name}"
        from git import Repo as GitRepo

        # Clone using pygit2 or git - use local shell git for now
        import subprocess

        subprocess.run(
            ["git", "clone", "--branch", branch, "--depth=1", repo.clone_url, temp_dir],
            check=True,
        )
        from app.models import Report

        report = Report(project_id=req.project_id, file_id=None, source_type="github")
        db.add(report)
        db.commit()
        db.refresh(report)
        from app.tasks import analyze_code_task

        analyze_code_task.delay(report.id, temp_dir)
        return Msg(msg=f"Analysis queued for GitHub repo {repo.full_name}")
    except Exception as e:
        logger.error(f"GitHub analyze failed: {e}")
        raise HTTPException(500, detail=str(e))
