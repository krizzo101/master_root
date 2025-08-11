"""
Web UI endpoints for login, sign up, dashboard, and report view pages with Jinja2.
"""
import logging
from fastapi import APIRouter, Request, Depends, Form, status, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.exc import UnknownHashError
from app.db import get_db
from app.auth import get_password_hash, authenticate_user, get_current_active_user
from app.models import User, Project, Report
from app.config import settings

logger = logging.getLogger("views")

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def require_auth(request: Request):
    user = request.session.get("user")
    if not user:
        raise RedirectResponse("/login")
    return user


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/signup", response_class=HTMLResponse)
def signup_get(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/signup", response_class=HTMLResponse)
def signup_post(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    try:
        existing = (
            db.query(User)
            .filter((User.username == username) | (User.email == email))
            .first()
        )
        if existing:
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "error": "Email or username already registered."},
            )
        user = User(
            username=username, email=email, hashed_password=get_password_hash(password)
        )
        db.add(user)
        db.commit()
        request.session["user"] = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
        return RedirectResponse("/dashboard", status_code=302)
    except Exception as e:
        logger.error(f"Signup error: {e}")
        return templates.TemplateResponse(
            "signup.html", {"request": request, "error": "Error during signup."}
        )


@router.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
def login_post(
    request: Request,
    db: Session = Depends(get_db),
    email: str = Form(...),
    password: str = Form(...),
):
    user = authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Invalid email or password."}
        )
    request.session["user"] = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
    }
    return RedirectResponse("/dashboard", status_code=302)


@router.get("/logout", response_class=HTMLResponse)
def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse("/", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user_data = request.session.get("user")
    if not user_data:
        return RedirectResponse("/login", status_code=302)
    user = db.query(User).filter(User.id == user_data["id"]).first()
    projects = db.query(Project).filter(Project.user_id == user.id).all()
    # Recent reports
    reports = (
        db.query(Report)
        .join(Project, Report.project_id == Project.id)
        .filter(Project.user_id == user.id)
        .order_by(Report.created_at.desc())
        .limit(5)
        .all()
    )
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user, "projects": projects, "reports": reports},
    )


@router.get("/projects/{project_id}/reports/{report_id}", response_class=HTMLResponse)
def view_report(
    request: Request, project_id: int, report_id: int, db: Session = Depends(get_db)
):
    user_data = request.session.get("user")
    if not user_data:
        return RedirectResponse("/login", status_code=302)
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or report.project_id != int(project_id):
        raise HTTPException(404)
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj or proj.user_id != user_data["id"]:
        raise HTTPException(404)
    detailed_path = report.detailed_report_path
    if not detailed_path or not os.path.exists(detailed_path):
        return templates.TemplateResponse(
            "report_unavailable.html",
            {"request": request, "error": "Report not yet available."},
        )
    with open(detailed_path, encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(content=html)
