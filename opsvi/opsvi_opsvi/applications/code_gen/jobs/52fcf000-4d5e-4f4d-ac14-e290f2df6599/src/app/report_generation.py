"""
Generates HTML report files from analysis results and calculates code score.
"""
from typing import Any, Dict
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
from app.config import settings
import logging
import pandas as pd

logger = logging.getLogger("report_generation")

env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


def generate_report_file(results: Dict[str, Any], report_id: int) -> str:
    """
    Generates HTML report from analysis results using Jinja2 and saves it to UPLOAD_DIR/reports/report-{id}.html
    """
    template = env.get_template("report.html")
    html = template.render(results=results, report_id=report_id)
    reports_dir = os.path.join(settings.UPLOAD_DIR, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    path = os.path.join(reports_dir, f"report-{report_id}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info(f"Generated report HTML: {path}")
    return path


def calculate_score(results: Dict[str, Any]) -> int:
    """
    Calculate a single code quality score from all categories, between 0-100.
    Uses a basic weighted formula on #issues and their severity/importance per tool.
    """
    score = 100
    # Security
    n_sec = len(results.get("security", []))
    score -= 10 * min(n_sec, 5)
    # Quality
    n_qual = len(results.get("quality", {}).get("issues", []))
    score -= 5 * min(n_qual, 10)
    # Complexity
    n_cplx = 0
    for f in results.get("complexity", []) or []:
        for func in results["complexity"].get(f, []):
            if func.get("rank") == "F":
                n_cplx += 1
    score -= 6 * min(n_cplx, 5)
    # Style
    n_style = len(results.get("style", []))
    score -= 4 * min(n_style, 10)
    # Performance
    n_perf = len(results.get("performance", []))
    score -= 5 * min(n_perf, 4)
    return max(score, 0)
