import logging
from datetime import datetime
from threading import Thread
from typing import Any

from openai import OpenAI

from .audit_log import audit_log_event
from .models import Task, db


def anonymize_task_data(task: Task) -> dict[str, Any]:
    return {
        "title": task.title,
        "description": "",  # remove sensitive text
        "due_date": task.due_date.isoformat() if task.due_date else "",
        "team_id": task.team_id,
        "created_at": task.created_at.isoformat() if task.created_at else "",
    }


class AIService:
    """
    Handles communication with OpenAI API (o3, o4-mini models) for auto-prioritization,
    time estimations, dependency resolution, and optimal scheduling suggestion.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = logging.getLogger("AIService")
        self.ai_client = OpenAI(api_key=self.api_key)

    def schedule_ai_prio_and_estimate(self, task_id: int) -> None:
        t = Thread(target=self._invoke_ai_for_task, args=(task_id,))
        t.daemon = True
        t.start()

    def _invoke_ai_for_task(self, task_id: int) -> None:
        task = Task.query.get(task_id)
        if not task:
            self.logger.error("Task not found for AI processing")
            return
        anon_data = anonymize_task_data(task)
        prompt = (
            f"Given the following anonymized task info: {anon_data}. "
            "Estimate the task priority (1-5), expected time (in minutes), "
            "and list any dependencies known (comma-separated task IDs). Output as JSON."
        )
        try:
            response = self.ai_client.completions.create(
                model="o3", prompt=prompt, max_tokens=150, temperature=0.2
            )
            # Example return: {'priority': 2, 'estimated_time_minutes': 45, 'dependencies': ''}
            ai_json = self._parse_ai_response(response.choices[0].text)

            task.priority = ai_json.get("priority", 3)
            task.estimated_time_minutes = ai_json.get("estimated_time_minutes", 60)
            task.dependencies = ai_json.get("dependencies", "")
            task.updated_at = datetime.utcnow()
            db.session.commit()
            audit_log_event(f"AI updated task: {task.title}", task.created_by_id)
        except Exception as e:
            self.logger.error(f"AI scheduling failed for task {task_id} - {e}")

    def _parse_ai_response(self, text: str) -> dict[str, Any]:
        import json
        import re

        # Attempt to extract valid JSON from AI output
        try:
            match = re.search(r"{.*}", text, re.DOTALL)
            data = json.loads(match.group(0))
            return data
        except Exception:
            self.logger.warning(
                "AI response could not be parsed. Falling back to defaults."
            )
            return {"priority": 3, "estimated_time_minutes": 60, "dependencies": ""}
