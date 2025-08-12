"""
AI Integration logic using OpenAI o3 and o4-mini models for prioritizing, estimating, dependency-detecting, and scheduling tasks.
"""
from backend.config import get_settings
from backend.models import Task, Dependency
from sqlalchemy.orm import Session
import logging
import openai

settings = get_settings()
logger = logging.getLogger("taskmgmt.ai")
openai.api_key = settings.openai_api_key


# Prioritize tasks (lower int = higher priority)
def prioritize_tasks(db: Session, tasks: list, user):
    task_dicts = [{"id": t.id, "title": t.title, "desc": t.description} for t in tasks]
    try:
        prompt = f"Prioritize these tasks for project. Output a JSON mapping of task ID to integer priority (0=highest): {task_dicts}"
        resp = openai.ChatCompletion.create(
            model="o3", messages=[{"role": "user", "content": prompt}]
        )
        priorities = resp.choices[0].message["content"]
        import json

        priorities = json.loads(priorities)
        for t in tasks:
            if t.id in priorities:
                t.priority = priorities[t.id]
        db.commit()
    except Exception as e:
        logger.exception("AI prioritize failed")


def estimate_duration(db: Session, task: Task):
    try:
        prompt = f"Estimate in hours how long it will take to complete this task: Title: {task.title}; Description: {task.description}. Return only the number."
        resp = openai.ChatCompletion.create(
            model="o4-mini", messages=[{"role": "user", "content": prompt}]
        )
        est = resp.choices[0].message["content"]
        task.estimated_duration = float(est.strip())
        db.commit()
    except Exception as e:
        logger.exception("AI duration estimate failed")


def detect_dependencies(db: Session, project_ids: list):
    # Find potential dependencies between tasks in project(s). Adds new Dependency entries if detected.
    for pid in project_ids:
        tasks = db.query(Task).filter(Task.project_id == pid).all()
        task_dicts = [
            {"id": t.id, "title": t.title, "desc": t.description} for t in tasks
        ]
        prompt = f"Given this list of tasks, output a JSON list of task dependency pairs: [(dependent_id, depends_on_id)] for scheduling: {task_dicts}"
        try:
            resp = openai.ChatCompletion.create(
                model="o4-mini", messages=[{"role": "user", "content": prompt}]
            )
            import json

            deps = json.loads(resp.choices[0].message["content"])
            for dep in deps:
                t, d = dep[0], dep[1]
                db.add(Dependency(task_id=t, depends_on_task_id=d))
            db.commit()
        except Exception as e:
            logger.exception("AI dependency detection failed")


def suggest_schedule(db: Session, project_id: str, user):
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    task_dicts = [
        {
            "id": t.id,
            "title": t.title,
            "priority": t.priority,
            "duration": t.estimated_duration,
        }
        for t in tasks
    ]
    prompt = (
        "Given the following tasks with estimated durations and priorities, and known dependencies, output a JSON-encoded optimal order of execution "
        "to maximize parallelism and minimize project time."
    )
    try:
        resp = openai.ChatCompletion.create(
            model="o3", messages=[{"role": "user", "content": prompt + str(task_dicts)}]
        )
        schedule = resp.choices[0].message["content"]
        import json

        return json.loads(schedule)
    except Exception as e:
        logger.exception("AI scheduling failed")
        return []
