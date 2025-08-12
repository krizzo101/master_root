"""
API CRUD and business logic endpoints for projects, tasks, comments, users, time entries, dashboards, reporting.
"""
import logging

from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.orm import Session

from backend.ai import (
    detect_dependencies,
    estimate_duration,
    prioritize_tasks,
    suggest_schedule,
)
from backend.audit import log_audit
from backend.auth import get_current_user
from backend.database import get_db
from backend.models import (
    Comment,
    Project,
    Task,
    TaskStatus,
    User,
)

logger = logging.getLogger("taskmgmt.api")
api_router = APIRouter()

# ... (CRUD Endpoints for Project, Task, Comment, TimeEntry, File, etc.) ...


# ----------- PROJECTS -----------
@api_router.get("/projects", response_model=list)
def list_projects(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    projects = (
        db.query(Project)
        .filter((Project.owner_id == user.id) | (user.role == "admin"))
        .all()
    )
    return [
        {"id": p.id, "name": p.name, "description": p.description} for p in projects
    ]


@api_router.post("/projects", response_model=dict)
def create_project(
    data: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    project = Project(
        name=data["name"], description=data.get("description", ""), owner_id=user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    log_audit("project_create", user.id, "project", project.id)
    return {"id": project.id, "name": project.name}


# ----------- TASKS -----------
@api_router.get("/projects/{project_id}/tasks", response_model=list)
def list_tasks(
    project_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    result = [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "assignee_id": t.assignee_id,
            "due_date": t.due_date,
            "estimated_duration": t.estimated_duration,
        }
        for t in tasks
    ]
    return result


@api_router.post("/projects/{project_id}/tasks", response_model=dict)
def create_task(
    project_id: str,
    data: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = Task(
        project_id=project_id,
        title=data["title"],
        description=data.get("description", ""),
        assignee_id=data.get("assignee_id"),
        status=TaskStatus.TODO,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    # AI enrichment (priority, estimate, deps)
    prioritize_tasks(db, [task], user)
    estimate_duration(db, task)
    detect_dependencies(db, [task.project_id])
    log_audit("task_create", user.id, "task", task.id)
    return {"id": task.id, "title": task.title}


# ----------- AI SCHEDULER -----------
@api_router.post("/projects/{project_id}/suggest_schedule", response_model=dict)
def schedule_suggest(
    project_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    schedule = suggest_schedule(db, project_id=project_id, user=user)
    return {"project_id": project_id, "schedule": schedule}


# ----------- Comments & Mentions -----------
@api_router.post("/tasks/{task_id}/comments", response_model=dict)
def add_comment(
    task_id: str,
    data: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    comment = Comment(
        task_id=task_id,
        user_id=user.id,
        content=data["content"],
        mentions=",".join(data.get("mentions", [])),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    log_audit("comment_add", user.id, "comment", comment.id)
    return {"id": comment.id}


# ... Time Tracking, File Sharing, Dashboard, etc. follow similar pattern ...
