from .models import Task, TimeEntry
from flask_login import current_user
from collections import defaultdict


def minutes(td) -> int:
    return int(td.total_seconds() // 60) if td else 0


class ReportingService:
    def generate_user_report(self, user):
        """
        Aggregates per-user total/avg time spent, task completion.
        """
        user_tasks = (
            Task.query.join(TaskAssignment)
            .filter(TaskAssignment.user_id == user.id)
            .all()
        )
        tasks_completed = [task for task in user_tasks if task.completed]
        time_entries = TimeEntry.query.filter_by(user_id=user.id).all()

        total_minutes = 0
        for entry in time_entries:
            if entry.end_time:
                total_minutes += minutes(entry.end_time - entry.start_time)
        completion_percentage = (
            (len(tasks_completed) / len(user_tasks) * 100) if user_tasks else 0
        )
        summary = {
            "username": user.username,
            "total_tasks": len(user_tasks),
            "completed": len(tasks_completed),
            "completion_percent": round(completion_percentage, 1),
            "total_time_spent": total_minutes,
        }
        return summary
