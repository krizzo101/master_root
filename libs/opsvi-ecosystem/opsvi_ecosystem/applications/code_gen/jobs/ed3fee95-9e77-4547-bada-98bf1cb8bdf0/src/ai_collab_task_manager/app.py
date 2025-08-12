import logging
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_bcrypt import Bcrypt
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_socketio import SocketIO, join_room, leave_room
from flask_wtf.csrf import CSRFProtect

from .ai_service import AIService
from .audit_log import audit_log_event
from .calendar import GoogleCalendarService
from .config import Config
from .forms import CommentForm, LoginForm, RegisterForm, TaskForm
from .models import (
    Comment,
    Notification,
    Task,
    Team,
    TimeEntry,
    User,
    db,
)
from .reporting import ReportingService

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Load secrets from .env ---
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
csrf = CSRFProtect(app)
bcrypt = Bcrypt(app)
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

# --- Login Manager ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

ai_service = AIService(api_key=Config.OPENAI_API_KEY)
calendar_service = GoogleCalendarService()
reporting_service = ReportingService()


# --- User Loader ---
@login_manager.user_loader
def load_user(user_id: str) -> Any:
    return User.query.get(int(user_id))


# --- Error Handlers ---
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


# --- Index / Auth Views ---
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            audit_log_event(f"User login: {user.email}", user.id)
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password", "danger")
    return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(
            email=form.email.data, username=form.username.data, password_hash=hashed_pw
        )
        db.session.add(user)
        db.session.commit()
        audit_log_event(f"User registered: {user.email}", user.id)
        flash("Account created! You may log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/logout")
@login_required
def logout():
    audit_log_event(f"User logout: {current_user.email}", current_user.id)
    logout_user()
    return redirect(url_for("index"))


# --- Dashboard / Task Management ---
@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin:
        teams = Team.query.all()
    else:
        teams = current_user.teams
    tasks = (
        Task.query.order_by(Task.due_date.asc())
        .filter(Task.team_id.in_([t.id for t in teams]))
        .all()
    )
    notifications = Notification.query.filter_by(user_id=current_user.id).all()
    return render_template(
        "dashboard.html", tasks=tasks, teams=teams, notifications=notifications
    )


@app.route("/task/new", methods=["GET", "POST"])
@login_required
def new_task():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            team_id=form.team.data,
            created_by_id=current_user.id,
        )
        db.session.add(task)
        db.session.commit()
        ai_service.schedule_ai_prio_and_estimate(task.id)
        audit_log_event(f"Created task: {task.title}", current_user.id)
        flash(
            "Task created successfully! AI will optimize scheduler and estimates soon.",
            "success",
        )
        socketio.emit(
            "task_created", {"task_id": task.id, "title": task.title}, broadcast=True
        )
        return redirect(url_for("dashboard"))
    return render_template("task_form.html", form=form)


@app.route("/task/<int:task_id>", methods=["GET", "POST"])
@login_required
def view_task(task_id: int):
    task = Task.query.get_or_404(task_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            task_id=task_id, author_id=current_user.id, content=form.content.data
        )
        db.session.add(comment)
        db.session.commit()
        audit_log_event(f"Added comment on task {task.title}", current_user.id)
        socketio.emit(
            "comment_added",
            {
                "task_id": task.id,
                "author": current_user.username,
                "content": comment.content,
            },
            room=f"task_{task.id}",
        )
        flash("Comment added.", "success")
        return redirect(url_for("view_task", task_id=task_id))
    comments = (
        Comment.query.filter_by(task_id=task_id)
        .order_by(Comment.timestamp.desc())
        .all()
    )
    time_entries = TimeEntry.query.filter_by(task_id=task_id).all()
    return render_template(
        "task_detail.html",
        task=task,
        comments=comments,
        form=form,
        time_entries=time_entries,
    )


@app.route("/task/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id: int):
    task = Task.query.get_or_404(task_id)
    if not current_user.is_admin and task.created_by_id != current_user.id:
        abort(403)
    form = TaskForm(obj=task)
    if form.validate_on_submit():
        form.populate_obj(task)
        db.session.commit()
        ai_service.schedule_ai_prio_and_estimate(task.id)
        audit_log_event(f"Edited task: {task.title}", current_user.id)
        flash("Task updated!", "success")
        return redirect(url_for("view_task", task_id=task_id))
    return render_template("task_form.html", form=form, task=task)


@app.route("/task/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id: int):
    task = Task.query.get_or_404(task_id)
    if not current_user.is_admin and task.created_by_id != current_user.id:
        abort(403)
    db.session.delete(task)
    db.session.commit()
    audit_log_event(f"Deleted task: {task.title}", current_user.id)
    flash("Task deleted!", "success")
    return redirect(url_for("dashboard"))


# --- Time Tracking ---
@app.route("/task/<int:task_id>/time/start", methods=["POST"])
@login_required
def start_timer(task_id: int):
    task = Task.query.get_or_404(task_id)
    entry = TimeEntry(
        user_id=current_user.id, task_id=task_id, start_time=datetime.utcnow()
    )
    db.session.add(entry)
    db.session.commit()
    audit_log_event(f"Started timer on task {task.title}", current_user.id)
    socketio.emit(
        "timer_started",
        {"task_id": task.id, "user_id": current_user.id},
        room=f"task_{task.id}",
    )
    return redirect(url_for("view_task", task_id=task_id))


@app.route("/task/<int:task_id>/time/stop", methods=["POST"])
@login_required
def stop_timer(task_id: int):
    entry = (
        TimeEntry.query.filter_by(
            user_id=current_user.id, task_id=task_id, end_time=None
        )
        .order_by(TimeEntry.start_time.desc())
        .first()
    )
    if entry:
        entry.end_time = datetime.utcnow()
        db.session.commit()
        audit_log_event(f"Stopped timer on task {entry.task_id}", current_user.id)
        socketio.emit(
            "timer_stopped",
            {"task_id": task_id, "user_id": current_user.id},
            room=f"task_{task_id}",
        )
    return redirect(url_for("view_task", task_id=task_id))


# --- Progress Reporting ---
@app.route("/reports")
@login_required
def reports():
    report_data = reporting_service.generate_user_report(current_user)
    return render_template("reports.html", report=report_data)


# --- Calendar Integration ---
@app.route("/calendar/sync")
@login_required
def sync_calendar():
    # Dummy: In real code, check user tokens, ask for OAuth, sync
    try:
        synced = calendar_service.sync_user_tasks(current_user)
        flash(f'Calendar synced! {"Success" if synced else "No update"}', "success")
    except Exception:
        logger.exception("Calendar sync failed")
        flash("Failed to sync calendar", "danger")
    return redirect(url_for("dashboard"))


# --- Real-time Collaboration (Socket.IO) ---
@socketio.on("join_task")
def handle_join_task(data):
    room = f'task_{data["task_id"]}'
    join_room(room)
    logger.debug(f"User joined room {room}")


@socketio.on("leave_task")
def handle_leave_task(data):
    room = f'task_{data["task_id"]}'
    leave_room(room)
    logger.debug(f"User left room {room}")


# --- Run this for Flask CLI and Gunicorn ---
def create_app() -> Flask:
    """
    Factory for Flask app (for Gunicorn or CLI)
    """
    return app


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
