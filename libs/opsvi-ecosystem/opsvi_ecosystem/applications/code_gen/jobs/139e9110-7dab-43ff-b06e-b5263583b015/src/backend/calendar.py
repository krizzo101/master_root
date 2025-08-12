"""
Google Calendar integration: bi-directional sync, event creation, OAuth2
"""
from fastapi import APIRouter, Depends, HTTPException
from backend.auth import get_current_user
from backend.models import User, Task
from backend.database import get_db
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from backend.config import get_settings
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

settings = get_settings()
calendar_router = APIRouter()

# Credentials for app (service account flow/simplified demo for single-user dev)
creds = Credentials(
    token=settings.google_refresh_token,
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
)
calendar_api = build("calendar", "v3", credentials=creds)


@calendar_router.post("/push_task/{task_id}", response_model=dict)
def push_task_to_calendar(
    task_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    task = db.query(Task).get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    event = {
        "summary": task.title,
        "description": task.description,
        "start": {"dateTime": task.due_date.isoformat(), "timeZone": "UTC"},
        "end": {
            "dateTime": (
                task.due_date + timedelta(hours=task.estimated_duration or 1)
            ).isoformat(),
            "timeZone": "UTC",
        },
        "attendees": [{"email": user.email}],
    }
    event = calendar_api.events().insert(calendarId="primary", body=event).execute()
    return {"event_id": event["id"]}
