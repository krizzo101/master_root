"""
FastAPI API routers: project CRUD, file upload, report fetch, etc.
"""
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth import get_current_active_user
from app.db import get_db
from app.models import File as FileModel
from app.models import Project, Report, User
from app.schemas import (
    Msg,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    ReportRead,
)
from app.storage import save_upload_file
from app.tasks import analyze_code_task

logger = logging.getLogger("api")

router = APIRouter()


# --- Projects ---
@router.post("/projects", response_model=ProjectRead)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create project for current user."""
    project = Project(
        name=project_in.name,
        description=project_in.description,
        user_id=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    logger.info(f"Project created: {project.name}")
    return project


@router.get("/projects", response_model=list[ProjectRead])
def list_projects(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """List all projects for current user."""
    projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    return projects


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(404, detail="Project not found")
    return project


@router.put("/projects/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(404, detail="Project not found")
    for k, v in project_in.dict(exclude_unset=True).items():
        setattr(project, k, v)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/projects/{project_id}", response_model=Msg)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(404, detail="Project not found")
    db.delete(project)
    db.commit()
    return Msg(msg="Project deleted")


# --- File Upload / Code Analysis ---
@router.post("/projects/{project_id}/upload", response_model=Msg)
def upload_python_code(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(404, detail="Project not found")
    if not file.filename.endswith(".py"):
        raise HTTPException(400, detail="Only .py files supported")
    path = save_upload_file(file, subdir=f"user{current_user.id}")
    new_file = FileModel(
        filename=file.filename,
        file_path=path,
        project_id=project_id,
        uploader_id=current_user.id,
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    # Create initial report entry & enqueue celery
    report = Report(project_id=project_id, file_id=new_file.id, source_type="upload")
    db.add(report)
    db.commit()
    db.refresh(report)
    analyze_code_task.delay(report.id, path)
    return Msg(msg="File uploaded and analysis queued.")


# --- Reports ---
@router.get("/projects/{project_id}/reports", response_model=list[ReportRead])
def list_project_reports(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(404, detail="Project not found")
    reports = db.query(Report).filter(Report.project_id == project_id).all()
    return reports


@router.get("/reports/{report_id}", response_model=ReportRead)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, detail="Report not found")
    project = db.query(Project).filter(Project.id == report.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(404, detail="Project/report does not belong to you")
    return report


@router.get("/reports/{report_id}/html", response_model=Msg)
def download_report_html(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or not report.detailed_report_path:
        raise HTTPException(404, detail="Report HTML not found")
    project = db.query(Project).filter(Project.id == report.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(403, detail="No access")
    return Msg(msg=report.detailed_report_path)
