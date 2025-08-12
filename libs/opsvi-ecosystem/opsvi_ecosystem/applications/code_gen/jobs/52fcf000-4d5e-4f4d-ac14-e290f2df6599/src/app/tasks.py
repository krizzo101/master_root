"""
Celery worker tasks for asynchronous code analysis.
Handles code report creation, status, and report persistence.
"""
import os
import logging
from celery import Celery
from sqlalchemy.orm import Session
from app.config import settings
from app.db import SessionLocal
from app.models import Report, File
from app.code_analysis import analyze_code
from app.report_generation import generate_report_file, calculate_score

celery = Celery(
    "tasks", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND
)
logger = logging.getLogger("celery.tasks")


@celery.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=2)
def analyze_code_task(self, report_id: int, file_path: str):
    """
    Celery task: run code analyzers, persist report, update status.
    """
    logger.info(f"[analyze_code_task] Report {report_id}: Analyzing file {file_path}")
    db: Session = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise Exception("Report not found")
        report.status = "in_progress"
        db.commit()
        results = analyze_code(file_path)
        suggestions = generate_suggestions(results)
        score = calculate_score(results)
        html_report_path = generate_report_file(results, report_id)
        report.issues = results
        report.suggestions = suggestions
        report.status = "completed"
        report.score = score
        report.detailed_report_path = html_report_path
        report.summary = f"Analysis completed. Score: {score}/100"
        db.commit()
        logger.info(f"[analyze_code_task] Report {report_id}: Done.")
    except Exception as e:
        logger.error(f"Analyze code task failed: {e}")
        if report:
            report.status = "failed"
            report.summary = str(e)
            db.commit()
        raise
    finally:
        db.close()
    return True


def generate_suggestions(results: dict) -> dict:
    """
    Generate actionable suggestions for each category.
    """
    suggestions = {}
    # Security
    suggestions["security"] = []
    for issue in results.get("security", []):
        suggestion = issue.get("issue_text") or issue.get("error")
        if suggestion:
            suggestions["security"].append(suggestion)
    # Quality
    q = results.get("quality", {}).get("issues", [])
    suggestions["quality"] = list({i.get("message") for i in q if i.get("message")})
    # Complexity
    suggestions["complexity"] = []
    for file, funcs in (
        results.get("complexity", {}).items()
        if hasattr(results.get("complexity", {}), "items")
        else []
    ):
        for entry in funcs:
            if entry.get("rank") and entry["rank"] not in {"A", "B", "C"}:
                suggestions["complexity"].append(
                    f"High complexity in {file}:{entry['name']} (rank {entry['rank']})"
                )
    # Style
    st = results.get("style", [])
    suggestions["style"] = [s.get("violation") or str(s) for s in st]
    # Performance
    suggestions["performance"] = [
        i.get("suggestion")
        for i in results.get("performance", [])
        if i.get("suggestion")
    ]
    return suggestions
